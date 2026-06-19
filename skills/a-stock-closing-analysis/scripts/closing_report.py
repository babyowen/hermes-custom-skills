#!/usr/bin/env python3
"""
A股收盘日报生成器 V3
每天16:00运行，调用东方财富妙想三个mx技能查询数据，生成收盘日报。
"""

import subprocess, json, os, re, time, sys
from pathlib import Path
from datetime import datetime, date
from concurrent.futures import ThreadPoolExecutor, as_completed
from duckduckgo_search import DDGS

# ==================== A股交易日历 ====================
# 2026年沪深北交易所节假日休市安排
# 来源：沪深北交易所公告（2025-12-22发布）
_HOLIDAYS_2026 = [
    # 元旦：1月1日(四) ~ 1月3日(六)
    (date(2026,1,1), date(2026,1,3)),
    # 春节：2月14日(六) ~ 2月23日(一)  [2/14周六连续休假]
    (date(2026,2,14), date(2026,2,23)),
    # 清明节：4月4日(六) ~ 4月6日(一)
    (date(2026,4,4), date(2026,4,6)),
    # 劳动节：5月1日(五) ~ 5月5日(二)
    (date(2026,5,1), date(2026,5,5)),
    # 端午节：6月19日(五) ~ 6月21日(日)
    (date(2026,6,19), date(2026,6,21)),
    # 中秋节：9月25日(五) ~ 9月27日(日)
    (date(2026,9,25), date(2026,9,27)),
    # 国庆节：10月1日(四) ~ 10月7日(三)
    (date(2026,10,1), date(2026,10,7)),
]

def is_trading_day(d: date = None) -> bool:
    """判断给定日期是否为A股交易日"""
    if d is None:
        d = date.today()
    # 周末休市
    if d.weekday() >= 5:  # Saturday=5, Sunday=6
        return False
    # 节假日休市
    for start, end in _HOLIDAYS_2026:
        if start <= d <= end:
            return False
    return True

MX_DATA = os.path.expanduser("~/.hermes/skills/mx-data/mx_data.py")
MX_SEARCH = os.path.expanduser("~/.hermes/skills/mx-search/mx_search.py")
MX_XUANGU = os.path.expanduser("~/.hermes/skills/mx-xuangu/mx_xuangu.py")
VENV_PYTHON = "/home/ubuntu/.hermes/hermes-agent/venv/bin/python3"
CACHE_DIR = Path.home() / ".hermes" / "cache" / "a-stock-closing"
OUTPUT_DIR = CACHE_DIR / "reports"
EXTREMES_FILE = CACHE_DIR / "_extremes.json"
TIMEOUT = 25

os.environ["MX_APIKEY"] = os.environ.get("MX_APIKEY", "mkt_AkXFubcYOSl33PlPayKpm8O0ca-oJmsma60eEILWGbI")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
CACHE_DIR.mkdir(parents=True, exist_ok=True)
today = datetime.now().strftime("%Y-%m-%d")

OUTPUT_DIRS = {
    MX_DATA: Path.home() / ".hermes" / "cache" / "mx_data" / "output",
    MX_SEARCH: Path.home() / ".hermes" / "cache" / "mx_search" / "output",
    MX_XUANGU: Path.home() / ".hermes" / "cache" / "mx_xuangu" / "output",
}

# ==================== JSON解析 ====================

def _safe_name(q): return re.sub(r'[\\/:*?"<>| ]', '_', q.strip())[:60]

def _find_json(od, kw, ttl=5):
    if not od.exists(): return None
    fs = sorted(od.glob(f"*{_safe_name(kw)[:15]}*.json"), key=os.path.getmtime, reverse=True)
    if fs:
        now = datetime.now().timestamp()
        rc = [f for f in fs if now - os.path.getmtime(f) < ttl * 60]
        return str(rc[0]) if rc else str(fs[0])
    return None

def _pxuangu(p):
    try:
        r = json.load(open(p))['data']['data']['allResults']['result']
        return {'total': r.get('total',0), 'data_list': r.get('dataList',[])}
    except: return {'total':0, 'data_list':[]}

def _pdata(p):
    try:
        data = json.load(open(p))['data']['data']['searchDataResultDTO']['dataTableDTOList']
        m = {}
        for t in data:
            nm, tb, e = t.get('nameMap',{}), t.get('table',{}), t.get('entityName','')
            if e not in m: m[e] = {'entity':e}
            for k,vs in tb.items():
                if k=='headName': continue
                v = str(vs[-1]) if vs else ''
                cn = nm.get(k,k)
                m[e][cn] = v.replace('点','').replace('元','').strip()
        return list(m.values())
    except: return []

def _psearch(p):
    try: return json.load(open(p))['data']['data']['llmSearchResponse']['data']
    except: return []

# ==================== 运行mx ====================

def run_mx(script, query):
    try:
        subprocess.run([VENV_PYTHON, script, query], capture_output=True, text=True, timeout=TIMEOUT,
                       env={**os.environ, "MX_APIKEY": os.environ["MX_APIKEY"]})
        jp = _find_json(OUTPUT_DIRS[script], query)
        if jp:
            if script == MX_XUANGU: return _pxuangu(jp)
            if script == MX_DATA: return _pdata(jp)
            if script == MX_SEARCH: return _psearch(jp)
        return None
    except: return None

def run_batch(script, queries):
    r = {}
    for q in queries:
        r[q] = run_mx(script, q)
        time.sleep(1.2)
    return r

# ==================== 查询 ====================

def q_indices(): return run_batch(MX_DATA, ["上证指数今日收盘价 涨跌幅","深证成指今日收盘价 涨跌幅","创业板指今日收盘价 涨跌幅","科创50今日收盘价 涨跌幅","沪深300今日收盘价 涨跌幅"])
def q_stats(): return run_batch(MX_XUANGU, ["今日涨停的A股","今日跌停的A股","今日涨幅大于5%的A股","今日跌幅大于5%的A股"])
def q_extremes(): return run_batch(MX_XUANGU, ["A股市值最大的5只股票","A股市值最小的5只股票（排除ST）","市盈率0到10倍的A股","今日成交额最大的10只A股","今日换手率最高的10只A股","今日涨幅最大的10只A股（排除新股）","今日跌幅最大的10只A股"])
def _ddg_search(query, limit=8):
    """备用搜索：使用 DuckDuckGo（零成本），mx_search 失败时回退"""
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=limit, region='cn-zh'))
            items = []
            for r in results:
                items.append({
                    "title": r.get("title", ""),
                    "link": r.get("href", ""),
                    "snippet": r.get("body", ""),
                    "source": r.get("source", ""),
                })
            return items
    except Exception as e:
        print(f"[_ddg_search] DuckDuckGo failed for '{query}': {e}")
        return []

def q_news():
    """使用东方财富妙想搜索今日A股重要新闻"""
    data = run_mx(MX_SEARCH, "A股大盘收盘 今日行情 市场热点 资金流向 板块涨跌")
    if data:
        items = []
        for item in data[:8]:
            items.append({
                "title": item.get("title", ""),
                "link": item.get("jumpUrl", ""),
                "snippet": item.get("content", ""),
                "source": item.get("source", ""),
            })
        return {"今日A股重要新闻": items}
    # fallback to DDG if mx_search fails
    return {"今日A股重要新闻": _ddg_search("A股 收评 市场 热点", 8)}

def q_special():
    """使用东方财富妙想搜索特别关注事件：股价创新高/新股异动/奇葩事件等"""
    data = run_mx(MX_SEARCH, "A股股价突破历史新高 新股暴涨 创纪录 股王 科创板异动")
    if data:
        items = []
        for item in data[:8]:
            items.append({
                "title": item.get("title", ""),
                "link": item.get("jumpUrl", ""),
                "snippet": item.get("content", ""),
                "source": item.get("source", ""),
            })
        return {"今日A股特别关注 股价创新高 股价创纪录 新股暴涨 个股奇葩事件 历史级行情": items}
    # fallback to DDG if mx_search fails
    return {"今日A股特别关注 股价创新高 股价创纪录 新股暴涨 个股奇葩事件 历史级行情": _ddg_search("A股 股价突破 创历史新高 新股 暴涨 纪录 股王 科创板", 8)}

# ==================== 极值对比 ====================

def _load_prev():
    if EXTREMES_FILE.exists():
        try: return json.load(open(EXTREMES_FILE))
        except: return {}
    return {}
def _save_prev(d):
    try: json.dump(d, open(EXTREMES_FILE,'w'), ensure_ascii=False, indent=2)
    except: pass

def _diff(prev, curr, key):
    pv, cv = prev.get(key,{}), curr.get(key,{})
    pl = pv.get('data_list',[]) if isinstance(pv,dict) else (pv if isinstance(pv,list) else [])
    cl = cv.get('data_list',[]) if isinstance(cv,dict) else (cv if isinstance(cv,list) else [])
    pn = {i.get('SECURITY_SHORT_NAME','') for i in pl}
    cn_ = {i.get('SECURITY_SHORT_NAME','') for i in cl}
    new = cn_ - pn
    if new: return f"←新入榜:{'、'.join(list(new)[:3])}"
    if pn and cn_ and pn!=cn_: return "←排名变动"
    return None

# ==================== 格式化 ====================

def _pct(v):
    try: return f"{float(str(v).replace('%','')):+.2f}%"
    except: return str(v)
def _price(v):
    try: return f"{float(str(v).replace(',','')):,.2f}"
    except: return str(v)
def _cap(v):
    s = str(v).replace(',','').replace('元','').strip()
    if '万亿' in s or '亿' in s or '万' in s: return s
    try:
        n = float(s)
        if n>=1e12: return f"{n/1e12:.2f}万亿"
        if n>=1e8: return f"{n/1e8:.2f}亿"
        if n>=1e4: return f"{n/1e4:.1f}万"
        return s
    except: return s
def _val(item, *ks):
    # Try exact key match first, then substring match
    for k in ks:
        v = item.get(k)
        if v is not None and v!='': return v
    # Substring match fallback: any key containing one of ks
    for k in ks:
        for item_k, item_v in item.items():
            if k in item_k and item_v is not None and item_v!='':
                return item_v
    return ''
def _chg(item):
    for k in ['CHG','chg','涨跌幅']:
        v = item.get(k)
        if v is not None: return _pct(v)
    return ''
def _name(item): return item.get('SECURITY_SHORT_NAME',item.get('entityName','?'))
def _code(item): return item.get('SECURITY_CODE','')

# ==================== 报告生成 ====================

def generate(indices, stats, extremes, news_data, special_data):
    prev = _load_prev()
    L = []
    sep = "─" * 34

    # ── 标题 ──
    L.append(sep)
    L.append(f"  📊 A股收盘日报 · {today}")
    L.append(sep)
    L.append("")

    # ── 大盘 ──
    rows = []
    for q, rs in indices.items():
        if not rs: continue
        r = rs[0] if isinstance(rs,list) else rs
        name = q.split('今日')[0][:4]
        pr = r.get('最新价',r.get('收盘价','?'))
        cg = r.get('涨跌幅',r.get('f3','?'))
        amt = r.get('成交额','')
        # 涨跌方向
        try:
            cg_n = float(str(cg).replace('%',''))
            arrow = "🔺" if cg_n > 0 else ("🔻" if cg_n < 0 else "➖")
        except:
            arrow = ""
        rs_ = f"  {arrow}{name} {_price(pr)} {_pct(cg)}"
        if amt: rs_ += f" {_cap(amt)}"
        rows.append(rs_)
    if rows:
        for i in range(0, len(rows), 2):
            L.append("".join(rows[i:i+2]))
        L.append("")

    # ── 情绪 ╱ 涨跌分布 ──
    zt = stats.get("今日涨停的A股",{})
    dt = stats.get("今日跌停的A股",{})
    up5 = stats.get("今日涨幅大于5%的A股",{})
    dn5 = stats.get("今日跌幅大于5%的A股",{})
    zc = zt.get('total',0) if isinstance(zt,dict) else 0
    dc = dt.get('total',0) if isinstance(dt,dict) else 0
    uc = up5.get('total',0) if isinstance(up5,dict) else 0
    vc = dn5.get('total',0) if isinstance(dn5,dict) else 0

    L.append(f"涨停 {zc}  ｜  跌停 {dc}  ｜  涨幅>5% {uc}  ｜  跌幅>5% {vc}")
    if zc or dc:
        ratio = zc / max(dc,1)
        if ratio >= 5: tag = "情绪活跃 ⚡"
        elif ratio >= 2: tag = "情绪偏正 📈"
        elif ratio >= 0.5: tag = "多空均衡 ➖"
        else: tag = "情绪偏弱 📉"
        L.append(f"【{tag}】{zc}:{dc}")
    L.append("")

    # ── 涨停 ──
    zl = zt.get('data_list',[]) if isinstance(zt,dict) else []
    if zl:
        zs = sorted(zl, key=lambda x: abs(float(x.get('CHG',0) or 0)), reverse=True)
        ns = [f"{_name(x)}({_code(x)})" for x in zs[:8]]
        L.append("🚀涨停  " + "  ".join(ns))
        L.append("")

    # ── 资金聚焦 ──
    vol_t = extremes.get("今日成交额最大的10只A股",{})
    vol_l = vol_t.get('data_list',[]) if isinstance(vol_t,dict) else []
    if vol_l:
        its = []
        for x in vol_l[:3]:
            a = _val(x,'TRADING_VOLUMES','AMOUNT','成交额')
            its.append(f"{_name(x)} {_cap(a)} {_chg(x)}")
        L.append("💰资金  " + "  ｜  ".join(its))
        L.append("")

    # ── 异动 ──
    gt = extremes.get("今日涨幅最大的10只A股（排除新股）",{})
    gl = gt.get('data_list',[]) if isinstance(gt,dict) else []
    lt = extremes.get("今日跌幅最大的10只A股",{})
    ll = lt.get('data_list',[]) if isinstance(lt,dict) else []
    tt = extremes.get("今日换手率最高的10只A股",{})
    tl = tt.get('data_list',[]) if isinstance(tt,dict) else []

    if gl:
        its = [f"{_name(x)}{_chg(x)}" for x in gl[:5]]
        L.append("🔺涨幅  " + "  ｜  ".join(its))
    if ll:
        its = [f"{_name(x)}{_chg(x)}" for x in ll[:5]]
        L.append("🔻跌幅  " + "  ｜  ".join(its))
    if tl:
        its = []
        for x in tl[:5]:
            v_ = _val(x,'TURNOVER_RATE','换手率')
            its.append(f"{_name(x)} {v_}%")
        L.append("🔄换手  " + "  ｜  ".join(its))
    if vol_l:
        its = []
        for x in vol_l[:3]:
            a = _val(x,'TRADING_VOLUMES','AMOUNT','成交额')
            its.append(f"{_name(x)} {_cap(a)}")
        L.append("💹量能  " + "  ｜  ".join(its))
    L.append("")

    # ── 极值 ──
    cmax = extremes.get("A股市值最大的5只股票",{})
    cmin = extremes.get("A股市值最小的5只股票（排除ST）",{})
    peq = extremes.get("市盈率0到10倍的A股",{})

    ex = []
    cml = cmax.get('data_list',[])
    if cml:
        x = cml[0]; v = _val(x,'TOAL_MARKET_VALUE','TOTAL_MARKET_CAP','总市值')
        s = f"👑市值最大  {_name(x)}  {_cap(v)}"
        d = _diff(prev, extremes, "A股市值最大的5只股票")
        if d: s += f"  {d}"
        ex.append(s)

    cnl = cmin.get('data_list',[])
    if cnl:
        x = cnl[-1]; v = _val(x,'TOAL_MARKET_VALUE','TOTAL_MARKET_CAP','总市值')
        s = f"🥚市值最小  {_name(x)}  {_cap(v)}"
        d = _diff(prev, extremes, "A股市值最小的5只股票（排除ST）")
        if d: s += f"  {d}"
        ex.append(s)

    pel = peq.get('data_list',[])
    if pel:
        pos = [x for x in pel if float(_val(x,'PE_D','PE_TTM','市盈率') or 0)>0]
        if pos:
            x = pos[0]; v = _val(x,'PE_D','PE_TTM','市盈率')
            s = f"💎市盈最低  {_name(x)}  {float(v):.2f}倍"
            d = _diff(prev, extremes, "市盈率0到10倍的A股")
            if d: s += f"  {d}"
            ex.append(s)

    if ex:
        for s in ex: L.append(s)
        L.append("")

    # ── 特别关注 ──
    special = special_data.get("今日A股特别关注 股价创新高 股价创纪录 新股暴涨 个股奇葩事件 历史级行情",[])
    if special:
        L.append("🔥 今日特别关注")
        seen = set(); cnt = 0
        for x in special:
            t = x.get('title','')
            if t and t not in seen and cnt < 4:
                # 跳过太短的标题（更像是关键词而非新闻）
                if len(t) < 5: continue
                seen.add(t)
                src = x.get('source','')
                L.append(f"📰 {t}" + (f"（{src}）" if src else ""))
                cnt += 1
        if cnt > 0: L.append("")

    # ── 要闻 ──
    news = news_data.get("今日A股重要新闻",[])
    if news:
        L.append("📢 其他要闻")
        seen = set(); cnt = 0
        for x in news:
            t = x.get('title','')
            if t and t not in seen and cnt < 4:
                seen.add(t)
                src = x.get('source','')
                L.append(f"📰 {t}" + (f"（{src}）" if src else ""))
                cnt += 1
        L.append("")

    # ── 小结 ──
    if zc > 50: L.append(f"📝涨停 {zc} 家，赚钱效应明显，关注明日连板持续性。")
    elif zc > 20: L.append(f"📝涨停 {zc} 家，结构性机会，关注板块持续性。")
    elif zc > 0: L.append(f"📝涨停 {zc} 家，情绪一般，聚焦核心个股。")
    else: L.append("📝今日无涨停，市场极度低迷，建议观望。")
    if dc > 20: L.append(f"⚠️跌停 {dc} 家偏多，注意控制回撤风险。")
    L.append("")
    L.append(f"数据来源：东方财富妙想  |  {datetime.now().strftime('%H:%M')}")

    _save_prev(extremes)
    return "\n".join(L)

# ==================== 主流程 ====================

def main():
    # 检查是否为交易日
    if not is_trading_day():
        msg = f"🛑 {today} 非交易日（周末或节假日），跳过日报生成。"
        print(msg)
        return msg

    print(f"🔄 A股收盘日报 · {today}\n")
    print("📡 正在采集数据...\n")

    i = q_indices(); print("  ✅ 指数")
    time.sleep(2)
    s = q_stats(); print("  ✅ 涨跌分布")
    time.sleep(2)
    e = q_extremes(); print("  ✅ 异动/极值")
    time.sleep(2)
    n = q_news(); print("  ✅ 要闻")
    time.sleep(2)
    sp = q_special(); print("  ✅ 特别关注")

    print("\n" + "─" * 34 + "\n")
    r = generate(i, s, e, n, sp)
    print(r)

    fp = OUTPUT_DIR / f"closing_{today}.md"
    with open(fp, 'w') as f: f.write(r)
    print(f"\n📁 {fp}")

    return r

if __name__ == "__main__":
    main()
