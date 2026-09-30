#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""dida 技能 · 读侧脚本：把 dida CLI 的输出压成"人能看/飞书能发"的内容。

设计要点：
- CLI 是唯一数据源；本脚本只做聚合、时区换算、压缩与排序，不改任何数据。
- 时区固定 Asia/Shanghai。dida 存的是 UTC：**全天任务**存成「北京日期 -8h」的 UTC 零点，
  所以必须先转北京时间再取 date()，否则全天任务会整体错一天。
- 默认输出 markdown（给飞书看），加 --json 输出结构化（给 cron/agent 读）；失败 exit 1。

用法：
  dida_view.py today [--limit 15]
  dida_view.py tomorrow
  dida_view.py upcoming --days 7
  dida_view.py search 关键词
  dida_view.py done --days 7
  dida_view.py projects | habits | countdowns
  dida_view.py checkins [--date YYYY-MM-DD] [--days 7]
  dida_view.py brief --mode morning|evening      # 给 cron 的聚合视图
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from datetime import date, datetime, timedelta, timezone
from typing import NoReturn

CST = timezone(timedelta(hours=8))
CLI_CANDIDATES = [
    os.environ.get("DIDA_BIN"),
    shutil.which("dida"),
    os.path.expanduser("~/.hermes/node/bin/dida"),
]
PRIO_LABEL = {0: "无", 1: "低", 3: "中", 5: "高"}


# ------------------------------------------------------------------ 基础

def cli_path() -> str:
    for c in CLI_CANDIDATES:
        if c and os.path.exists(c):
            return c
    die("找不到 dida CLI（试过 DIDA_BIN、PATH、~/.hermes/node/bin/dida）")


def die(msg: str, code: int = 1) -> "NoReturn":
    print(json.dumps({"_run_failed": True, "error": msg}, ensure_ascii=False))
    sys.exit(code)


def run_cli(args: list[str], timeout: int = 120):
    """调 CLI 并解析 JSON；失败直接 die（exit 1）。"""
    cmd = [cli_path()] + args
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        die("CLI 超时：%s" % " ".join(args))
    if p.returncode != 0:
        die("CLI 失败(%s)：%s" % (p.returncode, (p.stderr or p.stdout or "").strip()[:300]))
    out = (p.stdout or "").strip()
    if not out:
        return None
    try:
        return json.loads(out)
    except json.JSONDecodeError:
        die("CLI 返回非 JSON：%s" % out[:300])


def parse_dt(s):
    """CLI 回传形如 2026-09-30T16:00:00.000+0000 → aware datetime。"""
    if not s:
        return None
    t = str(s).replace(".000", "").replace("+0000", "+00:00")
    try:
        return datetime.fromisoformat(t)
    except ValueError:
        return None


def to_cst(s):
    d = parse_dt(s)
    return d.astimezone(CST) if d else None


def local_date(s) -> date | None:
    d = to_cst(s)
    return d.date() if d else None


def parse_user_date(v: str) -> date:
    """用户口径的日期：today/tomorrow/今天/明天/后天/YYYY-MM-DD/MM-DD/+3d"""
    if not v:
        return datetime.now(CST).date()
    v = v.strip().lower()
    today = datetime.now(CST).date()
    if v in ("today", "今天", "现在"):
        return today
    if v in ("tomorrow", "明天"):
        return today + timedelta(days=1)
    if v in ("后天",):
        return today + timedelta(days=2)
    if v in ("昨天", "yesterday"):
        return today - timedelta(days=1)
    if v.startswith("+"):
        n = v[1:].rstrip("d天")
        return today + timedelta(days=int(n))
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%m-%d", "%m/%d"):
        try:
            d = datetime.strptime(v, fmt).date()
            return d.replace(year=today.year) if "%Y" not in fmt else d
        except ValueError:
            continue
    die("无法解析日期：%s（可用 今天/明天/后天/YYYY-MM-DD/MM-DD/+3d）" % v)


def utc_iso(dt_cst: datetime) -> str:
    """北京时间 → CLI 需要的 UTC ISO（yyyy-MM-ddTHH:mm:ssZ）。"""
    return dt_cst.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ------------------------------------------------------------------ 数据层

def fetch_projects() -> list[dict]:
    d = run_cli(["project", "list", "--json"]) or []
    return d if isinstance(d, list) else (d.get("projects") or [])


def project_maps() -> tuple[dict, list[dict]]:
    ps = fetch_projects()
    return {p.get("id"): (p.get("name") or "") for p in ps}, ps


def fetch_open_tasks() -> list[dict]:
    d = run_cli(["task", "filter", "--status", "0", "--json"]) or []
    return d if isinstance(d, list) else (d.get("tasks") or [])


def fetch_habits() -> list[dict]:
    d = run_cli(["habit", "list", "--json"]) or []
    return d if isinstance(d, list) else (d.get("habits") or [])


def enrich(tasks: list[dict], pmap: dict) -> list[dict]:
    """统一成内部结构：北京日期 + 清单名 + 优先级标签 + 逾期天数。"""
    today = datetime.now(CST).date()
    out = []
    for t in tasks:
        due_local = to_cst(t.get("dueDate"))
        start_local = to_cst(t.get("startDate"))
        due_date = due_local.date() if due_local else None
        rec = {
            "id": t.get("id"),
            "title": (t.get("title") or "").strip(),
            "project_id": t.get("projectId"),
            "project": pmap.get(t.get("projectId"), ""),
            "priority": t.get("priority", 0),
            "priority_label": PRIO_LABEL.get(t.get("priority", 0), str(t.get("priority"))),
            "all_day": bool(t.get("isAllDay")),
            "due_local": due_local.strftime("%Y-%m-%d %H:%M") if due_local else None,
            "due_date": due_date.isoformat() if due_date else None,
            "start_local": start_local.strftime("%Y-%m-%d %H:%M") if start_local else None,
            "overdue_days": (today - due_date).days if (due_date and due_date < today) else 0,
            "is_today": bool(due_date and due_date == today),
            "is_tomorrow": bool(due_date and due_date == today + timedelta(days=1)),
        }
        out.append(rec)
    return out


def sort_tasks(rows: list[dict]) -> list[dict]:
    """逾期最久 → 优先级高 → 截止早。"""
    return sorted(rows, key=lambda r: (-r["overdue_days"], -int(r["priority"] or 0), r["due_date"] or "9999"))


def label(r: dict, with_due: bool = False) -> str:
    bits = []
    if r["project"]:
        bits.append(r["project"])
    if r["priority_label"] != "无":
        bits.append(r["priority_label"])
    if r["overdue_days"]:
        bits.append("逾期%d天" % r["overdue_days"])
    elif with_due and r["due_local"]:
        bits.append(r["due_local"][5:16].replace("T", " "))
    tail = "（%s）" % "·".join(bits) if bits else ""
    return "**%s**%s" % (r["title"], tail)


def emit(payload, as_json: bool, text: str):
    if as_json:
        print(json.dumps(payload, ensure_ascii=False, indent=1))
    else:
        print(text)


# ------------------------------------------------------------------ 各子命令

def cmd_today(a):
    pmap, _ = project_maps()
    rows = enrich(fetch_open_tasks(), pmap)
    over = sort_tasks([r for r in rows if r["overdue_days"]])
    today = sort_tasks([r for r in rows if r["is_today"]])
    nodate = sort_tasks([r for r in rows if not r["due_date"]])
    lim = a.limit
    payload = {"ok": True, "date": datetime.now(CST).date().isoformat(), "timezone": "Asia/Shanghai",
               "counts": {"overdue": len(over), "today": len(today), "undated": len(nodate),
                          "open_total": len(rows)},
               "overdue": over[:lim], "due_today": today[:lim], "undated": nodate[:lim]}
    L = ["📋 **今日任务 | %s（%s）**" % (datetime.now(CST).strftime("%Y-%m-%d"), "一二三四五六日"[datetime.now(CST).weekday()])]
    if over:
        L.append("🔴 **逾期 %d 条**" % len(over))
        L += ["- %s" % label(r) for r in over[:lim]]
    if today:
        L.append("📅 **今天到期 %d 条**" % len(today))
        L += ["- %s" % label(r) for r in today[:lim]]
    if not over and not today:
        L.append("今天没有到期任务 🎉")
    if nodate:
        L.append("💤 **无日期待办 %d 条**（列出前 %d）" % (len(nodate), min(lim, len(nodate))))
        L += ["- %s" % label(r) for r in nodate[:lim]]
        if len(nodate) > lim:
            L.append("  …另有 %d 条" % (len(nodate) - lim))
    emit(payload, a.json, "\n".join(L))
    return payload


def cmd_tomorrow(a):
    pmap, _ = project_maps()
    rows = enrich(fetch_open_tasks(), pmap)
    tmrw = sort_tasks([r for r in rows if r["is_tomorrow"]])
    carry = sort_tasks([r for r in rows if r["overdue_days"] or r["is_today"]])
    payload = {"ok": True, "date": datetime.now(CST).date().isoformat(),
               "counts": {"due_tomorrow": len(tmrw), "carried": len(carry)},
               "due_tomorrow": tmrw[:a.limit], "carried_over": carry[:a.limit]}
    L = ["📆 **明天到期 %d 条**" % len(tmrw)]
    L += ["- %s" % label(r) for r in tmrw[:a.limit]] or ["- 无"]
    L.append("")
    L.append("➡️ **今天/之前没完成、会带到明天的 %d 条**" % len(carry))
    L += ["- %s" % label(r) for r in carry[:a.limit]] or ["- 无"]
    emit(payload, a.json, "\n".join(L))
    return payload


def cmd_upcoming(a):
    pmap, _ = project_maps()
    today = datetime.now(CST).date()
    end = today + timedelta(days=a.days)
    rows = enrich(fetch_open_tasks(), pmap)
    win = sort_tasks([r for r in rows if r["due_date"] and today <= date.fromisoformat(r["due_date"]) <= end])
    payload = {"ok": True, "from": today.isoformat(), "to": end.isoformat(), "days": a.days,
               "count": len(win), "tasks": win[:a.limit]}
    L = ["🗓 **未来 %d 天（%s → %s）到期 %d 条**" % (a.days, today.isoformat(), end.isoformat(), len(win))]
    L += ["- %s（%s）" % (r["title"], (r["due_date"] or "")[5:]) for r in win[:a.limit]] or ["- 无"]
    if len(win) > a.limit:
        L.append("  …另有 %d 条" % (len(win) - a.limit))
    emit(payload, a.json, "\n".join(L))
    return payload


def cmd_search(a):
    pmap, _ = project_maps()
    kw = (a.keyword or "").lower()
    rows = [r for r in enrich(fetch_open_tasks(), pmap) if kw in r["title"].lower()]
    payload = {"ok": True, "keyword": a.keyword, "count": len(rows), "tasks": rows[:a.limit]}
    emit(payload, a.json, "\n".join(["🔍 **匹配 %d 条**" % len(rows)] + ["- %s" % label(r, True) for r in rows[:a.limit]]))
    return payload


def cmd_done(a):
    pmap, _ = project_maps()
    today = datetime.now(CST).date()
    start = datetime.combine(today - timedelta(days=a.days), datetime.min.time(), CST)
    end = datetime.combine(today, datetime.max.time(), CST)
    d = run_cli(["task", "completed", "--start-date", utc_iso(start), "--end-date", utc_iso(end), "--json"])
    rows = d if isinstance(d, list) else ((d or {}).get("tasks") or [])
    done = []
    for t in rows:
        c = to_cst(t.get("completedTime") or t.get("modifiedTime"))
        done.append({"id": t.get("id"), "title": (t.get("title") or "").strip(),
                     "project": pmap.get(t.get("projectId"), ""),
                     "completed_local": c.strftime("%Y-%m-%d %H:%M") if c else None})
    done.sort(key=lambda r: r["completed_local"] or "", reverse=True)
    payload = {"ok": True, "days": a.days, "count": len(done), "tasks": done[:a.limit]}
    emit(payload, a.json, "\n".join(["✅ **近 %d 天完成 %d 条**" % (a.days, len(done))]
                                    + ["- %s（%s %s）" % (r["title"], r["project"], (r["completed_local"] or "")[5:]) for r in done[:a.limit]]))
    return payload


def cmd_projects(a):
    ps = fetch_projects()
    payload = {"ok": True, "count": len(ps), "projects": [{"id": p.get("id"), "name": p.get("name")} for p in ps]}
    emit(payload, a.json, "\n".join(["📁 **清单 %d 个**" % len(ps)]
                                    + ["- %s（%s）" % (p.get("name"), p.get("id")) for p in ps]))
    return payload


def cmd_habits(a):
    hs = fetch_habits()
    payload = {"ok": True, "count": len(hs),
               "habits": [{"id": h.get("id"), "name": h.get("name"), "goal": h.get("goal"),
                           "unit": h.get("unit"), "total_checkins": h.get("totalCheckIns")} for h in hs]}
    emit(payload, a.json, "\n".join(["🔁 **习惯 %d 个**" % len(hs)]
                                    + ["- %s（目标 %s%s·累计打卡 %s）" % (h.get("name"), h.get("goal"), h.get("unit") or "", h.get("totalCheckIns")) for h in hs]))
    return payload


def checkins_between(from_d: date, to_d: date, habits: list[dict]) -> list[dict]:
    """CLI 要求必须带 --habits，所以先 list 再查。返回原始嵌套结构。

    ⚠️ 实测坑：CLI 的 **--to 是排他的**（[from, to)）：`--from 20260930 --to 20260930` 返回空，
    查当天必须写 `--from D --to D+1`。本函数对外是闭区间，内部 +1 天转换。
    """
    ids = ",".join(str(h.get("id")) for h in habits if h.get("id"))
    if not ids:
        return []
    d = run_cli(["habit", "checkins", "--habits", ids,
                 "--from", from_d.strftime("%Y%m%d"),
                 "--to", (to_d + timedelta(days=1)).strftime("%Y%m%d"), "--json"])
    rows = d if isinstance(d, list) else ((d or {}).get("checkins") or (d or {}).get("records") or [])
    return rows if isinstance(rows, list) else []


def flatten_checkins(rows: list[dict]) -> dict:
    """真实结构是嵌套的：[{id, habitId, year, checkins:[{id, stamp, time, value, goal, status}]}]
    → {(habitId, 'YYYYMMDD'): {'value': v, 'time': t}}"""
    hits = {}
    for grp in rows:
        hid = str(grp.get("habitId") or grp.get("habit_id") or "")
        for c in (grp.get("checkins") or []):
            stamp = c.get("stamp")
            if hid and stamp:
                hits[(hid, str(stamp))] = {"value": c.get("value"), "time": c.get("time"),
                                            "goal": c.get("goal")}
    return hits


def cmd_checkins(a):
    habits = fetch_habits()
    d0 = parse_user_date(a.date)
    d1 = d0 + timedelta(days=a.days - 1)
    hits = flatten_checkins(checkins_between(d0, d1, habits))
    items = []
    for h in habits:
        hid = str(h.get("id"))
        st = d0.strftime("%Y%m%d")
        rec = hits.get((hid, st))
        _t = to_cst((rec or {}).get("time")) if rec else None
        items.append({"habit": h.get("name"), "id": hid, "goal": h.get("goal"),
                      "done": rec is not None, "value": (rec or {}).get("value"),
                      "time_local": _t.strftime("%H:%M") if _t else None,
                      "days_hit_in_range": sum(1 for (x, _s) in hits if x == hid)})
    payload = {"ok": True, "from": d0.isoformat(), "to": d1.isoformat(), "days": a.days,
               "habits": items, "done_count": sum(1 for i in items if i["done"]), "total": len(items)}
    L = ["🔁 **习惯打卡 | %s**（已打卡 %d/%d）" % (d0.isoformat(), payload["done_count"], payload["total"])]
    for i in items:
        mark = "✅" if i["done"] else "⬜"
        extra = ""
        if i["done"] and i["time_local"]:
            extra = "（%s 打的）" % i["time_local"]
        elif a.days > 1:
            extra = "（区间内 %d 天有记录）" % i["days_hit_in_range"]
        L.append("- %s %s%s" % (mark, i["habit"], extra))
    emit(payload, a.json, "\n".join(L))
    return payload


def cmd_countdowns(a):
    d = run_cli(["countdown", "list", "--json"]) or []
    rows = d if isinstance(d, list) else []
    today = datetime.now(CST).date()
    items = []
    for c in rows:
        raw = str(c.get("date") or "")
        dt = None
        if len(raw) == 8 and raw.isdigit():
            try:
                dt = date(int(raw[:4]), int(raw[4:6]), int(raw[6:]))
            except ValueError:
                dt = None
        if dt and c.get("ignoreYear"):
            try:
                dt = dt.replace(year=today.year)
                if dt < today:
                    dt = dt.replace(year=today.year + 1)
            except ValueError:
                pass
        days = (dt - today).days if dt else None
        items.append({"name": c.get("name"), "date": raw, "days_left": days, "ignore_year": bool(c.get("ignoreYear"))})
    items.sort(key=lambda r: (r["days_left"] is None, r["days_left"]))
    payload = {"ok": True, "count": len(items), "countdowns": items}
    emit(payload, a.json, "\n".join(["⏳ **倒数日 %d 个**" % len(items)]
                                    + ["- %s：%s%s" % (i["name"], i["date"], ("（还有 %d 天）" % i["days_left"]) if i["days_left"] is not None else "") for i in items]))
    return payload


def cmd_brief(a):
    """给 cron 的聚合视图：morning = 全天概览 + 建议尽早办；evening = 明天 + 延期。"""
    pmap, _ = project_maps()
    rows = enrich(fetch_open_tasks(), pmap)
    today = datetime.now(CST).date()
    over = sort_tasks([r for r in rows if r["overdue_days"]])
    due_today = sort_tasks([r for r in rows if r["is_today"]])
    tomorrow = sort_tasks([r for r in rows if r["is_tomorrow"]])
    nodate = sort_tasks([r for r in rows if not r["due_date"]])
    soon = sort_tasks([r for r in rows if r["due_date"] and today < date.fromisoformat(r["due_date"]) <= today + timedelta(days=3)])
    habits = fetch_habits()
    ci = checkins_between(today, today, habits)
    done_today = {str(r.get("habitId") or r.get("habit_id") or "") for r in ci}
    habit_state = [{"habit": h.get("name"), "done": str(h.get("id")) in done_today} for h in habits]
    if a.mode == "morning":
        # 建议尽早办：逾期 > 今天到期且高优先级 > 今天到期 > 3 天内高优先级
        urgent = []
        urgent += [dict(r, why="已逾期 %d 天" % r["overdue_days"]) for r in over[:6]]
        urgent += [dict(r, why="今天到期·高优先级") for r in due_today if int(r["priority"] or 0) >= 5]
        urgent += [dict(r, why="今天到期") for r in due_today if int(r["priority"] or 0) < 5]
        urgent += [dict(r, why="%s 到期·高优先级" % r["due_date"]) for r in soon if int(r["priority"] or 0) >= 5]
        seen, uniq = set(), []
        for r in urgent:
            if r["id"] not in seen:
                seen.add(r["id"])
                uniq.append(r)
        payload = {"ok": True, "mode": "morning", "date": today.isoformat(), "timezone": "Asia/Shanghai",
                   "counts": {"overdue": len(over), "due_today": len(due_today), "undated": len(nodate),
                              "due_3d": len(soon), "open_total": len(rows)},
                   "suggest_today": uniq[:12], "due_today": due_today[:12], "overdue": over[:12],
                   "habits_today": habit_state}
    else:
        carry = sort_tasks([r for r in rows if r["overdue_days"] or r["is_today"]])
        payload = {"ok": True, "mode": "evening", "date": today.isoformat(), "timezone": "Asia/Shanghai",
                   "counts": {"carry_to_tomorrow": len(carry), "due_tomorrow": len(tomorrow),
                              "undated": len(nodate), "open_total": len(rows)},
                   "carry_to_tomorrow": carry[:12], "due_tomorrow": tomorrow[:12],
                   "habits_today": habit_state}
    emit(payload, a.json, json.dumps(payload, ensure_ascii=False, indent=1))
    return payload


def main():
    ap = argparse.ArgumentParser(description="dida 读侧脚本（只读，不改数据）")
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--json", action="store_true", help="输出 JSON（cron/agent 用）")
    common.add_argument("--limit", type=int, default=None, help="每个分组最多列几条（默认 15）")
    ap.add_argument("--json", action="store_true", help="输出 JSON（cron/agent 用）")
    ap.add_argument("--limit", type=int, default=None, help="每个分组最多列几条（默认 15）")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("today", parents=[common]).set_defaults(func=cmd_today)
    sub.add_parser("tomorrow", parents=[common]).set_defaults(func=cmd_tomorrow)
    p = sub.add_parser("upcoming", parents=[common]); p.add_argument("--days", type=int, default=7); p.set_defaults(func=cmd_upcoming)
    p = sub.add_parser("search", parents=[common]); p.add_argument("keyword", nargs="?"); p.set_defaults(func=cmd_search)
    p = sub.add_parser("done", parents=[common]); p.add_argument("--days", type=int, default=7); p.set_defaults(func=cmd_done)
    sub.add_parser("projects", parents=[common]).set_defaults(func=cmd_projects)
    sub.add_parser("habits", parents=[common]).set_defaults(func=cmd_habits)
    p = sub.add_parser("checkins", parents=[common]); p.add_argument("--date", default="今天"); p.add_argument("--days", type=int, default=1); p.set_defaults(func=cmd_checkins)
    sub.add_parser("countdowns", parents=[common]).set_defaults(func=cmd_countdowns)
    p = sub.add_parser("brief", parents=[common]); p.add_argument("--mode", choices=["morning", "evening"], required=True); p.set_defaults(func=cmd_brief)
    a = ap.parse_args()
    if a.limit is None:
        a.limit = 15
    a.func(a)
    return 0


if __name__ == "__main__":
    sys.exit(main())
