#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
hermes-update-watch: 采集 Hermes Agent 官方发布动态 + 本机版本 → JSON。

唯一数据源：官方 GitHub Releases API（NousResearch/hermes-agent）。
只用标准库（urllib），无第三方依赖；未认证限流 60 次/小时，本脚本只打 2 个请求。

用法：
  python3 fetch_hermes_updates.py --days 7 --json      # 给 cron / agent 读
  python3 fetch_hermes_updates.py --days 7             # 人肉看的摘要
  python3 fetch_hermes_updates.py --days 7 --json --no-state   # 不写 state（调试）

退出码：0 正常；1 采集彻底失败（输出带 _run_failed 的 JSON）。
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

OFFICIAL_REPO = "NousResearch/hermes-agent"
API = "https://api.github.com/repos/%s" % OFFICIAL_REPO
LOCAL_REPO = os.path.expanduser("~/.hermes/hermes-agent")
STATE_PATH = os.path.expanduser("~/.hermes/cache/hermes-update-watch/state.json")
MAX_TAGS_IN_STATE = 40

# 命中这些词 → 认为"影响本机"（用户环境：飞书网关 + 多 cron + 聚合网关 provider + 自定义技能）
IMPACT_KEYWORDS = [
    "gateway", "cron", "scheduler", "feishu", "lark", "weixin", "telegram",
    "provider", "model", "base_url", "fallback", "credential", "auth",
    "skill", "memory", "state.db", "session", "compression", "context",
    "approval", "security", "toolset", "mcp", "plugin", "desktop", "tui",
]
BREAKING_MARKERS = [
    "breaking", "⚠️", "deprecat", "incompatible", "renamed", "removed",
    "no longer", "must be", "opt-in", "requires a migration",
]
# release body 里的样板段落：不是"更新内容"，抽要点时丢掉
NOISE_PATTERNS = [
    "release date", "measured at commit", "full curated release notes",
    "full changelog", "updating", "git installs", "installer one-liner",
    "docker / hermes cloud", "contributor credits", "compare/v",
    "patch release", "this patch does not", "nothing in this window",
    "will document everything", "re-run the installer",
    "existing install", "fresh install", "managed deployments",
    " commits ·", "merged prs", "files changed", "since v0.2",
]


# ---------------------------------------------------------------- 工具

def _run(cmd, timeout=25):
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return (p.stdout or "").strip(), (p.stderr or "").strip(), p.returncode
    except Exception as exc:  # noqa: BLE001
        return "", str(exc), 1


def _api(path, retries=2):
    """GET 一个 GitHub API 路径 → dict/list。抛异常由调用方兜。"""
    url = API + path
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    last = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(
                url,
                headers={
                    "User-Agent": "hermes-update-watch/1.0",
                    "Accept": "application/vnd.github+json",
                    "X-GitHub-Api-Version": "2022-11-28",
                },
            )
            if token:
                req.add_header("Authorization", "Bearer %s" % token)
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode("utf-8", "replace"))
        except urllib.error.HTTPError as exc:
            last = "HTTP %s %s" % (exc.code, exc.reason)
            if exc.code == 403:  # 限流
                last += "（可能触发未认证限流：60 次/小时）"
            if attempt + 1 < retries:
                time.sleep(4)
        except Exception as exc:  # noqa: BLE001
            last = str(exc)
            if attempt + 1 < retries:
                time.sleep(4)
    raise RuntimeError(last or "unknown api error")


def _parse_dt(value):
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except Exception:  # noqa: BLE001
        return None


def _iso(dt):
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ") if dt else None


# ---------------------------------------------------------------- 本机版本

def local_info():
    info = {"path": LOCAL_REPO, "version": None, "version_source": None,
            "commit": None, "commit_date": None, "branch": None, "is_git": False}

    out, _, code = _run(["hermes", "--version"])
    if code == 0 and out:
        m = re.search(r"(\d+\.\d+\.\d+(?:[-+.\w]+)?)", out)
        if m:
            info["version"] = m.group(1)
            info["version_source"] = "hermes --version"

    if os.path.isdir(os.path.join(LOCAL_REPO, ".git")):
        info["is_git"] = True
        sha, _, code = _run(["git", "-C", LOCAL_REPO, "rev-parse", "--short", "HEAD"])
        if code == 0:
            info["commit"] = sha
        date, _, code = _run(["git", "-C", LOCAL_REPO, "log", "-1", "--format=%cI"])
        if code == 0:
            info["commit_date"] = date
        br, _, code = _run(["git", "-C", LOCAL_REPO, "rev-parse", "--abbrev-ref", "HEAD"])
        if code == 0:
            info["branch"] = br

    if not info["version"]:
        pyproject = os.path.join(LOCAL_REPO, "pyproject.toml")
        try:
            with open(pyproject, encoding="utf-8") as fh:
                m = re.search(r'^version\s*=\s*"([^"]+)"', fh.read(), re.M)
            if m:
                info["version"] = m.group(1)
                info["version_source"] = "pyproject.toml（可能滞后于实际 checkout）"
        except Exception:  # noqa: BLE001
            pass
    return info


# ---------------------------------------------------------------- release 解析

def _sections(body):
    """从 release body 里抽要点行 / 行为变化行 / compare 链接（剔样板段落）。"""
    highlights, breaking = [], []
    for raw in (body or "").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or line.startswith(">"):
            continue
        text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", line)          # 链接→文字
        text = re.sub(r"/(?:pull|issues)/\d+", "", text)
        text = text.replace("**", "").replace("`", "")
        text = re.sub(r"\s+", " ", text).strip(" -*\t")
        if len(text) < 25:
            continue
        low = text.lower()
        if any(n in low for n in NOISE_PATTERNS):
            continue
        is_marker = any(m in low for m in BREAKING_MARKERS)
        if is_marker:
            breaking.append(text)
        elif raw.strip().startswith(("-", "*")):
            highlights.append(text)
    compare = None
    m = re.search(r"(https://github\.com/%s/compare/\S+)" % re.escape(OFFICIAL_REPO), body or "")
    if m:
        compare = m.group(1).rstrip(").,")
    return highlights[:8], breaking[:6], compare


def _release_entry(rel):
    body = rel.get("body") or ""
    highlights, breaking, compare = _sections(body)
    return {
        "tag": rel.get("tag_name"),
        "name": (rel.get("name") or "").splitlines()[0][:120],
        "published_at": _iso(_parse_dt(rel.get("published_at"))),
        "url": rel.get("html_url"),
        "pr_count": len(set(re.findall(r"/pull/(\d+)", body))
                        | set(re.findall(r"#(\d{4,})", body))),
        "highlights": highlights,
        "breaking": breaking,
        "compare_url": compare,
        "body_excerpt": re.sub(r"\s+", " ", body)[:600],
    }


def _kw_hit(kw, low):
    """ASCII 短词按词边界匹配，避免 author 命中 auth 这类误判。"""
    if kw.isascii():
        return re.search(r"\b%s\b" % re.escape(kw), low) is not None
    return kw in low


def _impact(entries):
    hits = []
    for e in entries:
        for kind, lines in (("亮点", e["highlights"]), ("注意", e["breaking"])):
            for ln in lines:
                low = ln.lower()
                matched = [k for k in IMPACT_KEYWORDS if _kw_hit(k, low)]
                if matched:
                    hits.append({"tag": e["tag"], "kind": kind, "area": matched[0], "line": ln[:220]})
    return hits[:25]


# ---------------------------------------------------------------- state

def load_state():
    try:
        with open(STATE_PATH, encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:  # noqa: BLE001
        return {}


def save_state(state):
    os.makedirs(os.path.dirname(STATE_PATH), exist_ok=True)
    tmp = STATE_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(state, fh, ensure_ascii=False, indent=2)
    os.replace(tmp, STATE_PATH)


# ---------------------------------------------------------------- main

def collect(days):
    now = datetime.now(timezone.utc)
    since = now - timedelta(days=days)
    local = local_info()

    releases_raw, tags_raw, errors = [], [], []
    try:
        releases_raw = _api("/releases?per_page=30")
    except Exception as exc:  # noqa: BLE001
        errors.append("releases: %s" % exc)
    try:
        tags_raw = _api("/tags?per_page=30")
    except Exception as exc:  # noqa: BLE001
        errors.append("tags: %s" % exc)

    releases = [_release_entry(r) for r in releases_raw
                if not r.get("draft") and not r.get("prerelease")]
    releases.sort(key=lambda r: r["published_at"] or "", reverse=True)

    local_dt = _parse_dt(local.get("commit_date"))
    in_window = [r for r in releases if (_parse_dt(r["published_at"]) or since) >= since]
    # "本机没装上的"：发布时间晚于本机最后一次更新（无日期则取最近 3 个 release）
    if local_dt:
        pending = [r for r in releases if (_parse_dt(r["published_at"]) or now) > local_dt]
    else:
        pending = releases[:3]

    state = load_state()
    seen = set(state.get("reported_tags") or [])
    new_tags = [r["tag"] for r in releases if r["tag"] not in seen]
    latest = releases[0] if releases else {}

    tags_no_release = [t.get("name") for t in tags_raw
                       if t.get("name") not in {r["tag"] for r in releases}][:5]

    result = {
        "generated_at": _iso(now),
        "window_days": days,
        "window_since": _iso(since),
        "official_repo": OFFICIAL_REPO,
        "local": local,
        "latest": {"tag": latest.get("tag"), "published_at": latest.get("published_at"),
                   "url": latest.get("url"), "pr_count": latest.get("pr_count")},
        "days_behind": (round((now - local_dt).total_seconds() / 86400)
                        if local_dt else None),
        "releases_in_window": in_window,
        "pending_releases": pending,
        "pending_count": len(pending),
        "impact_for_local": _impact(pending or in_window),
        "tags_without_release": tags_no_release,
        "state": {
            "first_run": not state,
            "last_seen_tag": state.get("last_seen_tag"),
            "last_run_at": state.get("last_run_at"),
            "new_tags_since_last_report": new_tags,
        },
        "links": {
            "releases": "https://github.com/%s/releases" % OFFICIAL_REPO,
            "compare": (latest.get("compare_url")
                        or "https://github.com/%s/compare/%s...%s"
                           % (OFFICIAL_REPO, state.get("last_seen_tag") or "HEAD", latest.get("tag") or "main")),
            "docs": "https://hermes-agent.nousresearch.com/docs/",
        },
        "errors": errors,
    }
    return result


def digest(res):
    loc, lat = res["local"], res["latest"]
    lines = []
    lines.append("本地 %s（%s） | 最新 %s（%s） | 落后 %s 天"
                 % (loc.get("version"), (loc.get("commit_date") or "")[:10],
                    lat.get("tag"), (lat.get("published_at") or "")[:10],
                    res.get("days_behind")))
    lines.append("待升 %s 个 release，窗口内 %s 个，未装 tag: %s"
                 % (res["pending_count"], len(res["releases_in_window"]),
                    ", ".join(r["tag"] for r in res["pending_releases"][:8]) or "无"))
    for r in res["pending_releases"][:6]:
        refs = "，引用 %s 处" % r["pr_count"] if r["pr_count"] else ""
        lines.append("  · %s (%s)%s" % (r["tag"], (r["published_at"] or "")[:10], refs))
        for h in r["highlights"][:3]:
            lines.append("      - %s" % h[:150])
        for b in r["breaking"][:2]:
            lines.append("      ⚠️ %s" % b[:150])
    if res["impact_for_local"]:
        lines.append("影响本机：")
        for i in res["impact_for_local"][:10]:
            lines.append("  [%s/%s] %s" % (i["tag"], i["area"], i["line"][:140]))
    if res["errors"]:
        lines.append("错误: %s" % "; ".join(res["errors"]))
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description="采集 Hermes Agent 官方更新")
    ap.add_argument("--days", type=int, default=7, help="窗口天数（默认 7）")
    ap.add_argument("--json", action="store_true", help="输出 JSON")
    ap.add_argument("--no-state", action="store_true", help="不写 state.json（调试用）")
    args = ap.parse_args()

    try:
        res = collect(args.days)
    except Exception as exc:  # noqa: BLE001
        payload = {"_run_failed": True, "error": str(exc),
                   "official_repo": OFFICIAL_REPO, "generated_at": _iso(datetime.now(timezone.utc))}
        print(json.dumps(payload, ensure_ascii=False, indent=2) if args.json else
              "采集失败: %s" % exc)
        return 1

    if not args.no_state:
        state = load_state()
        seen = list(dict.fromkeys((state.get("reported_tags") or []) +
                                  [r["tag"] for r in res["pending_releases"]]))[-MAX_TAGS_IN_STATE:]
        state.update({"last_seen_tag": res["latest"].get("tag"),
                      "last_run_at": res["generated_at"],
                      "reported_tags": seen})
        try:
            save_state(state)
        except Exception as exc:  # noqa: BLE001
            res["errors"].append("state write failed: %s" % exc)

    print(json.dumps(res, ensure_ascii=False, indent=2) if args.json else digest(res))
    # 数据一条没拿到 → 非 0，让 cron 侧能识别
    if res["errors"] and not res["latest"].get("tag"):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
