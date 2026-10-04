#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""上海大师赛 · 抓取层（只读，纯标准库；JS 页面才降级到 scrapling）。

为什么是这些源（2026-10-04 实测，详见 references/sources.md）：
  ✅ 可达：B站搜索页、搜狗微信（公众号文章）、官方英文站（交通/概况/须知）、atp1000.cn 球迷站、本地媒体
  ❌ 不可达：小红书（登录墙）、微博（登录墙）、知乎搜索（反爬）、大众点评（滑块验证）
  ⚠️ 通用搜索必须硬过滤「斯诺克大师赛」——完全不同的赛事，污染极重且 -斯诺克 排除无效

用法：
  masters_fetch.py social              # B站 + 公众号 + 球迷站，去重后只报新增
  masters_fetch.py social --rescan     # 忽略去重（首次基线/排查用）
  masters_fetch.py official            # 官方站交通/概况/须知/票务正文
  masters_fetch.py all --json          # 组合（cron 用这个）
  masters_fetch.py parking             # OSM 周边停车场（实测数据稀疏，仅供参考）
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from typing import NoReturn

CST = timezone(timedelta(hours=8))
CACHE = os.path.expanduser("~/.hermes/cache/shanghai-masters")
SEEN = os.path.join(CACHE, "seen.json")
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")
SCRAPLING = os.path.expanduser("~/.scrapling-venv/bin/scrapling")
QIZHONG = (31.0456, 121.3645)

# ── 过滤与打分词表 ───────────────────────────────────────────────
BLACK = ["斯诺克", "snooker", "奥沙利文", "丁俊晖", "特鲁姆普", "塞尔比", "斯佳辉",
         "国锦赛", "中式台球", "台球", "九球", "World Snooker"]
STRONG = ["旗忠", "元江路", "上海大师赛", "劳力士大师赛", "上海网球大师赛", "ATP1000", "atp 1000",
          "网球大师赛", "中央球场", "大师赛"]
PRACTICAL = ["停车", "自驾", "接驳", "班车", "短驳", "地铁", "末班车", "打车", "滴滴", "网约车",
             "安检", "入场", "进场", "退场", "散场", "纪念品", "周边", "吃饭", "餐饮", "美食",
             "攻略", "体验", "避坑", "排队", "看台", "视野", "座位", "签名", "训练场", "天气",
             "观赛", "须知", "交通", "出行", "换乘", "门票", "实名", "人脸"]
CUR_YEAR = ["2026", "今年", "本届"]
# 硬门槛：必须命中网球大师赛相关词，否则丢弃
TENNIS_GATE = ["网球", "大师赛", "旗忠", "劳力士", "ATP", "atp"]
# 其他「XX大师赛/XX展/其他赛事」噪声：命中即丢
NEG = ["披萨", "冰淇淋", "酒店餐饮食材", "食材展", "展会", "展览会", "装修", "电竞", "游戏",
       "车展", "招聘", "五金", "建材", "台球", "冰壶", "羽毛球", "乒乓球",
       "蒙特卡洛", "罗马", "马德里", "辛辛那提", "迈阿密", "印第安维尔斯", "多伦多", "蒙特利尔",
       "澳网", "法网", "温网", "美网", "耐力赛", "摩托", "赛车"]

# 搜索关键词组（按用户关心的维度）。每天只跑「核心组 + 轮换 1 组」，避免请求量过大被限流：
#   · 核心组天天跑：停车自驾、交通往返（用户主要关心停车与往返）
#   · 轮换组每天换一个：吃饭餐饮 / 入场须知 / 观赛周边 / 体验口碑
KEYWORD_SETS = {
    "停车自驾": ["上海网球大师赛 停车 自驾 攻略", "旗忠网球中心 停车 换乘"],
    "交通往返": ["旗忠网球中心 交通 地铁 接驳 攻略", "上海大师赛 退场 打车 排队"],
    "吃饭餐饮": ["旗忠网球中心 吃饭 餐饮 攻略", "上海大师赛 现场 美食 攻略"],
    "入场须知": ["上海大师赛 入场 安检 须知", "上海大师赛 禁带物品 观赛 规则"],
    "观赛周边": ["上海大师赛 纪念品 周边 攻略", "上海大师赛 签名 训练场 追星"],
    "体验口碑": ["上海网球大师赛 观赛 体验 攻略", "上海大师赛 观赛 避坑 感受"],
}
CORE_GROUPS = ["停车自驾", "交通往返"]
ROTATE_GROUPS = ["吃饭餐饮", "入场须知", "观赛周边", "体验口碑"]

OFFICIAL_PAGES = {
    "transport": "https://en.rolexshanghaimasters.com/en/tournament/transportation-information",
    "general": "https://en.rolexshanghaimasters.com/en/tournament/general-information",
    "essential": "https://en.rolexshanghaimasters.com/en/tournament/essential-details",
    "opening": "https://en.rolexshanghaimasters.com/en/tournament/opening-times",
    "tickets": "https://en.rolexshanghaimasters.com/en/tickets/tickets",
}


def die(msg: str) -> NoReturn:
    print(json.dumps({"_run_failed": True, "error": msg}, ensure_ascii=False))
    sys.exit(1)


def ensure_cache() -> None:
    os.makedirs(os.path.join(CACHE, "daily"), exist_ok=True)


def http_get(url: str, referer: str | None = None, timeout: int = 25, ua: str | None = None) -> str:
    h = {"User-Agent": ua or UA, "Accept-Language": "zh-CN,zh;q=0.9"}
    if referer:
        h["Referer"] = referer
    req = urllib.request.Request(url, headers=h)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        raw = r.read()
    for enc in ("utf-8", "gbk", "latin-1"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", "ignore")


def strip_html(html: str) -> str:
    html = re.sub(r"<(script|style|noscript)[^>]*>.*?</\1>", " ", html, flags=re.S | re.I)
    html = re.sub(r"<br\s*/?>|</p>|</div>|</li>", "\n", html, flags=re.I)
    txt = re.sub(r"<[^>]+>", " ", html)
    txt = (txt.replace("&nbsp;", " ").replace("&amp;", "&").replace("&quot;", '"')
              .replace("&#39;", "'").replace("&lt;", "<").replace("&gt;", ">")
              .replace("&hellip;", "…").replace("&ldquo;", "“").replace("&rdquo;", "”")
              .replace("&mdash;", "—").replace("&rarr;", "→"))
    txt = re.sub(r"[ \t\u00a0]+", " ", txt)
    txt = re.sub(r"\n\s*\n+", "\n", txt)
    return txt.strip()


def scrapling_fetch(url: str, out_md: str, ai_targeted: bool = True) -> str:
    """JS 页面降级方案：调 scrapling CLI（stealthy-fetch）。失败返回空串。"""
    if not os.path.exists(SCRAPLING):
        return ""
    cmd = [SCRAPLING, "extract", "stealthy-fetch", url, out_md, "--headless", "--network-idle"]
    if ai_targeted:
        cmd.append("--ai-targeted")
    try:
        subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    except subprocess.TimeoutExpired:
        return ""
    if os.path.exists(out_md):
        try:
            return open(out_md, encoding="utf-8", errors="ignore").read()
        except OSError:
            return ""
    return ""


def unesc(s: str) -> str:
    return (s.replace("&amp;", "&").replace("&quot;", '"').replace("&#39;", "'")
             .replace("&lt;", "<").replace("&gt;", ">").replace("&nbsp;", " "))


def fingerprint(s: str) -> str:
    norm = re.sub(r"[\s\W_]+", "", s or "")[:60]
    return hashlib.sha1(norm.encode("utf-8")).hexdigest()[:12]


def score(text: str) -> tuple[int, dict]:
    t = (text or "").lower()
    black = sum(1 for w in BLACK if w.lower() in t)
    strong = sum(1 for w in STRONG if w.lower() in t)
    pract = sum(1 for w in PRACTICAL if w.lower() in t)
    cur = sum(1 for w in CUR_YEAR if w.lower() in t)
    s = 3 * strong + 2 * pract + (3 if cur else 0) - 8 * black
    return s, {"strong": strong, "practical": pract, "cur_year": cur, "blacklist": black}


# ── 各源抓取 ────────────────────────────────────────────────────
def fetch_bilibili(kw: str, limit: int = 6) -> list[dict]:
    url = "https://search.bilibili.com/all?keyword=" + urllib.parse.quote(kw)
    try:
        html = http_get(url, referer="https://www.bilibili.com/")
    except Exception as e:  # noqa: BLE001
        return [{"_error": "bilibili: %s" % e}]
    out, seen_bv = [], set()
    # 真实结构（2026-10-04 实测）：<a href="//www.bilibili.com/video/BVxxx/" ...><h3 class="bili-video-card__info--tit" title="真实标题">
    cards = re.findall(r'href="(//www\.bilibili\.com/video/(BV[0-9A-Za-z]{10})/)"[^>]*>\s*'
                       r'<h3 class="bili-video-card__info--tit" title="([^"]+)"', html)
    if not cards:  # 兜底：BV 与标题按出现顺序配对
        bvs = []
        for m in re.finditer(r'//www\.bilibili\.com/video/(BV[0-9A-Za-z]{10})/', html):
            if m.group(1) not in bvs:
                bvs.append(m.group(1))
        titles = re.findall(r'bili-video-card__info--tit" title="([^"]+)"', html)
        cards = [(None, bv, t) for bv, t in zip(bvs, titles)]
    for _href, bv, raw_title in cards:
        title = re.sub(r"\s+", " ", unesc(strip_html(raw_title))).strip()
        if bv in seen_bv or len(title) < 6:
            continue
        if re.fullmatch(r"[\d.万\s]+\s+[\d.]+\s+\d+:\d+", title):   # "664 0 02:30" 之类
            continue
        seen_bv.add(bv)
        out.append({"source": "B站", "title": title,
                    "url": "https://www.bilibili.com/video/" + bv, "snippet": "", "query": kw})
        if len(out) >= limit:
            break
    return out


def fetch_baidu(kw: str, limit: int = 6) -> list[dict]:
    """百度搜索结果（2026-10-04 实测可用；Bing 命中 0、头条是噪声、搜狗微信常触发验证码）。"""
    url = "https://www.baidu.com/s?wd=" + urllib.parse.quote(kw)
    try:
        html = http_get(url, referer="https://www.baidu.com/")
    except Exception as e:  # noqa: BLE001
        return [{"_error": "baidu: %s" % e}]
    if "安全验证" in html or "wappass" in html:
        return [{"_error": "baidu: 触发安全验证（本次跳过）"}]
    out = []
    blocks = re.split(r"<h3[^>]*class=\"[^\"]*\bt\b[^\"]*\"[^>]*>", html)[1:]
    for b in blocks:
        m = re.search(r'<a[^>]*href="([^"]+)"[^>]*>(.*?)</a>', b, re.S)
        if not m:
            continue
        href, title = m.group(1), strip_html(m.group(2))
        title = re.sub(r"\s+", " ", title).strip()
        if len(title) < 8:
            continue
        absm = re.search(r'class="[^"]*(?:abstract|content-right)[^"]*"[^>]*>(.*?)</(?:span|div)>', b, re.S)
        snippet = strip_html(absm.group(1))[:220] if absm else ""
        site = re.search(r'class="[^"]*c-color-gray[^"]*"[^>]*>(.*?)</span>', b, re.S)
        out.append({"source": "百度/%s" % (strip_html(site.group(1))[:18] if site else "网页"),
                    "title": title, "url": href.replace("&amp;", "&"), "snippet": snippet, "query": kw,
                    "url_note": "百度跳转链接"})
        if len(out) >= limit:
            break
    return out


def fetch_sogou_wechat(kw: str, limit: int = 6) -> list[dict]:
    url = "https://weixin.sogou.com/weixin?type=2&query=" + urllib.parse.quote(kw)
    try:
        html = http_get(url, referer="https://weixin.sogou.com/")
    except Exception as e:  # noqa: BLE001
        return [{"_error": "sogou: %s" % e}]
    if "请输入验证码" in html or "antispider" in html:
        return [{"_error": "sogou: 触发验证码（本次跳过）"}]
    out = []
    blocks = re.split(r'<li[^>]*id="sogou_vr_11002601_box_', html)
    for b in blocks[1:]:
        m = re.search(r'<h3>\s*<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', b, re.S)
        if not m:
            continue
        href, title = m.group(1), strip_html(m.group(2))
        sn = re.search(r'class="txt-info"[^>]*>(.*?)</p>', b, re.S)
        snippet = strip_html(sn.group(1)) if sn else ""
        title = re.sub(r"\s+", " ", title).strip()
        if not title:
            continue
        full = href if href.startswith("http") else "https://weixin.sogou.com" + href
        full = full.replace("&amp;", "&")
        out.append({"source": "公众号", "title": title, "url": full, "snippet": snippet[:220],
                    "query": kw, "url_note": "搜狗跳转链接（含时效 token，需在浏览器打开）"})
        if len(out) >= limit:
            break
    return out


def fetch_atp1000(limit: int = 8) -> list[dict]:
    """球迷站「观赛指南」栏目（连载，含餐饮/交通实操）。"""
    try:
        html = http_get("https://www.atp1000.cn/list-guide.html")
    except Exception as e:  # noqa: BLE001
        return [{"_error": "atp1000: %s" % e}]
    out = []
    for m in re.finditer(r'href="(/view-guide-\d+\.html)"[^>]*title="([^"]+)"', html):
        out.append({"source": "球迷站atp1000", "title": m.group(2).strip(),
                    "url": "https://www.atp1000.cn" + m.group(1), "snippet": "", "query": "观赛指南栏目"})
        if len(out) >= limit:
            break
    if not out:
        for m in re.finditer(r'href="(/view-guide-\d+\.html)"[^>]*>(.*?)</a>', html, re.S):
            t = strip_html(m.group(2))
            if len(t) > 8:
                out.append({"source": "球迷站atp1000", "title": t, "url": "https://www.atp1000.cn" + m.group(1),
                            "snippet": "", "query": "观赛指南栏目"})
            if len(out) >= limit:
                break
    return out


def do_social(a) -> dict:
    ensure_cache()
    limit = getattr(a, "limit", 15)
    rescan = getattr(a, "rescan", False)
    group = getattr(a, "group", "全部")
    throttle = getattr(a, "throttle", 3.0)
    if group == "核心":
        grouped = CORE_GROUPS
    elif group and group != "全部":
        grouped = [group]
    else:
        # 默认：核心组 + 按日期轮换 1 个组（控制请求量，防限流）
        rota = ROTATE_GROUPS[datetime.now(CST).toordinal() % len(ROTATE_GROUPS)]
        grouped = CORE_GROUPS + [rota]
    items, errors = [], []
    first = True
    for g in grouped:
        for kw in KEYWORD_SETS.get(g, []):
            if not first and throttle:
                time.sleep(throttle)          # 节流：搜狗连续请求容易触发验证码
            first = False
            for fn in (fetch_bilibili, fetch_baidu, fetch_sogou_wechat):
                for it in fn(kw):
                    if "_error" in it:
                        errors.append(it["_error"])
                        continue
                    it["group"] = g
                    items.append(it)
    items += [dict(it, group="观赛指南") for it in fetch_atp1000()]

    scored, dropped_neg, dropped_offtopic = [], 0, 0
    seen_fp = set()
    for it in items:
        txt = "%s %s %s" % (it.get("title", ""), it.get("snippet", ""), it.get("query", ""))
        if any(w in txt for w in NEG):        # 不是网球大师赛的其他展会/赛事
            dropped_neg += 1
            continue
        if not any(w in txt for w in TENNIS_GATE):   # 硬门槛：必须是网球大师赛相关
            dropped_offtopic += 1
            continue
        # B站标题短而具体：要求标题本身带赛事名，避免「上海自驾停车攻略」这类泛视频混入
        if it.get("source") == "B站" and not any(w in (it.get("title") or "")
                                                 for w in ("大师赛", "旗忠", "劳力士", "ATP", "atp")):
            dropped_offtopic += 1
            continue
        fp = fingerprint(it.get("title", ""))
        if fp in seen_fp:                     # 同一次运行内：同标题（多关键词命中）只留第一条
            continue
        seen_fp.add(fp)
        s, detail = score(txt)
        if detail["blacklist"]:
            continue
        if s < 3:
            continue
        scored.append(dict(it, score=s, score_detail=detail, fp=fp))
    scored.sort(key=lambda x: -x["score"])

    seen = {}
    if os.path.exists(SEEN):
        try:
            seen = json.load(open(SEEN, encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            seen = {}
    today = datetime.now(CST).date().isoformat()
    fresh, dup = [], 0
    for it in scored:
        if it["fp"] in seen and not rescan:
            dup += 1
            continue
        seen.setdefault(it["fp"], {"first_seen": today, "title": it["title"], "source": it["source"],
                                   "url": it["url"], "group": it.get("group")})
        fresh.append(it)
    tmp = SEEN + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(seen, f, ensure_ascii=False, indent=1)
    os.replace(tmp, SEEN)

    day_file = os.path.join(CACHE, "daily", "%s.json" % today)
    with open(day_file, "w", encoding="utf-8") as f:
        json.dump({"date": today, "new": fresh, "dup_skipped": dup}, f, ensure_ascii=False, indent=1)

    return {"ok": True, "date": today, "source": "social", "groups": grouped,
            "stats": {"fetched": len(items), "kept": len(scored), "new": len(fresh),
                      "dup_skipped": dup, "seen_total": len(seen), "dropped_neg": dropped_neg,
                      "dropped_offtopic": dropped_offtopic},
            "errors": sorted(set(errors))[:6],
            "day_file": day_file,
            "new_items": fresh[:limit]}


def do_official(a) -> dict:
    ensure_cache()
    pages = {}
    for key, url in OFFICIAL_PAGES.items():
        txt, tier = "", "urllib"
        try:
            txt = strip_html(http_get(url))
        except Exception:  # noqa: BLE001
            txt = ""
        if len(txt) < 1500:
            out_md = os.path.join(CACHE, "official_%s.md" % key)
            txt2 = scrapling_fetch(url, out_md)
            if len(txt2 or "") > len(txt):
                txt, tier = txt2, "scrapling-stealthy"
        path = os.path.join(CACHE, "official_%s.txt" % key)
        if txt:
            with open(path, "w", encoding="utf-8") as f:
                f.write(txt)
        pages[key] = {"url": url, "chars": len(txt), "tier": tier,
                      "file": path if txt else None,
                      # 只回带实操关键词的片段，避免把整页灌进上下文
                      "relevant": [l.strip() for l in txt.split("\n")
                                   if len(l.strip()) > 25 and any(w in l for w in
                                       ("metro", "Metro", "taxi", "Taxi", "shuttle", "Shuttle", "Gate",
                                        "gate", "Parking", "parking", "bus", "Bus", "Line", "session",
                                        "prohibited", "not allowed", "entry", "Entry"))][:25]}
    return {"ok": True, "source": "official", "pages": pages,
            "cached": [p["file"] for p in pages.values() if p["file"]]}


def do_parking(a) -> dict:
    """OSM 周边停车场（低价值参考源）——**任何失败都不许影响主流程**。"""
    q = ('[out:json][timeout:25];(node["amenity"="parking"](around:3000,%.4f,%.4f);'
         'way["amenity"="parking"](around:3000,%.4f,%.4f););out center tags;' % (QIZHONG + QIZHONG))
    url = "https://overpass-api.de/api/interpreter?" + urllib.parse.urlencode({"data": q})
    try:
        d = json.loads(http_get(url, timeout=45, ua="curl/8.5"))
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "source": "osm-overpass", "error": "Overpass 查询失败：%s" % e,
                "note": "低价值源，失败不影响报告；停车方案以官方交通页与媒体攻略为准。"}
    els = d.get("elements", [])
    named = [e.get("tags", {}).get("name") for e in els if e.get("tags", {}).get("name")]
    note = ("OSM 该区域数据稀疏：3km 内 %d 处停车场，其中具名仅 %d 处、均无容量字段 —— "
            "仅可参考『周边存在若干社会停车场』，具体停车方案以官方交通页与公众号攻略为准。"
            % (len(els), len(named)))
    return {"ok": True, "source": "osm-overpass", "count": len(els), "named": named[:10],
            "note": note, "coords": {"lat": QIZHONG[0], "lon": QIZHONG[1]}}


def main() -> int:
    ap = argparse.ArgumentParser(description="上海大师赛抓取层（只读）")
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--json", action="store_true")
    common.add_argument("--limit", type=int, default=None, help="最多返回几条新增（默认 15）")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--limit", type=int, default=None, help="最多返回几条新增（默认 15）")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("social", parents=[common], help="第三方讨论/攻略抓取（B站+公众号+球迷站）")
    p.add_argument("--group", default="全部",
                   choices=["全部", "核心"] + list(KEYWORD_SETS),
                   help="默认『全部』= 核心组+轮换1组；也可指定单个维度或『核心』")
    p.add_argument("--rescan", action="store_true", help="忽略去重，重新报全部（基线/排查）")
    p.add_argument("--throttle", type=float, default=3.0, help="每次搜索之间的间隔秒数（默认 3，防验证码）")
    p.set_defaults(func=do_social)

    p = sub.add_parser("official", parents=[common], help="官方站正文（交通/概况/须知/场次/票务）")
    p.set_defaults(func=do_official)

    p = sub.add_parser("parking", parents=[common], help="OSM 周边停车场（低价值，参考）")
    p.set_defaults(func=do_parking)

    p = sub.add_parser("all", parents=[common], help="官方 + 第三方（cron 用）")
    p.add_argument("--group", default="全部",
                   choices=["全部", "核心"] + list(KEYWORD_SETS),
                   help="默认『全部』= 核心组+轮换1组；也可指定单个维度或『核心』")
    p.add_argument("--rescan", action="store_true")
    p.add_argument("--throttle", type=float, default=3.0)
    p.set_defaults(func=lambda a: {"ok": True, "source": "all",
                                   "official": do_official(a), "social": do_social(a),
                                   "parking": do_parking(a)})
    a = ap.parse_args()
    if getattr(a, "limit", None) is None:
        a.limit = 15
    res = a.func(a)
    as_json = getattr(a, "json", False) or a.cmd in ("all", "official")
    if as_json:
        print(json.dumps(res, ensure_ascii=False, indent=1))
    else:
        st = res.get("stats", {})
        print("🔎 抓取 %s｜扫描 %s 条，保留 %s 条，**新增 %s 条**（去重跳过 %s，库内累计 %s）"
              % (res.get("date", ""), st.get("fetched"), st.get("kept"), st.get("new"),
                 st.get("dup_skipped"), st.get("seen_total")))
        for it in res.get("new_items", []):
            print("- [%s｜%s] %s" % (it.get("source"), it.get("group"), it.get("title")))
            if it.get("snippet"):
                print("   %s" % it["snippet"][:160])
            print("   %s" % it.get("url"))
        if res.get("errors"):
            print("⚠️ 源异常：%s" % "；".join(res["errors"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
