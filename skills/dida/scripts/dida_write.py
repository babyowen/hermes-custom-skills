#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""dida 技能 · 写侧脚本：所有写操作都经这里，不手拼 shell 命令。

为什么要有这一层：
- **不经 shell**：argv 数组直传 CLI，中文标题里的空格/引号/`$`/换行不会炸。
- **名字→ID**：清单/习惯用名字给，脚本自己解析（精确优先，其次包含；歧义报候选并 exit 1）。
- **日期口语化**：--due 今天/明天/2026-10-05/"2026-10-05 15:00"/+3d → CLI 要的 UTC ISO。
- **写完回读**：每个写操作结束都回读一次，确认真的生效，再回报。
- **删除要显式确认**：delete-* 必须带 --yes，否则拒绝执行（exit 1）。

用法：
  dida_write.py add-task --title "交报销" [--project 💰报销] [--due 明天] [--priority 高] [--tags a,b]
  dida_write.py complete --title 交报销        # 或 --task-id <id>
  dida_write.py update --task-id <id> --due 2026-10-05 --priority 中
  dida_write.py checkin --habit 锻炼身体 [--date 今天] [--value 1]
  dida_write.py delete-task --task-id <id> --yes
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import date, datetime, time, timedelta, timezone
from typing import Any, NoReturn

CST = timezone(timedelta(hours=8))
WRITE_VERBS = {"create", "update", "complete", "complete-batch", "delete", "move", "assign",
               "unassign", "checkin", "rename", "token", "login", "logout"}
DRY = {"on": False}
CLI_CANDIDATES = [
    os.environ.get("DIDA_BIN"),
    shutil.which("dida"),
    os.path.expanduser("~/.hermes/node/bin/dida"),
]
PRIO_MAP = {"高": 5, "高优先级": 5, "high": 5, "重要": 5,
            "中": 3, "中优先级": 3, "medium": 3, "mid": 3,
            "低": 1, "低优先级": 1, "low": 1,
            "无": 0, "none": 0, "0": 0}
PRIO_LABEL = {0: "无", 1: "低", 3: "中", 5: "高"}


def die(msg: str, code: int = 1) -> NoReturn:
    print(json.dumps({"_run_failed": True, "error": msg}, ensure_ascii=False))
    sys.exit(code)


def cli_path() -> str:
    for c in CLI_CANDIDATES:
        if c and os.path.exists(c):
            return c
    die("找不到 dida CLI")


def run_cli(args: list[str], timeout: int = 120, allow_fail: bool = False) -> Any:
    """调 CLI。DRY 模式下一个都不执行——写动词直接返回计划，读动词照常（解析名字要用）。"""
    if DRY["on"] and any(v in args for v in WRITE_VERBS):
        return {"_dry_run": True, "argv": [cli_path()] + args}
    try:
        p = subprocess.run([cli_path()] + args, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        die("CLI 超时：%s" % " ".join(args))
    if p.returncode != 0 and not allow_fail:
        die("CLI 失败(%s)：%s" % (p.returncode, (p.stderr or p.stdout or "").strip()[:300]))
    out = (p.stdout or "").strip()
    if not out:
        return None if p.returncode == 0 else {"_cli_error": (p.stderr or "").strip()[:300]}
    try:
        return json.loads(out)
    except json.JSONDecodeError:
        return {"_raw": out[:400]} if p.returncode == 0 else {"_cli_error": out[:300]}


# ---------------------------------------------------------------- 解析辅助

def to_cst(s):
    """CLI 回传的 UTC ISO → 北京时间 datetime。"""
    if not s:
        return None
    t = str(s).replace(".000", "").replace("+0000", "+00:00")
    try:
        return datetime.fromisoformat(t).astimezone(CST)
    except ValueError:
        return None


def parse_when(v: str | None) -> tuple[date, time | None]:
    """返回 (日期, 时间或 None)。时间 None = 全天。"""
    if not v:
        return datetime.now(CST).date(), None
    v = v.strip()
    m = re.match(r"^(.*?)[\sT](\d{1,2})[:：](\d{2})$", v)
    if m:
        d = parse_date(m.group(1))
        return d, time(int(m.group(2)), int(m.group(3)))
    return parse_date(v), None


def parse_date(v: str) -> date:
    v = (v or "").strip().lower()
    today = datetime.now(CST).date()
    if v in ("today", "今天", "现在"):
        return today
    if v in ("tomorrow", "明天"):
        return today + timedelta(days=1)
    if v == "后天":
        return today + timedelta(days=2)
    if v.startswith("+"):
        return today + timedelta(days=int(v[1:].rstrip("d天")))
    if v.startswith("周") or v.startswith("星期"):
        num = {"一": 0, "二": 1, "三": 2, "四": 3, "五": 4, "六": 5, "日": 6, "天": 6}
        k = v[-1]
        if k in num:
            delta = (num[k] - today.weekday()) % 7
            return today + timedelta(days=delta or 7)
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%m-%d", "%m/%d"):
        try:
            d = datetime.strptime(v, fmt).date()
            return d if "%Y" in fmt else d.replace(year=today.year)
        except ValueError:
            continue
    die("无法解析日期：%s（可用 今天/明天/后天/周三/YYYY-MM-DD/MM-DD/+3d，可加 ' 15:00' 表示具体时刻）" % v)


def due_args(when: str | None) -> list[str]:
    """日期 → CLI 的 --due-date / --all-day / --time-zone 参数。"""
    if not when:
        return []
    d, t = parse_when(when)
    out = ["--time-zone", "Asia/Shanghai"]
    if t is None:
        out += ["--all-day", "--due-date", datetime.combine(d, time(0, 0), CST).astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")]
    else:
        out += ["--due-date", datetime.combine(d, t, CST).astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")]
    return out


def parse_priority(v) -> int:
    if v is None:
        return 0
    s = str(v).strip()
    if s in PRIO_MAP:
        return PRIO_MAP[s]
    if s.isdigit() and int(s) in (0, 1, 3, 5):
        return int(s)
    die("优先级只能是 高/中/低/无 或 5/3/1/0，收到：%s" % v)


def pmap() -> tuple[dict, list[dict]]:
    d = run_cli(["project", "list", "--json"]) or []
    ps = d if isinstance(d, list) else (d.get("projects") or [])
    return {p.get("id"): (p.get("name") or "") for p in ps}, ps


def resolve_project(name: str | None) -> str | None:
    """清单名 → id：id 直接透传；空 = 收件箱（不传 --project）；歧义报候选。"""
    if not name:
        return None
    _, ps = pmap()
    ids = {str(p.get("id")) for p in ps}
    if name in ids:
        return name
    exact = [p for p in ps if (p.get("name") or "") == name]
    if len(exact) == 1:
        return str(exact[0]["id"])
    hits = [p for p in ps if name.lower() in (p.get("name") or "").lower()]
    if len(hits) == 1:
        return str(hits[0]["id"])
    if not hits:
        die("找不到清单「%s」。现有：%s" % (name, " / ".join(str(p.get("name")) for p in ps)))
    die("清单名「%s」匹配到多个：%s（请写全名）" % (name, " / ".join(str(p.get("name")) for p in hits)))


def resolve_habit(name: str) -> str:
    d = run_cli(["habit", "list", "--json"]) or []
    hs = d if isinstance(d, list) else (d.get("habits") or [])
    exact = [h for h in hs if (h.get("name") or "") == name]
    if len(exact) == 1:
        return str(exact[0]["id"])
    hits = [h for h in hs if name.lower() in (h.get("name") or "").lower()]
    if len(hits) == 1:
        return str(hits[0]["id"])
    if not hits:
        die("找不到习惯「%s」。现有：%s" % (name, " / ".join(str(h.get("name")) for h in hs)))
    die("习惯名「%s」匹配到多个：%s" % (name, " / ".join(str(h.get("name")) for h in hits)))


def open_tasks() -> list[dict]:
    d = run_cli(["task", "filter", "--status", "0", "--json"]) or []
    return d if isinstance(d, list) else (d.get("tasks") or [])


def find_open_by_title(kw: str) -> list[dict]:
    kw = kw.strip().lower()
    return [t for t in open_tasks() if kw in (t.get("title") or "").lower()]


def parse_stamp(s: str | None) -> date:
    if not s or s in ("今天", "today"):
        return datetime.now(CST).date()
    if s in ("昨天", "yesterday"):
        return datetime.now(CST).date() - timedelta(days=1)
    if re.match(r"^\d{8}$", s):
        return date(int(s[:4]), int(s[4:6]), int(s[6:]))
    return parse_date(s)


def dry_out(args: list[str], as_json: bool) -> bool:
    """DRY 模式：只打印将要执行的 CLI 命令，不真执行。返回 True 表示已处理。"""
    if not DRY["on"]:
        return False
    plan = [cli_path()] + args
    if as_json:
        print(json.dumps({"ok": True, "dry_run": True, "argv": plan}, ensure_ascii=False, indent=1))
    else:
        print("🧪 dry-run：将执行 `%s`" % " ".join(args))
    return True


def out(payload: dict, as_json: bool, line: str):
    payload.setdefault("ok", True)
    if as_json:
        print(json.dumps(payload, ensure_ascii=False, indent=1))
    else:
        print(line)
    if not payload.get("ok"):
        sys.exit(1)


# ---------------------------------------------------------------- 子命令

def cmd_add_task(a):
    proj_id = resolve_project(a.project)
    args = ["task", "create", "--title", a.title]
    if proj_id:
        args += ["--project", proj_id]
    args += due_args(a.due)
    if a.priority is not None:
        args += ["--priority", str(parse_priority(a.priority))]
    if a.tags:
        args += ["--tags", a.tags]
    if a.content:
        args += ["--content", a.content]
    if a.items:
        args += ["--items", a.items if a.items.strip().startswith("[") else a.items]
    if a.repeat:
        args += ["--repeat", a.repeat]
    if a.reminders:
        args += ["--reminders", a.reminders]
    if dry_out(args + ["--json"], a.json):
        return {"ok": True, "dry_run": True}
    res = run_cli(args + ["--json"]) or {}
    tid = res.get("id") if isinstance(res, dict) else None
    # 回读验证（写生效有 1~3 秒延迟，轮询等它出现）
    verified, found = False, None
    if tid and wait_open(tid, want_gone=False):
        verified = True
        found = next((t for t in open_tasks() if t.get("id") == tid), None)
    due_show = ""
    if found and found.get("dueDate"):
        _dl = to_cst(found.get("dueDate"))
        if _dl:
            due_show = _dl.strftime("%m-%d") + "（全天）" if found.get("isAllDay") else _dl.strftime("%m-%d %H:%M")
    pname = dict((p.get("id"), p.get("name")) for p in pmap()[1])
    payload = {"ok": bool(tid), "action": "add-task", "task_id": tid,
               "title": a.title, "project": (found or {}).get("projectId") and pname.get((found or {}).get("projectId")) or (pname.get(proj_id) if proj_id else "收件箱"),
               "due_local": due_show or None, "priority": (found or {}).get("priority"),
               "readback_verified": verified,
               "raw": res if not tid else None}
    line = ("✅ 已创建：**%s**（%s%s）\n   id=%s%s"
            % (a.title, payload["project"], "·%s" % due_show if due_show else "",
               tid or "创建失败", "｜回读已确认" if verified else "｜⚠️ 回读未找到，需人工确认"))
    out(payload, a.json, line)
    return payload


def wait_open(tid, want_gone: bool, tries: int = 5, delay: float = 1.5) -> bool:
    """轮询未完成列表：want_gone=True 等它消失，False 等它出现。
    实测写操作生效有 1~3 秒延迟，写完立刻回读会误判失败。"""
    import time as _t
    for i in range(tries):
        hit = any(str(x.get("id")) == str(tid) for x in open_tasks())
        if hit != want_gone:
            return True
        if i < tries - 1:
            _t.sleep(delay)
    return False


def cli_err(res) -> str:
    """从 run_cli 的返回值里取出 CLI 报错文本（非零退出时才有）。"""
    if isinstance(res, dict) and res.get("_cli_error"):
        return str(res["_cli_error"])
    return ""


def cmd_complete(a):
    targets = []
    if a.task_id:
        for t in open_tasks():
            if t.get("id") == a.task_id:
                targets = [t]
                break
        if not targets:
            die("未在未完成任务里找到 id=%s（可能已完成或 id 写错）" % a.task_id)
    else:
        if not a.title:
            die("需要 --title 关键词 或 --task-id")
        targets = find_open_by_title(a.title)
        if not targets:
            die("未找到标题含「%s」的未完成任务" % a.title)
        if len(targets) > 1:
            die("「%s」匹配到 %d 条，请写更精确的关键词或直接用 --task-id：\n%s"
                % (a.title, len(targets), "\n".join("  %s  %s" % (t.get("id"), t.get("title")) for t in targets[:8])))
    t = targets[0]
    # ⚠️ task complete 不支持 --json（加了会 unknown option 直接失败）
    cargs = ["task", "complete", str(t.get("projectId")), str(t.get("id"))]
    if dry_out(cargs, a.json):
        return {"ok": True, "dry_run": True}
    res = run_cli(cargs, allow_fail=True)
    err = cli_err(res)
    if err:
        die("完成失败：%s（任务：%s）" % (err, t.get("title")))
    ok = wait_open(t.get("id"), want_gone=True)
    payload = {"ok": ok, "action": "complete", "task_id": t.get("id"), "title": t.get("title"),
               "readback_still_open": not ok, "raw": res}
    out(payload, a.json, ("✅ 已完成：**%s**（回读确认已从待办消失）" % t.get("title")) if ok
        else ("⚠️ complete 命令成功但 5 次回读仍在待办，请人工确认：%s" % t.get("title")))
    return payload


def cmd_update(a):
    if not a.task_id and not a.title:
        die("需要 --task-id 或 --title 关键词")
    tid = a.task_id
    t = None
    if not tid:
        hits = find_open_by_title(a.title)
        if len(hits) != 1:
            die("「%s」匹配 %d 条，请用 --task-id" % (a.title, len(hits)))
        tid, t = hits[0].get("id"), hits[0]
    if t is None:
        for x in open_tasks():
            if str(x.get("id")) == str(tid):
                t = x
                break
    pid = (t or {}).get("projectId")
    if not pid:
        die("未在未完成任务里找到 id=%s（update 必须同时给 --project，所以只处理未完成任务）" % tid)
    # ⚠️ task update：位置参数 + --id + --project 三者都给（实测缺 --id 或 --project 都直接报错）
    args = ["task", "update", str(tid), "--id", str(tid), "--project", str(pid)]
    if a.title_new:
        args += ["--title", a.title_new]
    if a.due:
        args += due_args(a.due)
    if a.priority is not None:
        args += ["--priority", str(parse_priority(a.priority))]
    if a.content is not None:
        args += ["--content", a.content]
    if a.tags is not None:
        args += ["--tags", a.tags]
    if dry_out(args + ["--json"], a.json):
        return {"ok": True, "dry_run": True}
    res = run_cli(args + ["--json"], allow_fail=True)
    err = cli_err(res)
    if err:
        die("更新失败：%s（id=%s）" % (err, tid))
    after = run_cli(["task", "get", str(pid), str(tid), "--json"], allow_fail=True)
    ok = isinstance(after, dict) and not after.get("_cli_error") and after.get("id")
    payload = {"ok": bool(ok), "action": "update", "task_id": tid, "after": after if ok else None, "raw": res}
    line = "✅ 已更新 id=%s（回读：优先级=%s）" % (tid, (after or {}).get("priority")) if ok \
        else "⚠️ 更新命令已发，但回读失败（%s）" % (err or (after or {}).get("_cli_error"))
    out(payload, a.json, line)
    return payload


def cmd_checkin(a):
    hid = resolve_habit(a.habit)
    d = parse_stamp(a.date)
    args = ["habit", "checkin", hid, "--stamp", d.strftime("%Y%m%d")]
    if a.value is not None:
        args += ["--value", str(a.value)]
    if a.goal is not None:
        args += ["--goal", str(a.goal)]
    if dry_out(args + ["--json"], a.json):
        return {"ok": True, "dry_run": True}
    res = run_cli(args + ["--json"], allow_fail=True)
    # 回读：查当天记录（--to 排他，需 +1 天）
    back = run_cli(["habit", "checkins", "--habits", hid, "--from", d.strftime("%Y%m%d"),
                    "--to", (d + timedelta(days=1)).strftime("%Y%m%d"), "--json"], allow_fail=True)
    stamps = [str(c.get("stamp")) for grp in (back if isinstance(back, list) else [])
              for c in (grp.get("checkins") or [])]
    ok = d.strftime("%Y%m%d") in stamps
    payload = {"ok": ok, "action": "checkin", "habit": a.habit, "habit_id": hid,
               "date": d.isoformat(), "readback_verified": ok, "raw": res}
    out(payload, a.json, ("✅ 已打卡：%s（%s，回读确认）" % (a.habit, d.isoformat())) if ok
        else ("⚠️ 打卡命令已发，但回读没看到记录：%s（%s）" % (a.habit, d.isoformat())))
    return payload


def cmd_delete_task(a):
    if not a.yes:
        die("删除是危险操作：确认要删就加 --yes；未加则拒绝执行。")
    if not a.task_id and not a.title:
        die("需要 --task-id 或 --title 关键词")
    tid, title = a.task_id, None
    if not tid:
        hits = find_open_by_title(a.title)
        if len(hits) != 1:
            die("「%s」匹配 %d 条，请用 --task-id 精确指定" % (a.title, len(hits)))
        tid, title = hits[0].get("id"), hits[0].get("title")
    pid = None
    for t in open_tasks():
        if t.get("id") == str(tid):
            pid, title = t.get("projectId"), t.get("title")
            break
    if not pid:
        die("未找到 id=%s 的未完成任务（已完成的任务不在此脚本处理范围）" % tid)
    dargs = ["task", "delete", str(pid), str(tid)]  # ⚠️ 不支持 --json
    if dry_out(dargs, a.json):
        return {"ok": True, "dry_run": True}
    res = run_cli(dargs, allow_fail=True)
    err = cli_err(res)
    if err:
        die("删除失败：%s（任务：%s）" % (err, title))
    ok = wait_open(tid, want_gone=True)
    payload = {"ok": ok, "action": "delete-task", "task_id": tid, "title": title,
               "readback_still_present": not ok, "raw": res}
    out(payload, a.json, ("🗑 已删除：**%s**（回读确认已消失）" % title) if ok
        else ("⚠️ delete 命令成功但 5 次回读仍在：%s" % title))
    return payload


def main():
    ap = argparse.ArgumentParser(description="dida 写侧脚本（写操作统一入口）")
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--json", action="store_true")
    common.add_argument("--dry-run", action="store_true", help="只打印将执行的 CLI 命令，不真写")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("add-task", parents=[common])
    p.add_argument("--title", required=True)
    p.add_argument("--project")
    p.add_argument("--due")
    p.add_argument("--priority")
    p.add_argument("--tags")
    p.add_argument("--content")
    p.add_argument("--items")
    p.add_argument("--repeat")
    p.add_argument("--reminders")
    p.set_defaults(func=cmd_add_task)

    p = sub.add_parser("complete", parents=[common])
    p.add_argument("--title")
    p.add_argument("--task-id")
    p.set_defaults(func=cmd_complete)

    p = sub.add_parser("update", parents=[common])
    p.add_argument("--task-id")
    p.add_argument("--title")
    p.add_argument("--title-new")
    p.add_argument("--due")
    p.add_argument("--priority")
    p.add_argument("--content")
    p.add_argument("--tags")
    p.set_defaults(func=cmd_update)

    p = sub.add_parser("checkin", parents=[common])
    p.add_argument("--habit", required=True)
    p.add_argument("--date")
    p.add_argument("--value", type=float)
    p.add_argument("--goal", type=float)
    p.set_defaults(func=cmd_checkin)

    p = sub.add_parser("delete-task", parents=[common])
    p.add_argument("--task-id")
    p.add_argument("--title")
    p.add_argument("--yes", action="store_true")
    p.set_defaults(func=cmd_delete_task)

    a = ap.parse_args()
    DRY["on"] = bool(getattr(a, "dry_run", False))
    a.func(a)
    return 0


if __name__ == "__main__":
    sys.exit(main())
