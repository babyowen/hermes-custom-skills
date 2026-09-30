#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
claude-code-update-watch: 采集 Claude Code（@anthropic-ai/claude-code）官方发布动态 → JSON。

数据源（只用官方，标准库 urllib，无第三方依赖）：
  1) npm registry packument  —— 权威版本表 + 每个版本的发布时间 + 三个通道（latest/stable/next）
  2) GitHub Releases API     —— 逐版本 changelog 正文（anthropics/claude-code）
  3) 回退：raw CHANGELOG.md  —— GitHub API 不可用时解析同一份 changelog
本机版本探测：claude --version → npm -g → ~/.claude/local → 手写覆盖文件（跨机使用时用）

用法：
  python3 fetch_claude_code_updates.py --days 7 --json      # 给 cron / agent 读
  python3 fetch_claude_code_updates.py --days 7             # 人肉看的摘要
  python3 fetch_claude_code_updates.py --days 7 --json --no-state   # 调试：不写 state
  python3 fetch_claude_code_updates.py --local-version 2.1.270 --json

退出码：0 正常（哪怕部分源失败，JSON 里会有 errors）；1 两个数据源全挂（输出 _run_failed）。
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone

NPM_PACKAGE = "@anthropic-ai/claude-code"
NPM_URL = "https://registry.npmjs.org/%s" % NPM_PACKAGE
GH_REPO = "anthropics/claude-code"
GH_API = "https://api.github.com/repos/%s" % GH_REPO
CHANGELOG_RAW = "https://raw.githubusercontent.com/%s/main/CHANGELOG.md" % GH_REPO
STATE_PATH = os.path.expanduser("~/.hermes/cache/claude-code-update-watch/state.json")
LOCAL_OVERRIDE_PATH = os.path.expanduser("~/.hermes/cache/claude-code-update-watch/local_version.txt")
MAX_VERSIONS_IN_STATE = 60
MAX_BULLETS_PER_VERSION = 60

# 命中 → 破坏性/需注意（只看"强信号"：一般的 "no longer" 出现在改进条目里太常见，会误报）
BREAKING_MARKERS = [
    "breaking", "no longer supported", "removed", "remove the", "deprecat", "renamed",
    "must now", "now requires", "requires a migration", "migration", "default changed",
    "dropped support", "no longer accepts", "no longer works",
]
# 命中 → 行为变更（值得提，但不必拦住升级）
CHANGE_MARKERS = ["improved", "changed", "updated", "reworked", "replaced", "now defaults"]
SECURITY_MARKERS = [
    "security", "vulnerability", "cve-", "sandbox", "credential", "secret",
    "permission", "escape", "injection",
]
# 命中 → 对"自动化 / 脚本化 / 网关"用户影响更大
IMPACT_KEYWORDS = [
    "mcp", "hook", "subagent", "sub-agent", "skill", "slash command", "plugin",
    "headless", "print mode", "-p ", "sdk", "api", "background", "cron", "schedule",
    "model", "sonnet", "opus", "haiku", "context window", "usage limit", "rate limit",
    "cost", "spend", "token", "permission", "settings.json", "config", "npm", "install",
    "update", "node", "windows", "macos", "linux", "ide", "vscode", "jetbrains", "terminal",
]
FIX_MARKERS = ["fixed", "fix ", "fixes", "resolved", "repair", "no longer crashes", "no longer fails"]
FEATURE_MARKERS = ["added", "new ", "introduced", "introduces", "support for", "supports", "now shows", "can now"]
NOISE_PATTERNS = [
    "full changelog", "release date", "measured at commit", "contributor credits",
    "<!---", "-->",
]


# ------------------------------------------------------------------ 工具

def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _http(url: str, headers: dict | None = None, timeout: int = 60, retries: int = 2):
    """GET → (bytes, error_str)。失败返回 (None, '错误描述')。"""
    last = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers=headers or {"User-Agent": "claude-code-update-watch/1.0"})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.read(), None
        except urllib.error.HTTPError as exc:
            last = "HTTP %s %s" % (exc.code, exc.reason)
            if exc.code in (403, 429) and attempt == 0:  # 限流，等一下再试
                time.sleep(3)
                continue
            return None, last
        except Exception as exc:  # noqa: BLE001
            last = "%s: %s" % (type(exc).__name__, str(exc)[:150])
            time.sleep(1.5)
    return None, last


def _run(cmd, timeout=25):
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return (p.stdout or "").strip(), (p.stderr or "").strip(), p.returncode
    except Exception as exc:  # noqa: BLE001
        return "", str(exc), 1


def _parse_version(v: str):
    m = re.match(r"^v?(\d+)\.(\d+)\.(\d+)", str(v or "").strip())
    return tuple(int(x) for x in m.groups()) if m else None


def _vkey(v: str):
    p = _parse_version(v)
    return p if p else (0, 0, 0)


def _iso(ts):
    """npm 的 ISO 时间 → aware datetime；失败返回 None。"""
    try:
        return datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
    except Exception:  # noqa: BLE001
        return None


def _strip_md(s: str) -> str:
    s = re.sub(r"`([^`]*)`", r"\1", s)
    s = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", s)
    s = re.sub(r"\*\*([^*]+)\*\*", r"\1", s)
    s = re.sub(r"^\s*[-*]\s+", "", s)
    return re.sub(r"\s+", " ", s).strip()


def _classify(bullet: str) -> str:
    """按"开头动词"定主类，再补标记——避免 "Fixed … are no longer …" 被误判成破坏性变更。"""
    low = bullet.lower()
    is_fix = bool(re.match(r"^(fixed|fixes|fix|repaired|resolved|restored|corrected)\b", low))
    if is_fix:
        return "security" if any(m in low for m in SECURITY_MARKERS) else "fix"
    if any(m in low for m in BREAKING_MARKERS):
        return "breaking"
    if any(m in low for m in SECURITY_MARKERS):
        return "security"
    if any(m in low for m in FEATURE_MARKERS):
        return "feature"
    if any(m in low for m in CHANGE_MARKERS):
        return "change"
    return "other"


# ------------------------------------------------------------------ 采集

def fetch_npm() -> tuple[dict, str | None]:
    raw, err = _http(NPM_URL, headers={"User-Agent": "claude-code-update-watch/1.0", "Accept": "application/json"})
    if raw is None:
        return {}, err
    try:
        d = json.loads(raw.decode("utf-8", "replace"))
    except Exception as exc:  # noqa: BLE001
        return {}, "packument JSON 解析失败: %s" % exc
    return d, None


def fetch_releases(per_page: int = 25) -> tuple[dict, str | None]:
    """GitHub Releases → {version: {body, published_at, url, prerelease}}。"""
    tok = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    headers = {
        "User-Agent": "claude-code-update-watch/1.0",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if tok:
        headers["Authorization"] = "Bearer %s" % tok
    raw, err = _http("%s/releases?per_page=%d" % (GH_API, per_page), headers=headers)
    if raw is None:
        return {}, err
    try:
        rels = json.loads(raw.decode("utf-8", "replace"))
    except Exception as exc:  # noqa: BLE001
        return {}, "releases JSON 解析失败: %s" % exc
    out = {}
    for r in rels if isinstance(rels, list) else []:
        tag = str(r.get("tag_name") or "").lstrip("v")
        if not tag or r.get("draft"):
            continue
        out[tag] = {
            "body": r.get("body") or "",
            "published_at": r.get("published_at"),
            "url": r.get("html_url"),
            "prerelease": bool(r.get("prerelease")),
        }
    return out, None


def fetch_changelog() -> tuple[dict, str | None]:
    """回退：解析 raw CHANGELOG.md → {version: bullets[]}（无发布时间）。"""
    raw, err = _http(CHANGELOG_RAW)
    if raw is None:
        return {}, err
    txt = raw.decode("utf-8", "replace")
    out = {}
    cur = None
    for line in txt.split("\n"):
        m = re.match(r"^##\s+v?([0-9][0-9.]*)\s*$", line.strip())
        if m:
            cur = m.group(1)
            out[cur] = []
            continue
        if cur and re.match(r"^\s*[-*]\s+\S", line):
            out[cur].append(_strip_md(line))
    return {k: v for k, v in out.items() if v}, None


def detect_local_version() -> dict:
    """本机 Claude Code 版本：claude CLI → npm 全局 → ~/.claude/local → 覆盖文件。"""
    out, err, rc = _run(["bash", "-lc", "command -v claude && claude --version"])
    if rc == 0 and out:
        m = re.search(r"(\d+\.\d+\.\d+)", out)
        if m:
            return {"version": m.group(1), "source": "claude --version", "raw": out.split("\n")[0][:120]}
    for npm in ("npm", os.path.expanduser("~/.hermes/node/bin/npm")):
        out, _, rc = _run([npm, "ls", "-g", "--depth=0", NPM_PACKAGE, "--json"], timeout=40)
        if rc == 0 and out:
            try:
                d = json.loads(out)
                v = (d.get("dependencies") or {}).get(NPM_PACKAGE, {}).get("version")
                if v:
                    return {"version": v, "source": "npm ls -g", "raw": None}
            except Exception:  # noqa: BLE001
                pass
    pkg = os.path.expanduser("~/.claude/local/node_modules/%s/package.json" % NPM_PACKAGE)
    if os.path.exists(pkg):
        try:
            v = json.load(open(pkg, encoding="utf-8")).get("version")
            if v:
                return {"version": v, "source": "~/.claude/local", "raw": None}
        except Exception:  # noqa: BLE001
            pass
    if os.path.exists(LOCAL_OVERRIDE_PATH):
        try:
            v = open(LOCAL_OVERRIDE_PATH, encoding="utf-8").read().strip()
            if v:
                return {"version": v, "source": LOCAL_OVERRIDE_PATH, "raw": None}
        except Exception:  # noqa: BLE001
            pass
    return {"version": None, "source": "not_detected", "raw": None}


# ------------------------------------------------------------------ state

def load_state() -> dict:
    try:
        with open(STATE_PATH, encoding="utf-8") as fh:
            d = json.load(fh)
        return d if isinstance(d, dict) else {}
    except Exception:  # noqa: BLE001
        return {}


def save_state(state: dict) -> None:
    os.makedirs(os.path.dirname(STATE_PATH), exist_ok=True)
    tmp = STATE_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(state, fh, ensure_ascii=False, indent=1)
    os.replace(tmp, STATE_PATH)


# ------------------------------------------------------------------ 主逻辑

def build(days: int, write_state: bool, local_override: str | None) -> dict:
    errors: list[str] = []
    pack, err = fetch_npm()
    if err:
        errors.append("npm: %s" % err)
    rels, err2 = fetch_releases()
    if err2:
        errors.append("github-releases: %s" % err2)
    changelog = {}
    if not rels:
        changelog, err3 = fetch_changelog()
        if err3:
            errors.append("changelog: %s" % err3)

    if not pack and not rels and not changelog:
        return {
            "_run_failed": True,
            "errors": errors,
            "generated_at": _now_utc().isoformat(),
            "hint": "npm / GitHub Releases / raw CHANGELOG 都取不到，检查出网或稍后重试",
        }

    times = {k: v for k, v in (pack.get("time") or {}).items() if k not in ("created", "modified")}
    tags = pack.get("dist-tags") or {}
    versions = sorted(times, key=_vkey)
    now = _now_utc()
    cutoff = now - timedelta(days=days)

    # 每个版本的要点
    def entry_for(v: str) -> dict:
        rec = rels.get(v) or {}
        body = rec.get("body") or ""
        if body:
            bullets = [_strip_md(l) for l in body.split("\n") if re.match(r"^\s*[-*]\s+\S", l)]
        else:
            bullets = list(changelog.get(v, []))
        bullets = [b for b in bullets if b and not any(n in b.lower() for n in NOISE_PATTERNS)]
        kept = bullets[:MAX_BULLETS_PER_VERSION]
        kinds = {"breaking": [], "security": [], "feature": [], "change": [], "fix": [], "other": []}
        for b in kept:
            kinds[_classify(b)].append(b)
        impact = [b for b in bullets if any(k in b.lower() for k in IMPACT_KEYWORDS)]
        # 重要度：破坏性 3 分、安全 2 分、影响本机链路 1 分、新功能 1 分（仅供排序，不是结论）
        importance = (3 * len(kinds["breaking"]) + 2 * len(kinds["security"])
                      + len(impact) + len(kinds["feature"]))
        return {
            "version": v,
            "published_at": times.get(v) or rec.get("published_at"),
            "prerelease": bool(rec.get("prerelease")),
            "url": rec.get("url") or "https://github.com/%s/releases/tag/v%s" % (GH_REPO, v),
            "changelog_source": "github-release" if body else ("changelog-md" if bullets else "none"),
            "bullet_total": len(kept),
            "bullets_omitted": max(0, len(bullets) - len(kept)),
            "importance_score": importance,
            "counts": {k: len(v2) for k, v2 in kinds.items()},
            "breaking": kinds["breaking"][:12],
            "security": kinds["security"][:12],
            "features": kinds["feature"][:12],
            "changes": kinds["change"][:8],
            "fixes": kinds["fix"][:8],
            "other": kinds["other"][:8],
            "impact_hits": impact[:12],
        }

    in_window = []
    for v in versions:
        t = _iso(times.get(v))
        if t and t >= cutoff:
            in_window.append(entry_for(v))
    in_window.sort(key=lambda e: _vkey(e["version"]), reverse=True)

    local = {"version": local_override, "source": "cli-arg", "raw": None} if local_override else detect_local_version()
    latest = tags.get("latest") or (versions[-1] if versions else None)
    stable = tags.get("stable")
    pending, behind = [], None
    if local.get("version") and latest:
        lv, lt = _vkey(local["version"]), _vkey(latest)
        if lv < lt:
            behind = sum(1 for v in versions if lv < _vkey(v) <= lt)
            pending = [entry_for(v) for v in versions if lv < _vkey(v) <= lt]
            pending.sort(key=lambda e: _vkey(e["version"]), reverse=True)

    # 发布节奏（用最近 30 天估计）
    c30 = [v for v in versions if (_iso(times.get(v)) or now - timedelta(days=999)) >= now - timedelta(days=30)]
    gaps = []
    ts30 = sorted((_iso(times[v]) for v in c30 if _iso(times.get(v))))
    for a, b in zip(ts30, ts30[1:]):
        gaps.append((b - a).total_seconds() / 86400)
    cadence = {
        "versions_last_7d": sum(1 for v in versions if (_iso(times.get(v)) or now - timedelta(days=999)) >= now - timedelta(days=7)),
        "versions_last_30d": len(c30),
        "median_gap_days_last30d": round(sorted(gaps)[len(gaps) // 2], 2) if gaps else None,
    }

    state = load_state()
    prev_reported = state.get("reported_versions") or []
    first_run = not prev_reported
    window_versions = [e["version"] for e in in_window]
    new_versions = [v for v in window_versions if v not in prev_reported]
    top_versions = sorted(
        [{"version": e["version"], "published_at": e["published_at"],
          "importance_score": e["importance_score"],
          "breaking": e["counts"]["breaking"], "security": e["counts"]["security"],
          "features": e["counts"]["feature"]} for e in in_window],
        key=lambda x: x["importance_score"], reverse=True)[:5]

    result = {
        "_run_failed": False,
        "generated_at": now.isoformat(),
        "window_days": days,
        "channel": {
            "latest": latest,
            "stable": stable,
            "next": tags.get("next"),
            "latest_published_at": times.get(latest) if latest else None,
            "note": "latest=最新发布；stable=更保守的稳定通道（可能落后 latest）；next=预发布通道",
        },
        "local": local,
        "behind_latest": behind,
        "pending_versions": [e["version"] for e in pending],
        "pending": pending[:15],
        "released_in_window": in_window,
        "released_in_window_count": len(in_window),
        "state": {
            "first_run": first_run,
            "new_versions_since_last_report": new_versions,
            "last_report_at": state.get("last_report_at"),
            "reported_versions_tracked": len(prev_reported),
        },
        "cadence": cadence,
        "top_versions_by_importance": top_versions,
        "impact_for_local": [
            {"version": e["version"], "hits": e["impact_hits"]} for e in in_window if e["impact_hits"]
        ][:8],
        "links": {
            "npm": "https://www.npmjs.com/package/%s" % NPM_PACKAGE,
            "releases": "https://github.com/%s/releases" % GH_REPO,
            "changelog": "https://github.com/%s/blob/main/CHANGELOG.md" % GH_REPO,
            "docs": "https://docs.claude.com/en/release-notes/claude-code",
        },
        "errors": errors,
    }

    if write_state:
        merged = sorted(set(prev_reported) | set(window_versions), key=_vkey)
        if len(merged) > MAX_VERSIONS_IN_STATE:
            merged = merged[-MAX_VERSIONS_IN_STATE:]
        state.update({
            "reported_versions": merged,
            "last_report_at": now.isoformat(),
            "last_latest": latest,
            "last_local": local.get("version"),
        })
        save_state(state)
    return result


def human(d: dict) -> str:
    if d.get("_run_failed"):
        return "采集失败：%s" % "；".join(d.get("errors") or ["未知"])
    ch, lo = d["channel"], d["local"]
    lines = [
        "Claude Code 更新检查 — 近 %d 天" % d["window_days"],
        "通道：latest=%s（%s）｜stable=%s｜next=%s" % (
            ch["latest"], (ch["latest_published_at"] or "?")[:10], ch["stable"], ch["next"]),
        "本机：%s%s" % (lo.get("version") or "未检测到", "（来源 %s）" % lo.get("source")),
        "节奏：近 7 天 %d 个版本 ｜ 近 30 天 %d 个 ｜ 中位间隔 %s 天" % (
            d["cadence"]["versions_last_7d"], d["cadence"]["versions_last_30d"],
            d["cadence"]["median_gap_days_last30d"]),
    ]
    if d.get("behind_latest"):
        lines.append("落后 latest %d 个版本：%s" % (d["behind_latest"], ", ".join(d["pending_versions"][:10])))
    lines.append("")
    for e in d["released_in_window"]:
        lines.append("## %s（%s）重要度 %d" % (e["version"], (e["published_at"] or "?")[:10], e["importance_score"]))
        lines.append("   要点 %d 条｜破坏性 %d｜安全 %d｜新功能 %d｜行为变更 %d｜修复 %d" % (
            e["bullet_total"], e["counts"]["breaking"], e["counts"]["security"],
            e["counts"]["feature"], e["counts"]["change"], e["counts"]["fix"]))
        for b in e["breaking"][:4]:
            lines.append("   ⚠️ %s" % b[:160])
        for b in e["features"][:5]:
            lines.append("   + %s" % b[:160])
        for b in e["security"][:3]:
            lines.append("   🔒 %s" % b[:160])
        for b in e["changes"][:3]:
            lines.append("   ↻ %s" % b[:160])
        for b in e["fixes"][:3]:
            lines.append("   ~ %s" % b[:160])
    if d["errors"]:
        lines.append("")
        lines.append("⚠️ 部分数据源失败：%s" % "；".join(d["errors"]))
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description="采集 Claude Code 官方发布动态")
    ap.add_argument("--days", type=int, default=7, help="窗口天数（默认 7）")
    ap.add_argument("--json", action="store_true", help="输出 JSON（cron/agent 用）")
    ap.add_argument("--no-state", action="store_true", help="不读写 state.json")
    ap.add_argument("--local-version", default=None, help="覆盖本机版本探测（跨机使用）")
    args = ap.parse_args()

    d = build(args.days, write_state=not args.no_state, local_override=args.local_version)
    if args.json:
        print(json.dumps(d, ensure_ascii=False, indent=1))
    else:
        print(human(d))
    return 1 if d.get("_run_failed") else 0


if __name__ == "__main__":
    sys.exit(main())
