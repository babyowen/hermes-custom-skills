#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
serp-news-monitor 只读数据探针。

子命令
  stats     D 与之前 N 天的聚合统计、主题对比、程序化风险提示
  sample    D 当日普通来源的确定性随机抽样（按业务日期设种子）
  contents  按 id 批量取正文/摘要（截断），供模型质检用
  official  官网抓取(sourceapi='官网抓取')的数量、最近产出日期、当日记录
  weekday   过去 N 个同星期的数量对比（判断工作日/周末差异）
  state     读写当日运行状态（去重用），落在 config.state_dir

约定
  * 只读：仅 SELECT / SHOW COLUMNS，语句前缀有白名单校验
  * 密码只从环境变量或 ~/.hermes/.env 读取，绝不打印
  * 退出码：0 正常；2 有风险提示(flags)；1 执行失败（连接/参数/权限）
运行环境：~/.serp-monitor-venv/bin/python（需 pymysql）
"""
import argparse
import json
import os
import random
import re
import sys
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone

try:
    import pymysql
except ImportError:  # pragma: no cover
    sys.stderr.write("缺少 pymysql，请用 ~/.serp-monitor-venv/bin/python 运行\n")
    sys.exit(1)

HERE = os.path.dirname(os.path.abspath(__file__))
CST = timezone(timedelta(hours=8))
SECRET_KEYS = ("HOST", "PORT", "NAME", "USER", "PASSWORD")


def die(msg, code=1):
    print(json.dumps({"ok": False, "error": re.sub(r"(?i)(pass[^\s\"']*)[=:]\s*\S+", r"\1=***", str(msg))},
                     ensure_ascii=False), file=sys.stdout)
    sys.exit(code)


def load_config(path=None):
    p = path or os.path.join(HERE, "config.json")
    try:
        with open(p, encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        die("读取 config.json 失败: %s" % e)


def parse_env_file(path):
    """解析 KEY=VALUE 配置行（忽略注释/引号）。"""
    out = {}
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                k = k.strip()
                if k.startswith("SERP_NEWS_DB_"):
                    out[k] = v.strip().strip('"').strip("'")
    except OSError:
        pass
    return out


ENV_FILES = ("~/.hermes/secrets/serp_news_db.env", "~/.hermes/.env")


def db_params(cfg):
    file_env = {}
    for p in ENV_FILES:
        for k, v in parse_env_file(os.path.expanduser(p)).items():
            file_env.setdefault(k, v)
    # 优先级：环境变量 > 私密配置文件 > ~/.hermes/.env
    get = lambda suf, default=None: os.environ.get("SERP_NEWS_DB_" + suf) or file_env.get("SERP_NEWS_DB_" + suf) or default  # noqa: E731
    p = {
        "host": get("HOST"),
        "port": int(get("PORT") or 3306),
        "user": get("USER"),
        "password": get("PASSWORD"),
        "database": get("NAME") or cfg["db"]["name"],
    }
    missing = [k for k in ("host", "user", "password") if not p.get(k)]
    if missing:
        die("缺少数据库连接配置 %s（写入 %s 或环境变量，勿写进命令行）"
            % (",".join("SERP_NEWS_DB_" + k.upper() for k in missing), ENV_FILES[0]))
    return p


def connect(cfg):
    p = db_params(cfg)
    try:
        return pymysql.connect(connect_timeout=cfg["db"]["connect_timeout"],
                               read_timeout=cfg["db"]["read_timeout"],
                               charset="utf8mb4", cursorclass=pymysql.cursors.DictCursor, **p)
    except Exception as e:
        die("数据库连接失败(%s:%s/%s): %s" % (p["host"], p["port"], p["database"], type(e).__name__))


def q(cur, sql, args=None):
    head = re.sub(r"\s+", " ", sql.strip()).upper()
    if not (head.startswith("SELECT") or head.startswith("SHOW COLUMNS")):
        raise RuntimeError("非只读语句被拒绝: %s" % sql[:60])
    t = cfg_global["db"]["table"]
    for bad in cfg_global["db"]["forbidden_tables"]:
        if bad in sql:
            raise RuntimeError("禁止查询 %s" % bad)
    if t not in sql and not head.startswith("SHOW COLUMNS"):
        raise RuntimeError("查询未指向生产表 %s: %s" % (t, sql[:60]))
    cur.execute(sql, args)
    return cur.fetchall()


def jdefault(o):
    if isinstance(o, (date, datetime)):
        return o.isoformat()
    if isinstance(o, bytes):
        return o.decode("utf-8", "replace")
    return str(o)


def emit(obj, as_json, text_lines=None):
    if as_json:
        print(json.dumps(obj, ensure_ascii=False, indent=1, default=jdefault))
    else:
        for ln in (text_lines or []):
            print(ln)


def biz_date(s):
    if not s:
        return (datetime.now(CST).date() - timedelta(days=1))
    return datetime.strptime(s, "%Y-%m-%d").date()


# ---------------------------------------------------------------- stats
def cmd_stats(cur, cfg, a):
    D = biz_date(a.date)
    days = a.baseline_days or cfg["baseline"]["days"]
    base_dates = [D - timedelta(days=i) for i in range(1, days + 1)]
    start = base_dates[-1]
    T = cfg["db"]["table"]

    # 一次拉出 D 及基线期的全部必要字段（仅元数据，不含正文）
    rows = q(cur, f"""SELECT fetchdate d, keyword, score, sourceapi,
                             CHAR_LENGTH(COALESCE(content,'')) clen,
                             (content IS NULL OR content='') c_null,
                             (content IS NOT NULL AND content<>'' AND TRIM(content)='') c_blank,
                             (short_summary IS NULL OR TRIM(COALESCE(short_summary,''))='') sum_missing
                      FROM {T} WHERE fetchdate BETWEEN %s AND %s""", (start, D))

    def blank():
        return {"total": 0, "high": 0, "score_counts": {}, "null_score": 0, "out_of_range": 0,
                "regular": 0, "summary_candidates": 0, "summary_missing": 0, "summary_done": 0,
                "official": 0, "content_empty": 0, "content_blank_only": 0, "sum_score": 0, "scored": 0,
                "themes": defaultdict(int), "high_themes": defaultdict(int)}

    agg = defaultdict(blank)
    officialapi = cfg["official_sourceapi"]
    hi = cfg["high_score_threshold"]
    smin = cfg["summary_score_threshold"]
    for r in rows:
        b = agg[r["d"]]
        b["total"] += 1
        is_off = (r["sourceapi"] == officialapi)
        if is_off:
            b["official"] += 1
        else:
            b["regular"] += 1
            if r["score"] is None:
                b["null_score"] += 1
            else:
                b["score_counts"][str(r["score"])] = b["score_counts"].get(str(r["score"]), 0) + 1
                b["sum_score"] += r["score"]
                b["scored"] += 1
                if r["score"] < 0 or r["score"] > 5:
                    b["out_of_range"] += 1
            if r["c_null"]:
                b["content_empty"] += 1
            elif r["c_blank"]:
                b["content_blank_only"] += 1
            if r["score"] is not None and r["score"] >= smin and not r["c_null"] and not r["c_blank"]:
                b["summary_candidates"] += 1
                if r["sum_missing"]:
                    b["summary_missing"] += 1
                else:
                    b["summary_done"] += 1
        if r["score"] is not None and r["score"] >= hi:
            b["high"] += 1
            b["high_themes"][r["keyword"]] += 1
        b["themes"][r["keyword"]] += 1

    d = agg.get(D, blank())
    base = [agg.get(x, blank()) for x in base_dates]
    valid_days = sum(1 for b in base if b["total"] > 0)
    zero_dates = [x.isoformat() for x, b in zip(base_dates, base) if b["total"] == 0]
    avg_total = (sum(b["total"] for b in base) / valid_days) if valid_days else None
    avg_high = (sum(b["high"] for b in base) / valid_days) if valid_days else None
    avg_score = (d["sum_score"] / d["scored"]) if d["scored"] else None

    dev = cfg["baseline"]["deviation_pct"] / 100.0
    minabs = cfg["baseline"]["min_abs_diff"]

    def compare(cur_n, base_avg, label):
        if base_avg is None or base_avg == 0:
            return {"label": label, "current": cur_n, "baseline_avg": base_avg,
                    "delta_pct": None, "status": "基线为零/不足，不计算百分比"}
        pct = (cur_n - base_avg) / base_avg * 100.0
        big = abs(cur_n - base_avg) >= minabs and abs(pct) >= dev * 100
        return {"label": label, "current": cur_n, "baseline_avg": round(base_avg, 1),
                "delta_pct": round(pct, 1), "abs_diff": round(cur_n - base_avg, 1),
                "status": "需关注" if big else "正常"}

    total_cmp = compare(d["total"], avg_total, "总量")
    high_cmp = compare(d["high"], avg_high, "高分")

    themes = []
    d_themes = {k: v for k, v in d["themes"].items()}
    all_keys = set(d_themes) | {k for b in base for k in b["themes"]}
    for k in sorted(all_keys, key=lambda x: -d_themes.get(x, 0)):
        base_vals = [b["themes"].get(k, 0) for b in base]
        bavg = (sum(base_vals) / valid_days) if valid_days else None
        present_days = sum(1 for v in base_vals if v > 0)
        cur_n = d_themes.get(k, 0)
        t = compare(cur_n, bavg, k) if bavg else {"label": k, "current": cur_n, "baseline_avg": bavg,
                                                  "delta_pct": None, "status": "基线不足，不计算百分比"}
        t["baseline_days_with_data"] = present_days
        t["baseline_daily"] = base_vals
        t["known_theme"] = k in cfg["themes"]
        if cur_n == 0 and present_days >= max(3, valid_days - 2) and valid_days >= 3:
            t["status"] = "主题突然归零，需关注"
        themes.append(t)

    flags = []
    if d["total"] == 0:
        flags.append({"code": "no_data_today", "level": "attention",
                      "msg": "当日无任何记录，可能未开跑或尚未写完，需人工查运行情况"})
    if valid_days < cfg["baseline"]["min_valid_days"]:
        flags.append({"code": "baseline_insufficient", "level": "info",
                      "msg": "基线有效样本仅 %d 天，数量对比仅供参考" % valid_days})
    if zero_dates:
        flags.append({"code": "baseline_zero_record_days", "level": "info",
                      "msg": "基线期零记录日期: %s（属零记录，非未知缺失）" % ",".join(zero_dates)})
    for t in themes:
        if t["status"] == "需关注" or "归零" in str(t["status"]):
            flags.append({"code": "theme_deviation", "level": "attention",
                          "msg": "主题[%s] 当日 %s 条 vs 基线 %.1f 条（%s）" %
                                 (t["label"], t["current"], t["baseline_avg"] or 0, t["status"])})
    if total_cmp["status"] == "需关注":
        flags.append({"code": "total_deviation", "level": "attention", "msg": total_cmp})
    if high_cmp["status"] == "需关注":
        flags.append({"code": "high_deviation", "level": "attention", "msg": high_cmp})
    if d["null_score"]:
        flags.append({"code": "unscored_rows", "level": "attention",
                      "msg": "普通来源有 %d 条 score 为 NULL（未评分）" % d["null_score"]})
    if d["out_of_range"]:
        flags.append({"code": "score_out_of_range", "level": "attention",
                      "msg": "有 %d 条 score 超出 0-5" % d["out_of_range"]})
    if d["summary_missing"]:
        flags.append({"code": "summary_missing", "level": "attention",
                      "msg": "普通来源摘要候选 %d 条中缺摘要 %d 条" % (d["summary_candidates"], d["summary_missing"])})
    if d["official"] == 0:
        flags.append({"code": "official_none_today", "level": "info",
                      "msg": "当日无官网抓取记录（官网可能当天没有新闻，不单独告警）"})

    out = {
        "ok": True, "date": D.isoformat(), "generated_at": datetime.now(CST).isoformat(timespec="seconds"),
        "baseline_days": days, "baseline_dates": [x.isoformat() for x in base_dates],
        "baseline_valid_days": valid_days,
        "d": {"total": d["total"], "high": d["high"], "high_threshold": hi,
              "regular": d["regular"], "official": d["official"],
              "score_counts_nonnull": d["score_counts"], "null_score": d["null_score"],
              "out_of_range": d["out_of_range"], "avg_score_regular_excl_null": round(avg_score, 2) if avg_score is not None else None,
              "summary_candidates": d["summary_candidates"], "summary_done": d["summary_done"],
              "summary_missing": d["summary_missing"],
              "content_empty_string_or_null": d["content_empty"], "content_blank_only": d["content_blank_only"]},
        "theme_breakdown": themes,
        "baseline_total_avg": round(avg_total, 1) if avg_total is not None else None,
        "baseline_high_avg": round(avg_high, 1) if avg_high is not None else None,
        "compare_total": total_cmp, "compare_high": high_cmp,
        "flags": flags,
        "verdict_hint": "attention" if any(f["level"] == "attention" for f in flags) else "normal",
        "boundary": "仅为数据库记录口径，未核验服务器执行日志",
    }
    lines = ["业务日期 %s | 共 %s 条（官网 %s）| 高分 %s | 基线日均 %s（%s 天）| 对比 %s%%"
             % (out["date"], d["total"], d["official"], d["high"],
                out["baseline_total_avg"], valid_days,
                total_cmp.get("delta_pct") if total_cmp.get("delta_pct") is not None else "NA"),
             "评分分布(普通来源,不含NULL):%s | NULL %s | 越界 %s | 均值 %s"
             % (d["score_counts"], d["null_score"], d["out_of_range"], out["d"]["avg_score_regular_excl_null"]),
             "摘要候选 %s / 完成 %s / 缺失 %s | 空正文 %s 条、纯空白 %s 条"
             % (d["summary_candidates"], d["summary_done"], d["summary_missing"],
                d["content_empty"], d["content_blank_only"])]
    for t in themes[:12]:
        lines.append("  主题 %-8s 当日 %4d | 基线日均 %s | 状态 %s" %
                     (t["label"], t["current"], t["baseline_avg"], t["status"]))
    lines.append("提示:" + ("; ".join(f["msg"] if isinstance(f["msg"], str) else json.dumps(f["msg"], ensure_ascii=False) for f in flags) or "无"))
    emit(out, a.json, lines)
    return out


# -------------------------------------------------------------- sample
def cmd_sample(cur, cfg, a):
    D = biz_date(a.date)
    n = a.n or cfg["sample"]["n"]
    T = cfg["db"]["table"]
    rows = q(cur, f"""SELECT id, keyword, score, sourceapi, title, link,
                             CHAR_LENGTH(COALESCE(content,'')) clen,
                             (short_summary IS NULL OR TRIM(COALESCE(short_summary,''))='') sum_missing
                      FROM {T}
                      WHERE fetchdate=%s AND (sourceapi IS NULL OR sourceapi<>%s)""",
             (D, cfg["official_sourceapi"]))
    for r in rows:
        r["has_summary"] = not r["sum_missing"] and r["clen"] > 0
    rnd = random.Random(int(D.strftime("%Y%m%d")))  # 按业务日期设种子，同日可复现
    long_min = cfg["sample"]["long_content_chars"]
    lowmax = cfg["sample"]["low_score_threshold"]
    hi = cfg["high_score_threshold"]
    LONG = lambda r: r["has_summary"] and r["clen"] > long_min  # noqa: E731
    LOW = lambda r: r["score"] is not None and r["score"] <= lowmax  # noqa: E731

    picked = {}
    by_theme = defaultdict(list)
    for r in rows:
        by_theme[r["keyword"]].append(r)
    for k in by_theme:
        rnd.shuffle(by_theme[k])
    thrift = defaultdict(int)  # 已选条数，用于主题均衡

    def take(pred, limit):
        """按主题轮转挑选，优先选得少的主题；同主题内用种子打乱后的顺序。"""
        c = 0
        progress = True
        while c < limit and progress and len(picked) < n:
            progress = False
            for k in sorted(by_theme, key=lambda x: (thrift[x], -len(by_theme[x]), x)):
                lst = by_theme[k]
                for i, r in enumerate(lst):
                    if pred(r):
                        picked[r["id"]] = r
                        thrift[k] += 1
                        lst.pop(i)
                        c += 1
                        progress = True
                        break
                if c >= limit or len(picked) >= n:
                    break
        return c

    # 1) 先满足「有摘要且正文>500字」的硬性条数；2) 补低分样本；3) 补高分样本；4) 按主题轮转补齐
    take(LONG, min(cfg["sample"]["min_long_with_summary"], len(rows)))
    take(LOW, min(cfg["sample"]["low_score_max"], max(0, n - len(picked))))
    take(lambda r: r["score"] is not None and r["score"] >= hi, max(0, n - len(picked)))
    take(lambda r: True, max(0, n - len(picked)))

    sample = sorted(picked.values(), key=lambda r: r["id"])
    covered = sorted({r["keyword"] for r in sample})
    sat = {
        "picked": len(sample), "pool": len(rows),
        "long_with_summary": sum(1 for r in sample if r["has_summary"] and r["clen"] > long_min),
        "low_score": sum(1 for r in sample if r["score"] is not None and r["score"] <= lowmax),
        "high_score": sum(1 for r in sample if r["score"] is not None and r["score"] >= cfg["high_score_threshold"]),
        "themes_covered": covered,
        "uncovered_themes": sorted(set(by_theme) - set(covered)),
    }
    out = {"ok": True, "date": D.isoformat(), "seed": int(D.strftime("%Y%m%d")),
           "sample": [{k: r[k] for k in ("id", "keyword", "score", "title", "link", "clen", "has_summary")} for r in sample],
           "constraints": sat,
           "note": "样本仅代表本次抽检，不可外推为全量错误率"}
    lines = ["抽样 %d/%d 条（长文含摘要 %d，低分 %d，覆盖主题 %d 个）"
             % (sat["picked"], sat["pool"], sat["long_with_summary"], sat["low_score"], len(covered))]
    for r in sample:
        lines.append("  id=%s [%s] score=%s len=%s sum=%s %s" %
                     (r["id"], r["keyword"], r["score"], r["clen"], "Y" if r["has_summary"] else "N", (r["title"] or "")[:46]))
    emit(out, a.json, lines)
    return out


# ------------------------------------------------------------ contents
def cmd_contents(cur, cfg, a):
    ids = [int(x) for x in re.split(r"[,\s]+", a.ids.strip()) if x]
    if not ids:
        die("--ids 为空")
    mx = a.max_chars or cfg["sample"]["content_excerpt_chars"]
    T = cfg["db"]["table"]
    ph = ",".join(["%s"] * len(ids))
    rows = q(cur, f"""SELECT id, keyword, score, sourceapi, title, link, region,
                             CHAR_LENGTH(COALESCE(content,'')) clen,
                             CHAR_LENGTH(COALESCE(short_summary,'')) slen,
                             content, short_summary
                      FROM {T} WHERE id IN ({ph})""", tuple(ids))
    out = {"ok": True, "requested": ids, "found": len(rows), "missing_ids": sorted(set(ids) - {r["id"] for r in rows}), "records": []}
    for r in rows:
        body = r["content"] or ""
        trunc = len(body) > mx
        out["records"].append({
            "id": r["id"], "keyword": r["keyword"], "score": r["score"], "sourceapi": r["sourceapi"],
            "title": r["title"], "link": r["link"], "region": r["region"],
            "content_len": r["clen"], "summary_len": r["slen"],
            "content_truncated": trunc,
            "content_excerpt": body[:mx] + ("\n...[已截断，原文共 %d 字，如需上下文用 read 模式或加大 --max-chars]" % r["clen"] if trunc else ""),
            "short_summary": r["short_summary"],
        })
    lines = ["取回 %d/%d 条正文（每条约 %d 字上限）" % (len(rows), len(ids), mx)]
    for r in out["records"]:
        lines.append("  id=%s [%s] score=%s src=%s 正文%d字 摘要%d字 %s"
                     % (r["id"], r["keyword"], r["score"], r["sourceapi"], r["content_len"], r["summary_len"], r["title"]))
        lines.append("    摘要: %s" % ((r["short_summary"] or "")[:120].replace("\n", " ") or "(无)"))
        lines.append("    正文: %s" % r["content_excerpt"][:300].replace("\n", " "))
    if out["missing_ids"]:
        lines.append("  未取到: %s" % out["missing_ids"])
    emit(out, a.json, lines)
    return out


# ------------------------------------------------------------ official
def cmd_official(cur, cfg, a):
    D = biz_date(a.date)
    look = cfg["official_lookback_days"]
    T, api = cfg["db"]["table"], cfg["official_sourceapi"]
    per_day = q(cur, f"""SELECT fetchdate d, COUNT(*) n FROM {T}
                         WHERE sourceapi=%s AND fetchdate BETWEEN %s AND %s
                         GROUP BY fetchdate ORDER BY fetchdate DESC""", (api, D - timedelta(days=look - 1), D))
    last = q(cur, f"SELECT MAX(fetchdate) d FROM {T} WHERE sourceapi=%s", (api,))
    today = q(cur, f"""SELECT id, keyword, score, title, link, CHAR_LENGTH(COALESCE(content,'')) clen,
                              CHAR_LENGTH(COALESCE(short_summary,'')) slen
                       FROM {T} WHERE sourceapi=%s AND fetchdate=%s ORDER BY id""", (api, D))
    zero_days = (D - per_day[0]["d"]).days if per_day else None
    out = {"ok": True, "date": D.isoformat(), "lookback_days": look,
           "count_by_date": [{"date": r["d"], "n": r["n"]} for r in per_day],
           "today_count": len(today),
           "has_records": len(today) > 0,
           "verdict_line": ("官网：有，当日 %d 条" % len(today)) if today else "官网：当日无抓取记录",
           "last_date_with_records": last[0]["d"] if last and last[0]["d"] else None,
           "days_since_last": zero_days,
           "today_records": today,
           "boundary": "只看库内官网抓取记录的有/无，不访问官网页面、不推断漏采；执行日志未验证（上海任务）"}
    lines = ["官网：%s ｜ 最近一次产出 %s ｜ 回看 %d 天分布 %s"
             % ("有" if today else "当日无抓取记录", out["last_date_with_records"], look,
                ", ".join("%s:%d" % (r["d"], r["n"]) for r in per_day) or "无")]
    for r in today:
        lines.append("  id=%s score=%s len=%s %s" % (r["id"], r["score"], r["clen"], (r["title"] or "")[:60]))
    emit(out, a.json, lines)
    return out


# ------------------------------------------------------------- weekday
def cmd_weekday(cur, cfg, a):
    D = biz_date(a.date)
    weeks = a.weeks or 4
    T = cfg["db"]["table"]
    dates = [D - timedelta(days=7 * i) for i in range(1, weeks + 1)]
    rows = q(cur, f"""SELECT fetchdate d, COUNT(*) n, SUM(CASE WHEN score>=%s THEN 1 ELSE 0 END) h
                      FROM {T} WHERE fetchdate IN ({', '.join(['%s'] * len(dates))})
                      GROUP BY fetchdate""", (cfg["high_score_threshold"],) + tuple(dates))
    m = {r["d"]: r for r in rows}
    out = {"ok": True, "date": D.isoformat(), "weekday": D.strftime("%A"), "weeks": weeks,
           "same_weekday": [{"date": x.isoformat(), "total": int(m.get(x, {}).get("n") or 0),
                             "high": int(m.get(x, {}).get("h") or 0)} for x in dates]}
    emit(out, a.json, ["过去 %d 个%s：%s" % (weeks, D.strftime("%A"),
          ", ".join("%s:%d(高%d)" % (i["date"], i["total"], i["high"]) for i in out["same_weekday"]))])
    return out


# --------------------------------------------------------------- state
def cmd_state(cur, cfg, a):
    d = os.path.expanduser(cfg["state_dir"])
    os.makedirs(d, exist_ok=True)
    f = os.path.join(d, "%s.json" % biz_date(a.date).isoformat())
    cur_state = {}
    if os.path.exists(f):
        with open(f, encoding="utf-8") as fh:
            cur_state = json.load(fh)
    if a.merge:
        try:
            cur_state.update(json.loads(a.merge))
        except Exception as e:
            die("--merge 不是合法 JSON: %s" % e)
        cur_state["updated_at"] = datetime.now(CST).isoformat(timespec="seconds")
        with open(f, "w", encoding="utf-8") as fh:
            json.dump(cur_state, fh, ensure_ascii=False, indent=1)
    out = {"ok": True, "file": f, "state": cur_state}
    emit(out, a.json, ["状态文件 %s\n%s" % (f, json.dumps(cur_state, ensure_ascii=False, indent=1))])
    return out


def main():
    global cfg_global
    ap = argparse.ArgumentParser(description="serp_news 只读巡检探针")
    ap.add_argument("--config", help="config.json 路径")
    ap.add_argument("--json", action="store_true", help="JSON 输出")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("stats"); p.add_argument("--date"); p.add_argument("--baseline-days", type=int)
    p = sub.add_parser("sample"); p.add_argument("--date"); p.add_argument("--n", type=int)
    p = sub.add_parser("contents"); p.add_argument("--ids", required=True); p.add_argument("--max-chars", type=int)
    p = sub.add_parser("official"); p.add_argument("--date")
    p = sub.add_parser("weekday"); p.add_argument("--date"); p.add_argument("--weeks", type=int)
    p = sub.add_parser("state"); p.add_argument("--date"); p.add_argument("--merge")
    args = ap.parse_args()

    cfg_global = load_config(args.config)
    conn = connect(cfg_global)
    cur = conn.cursor()
    try:
        result = {"stats": cmd_stats, "sample": cmd_sample, "contents": cmd_contents,
                  "official": cmd_official, "weekday": cmd_weekday, "state": cmd_state}[args.cmd](cur, cfg_global, args)
    except RuntimeError as e:
        die(str(e))
    finally:
        conn.close()
    if args.cmd != "state" and result.get("verdict_hint") == "attention":
        sys.exit(2)
    sys.exit(0)


if __name__ == "__main__":
    main()
