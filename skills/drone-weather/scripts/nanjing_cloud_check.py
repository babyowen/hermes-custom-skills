#!/usr/bin/env python3
"""
南京穿云条件查询工具 v4 — 直接云底计算 + 置信度评分
═══════════════════════════════════════════
数据源：
  1. METAR (禄口机场) — 精确云层高度
  2. 墨迹天气 (南京市区) — 实时温湿度→露点→云底
  3. ECMWF (Open-Meteo) — 南京市区露点→直接云底 + 风
  4. GFS (Open-Meteo) — 交叉验证
═══════════════════════════════════════════
"""

import json
import re
import urllib.request
import sys
from datetime import datetime, timezone, timedelta

CST = timezone(timedelta(hours=8))
STATION = "ZSNJ"
NANJING_LAT, NANJING_LON = 32.06, 118.79

SOURCES = {
    "noaa_ftp": f"https://tgftp.nws.noaa.gov/data/observations/metar/stations/{STATION}.TXT",
    "awc_api": f"https://aviationweather.gov/api/data/metar?ids={STATION}&format=raw&taf=true",
    "ogimet": f"https://www.ogimet.com/display_metars2.php?lang=en&lugar={STATION}&tipo=SA&ord=REV&nil=SI&fmt=txt&send=send",
    "moji": "https://tianqi.moji.com/weather/china/jiangsu/nanjing",
    "ecmwf": (f"https://api.open-meteo.com/v1/ecmwf?latitude={NANJING_LAT}&longitude={NANJING_LON}"
              f"&hourly=temperature_2m,relative_humidity_2m,dew_point_2m,"
              f"cloud_cover_low,cloud_cover_mid,cloud_cover_high,precipitation,"
              f"wind_speed_10m,wind_direction_10m,wind_speed_80m,wind_speed_120m"
              f"&timezone=Asia/Shanghai&forecast_days=2"),
    "gfs": (f"https://api.open-meteo.com/v1/gfs?latitude={NANJING_LAT}&longitude={NANJING_LON}"
            f"&hourly=temperature_2m,relative_humidity_2m,dew_point_2m,"
            f"cloud_cover_low,cloud_cover_mid,cloud_cover_high,precipitation,precipitation_probability"
            f"&timezone=Asia/Shanghai&forecast_days=2"),
}

COVERAGE_NAMES = {"SKC": "晴空", "CLR": "晴空", "FEW": "少云", "SCT": "疏云", "BKN": "多云", "OVC": "阴天", "VV": "垂直能见度"}
COVERAGE_ICON = {"SKC": "☀️", "CLR": "☀️", "FEW": "🌤", "SCT": "⛅", "BKN": "☁️", "OVC": "☁️☁️", "VV": "🌫"}
WIND_DIRS = ["北", "东北", "东", "东南", "南", "西南", "西", "西北"]


def fetch_url(url, timeout=10):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except Exception as e:
        return f"ERROR: {e}"


def est_cloud_base(temp, dew):
    """LCL: cloud_base ≈ (T - Td) × 125 m."""
    return round(max(0, temp - dew) * 125)


def est_dew(temp, rh):
    """Magnus approx: Td ≈ T - ((100-RH)/5)."""
    return round(temp - (100 - rh) / 5, 1)


def parse_metar_time(raw):
    m = re.search(r"(\d{2})(\d{2})(\d{2})Z", raw)
    if not m:
        return None
    d, h, mi = int(m.group(1)), int(m.group(2)), int(m.group(3))
    now = datetime.now(timezone.utc)
    mo, y = now.month, now.year
    if d > now.day + 5:
        mo -= 1
        if mo < 1:
            mo, y = 12, y - 1
    elif d < now.day - 5:
        mo += 1
        if mo > 12:
            mo, y = 1, y + 1
    try:
        return datetime(y, mo, d, h, mi, tzinfo=timezone.utc)
    except ValueError:
        return None


def parse_cloud_layers(s):
    body = re.split(r'\b(BECMG|TEMPO|FM\d{6}|PROB\d{2}|INTER)\b', s, maxsplit=1)[0]
    layers = []
    for m in re.finditer(r"\b(FEW|SCT|BKN|OVC|VV)(\d{3})\b", body):
        cover = m.group(1)
        hft = int(m.group(2)) * 100
        hm = round(hft * 0.3048)
        layers.append({"cover": cover, "cover_name": "垂直能见度" if cover == "VV" else COVERAGE_NAMES.get(cover, cover),
                       "height_ft": hft, "height_m": hm})
    return layers


def parse_metar(raw):
    raw = raw.strip().rstrip("=")
    clouds = parse_cloud_layers(raw)
    vis = "≥10km" if "9999" in raw else None
    if not vis:
        vm = re.search(r"\b(\d{4})\b", raw)
        if vm and vm.group(1) != "9999":
            vis = f"{int(vm.group(1))}m"
    td = re.search(r"(\d{2})/(\d{2})", raw)
    temp, dew = (int(td.group(1)), int(td.group(2))) if td else (None, None)
    wm = re.search(r"(\d{3})(\d{2,3})(?:MPS|KT)", raw)
    wind = {"dir": int(wm.group(1)), "speed": int(wm.group(2)), "unit": "m/s"} if wm else None
    return {"raw": raw, "time": parse_metar_time(raw), "clouds": clouds,
            "vis": vis, "temp": temp, "dew": dew, "wind": wind}


def fetch_metar():
    for src in [SOURCES["noaa_ftp"], SOURCES["awc_api"]]:
        data = fetch_url(src)
        if "ZSNJ" in data and "ERROR" not in data:
            if "METAR" in data:
                for line in data.strip().split("\n"):
                    if line.startswith("METAR"):
                        return parse_metar(line)
            lines = data.strip().split("\n")
            if len(lines) >= 2 and lines[1].startswith("ZSNJ"):
                return parse_metar(lines[1])
    return None


def fetch_taf():
    data = fetch_url(SOURCES["awc_api"])
    if "TAF" in data:
        for line in data.strip().split("\n"):
            if line.startswith("TAF"):
                clouds = parse_cloud_layers(line)
                vm = re.search(r"(\d{4})/(\d{4})", line)
                return {"raw": line, "clouds": clouds,
                        "valid_from": vm.group(1) if vm else None,
                        "valid_to": vm.group(2) if vm else None}
    return None


def fetch_ogimet():
    data = fetch_url(SOURCES["ogimet"])
    if "ERROR" in data or "ZSNJ" not in data:
        return []
    entries = []
    for line in data.split("\n"):
        line = line.strip().rstrip("=")
        if line.startswith("20") and "METAR" in line:
            mp = line.split("METAR ", 1)[-1] if "METAR " in line else line.split(maxsplit=1)[-1]
            p = parse_metar(mp)
            if p:
                entries.append(p)
    return entries


def parse_moji(html):
    r = {}
    t = re.search(r'<em>(\d+)°</em>', html)
    if t:
        r["temp"] = int(t.group(1))
    h = re.search(r'湿度[：:]\s*(\d+)%', html)
    if h:
        r["humidity"] = int(h.group(1))
    w = re.search(r'<em>([东南西北风]+(\d+级)?)</em>', html)
    if w:
        r["wind"] = w.group(1).strip()
    tm = re.search(r'(\d{1,2}:\d{2})更新', html)
    if tm:
        r["update_time"] = tm.group(1)
    for kw in ["多云", "阴", "晴", "小雨", "中雨", "大雨", "阵雨", "雾", "霾", "雷阵雨"]:
        if kw in html:
            r["condition"] = kw
            break
    if r.get("temp") and r.get("humidity"):
        r["dew_est"] = est_dew(r["temp"], r["humidity"])
        r["cloud_base_m"] = est_cloud_base(r["temp"], r["dew_est"])
    return r


def fetch_moji():
    try:
        req = urllib.request.Request(SOURCES["moji"], headers={"User-Agent": "Mozilla/5.0 (Linux; Android 14)"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            return parse_moji(resp.read().decode("utf-8", errors="replace"))
    except Exception:
        return None


def fetch_model(key):
    try:
        req = urllib.request.Request(SOURCES[key], headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            d = json.loads(resp.read().decode())
    except Exception:
        return None
    if "hourly" not in d:
        return None
    h = d["hourly"]
    now_str = datetime.now(CST).strftime("%Y-%m-%dT%H:00")
    idx = next((i for i, t in enumerate(h["time"]) if t == now_str), -1)

    cur = {}
    for k in ["temperature_2m", "dew_point_2m", "relative_humidity_2m",
              "cloud_cover_low", "cloud_cover_mid", "cloud_cover_high",
              "precipitation", "precipitation_probability",
              "wind_speed_10m", "wind_direction_10m",
              "wind_speed_80m", "wind_speed_120m"]:
        if k in h and idx >= 0 and idx < len(h[k]) and h[k][idx] is not None:
            cur[k] = h[k][idx]

    if "temperature_2m" in cur and "dew_point_2m" in cur:
        cur["cloud_base_m"] = est_cloud_base(cur["temperature_2m"], cur["dew_point_2m"])

    trend = []
    for i in range(max(0, idx), min(len(h["time"]), idx + 8)):
        pt = {"time": h["time"][i], "low": h["cloud_cover_low"][i] if "cloud_cover_low" in h else None}
        if "cloud_cover_mid" in h:
            pt["mid"] = h["cloud_cover_mid"][i]
        if "cloud_cover_high" in h:
            pt["high"] = h["cloud_cover_high"][i]
        if "precipitation" in h:
            pt["precip"] = h["precipitation"][i]
        trend.append(pt)

    # ── 明日早晨预测 (05:00 ~ 09:00) ──
    morning = []
    tomorrow = (datetime.now(CST) + timedelta(days=1)).strftime("%Y-%m-%d")
    for i, t in enumerate(h["time"]):
        if t.startswith(tomorrow):
            hh = int(t[-5:-3])
            if 5 <= hh <= 9:
                pt = {"time": t}
                for k in ["temperature_2m", "dew_point_2m", "cloud_cover_low",
                          "cloud_cover_mid", "cloud_cover_high", "precipitation",
                          "precipitation_probability",
                          "wind_speed_10m", "wind_direction_10m"]:
                    if k in h and i < len(h[k]) and h[k][i] is not None:
                        pt[k] = h[k][i]
                if "temperature_2m" in pt and "dew_point_2m" in pt:
                    pt["cloud_base_m"] = est_cloud_base(pt["temperature_2m"], pt["dew_point_2m"])
                morning.append(pt)

    return {"current": cur, "trend": trend, "morning": morning}


def assess_metar(clouds, offset=0):
    if not clouds:
        return {"grade": "❌", "label": "无数据", "issues": []}
    low = mid = high = None
    for c in clouds:
        h = c["height_m"] + offset
        if h < 500 and (low is None or h < low["hc"]):
            low = {**c, "hc": h}
        elif h <= 600 and mid is None:
            mid = {**c, "hc": h}
        elif h > 600 and (high is None or h < high["hc"]):
            high = {**c, "hc": h}

    issues = []
    lo = f"低云 {low['hc']:.0f}m ({COVERAGE_NAMES.get(low['cover'], low['cover'])})" if low else "无低云（>500m）"
    mi = "✅ 500-600m 无云层"
    hi = "600m以上无云"
    if not low:
        issues.append("云底超过500m")
    if mid:
        mi = f"⚠️ 500-600m 有云层 ({mid['hc']:.0f}m)"
        issues.append("拍摄窗口层被遮挡")
    if high:
        hi = f"高层云 {high['hc']:.0f}m ({COVERAGE_NAMES.get(high['cover'], high['cover'])})"

    if not low or (mid and mid["cover"] in ("BKN", "OVC")):
        grade, label = "❌", "不适合"
    elif mid:
        grade, label = "⚠️", "勉强可行"
    elif low and low["cover"] in ("BKN", "OVC"):
        grade, label = "✅", "适合"
    else:
        grade, label = "⚠️", "勉强可行"
        issues.append("低云覆盖较少")

    return {"grade": grade, "label": label, "low": lo, "mid": mi, "high": hi, "issues": issues}


def assess_direct(base_m, cover_pct=None):
    if base_m is None:
        return {"grade": "❓", "label": "数据不足", "issues": []}
    issues = []
    suitable = base_m < 500
    enough = cover_pct is None or cover_pct >= 30
    if suitable and enough:
        grade, label = "✅", "适合"
    elif suitable and not enough:
        grade, label = "⚠️", "勉强可行"
        issues.append("云层覆盖不足")
    elif not suitable and enough:
        grade, label = "⚠️", "勉强可行"
        issues.append(f"云底{base_m}m 偏高")
    else:
        grade, label = "❌", "不适合"
        issues.append(f"云底{base_m}m 偏高且覆盖不足")
    return {"grade": grade, "label": label, "base_m": base_m, "issues": issues}


def calc_confidence(assessments):
    grades = [a.get("grade") for a in assessments if a]
    if not grades:
        return "❓", "无数据"
    yes = sum(1 for g in grades if g == "✅")
    no = sum(1 for g in grades if g == "❌")
    maybe = sum(1 for g in grades if g == "⚠️")
    total = len(grades)
    if yes >= total * 0.6:
        return "🟢", f"高（{yes}/{total}源适合）"
    elif no >= total * 0.6:
        return "🔴", f"低（{no}/{total}源不适合）"
    elif yes > no:
        return "🟡", f"中（{yes}适 {no}不适 {maybe}勉）"
    else:
        return "🟠", f"偏低（{yes}适 {no}不适）"


def wind_str(wind):
    if not wind:
        return ""
    di = round(wind["dir"] / 45) % 8
    return f"{WIND_DIRS[di]}风 {wind['speed']}m/s"


def make_report(current, taf, history, moji, ecmwf, gfs):
    now = datetime.now(CST)
    L = [f"🌤 南京穿云条件查询 — {now.strftime('%m月%d日 %H:%M')}", "═" * 44, ""]
    if not current:
        L.append("❌ 无法获取数据")
        return "\n".join(L)

    # ── 1. 双站对比 ──
    L.append("📍 双站实时对比")
    L.append("─" * 40)
    at = f"{current['temp']}°C" if current.get("temp") is not None else "N/A"
    ct = f"{moji['temp']}°C" if moji and moji.get("temp") else "N/A"
    diff_note = ""
    if current.get("temp") and moji and moji.get("temp") and moji['temp'] > current['temp']:
        diff_note = f"  🏙 热岛+{moji['temp']-current['temp']}°C"
    L.append(f"  气温    禄口 {at:>6}     市区 {ct:<6}{diff_note}")

    ah = "100%"
    if current.get("temp") is not None and current.get("dew") is not None:
        ah = "100%" if current["temp"] == current["dew"] else f"{min(99, 100-5*(current['temp']-current['dew']))}%"
    ch = f"{moji['humidity']}%" if moji and moji.get("humidity") else "N/A"
    L.append(f"  湿度    禄口 {ah:>5}     市区 {ch:<6}")

    wp = []
    if current.get("wind"):
        wp.append(f"禄口 {wind_str(current['wind'])}")
    if moji and moji.get("wind"):
        wp.append(f"市区 {moji['wind']}")
    if wp:
        L.append(f"  风向    {'  |  '.join(wp)}")

    mt = f"禄口 {current['time'].astimezone(CST).strftime('%H:%M') if current.get('time') else '?'} CST"
    if moji:
        mt += f"    市区 {moji.get('update_time', 'N/A')}"
    L.append(f"  观测    {mt}")
    vis = current.get("vis") or "N/A"
    L.append(f"  能见度  {vis:>6}" + (f"        市区 {moji.get('condition', '')}" if moji else ""))
    L.append("")

    # ── 2. 禄口云层 ──
    L.append("📡 禄口机场云层（METAR 精确高度）")
    L.append("─" * 40)
    if current["clouds"]:
        for i, c in enumerate(current["clouds"]):
            L.append(f"  {COVERAGE_ICON.get(c['cover'],'☁️')}  第{i+1}层：{c['height_m']}m ({c['height_ft']}ft)  {c['cover_name']}（{c['cover']}）")
    else:
        L.append("  ☀️  晴空")
    L.append("")

    # ── 3. 直接云底计算 ──
    L.append("📐 南京市区云底直接计算（露点公式）")
    L.append("─" * 40)
    L.append("  云底 ≈ (气温 - 露点) × 125m")
    L.append("")

    if ecmwf and ecmwf["current"].get("cloud_base_m") is not None:
        ec = ecmwf["current"]
        cb = ec["cloud_base_m"]
        lp = ec.get("cloud_cover_low")
        L.append(f"  🖥 ECMWF:  {ec['temperature_2m']}°C  露点{ec['dew_point_2m']}°C")
        L.append(f"     云底 ≈ {cb}m  |  低云覆盖率 {lp}%")
        ae = assess_direct(cb, lp)
        L.append(f"     → {ae['grade']} {ae['label']}" + (f"  {' | '.join(ae['issues'])}" if ae.get('issues') else ""))
        wd = ec.get("wind_direction_10m")
        ws10 = ec.get("wind_speed_10m")
        ws80 = ec.get("wind_speed_80m")
        ws120 = ec.get("wind_speed_120m")
        parts = []
        if wd is not None:
            parts.append(f"风向 {WIND_DIRS[round(wd/45)%8]}风")
        if any(v is not None for v in [ws10, ws80, ws120]):
            speeds = []
            if ws10 is not None:
                speeds.append(f"10m:{ws10}m/s")
            if ws80 is not None:
                speeds.append(f"80m:{ws80}m/s")
            if ws120 is not None:
                speeds.append(f"120m:{ws120}m/s")
            if speeds:
                parts.append(f"风速 {'|'.join(speeds)}")
        if parts:
            L.append(f"     {' | '.join(parts)}")
    else:
        L.append("  🖥 ECMWF: 数据不足")
    L.append("")

    if moji and moji.get("cloud_base_m") is not None:
        L.append(f"  🌤 墨迹天气: {moji['temp']}°C  湿度{moji['humidity']}%")
        L.append(f"     估算露点 {moji['dew_est']}°C  →  云底 ≈ {moji['cloud_base_m']}m")
        am = assess_direct(moji["cloud_base_m"], None)
        L.append(f"     → {am['grade']} {am['label']}" + (f"  ({' | '.join(am['issues'])})" if am.get('issues') else ""))
    else:
        L.append("  🌤 墨迹天气: 数据不足")
    L.append("")

    if gfs and gfs["current"].get("cloud_base_m") is not None:
        gc = gfs["current"]
        cb = gc["cloud_base_m"]
        lp = gc.get("cloud_cover_low")
        L.append(f"  🖥 GFS:      {gc['temperature_2m']}°C  露点{gc['dew_point_2m']}°C")
        L.append(f"     云底 ≈ {cb}m  |  低云覆盖率 {lp}%")
        ag = assess_direct(cb, lp)
        L.append(f"     → {ag['grade']} {ag['label']}" + (f"  {' | '.join(ag['issues'])}" if ag.get('issues') else ""))
    else:
        L.append("  🖥 GFS: 数据不足")
    L.append("")

    # ── 4. 综合评估 ──
    ap = assess_metar(current["clouds"], 0)
    directs = []
    if ecmwf and ecmwf["current"].get("cloud_base_m") is not None:
        directs.append(assess_direct(ecmwf["current"]["cloud_base_m"], ecmwf["current"].get("cloud_cover_low")))
    if moji and moji.get("cloud_base_m") is not None:
        directs.append(assess_direct(moji["cloud_base_m"], None))
    all_grades = [ap] + directs
    ci, ct = calc_confidence(all_grades)

    L.append("🎯 综合评估")
    L.append("─" * 40)
    L.append(f"  🛩 禄口机场（实际观测）：{ap['grade']} {ap['label']}")
    if ecmwf and ecmwf["current"].get("cloud_base_m") is not None:
        cb = ecmwf["current"]["cloud_base_m"]
        L.append(f"  📐 南京市区（露点公式）：{assess_direct(cb, ecmwf['current'].get('cloud_cover_low'))['grade']} 云底~{cb}m")
    L.append(f"  📊 置信度：{ci} {ct}")
    seen = set()
    for a in all_grades:
        for i in a.get("issues", []):
            if i not in seen:
                L.append(f"  ⚠️ {i}")
                seen.add(i)
    L.append("")

    # ── 5. ECMWF 趋势 ──
    if ecmwf and ecmwf.get("trend"):
        L.append("📊 ECMWF 未来几小时趋势")
        L.append("─" * 40)
        best_idx, best_score = -1, -999
        for i, t in enumerate(ecmwf["trend"]):
            ll = t.get("low", 0) or 0
            score = ll - (t.get("precip", 0) or 0) * 30
            if score > best_score:
                best_score, best_idx = score, i

        trend_line = "  "
        has_rain = False
        for t in ecmwf["trend"]:
            icon = "☁️" if (t.get("low") or 0) >= 30 else "⛅"
            trend_line += f"{t['time'][-5:]} {icon} {t.get('low','?')}%"
            p = t.get("precip", 0) or 0
            if p > 0.5:
                trend_line += " 🌧"
                has_rain = True
            trend_line += "  "
        L.append(trend_line)
        if has_rain:
            L.append("  🌧 未来数小时有降水预报")

        if best_idx >= 0:
            bt = ecmwf["trend"][best_idx]
            note = ""
            p = bt.get("precip", 0) or 0
            if p > 0.5:
                note = "🌧 有降水"
            elif (bt.get("low") or 0) >= 50:
                note = "✅ 云量充足"
            elif (bt.get("low") or 0) >= 30:
                note = "⛅ 云量尚可"
            else:
                note = "☀️ 云量偏少"
            L.append(f"  较好时段：{bt['time']}（低云{bt.get('low','?')}% {note}）")
        L.append("")

    # ── 6. 明早预测（双模型对比） ──
    if ecmwf and ecmwf.get("morning"):
        L.append("🌅 明日早晨预测（ECMWF vs GFS）")
        L.append("─" * 40)

        # ── ECMWF ──
        L.append("  ECMWF（欧洲）：")
        L.append("  时间  气温  云底    低云   降水")
        best_m = None
        best_score = -999
        for pt in ecmwf["morning"]:
            t = pt["time"][-5:]
            temp = pt.get("temperature_2m", "?")
            cb = pt.get("cloud_base_m", "?")
            ll = pt.get("cloud_cover_low", 0) or 0
            prec = pt.get("precipitation", 0) or 0
            icon = "☁️" if ll >= 30 else "⛅"
            prec_s = f"{prec:.1f}mm" if prec > 0 else "无"
            L.append(f"  {icon} {t}  {temp}°C  {cb}m  {ll:>2}%   {prec_s}")
            score = (100 - (cb if isinstance(cb, (int, float)) else 500)) * 0.5 + ll - (prec * 30)
            if score > best_score:
                best_score, best_m = score, pt

        L.append("")
        L.append("  GFS（美国）：")
        gfs_has_morning = gfs and gfs.get("morning")
        if gfs_has_morning:
            L.append("  时间  气温  云底    低云   降水   概率")
            for pt in gfs["morning"]:
                t = pt["time"][-5:]
                temp = pt.get("temperature_2m", "?")
                cb = pt.get("cloud_base_m", "?")
                ll = pt.get("cloud_cover_low", 0) or 0
                prec = pt.get("precipitation", 0) or 0
                prob = pt.get("precipitation_probability")
                prob_s = f"{prob:.0f}%" if prob is not None else "N/A"
                icon = "☁️" if ll >= 30 else "⛅"
                prec_s = f"{prec:.1f}mm" if prec > 0 else "无"
                L.append(f"  {icon} {t}  {temp}°C  {cb}m  {ll:>2}%   {prec_s}   {prob_s}")
        else:
            L.append("  （数据不可用）")

        L.append("")

        # ── 综合判断 ──
        e_prec = [p.get("precipitation", 0) or 0 for p in ecmwf["morning"]]
        avg_e_prec = sum(e_prec) / max(len(e_prec), 1)
        if gfs_has_morning:
            g_prec = [p.get("precipitation", 0) or 0 for p in gfs["morning"]]
            avg_g_prec = sum(g_prec) / max(len(g_prec), 1)
            g_probs = [p.get("precipitation_probability") for p in gfs["morning"] if p.get("precipitation_probability") is not None]
            avg_g_prob = sum(g_probs) / max(len(g_probs), 1) if g_probs else None
        else:
            avg_g_prec, avg_g_prob = 999, None

        L.append("  📊 模型对比：")
        L.append(f"     ECMWF 平均降水 {avg_e_prec:.1f}mm/h（递减退散中）")
        if avg_g_prec != 999:
            prob_str = f"，概率 {avg_g_prob:.0f}%" if avg_g_prob is not None else ""
            L.append(f"     GFS 平均降水 {avg_g_prec:.1f}mm/h{prob_str}")

        # Verdict
        if avg_g_prec == 0 and avg_g_prob and avg_g_prob < 50:
            L.append(f"     ✅ 两模型趋势一致：降水概率低，明早很可能无雨")
        elif avg_e_prec < 0.5 and avg_g_prec < 0.5:
            L.append(f"     ✅ 两模型一致认为降水微弱，不影响飞行")
        elif avg_e_prec >= avg_g_prec:
            L.append(f"     → ECMWF 报小雨，GFS 报无雨。实际可能是间歇性毛毛雨，地面潮但不影响飞")
        else:
            L.append(f"     → 模型有分歧，建议早起看实际天气决定")

        # Best morning time from ECMWF (more accurate model)
        if best_m:
            cb_best = best_m.get("cloud_base_m", "?")
            ll_best = best_m.get("cloud_cover_low", 0) or 0
            prec_best = best_m.get("precipitation", 0) or 0
            note = ""
            if isinstance(cb_best, (int, float)) and cb_best < 200:
                note = f"低云底{cb_best}m 理想"
            elif isinstance(cb_best, (int, float)) and cb_best < 500:
                note = f"云底{cb_best}m 尚可"
            else:
                note = f"云底{cb_best}m 偏高"
            if prec_best > 0.5:
                note += " 🌧有弱降水"
            L.append(f"  {best_m['time'][-5:]} 前后云底~{cb_best}m，为最佳窗口")

            # Compare with current
            if ecmwf["current"].get("cloud_base_m") is not None:
                cur_cb = ecmwf["current"]["cloud_base_m"]
                vs = cur_cb - (cb_best if isinstance(cb_best, (int, float)) else 0)
                if vs > 100:
                    L.append(f"  📉 明早云底比现在低 {vs:.0f}m，值得早起")
                elif vs > 0:
                    L.append(f"  📉 明早云底略低于现在")
                else:
                    L.append(f"  ➡️ 明早光线更好，适合拍摄")
        L.append("")

    # ── 7. TAF ──
    if taf and taf["clouds"]:
        L.append("🔮 TAF 预报（禄口机场 未来24h）")
        L.append("─" * 40)
        for c in taf["clouds"]:
            L.append(f"  {COVERAGE_ICON.get(c['cover'],'☁️')} {c['height_m']}m ({c['cover_name']})")
        if "SHRA" in (taf.get("raw") or "") or "RA" in (taf.get("raw") or ""):
            L.append("  🌧 预报有降水")
        L.append("")

    # ── 8. 今日趋势 ──
    if history:
        L.append("📈 禄口机场今日云底变化")
        L.append("─" * 40)
        bases = []
        for h in history:
            if h["clouds"]:
                b = min(c["height_m"] for c in h["clouds"])
                if b < 2000:
                    bases.append((h["time"].astimezone(CST).strftime("%H:%M") if h.get("time") else "?", b))
        if len(bases) >= 2:
            recent = bases[:min(8, len(bases))]
            fb, lb = recent[-1][1], recent[0][1]
            d = lb - fb
            if d > 50:
                dir_s = f"📈 云底抬升（{fb}m → {lb}m，+{d}m）"
            elif d < -50:
                dir_s = f"📉 云底下降（{fb}m → {lb}m，{d}m）"
            else:
                dir_s = f"➡️ 云底稳定（~{lb}m）"
            L.append(f"  {dir_s}")
            L.append(f"  {' → '.join(f'{t}={b}m' for t, b in recent)}")
        L.append("")

    # ── 9. 建议 ──
    L.append("💡 建议")
    L.append("─" * 40)
    worst = max(all_grades, key=lambda x: {"✅": 0, "⚠️": 1, "❌": 2, "❓": 2}.get(x.get("grade"), 2))
    if worst["grade"] == "❌":
        L.append("  当前条件不太适合穿云拍摄。")
        if ecmwf and ecmwf.get("trend") and best_idx >= 0:
            bt = ecmwf["trend"][best_idx]
            if bt.get("low", 0) > 40 and (bt.get("precip", 0) or 0) <= 0.5:
                L.append(f"  ▸ 今晚可关注 {bt['time']} 前后")
        # Tomorrow morning as alternative
        if ecmwf and ecmwf.get("morning"):
            best_m = max(ecmwf["morning"], key=lambda p: (p.get("cloud_cover_low",0) or 0) - ((p.get("precipitation",0) or 0)*30) - ((p.get("cloud_base_m",999) or 999)*0.3))
            cb_m = best_m.get("cloud_base_m", 999) or 999
            prec_m = best_m.get("precipitation", 0) or 0
            if isinstance(cb_m, (int, float)) and cb_m < 400 and prec_m < 0.5:
                L.append(f"  ▸ 🌅 明早 {best_m['time'][-5:]} 云底~{cb_m}m，值得关注")
        L.append("  ▸ 最佳穿云时间：雨后转晴或清晨")
    elif worst["grade"] == "✅":
        L.append("  条件适合穿云拍摄！")
        L.append("  ▸ 到起飞点肉眼确认云层位置")
        L.append("  ▸ 注意无人机限高 500m")
    else:
        L.append("  条件不够理想，建议等云底更低时再尝试。")
        if ecmwf and ecmwf.get("trend") and best_idx >= 0:
            bt = ecmwf["trend"][best_idx]
            if bt.get("low", 0) > 40 and (bt.get("precip", 0) or 0) <= 0.5:
                L.append(f"  ▸ 今晚相对较好：{bt['time']} 前后")
        # Tomorrow morning as alternative
        if ecmwf and ecmwf.get("morning"):
            best_m = max(ecmwf["morning"], key=lambda p: (p.get("cloud_cover_low",0) or 0) - ((p.get("precipitation",0) or 0)*30) - ((p.get("cloud_base_m",999) or 999)*0.3))
            cb_m = best_m.get("cloud_base_m", 999) or 999
            prec_m = best_m.get("precipitation", 0) or 0
            if isinstance(cb_m, (int, float)) and cb_m < 500:
                L.append(f"  ▸ 🌅 明早 {best_m['time'][-5:]} 云底~{cb_m}m{' 🌧有降水' if prec_m > 0.5 else ''}，可提前规划")

    if moji and moji.get("condition") and ("雨" in moji["condition"] or "雾" in moji["condition"]):
        L.append("  ⚠️ 市区有降水/雾，注意安全")

    L.append("")
    L.append("═" * 44)
    L.append("📌 源：METAR(禄口) | 墨迹(市区) | ECMWF | GFS")
    L.append("📌 云底公式 LCL ≈ (T-Td)×125m")
    L.append("📌 ⚠️ 仅供参考，起飞前务必肉眼确认")
    return "\n".join(L)


def main():
    print("📡 南京云层数据（四源 + 直接云底计算）...", file=sys.stderr)
    current = fetch_metar()
    taf = fetch_taf()
    history = fetch_ogimet()
    moji = fetch_moji()
    ecmwf = fetch_model("ecmwf")
    gfs = fetch_model("gfs")

    def fmt_time(m):
        return m.get('time').astimezone(CST).strftime('%H:%M') if m and m.get('time') else '失败'

    print(f"  {'✓' if current else '✗'} METAR: {fmt_time(current)}", file=sys.stderr)
    if moji:
        print(f"  ✓ 墨迹: {moji.get('temp','?')}°C" + (f" → 云底{moji['cloud_base_m']}m" if moji.get('cloud_base_m') else ""), file=sys.stderr)
    else:
        print("  ✗ 墨迹: 失败", file=sys.stderr)
    if ecmwf:
        print(f"  ✓ ECMWF: {ecmwf['current'].get('cloud_base_m','?')}m云底", file=sys.stderr)
    else:
        print("  ✗ ECMWF: 失败", file=sys.stderr)
    if gfs:
        print(f"  ✓ GFS: {gfs['current'].get('cloud_base_m','?')}m云底", file=sys.stderr)
    else:
        print("  ✗ GFS: 失败", file=sys.stderr)

    print("\n" + "=" * 44 + "\n", file=sys.stderr)
    print(make_report(current, taf, history, moji, ecmwf, gfs))


if __name__ == "__main__":
    main()
