#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""上海大师赛 · 抓取层（只读，纯标准库；JS 页面才降级到 scrapling）。

数据源与实测（2026-10-11 全量复测，详见 references/sources.md）：
  ✅ 可达：官方英文站（交通/概况/须知/场次/票务/**签表/赛果**）、B站搜索、百度（会限流）、
          **DDG（html.duckduckgo.com，支持 site:）**、**微博帖子正文页**、本地媒体稿（本地宝/澎湃/搜狐/上观）
  ⚠️ 有限流：DDG 连续查询返回 202/空 → 内置退避重试，每期查询数受限；百度/搜狗会出验证码
  ❌ 不可达：小红书笔记正文（登录墙，只能引标题+摘要并标『转述』）、知乎搜索、大众点评、微博搜索页

用户的口径（2026-10-11 确认）：
  · 交通**只看自驾**（公共交通/短驳不再报）
  · 关心：停车停哪条路最近 + 导航到哪、能带什么/不能带什么、赛果与决赛走势、网上大家在讨论什么

用法：
  masters_fetch.py social              # 第三方讨论（B站/百度/公众号/微博/小红书转述/媒体稿），去重后只报新增
  masters_fetch.py social --rescan     # 忽略去重（首次基线/排查用）
  masters_fetch.py official            # 官方站交通/概况/须知/票务正文
  masters_fetch.py scores              # 官方签表 + 赛果（累积，用于算谁已出局）
  masters_fetch.py scores --days all   # 回填全部比赛日（首次建基线用）
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
CACHE = os.environ.get("MASTERS_CACHE") or os.path.expanduser("~/.hermes/cache/shanghai-masters")
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
             "观赛", "须知", "交通", "出行", "换乘", "门票", "实名", "人脸",
             # 2026-10-11 新增（用户关心的四类：带物/自驾/赛况/讨论）
             "泊位", "车位", "临时停车", "导航", "即停即走", "管控", "警方", "指引",
             "水杯", "保温杯", "限带", "违禁", "禁带", "可带", "折叠伞", "三脚架", "独脚架",
             "赛果", "比分", "签表", "种子", "出局", "淘汰", "四强", "半决赛", "决赛", "对阵", "赔率"]
CUR_YEAR = ["2026", "今年", "本届"]
# 硬门槛：必须命中网球大师赛相关词，否则丢弃
TENNIS_GATE = ["网球", "大师赛", "旗忠", "劳力士", "ATP", "atp"]
# 其他「XX大师赛/XX展/其他赛事」噪声：命中即丢
NEG = ["披萨", "冰淇淋", "酒店餐饮食材", "食材展", "展会", "展览会", "装修", "电竞", "游戏",
       "车展", "招聘", "五金", "建材", "台球", "冰壶", "羽毛球", "乒乓球", "狼人杀", "剑网3", "京城大师赛",
       "蒙特卡洛", "罗马", "马德里", "辛辛那提", "迈阿密", "印第安维尔斯", "多伦多", "蒙特利尔",
       "澳网", "法网", "温网", "美网", "耐力赛", "摩托", "赛车",
       # 2026-10-11 实测补：泛「大师赛」噪声（象棋/钢琴…都叫大师赛，会绕过 TENNIS_GATE 的「大师赛」）
       "象棋", "围棋", "国际象棋", "五子棋", "桥牌", "麻将", "斗地主", "钢琴", "弦乐", "管乐",
       "合唱", "舞蹈", "书画", "书法", "作文", "诗词", "厨艺", "咖啡师", "马拉松", "龙舟",
       "武术", "拳击", "健美", "钓鱼", "航模", "机器人"]

# 搜索关键词组（按用户关心的维度，2026-10-11 按用户新需求重排）。
# 用户只看自驾（不看公共交通）、关心带物/赛况/网上讨论；每天跑「核心组 + 轮换 1 组」，控制请求量防限流。
#   · 核心组天天跑：停车自驾、带物安检
#   · 轮换组每天换一个：讨论热点 / 吃饭餐饮 / 观赛周边 / 赛况赔率
KEYWORD_SETS = {
    "停车自驾": ["上海大师赛 停车 自驾 攻略", "旗忠网球中心 停车 泊位 导航"],
    "带物安检": ["上海大师赛 限带物品 清单 水杯", "上海大师赛 安检 禁带 折叠伞"],
    "讨论热点": ["上海大师赛 观赛 体验 吐槽", "旗忠 观赛 攻略 现场"],
    "吃饭餐饮": ["旗忠网球中心 吃饭 餐饮 攻略", "上海大师赛 现场 美食 攻略"],
    "观赛周边": ["上海大师赛 纪念品 周边 攻略", "上海大师赛 签名 训练场 追星"],
    "赛况赔率": ["上海大师赛 四强 决赛 对阵", "上海大师赛 夺冠 赔率 预测"],
}
CORE_GROUPS = ["停车自驾", "带物安检"]
ROTATE_GROUPS = ["讨论热点", "吃饭餐饮", "观赛周边", "赛况赔率"]
# 微博/小红书专项检索词（走 DDG site: 检索；DDG 有限流，每期只跑 core 那一条 + 轮换）
SOCIAL_DDG_CORE = ["上海劳力士大师赛 停车"]
SOCIAL_DDG_ROTATE = ["上海大师赛 观赛 体验", "旗忠网球中心 攻略", "上海大师赛 带什么 现场", "上海大师赛 决赛"]
DDG_BACKOFF = 20.0        # DDG 返回 202/空结果时的退避秒数（实测连续查询会被限流）

OFFICIAL_PAGES = {
    "transport": "https://en.rolexshanghaimasters.com/en/tournament/transportation-information",
    "general": "https://en.rolexshanghaimasters.com/en/tournament/general-information",
    "essential": "https://en.rolexshanghaimasters.com/en/tournament/essential-details",
    "opening": "https://en.rolexshanghaimasters.com/en/tournament/opening-times",
    "tickets": "https://en.rolexshanghaimasters.com/en/tickets/tickets",
}
SCORES = {
    "draw": "https://en.rolexshanghaimasters.com/en/scores/draw",
    "results": "https://en.rolexshanghaimasters.com/en/scores/results",       # 默认最新比赛日
    "results_day": "https://en.rolexshanghaimasters.com/en/scores/results?resultDay=%d",
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


# ── DDG 检索（媒体稿 / 微博 / 小红书 的通用入口）──────────────────
# 实测（2026-10-11）：html.duckduckgo.com 可达且支持 site: ；
#   但连续查询会被限流（返回 202 / 空结果）→ 必须退避重试，且每期查询数要少。
def _ddg_html(kw: str) -> tuple[str, str | None]:
    url = "https://html.duckduckgo.com/html/?q=" + urllib.parse.quote(kw)
    for attempt in range(2):
        try:
            html = http_get(url, referer="https://duckduckgo.com/", timeout=20)
        except Exception as e:  # noqa: BLE001
            if attempt == 0:
                time.sleep(DDG_BACKOFF)
                continue
            return "", "ddg: %s" % e
        if "result__a" in html:
            return html, None
        if attempt == 0:
            time.sleep(DDG_BACKOFF)      # 空结果多为限流，退避后重试一次
    return "", "ddg: 无结果（疑似限流，已退避重试一次）"


def _ddg_results(html: str, limit: int = 8) -> list[tuple[str, str, str]]:
    out = []
    for m in re.finditer(r'result__a"[^>]*href="([^"]+)"[^>]*>(.*?)</a>', html, re.S):
        raw, title = m.group(1), unesc(strip_html(m.group(2)))
        mm = re.search(r"uddg=([^&]+)", raw)
        u = urllib.parse.unquote(mm.group(1)) if mm else raw
        tail = html[m.end():m.end() + 1500]
        sm = re.search(r'result__snippet"[^>]*>(.*?)</a>', tail, re.S)
        snip = unesc(strip_html(sm.group(1))) if sm else ""
        title = re.sub(r"\s+", " ", title).strip()
        snip = re.sub(r"\s+", " ", snip).strip()
        if title and u.startswith("http"):
            out.append((title, u, snip))
        if len(out) >= limit:
            break
    return out


def ddg_search(kw: str, limit: int = 8, host_filter: str | None = None) -> tuple[list[dict], list[str]]:
    html, err = _ddg_html(kw)
    if err:
        return [], [err]
    items = []
    for title, u, snip in _ddg_results(html, limit=limit * 3):
        host = urllib.parse.urlparse(u).netloc.lower()
        if host_filter and host_filter not in host:
            continue
        items.append({"source": "DDG/%s" % (host or "web"), "title": title, "url": u,
                      "snippet": snip[:220], "query": kw})
        if len(items) >= limit:
            break
    return items, []


def fetch_media(kw: str, limit: int = 6) -> list[dict]:
    """媒体稿检索（本地宝/澎湃/搜狐/上观…）——2026 停车警方口径、限带清单全文多来自这类稿件。"""
    items, errs = ddg_search(kw, limit=limit)
    return items or [{"_error": e} for e in errs[:1]]


def fetch_weibo(kw: str, limit: int = 4) -> list[dict]:
    """微博：DDG 找站内帖 → 抓正文。实测 www.weibo.com/<uid>/detail/<id> 页面可直读，
    正文在 og:description（2026-10-11 实测 58KB、无登录墙）。"""
    hits, errs = ddg_search("site:weibo.com " + kw, limit=limit * 3, host_filter="weibo.com")
    out = []
    for it in hits:
        if not re.search(r"(?:detail|status)/\d+", it["url"]):
            continue
        try:
            html = http_get(it["url"], referer="https://weibo.com/", timeout=20)
        except Exception as e:  # noqa: BLE001
            errs.append("weibo: 抓取失败 %s" % e)
            continue
        m = (re.search(r'property="og:description" content="([^"]{20,800})"', html)
             or re.search(r'<meta name="description" content="([^"]{20,800})"', html))
        body = unesc(m.group(1)) if m else ""
        if len(body) < 20:
            errs.append("weibo: 帖子无正文（%s）" % it["url"][-16:])
            continue
        out.append(dict(it, source="微博", snippet=body[:300], url_note="微博帖（正文已抓取）"))
        if len(out) >= limit:
            break
        time.sleep(2.0)
    return out or [{"_error": e} for e in (errs[:2] or ["weibo: 本期无结果"])]


def fetch_xhs(kw: str, limit: int = 6) -> list[dict]:
    """小红书：**只能拿标题+摘要，正文一律登录墙**（2026-10-11 实测）→ 报告里必须标『转述』。"""
    hits, errs = ddg_search("site:xiaohongshu.com " + kw, limit=limit * 2, host_filter="xiaohongshu.com")
    out = [dict(it, source="小红书·转述", url_note="小红书笔记（正文需登录，仅标题/摘要可引）")
           for it in hits if len(it.get("title", "")) > 6]
    return out or [{"_error": e} for e in (errs[:1] or ["xiaohongshu: 本期无结果"])]


# ── 官方签表 / 赛果 ─────────────────────────────────────────────
def parse_draw_players(html: str) -> list[dict]:
    """签表页选手（含种子）：真实结构 <div class="name"><a href="/en/players/x/z355">A. Zverev</a><span>(1)</span>"""
    out, seen = [], set()
    for m in re.finditer(r'<div class="name">\s*<a href="/en/players/[^"]+">([^<]{3,32})</a>\s*'
                         r'(?:<span>\s*\((\d{1,2})\)\s*</span>)?', html):
        name = re.sub(r"\s+", " ", m.group(1)).strip()
        seed = int(m.group(2)) if m.group(2) else None
        if name and name not in seen:
            seen.add(name)
            out.append({"name": name, "seed": seed})
    return out


def parse_results_day(html: str) -> dict:
    """官方赛果页：逐场解析 round/court/双方/比分/胜者。结构见 references/scores-format.md"""
    txt = strip_html(html)
    day = {}
    m = re.search(r"([A-Z][a-z]+day, \w+ \d+, \d{4})\s*\(Day (\d+)\)", txt)
    if m:
        day = {"date": m.group(1), "day": int(m.group(2))}
    matches = []
    doubles_skipped = 0
    for block in re.split(r'<div class="completed-stats"', html)[1:]:
        head = re.search(r'<div class="stats-header">(.*?)</div>', block, re.S)
        head_txt = strip_html(head.group(1)) if head else ""
        rm = re.search(r"Men's ([^.]+)\.", head_txt)
        rnd = ("Men's " + rm.group(1).strip()) if rm else head_txt[:40]
        court = re.sub(r"^Men's [^.]+\.\s*", "", head_txt).split("\n")[0].strip()
        dm = re.search(r"\b(\d{1,2}:\d{2}:\d{2})\b", head_txt)
        dur = dm.group(1) if dm else ""
        players = []
        for pc in re.split(r'<div class="stats-item"', block)[1:]:
            pm = re.search(r'<div class="name">\s*<a href="/en/players/[^"]+">([^<]{3,32})</a>\s*'
                           r'(?:<span>\s*(?:\((\d{1,2})\))?\s*</span>)?', pc)
            if not pm:
                continue
            scores = re.findall(r'<div class="score-item[^"]*">\s*(?:<span>(\d+)</span>)+', pc)
            nums = re.findall(r'<div class="score-item[^"]*">\s*((?:<span>\d+</span>\s*)+)', pc)
            set_scores = [re.findall(r">(\d+)<", n) for n in nums]
            # ⚠️ 注意：赢下一盘的选手也会带 class="score-item won"，所以**不能只看有没有 won**
            #（2026-10-11 实测：Zverev 2 盘 won vs Halys 1 盘 won）。胜者 = won 盘数多者，
            # 平局时用 stats-note 里的 "Game Set and Match <全名>." 兜底。
            won_sets = len(re.findall(r'class="score-item won"', pc))
            players.append({"name": re.sub(r"\s+", " ", pm.group(1)).strip(),
                            "seed": int(pm.group(2)) if pm.group(2) else None,
                            "sets": set_scores, "won_sets": won_sets, "won": won_sets > 0})
        if len(players) < 2:
            continue
        # ⚠️ 单打/双打区分（2026-10-11 实测）：双打块里是 **4 个选手名**（两队各 2 人，每队一个
        # stats-item 内含两个 name 节点），而 stats-header 文案与单打一模一样（都是「Men's Round of 32.」）
        # → 必须数**整块**的 name 节点数，不能只数 stats-item。
        if len(re.findall(r'<div class="name">\s*<a href="/en/players/', block)) != 2:
            doubles_skipped += 1
            continue
        note = re.search(r'<div class="stats-note">(.*?)</div>', block, re.S)
        note_txt = strip_html(note.group(1)) if note else ""
        sm = re.search(r"wins the match\s+([\d\-\(\)\s]+)", note_txt)
        gm = re.search(r"Game Set and Match\s+([A-Z][^.]{2,30})\.", note_txt)
        winner = None
        if gm:                                    # 权威依据：通报里的胜者全名
            surname = gm.group(1).strip().split()[-1].lower().strip(".")
            winner = next((p for p in players
                           if p["name"].split()[-1].lower().strip(".") == surname), None)
        if winner is None:                        # 兜底：won 盘数多者
            winner = max(players, key=lambda p: p["won_sets"])
        loser = next((p for p in players if p is not winner), players[-1])
        matches.append({"round": rnd, "court": court, "duration": dur, "discipline": "singles",
                        "winner": winner, "loser": loser,
                        "score": re.sub(r"\s+", " ", sm.group(1)).strip() if sm else ""})
    return {"day": day, "matches": matches, "doubles_skipped": doubles_skipped}


def do_scores(a) -> dict:
    """官方签表 + 赛果（增量累积到 cache/scores.json，用于算『谁还在、谁已出局』）。"""
    ensure_cache()
    cache_path = os.path.join(CACHE, "scores.json")
    state = {"days": {}, "entry_list": [], "updated_at": None}
    if os.path.exists(cache_path):
        try:
            state = json.load(open(cache_path, encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            pass
    state.setdefault("days", {})
    errors = []

    days_req = getattr(a, "days", None)
    try:
        if days_req == "all":
            latest = parse_results_day(http_get(SCORES["results"]))
            n_max = (latest.get("day") or {}).get("day") or 7
            todo = list(range(1, n_max + 1))
        elif days_req:
            todo = [int(x) for x in str(days_req).split(",")]
        else:
            todo = []          # 默认只取最新比赛日
            latest = parse_results_day(http_get(SCORES["results"]))
            if latest.get("day"):
                state["days"][str(latest["day"]["day"])] = latest
        for n in todo:
            try:
                d = parse_results_day(http_get(SCORES["results_day"] % n))
                if d.get("day"):
                    state["days"][str(d["day"]["day"])] = d
                time.sleep(1.5)
            except Exception as e:  # noqa: BLE001
                errors.append("results day %d: %s" % (n, e))
    except Exception as e:  # noqa: BLE001
        errors.append("results: %s" % e)

    if not state.get("entry_list"):
        try:
            state["entry_list"] = parse_draw_players(http_get(SCORES["draw"]))
        except Exception as e:  # noqa: BLE001
            errors.append("draw: %s" % e)

    state["updated_at"] = datetime.now(CST).isoformat(timespec="seconds")
    tmp = cache_path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=1)
    os.replace(tmp, cache_path)

    matches = [m for d in state["days"].values() for m in d.get("matches", [])]
    losers = {}
    for m in matches:
        ls = m.get("loser") or {}
        if ls.get("name"):
            losers[ls["name"]] = {"seed": ls.get("seed"), "round": m.get("round")}
    seeded_all = [p for p in state.get("entry_list", []) if p.get("seed")]
    out_seeded = sorted([dict(p, lost_in=losers[p["name"]]["round"]) for p in seeded_all if p["name"] in losers],
                        key=lambda x: x["seed"])
    alive_seeded = sorted([p for p in seeded_all if p["name"] not in losers], key=lambda x: x["seed"])
    latest_day = max(state["days"].values(), key=lambda d: (d.get("day") or {}).get("day", 0)) if state["days"] else {}
    ld = latest_day.get("day") or {}
    return {"ok": not errors or bool(matches), "source": "scores",
            "latest_day": ld.get("day"), "latest_date": ld.get("date"),
            "latest_matches": latest_day.get("matches", []),
            "days_cached": sorted(int(k) for k in state["days"]),
            "seeded_total": len(seeded_all),
            "seeded_alive": alive_seeded, "seeded_out": out_seeded,
            "note": "签表页无胜负标记，出局判定来自赛果页累积（首次运行只有最新一天，往后每日累积更完整）",
            "cache": cache_path, "errors": errors[:5]}


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

    # ── DDG 专项（2026-10-11 新增；DDG 有限流，所以给出**每期固定预算**：媒体稿 2 + 微博 1 + 小红书 1）──
    # 媒体稿：2026 停车警方口径、限带清单全文这类内容多登在本地媒体（本地宝/澎湃/搜狐/上观）
    ddg_plan = []
    for g in CORE_GROUPS:
        kw0 = (KEYWORD_SETS.get(g) or [None])[0]
        if kw0:
            ddg_plan.append((g, kw0, fetch_media))
    social_core = (SOCIAL_DDG_CORE or [None])[0]
    social_rot = SOCIAL_DDG_ROTATE[datetime.now(CST).toordinal() % len(SOCIAL_DDG_ROTATE)]
    if social_core:
        ddg_plan.append(("讨论热点", social_core, fetch_weibo))
    ddg_plan.append(("讨论热点", social_rot, fetch_xhs))
    for g, kw, fn in ddg_plan:
        if throttle:
            time.sleep(throttle)
        for it in fn(kw):
            if "_error" in it:
                errors.append(it["_error"])
                continue
            it["group"] = g
            items.append(it)

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

    p = sub.add_parser("scores", parents=[common], help="官方签表 + 赛果（增量累积，用于算谁已出局）")
    p.add_argument("--days", default=None, help="指定比赛日，如 3,4,5；或 all 回填全部（默认只取最新一天）")
    p.set_defaults(func=do_scores)

    p = sub.add_parser("all", parents=[common], help="官方 + 第三方 + 赛果（cron 用）")
    p.add_argument("--group", default="全部",
                   choices=["全部", "核心"] + list(KEYWORD_SETS),
                   help="默认『全部』= 核心组+轮换1组；也可指定单个维度或『核心』")
    p.add_argument("--rescan", action="store_true")
    p.add_argument("--throttle", type=float, default=3.0)
    p.add_argument("--days", default=None, help="赛果回填：3,4,5 或 all")
    p.set_defaults(func=lambda a: {"ok": True, "source": "all",
                                   "official": do_official(a), "social": do_social(a),
                                   "scores": do_scores(a), "parking": do_parking(a)})
    a = ap.parse_args()
    if getattr(a, "limit", None) is None:
        a.limit = 15
    res = a.func(a)
    as_json = getattr(a, "json", False) or a.cmd in ("all", "official", "scores")
    if as_json:
        print(json.dumps(res, ensure_ascii=False, indent=1))
    elif res.get("source") == "scores":
        print("🏁 赛果 ｜ 最新比赛日 %s（Day %s）｜ 已缓存 %s 天（%s）"
              % (res.get("latest_date"), res.get("latest_day"), len(res.get("days_cached") or []),
                 res.get("days_cached")))
        for m in res.get("latest_matches", []):
            w, l = m.get("winner") or {}, m.get("loser") or {}
            print("- [%s｜%s] %s def. %s %s" % (m.get("round"), m.get("court"),
                                                w.get("name"), l.get("name"), m.get("score")))
        print("仍在签表种子: %s" % ("、".join("%d %s" % (p["seed"], p["name"])
                                              for p in res.get("seeded_alive") or []) or "—"))
        print("已出局种子: %s" % ("、".join("%d %s（%s）" % (p["seed"], p["name"], p.get("lost_in"))
                                             for p in res.get("seeded_out") or []) or "无"))
        if res.get("errors"):
            print("⚠️ 异常: %s" % "；".join(res["errors"]))
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
