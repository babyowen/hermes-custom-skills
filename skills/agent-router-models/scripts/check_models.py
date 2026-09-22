#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""agent-router 网关模型清单：快照 + 与上一次快照对比。

用法:
  python3 check_models.py                        # 拉取今日清单 → 存快照 → 与最近一次历史快照对比，输出 JSON
  python3 check_models.py --list                 # 仅打印当前清单（不写快照、不对比）
  python3 check_models.py --history              # 列出已有快照日期
  python3 check_models.py --baseline 2026-09-21  # 强制与指定日期快照对比
  python3 check_models.py --keep 7               # 快照保留天数（默认 30）
  python3 check_models.py --cache-dir /tmp/x     # 覆盖缓存目录（测试用）
  python3 check_models.py --json                 # 显式 JSON 输出（默认行为）
  python3 check_models.py --compact              # 单行 JSON

退出码: 0 成功；1 失败（缺 key / 网络错误 / HTTP 非 200 / 解析失败 / 无快照可比）
仅依赖标准库。凭据从 ~/.hermes/secrets/agent-router.env 读取，不打印 key。
"""
import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from typing import NoReturn

BJT = timezone(timedelta(hours=8))
SECRETS = os.path.expanduser("~/.hermes/secrets/agent-router.env")
DEFAULT_CACHE = os.path.expanduser("~/.hermes/cache/agent-router-models")
DEFAULT_KEEP = 30
TIMEOUT = 90

# 参与对比的字段（id 之外）
TRACKED = ("category", "mode", "owned_by", "max_input_tokens", "max_output_tokens")
# 字段中文名，供报告层使用
FIELD_CN = {
    "category": "类型",
    "mode": "模式",
    "owned_by": "归属",
    "max_input_tokens": "输入上限",
    "max_output_tokens": "输出上限",
}


def die(msg, extra=None) -> NoReturn:
    out = {"_run_failed": True, "error": msg}
    if extra:
        out.update(extra)
    print(json.dumps(out, ensure_ascii=False, indent=2))
    sys.exit(1)


def emit(obj, compact=False):
    if compact:
        print(json.dumps(obj, ensure_ascii=False, separators=(",", ":")))
    else:
        print(json.dumps(obj, ensure_ascii=False, indent=2))


def load_env(path):
    cfg = {}
    if not os.path.exists(path):
        return cfg
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            cfg[k.strip()] = v.strip().strip('"').strip("'")
    return cfg


def fetch_models(base, key):
    url = base.rstrip("/") + "/models"
    req = urllib.request.Request(
        url,
        headers={
            "Authorization": "Bearer " + key,
            "Content-Type": "application/json",
            "User-Agent": "hermes-agent-router-models/1.0",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            status = resp.getcode()
            body = resp.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", "replace")[:400]
        die(
            "HTTP %s from %s" % (exc.code, url),
            {"http_status": exc.code, "response_head": body,
             "hint": {400: "模型/参数问题", 401: "Key 无效或已停用", 402: "余额不足",
                      429: "限流，稍后重试"}.get(exc.code, "上游或网关错误")},
        )
    except Exception as exc:  # 网络/超时
        die("请求失败: %s: %s" % (type(exc).__name__, exc), {"url": url})
    if status != 200:
        die("非 200 响应: %s" % status, {"http_status": status})
    try:
        payload = json.loads(body)
    except Exception as exc:
        die("响应非 JSON: %s" % exc, {"response_head": body[:300]})
    data = payload.get("data")
    if not isinstance(data, list) or not data:
        die("响应缺少 data[] 或为空", {"top_keys": list(payload.keys())})
    return data


def normalize(raw):
    out = {}
    for item in raw:
        if not isinstance(item, dict) or not item.get("id"):
            continue
        mid = str(item["id"])
        entry = {"category": item.get("category") or "unknown"}
        for f in TRACKED[1:]:
            entry[f] = item.get(f)
        out[mid] = entry
    if not out:
        die("归一化后无有效模型条目")
    return out


def snapshot_dir(cache_dir):
    return os.path.join(cache_dir, "snapshots")


def list_snapshots(cache_dir):
    d = snapshot_dir(cache_dir)
    if not os.path.isdir(d):
        return []
    names = []
    for fn in os.listdir(d):
        if fn.endswith(".json") and len(fn) == 15:  # YYYY-MM-DD.json
            try:
                datetime.strptime(fn[:10], "%Y-%m-%d")
            except ValueError:
                continue
            names.append(fn[:10])
    return sorted(names)


def prune(cache_dir, keep):
    dates = list_snapshots(cache_dir)
    removed = []
    for d in dates[:-keep] if keep > 0 else dates:
        try:
            os.remove(os.path.join(snapshot_dir(cache_dir), d + ".json"))
            removed.append(d)
        except OSError:
            pass
    return removed


def load_snapshot(cache_dir, date):
    path = os.path.join(snapshot_dir(cache_dir), date + ".json")
    if not os.path.exists(path):
        die("基线快照不存在: %s" % path,
            {"baseline": date, "hint": "用 --history 查看已有快照日期"})
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except Exception as exc:
        die("基线快照损坏: %s" % exc, {"baseline_path": path})


def diff(prev_models, cur_models):
    added = sorted(set(cur_models) - set(prev_models))
    removed = sorted(set(prev_models) - set(cur_models))
    changed = []
    for mid in sorted(set(prev_models) & set(cur_models)):
        fields = {}
        for f in TRACKED:
            a, b = prev_models[mid].get(f), cur_models[mid].get(f)
            if a != b:
                fields[f] = {"from": a, "to": b, "label": FIELD_CN.get(f, f)}
        if fields:
            changed.append({"id": mid, "fields": fields})
    unchanged = len(prev_models) - len(added) - len(changed)
    return added, removed, changed, unchanged


def main():
    ap = argparse.ArgumentParser(add_help=True)
    ap.add_argument("--list", action="store_true", help="仅列出当前模型，不写快照不对比")
    ap.add_argument("--history", action="store_true", help="列出已有快照日期")
    ap.add_argument("--baseline", help="强制与指定日期(YYYY-MM-DD)的快照对比")
    ap.add_argument("--keep", type=int, default=DEFAULT_KEEP, help="快照保留天数，默认 30")
    ap.add_argument("--cache-dir", default=DEFAULT_CACHE, help="缓存目录覆盖（测试用）")
    ap.add_argument("--json", action="store_true", help="JSON 输出（默认）")
    ap.add_argument("--compact", action="store_true", help="单行 JSON")
    args = ap.parse_args()

    cache_dir = os.path.abspath(os.path.expanduser(args.cache_dir))
    os.makedirs(snapshot_dir(cache_dir), exist_ok=True)

    if args.history:
        dates = list_snapshots(cache_dir)
        emit({"snapshot_dir": snapshot_dir(cache_dir), "count": len(dates), "dates": dates})
        return

    env = load_env(SECRETS)
    key = env.get("AGENT_ROUTER_KEY") or os.environ.get("AGENT_ROUTER_KEY") or ""
    base = env.get("AGENT_ROUTER_BASE", "http://api.agent-router.cn/v1")
    if not key:
        die("未找到 AGENT_ROUTER_KEY", {"secrets_path": SECRETS})
    if not key.startswith("sk-"):
        die("AGENT_ROUTER_KEY 格式异常（应以 sk- 开头）", {"secrets_path": SECRETS})

    today = datetime.now(BJT).strftime("%Y-%m-%d")
    models = normalize(fetch_models(base, key))
    by_cat = {}
    for m in models.values():
        by_cat[m["category"]] = by_cat.get(m["category"], 0) + 1

    result = {
        "date": today,
        "fetched_at": datetime.now(BJT).isoformat(timespec="seconds"),
        "base_url": base,
        "total": len(models),
        "by_category": dict(sorted(by_cat.items())),
    }

    if args.list:
        result["models"] = {k: models[k] for k in sorted(models)}
        emit(result, args.compact)
        return

    # 取对比基线：优先 --baseline，否则今日之前最近的一次快照
    prev_dates = [d for d in list_snapshots(cache_dir) if d < today]
    baseline = args.baseline or (prev_dates[-1] if prev_dates else None)

    snap_path = os.path.join(snapshot_dir(cache_dir), today + ".json")
    with open(snap_path, "w", encoding="utf-8") as fh:
        json.dump({"date": today, "fetched_at": result["fetched_at"], "base_url": base,
                   "count": len(models), "models": {k: models[k] for k in sorted(models)}},
                  fh, ensure_ascii=False, indent=1)

    pruned = prune(cache_dir, args.keep)
    result["snapshot_path"] = snap_path
    result["pruned_snapshots"] = pruned
    result["retention_days"] = args.keep

    if not baseline:
        result["verdict"] = "baseline"
        result["baseline"] = None
        result["models"] = {k: models[k] for k in sorted(models)}
        result["note"] = "首次运行，已建立基线快照；下次运行起可对比变化"
        emit(result, args.compact)
        return

    prev = load_snapshot(cache_dir, baseline)
    prev_models = prev.get("models") or {}
    added, removed, changed, unchanged = diff(prev_models, models)
    gap = (datetime.strptime(today, "%Y-%m-%d") - datetime.strptime(baseline, "%Y-%m-%d")).days
    result.update({
        "baseline": baseline,
        "baseline_age_days": gap,
        "baseline_count": len(prev_models),
        "added": added,
        "removed": removed,
        "changed": changed,
        "unchanged_count": max(unchanged, 0),
        "verdict": "changed" if (added or removed or changed) else "unchanged",
    })
    emit(result, args.compact)


if __name__ == "__main__":
    main()
