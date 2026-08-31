#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
国内官方气象数据采集脚本（cron 安全，Python 标准库，无需 key）：
- 中国气象局 weather.cma.cn：国家站实况(56543香格里拉/56651丽江) + 官方逐日预报
- 中国天气网 d1.weather.com.cn：站点24h雨量实况(sk_2d) + 官方预警 JSON(dingzhi alarm)
输出 JSON；全部站点失败则 exit 1（部分失败仍输出 + fetch_errors）。
"""
import json
import re
import sys
import urllib.request
import urllib.parse

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0 Safari/537.36"}

STATIONS = [
    ("xianggelila", "香格里拉", "56543", "101291301"),  # 迪庆州府，海拔3280m
    ("lijiang", "丽江", "56651", "101291401"),          # 毗邻玉龙县，虎跳峡东岸
]

CMA_NOW = "https://weather.cma.cn/api/now/{sid}"
CMA_WEATHER = "https://weather.cma.cn/api/weather/{sid}"
WC_SK2D = "https://d1.weather.com.cn/sk_2d/{wcode}.html"
WC_DINGZHI = "https://d1.weather.com.cn/dingzhi/{wcode}.html"


def get(url, referer=None, timeout=20, retries=2):
    hdr = dict(UA)
    if referer:
        hdr["Referer"] = referer
    last = None
    for _ in range(retries):
        try:
            req = urllib.request.Request(url, headers=hdr)
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read().decode("utf-8", errors="replace")
        except Exception as e:  # noqa: BLE001
            last = e
    raise last


def extract_js_obj(text, marker):
    """从 JS 文本中提取 marker= {...}; 的 JSON 对象"""
    i = text.find(marker)
    if i < 0:
        return None
    start = text.find("{", i)
    if start < 0:
        return None
    depth = 0
    for j in range(start, len(text)):
        c = text[j]
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return json.loads(text[start:j + 1])
    return None


def fetch_cma_station(name, sid, wcode, out):
    try:
        now_raw = json.loads(get(CMA_NOW.format(sid=sid)))
        now = now_raw.get("data", {}).get("now", {})
        loc = now_raw.get("data", {}).get("location", {})
        out["now"] = {
            "station": loc.get("name", name),
            "obs_time_bjt": now_raw.get("data", {}).get("lastUpdate"),
            "temperature_c": now.get("temperature"),
            "precip_mm": now.get("precipitation"),
            "humidity_pct": now.get("humidity"),
            "pressure_hpa": now.get("pressure"),
            "wind": f"{now.get('windDirection','')}{now.get('windScale','')}",
            "feel_c": now.get("feelst"),
        }
    except Exception as e:  # noqa: BLE001
        out["errors"].append(f"{name} cma_now: {str(e)[:120]}")

    try:
        w_raw = json.loads(get(CMA_WEATHER.format(sid=sid)))
        daily = w_raw.get("data", {}).get("daily", [])
        out["daily"] = [
            {"date": d.get("date"), "high_c": d.get("high"), "low_c": d.get("low"),
             "day": d.get("dayText"), "night": d.get("nightText"),
             "wind": f"{d.get('dayWindDirection','')}{d.get('dayWindScale','')}"}
            for d in daily[:7]
        ]
    except Exception as e:  # noqa: BLE001
        out["errors"].append(f"{name} cma_weather: {str(e)[:120]}")

    try:
        sk = extract_js_obj(get(WC_SK2D.format(wcode=wcode), referer="http://www.weather.com.cn/"), "dataSK")
        if sk:
            out["wc_obs"] = {
                "obs_time_bjt": f"{sk.get('date','')} {sk.get('time','')}",
                "temp_c": sk.get("temp"),
                "rain24h_mm": sk.get("rain24h"),
                "humidity_pct": sk.get("SD"),
                "wind": f"{sk.get('WD','')}{sk.get('WS','')}",
                "weather": sk.get("weather"),
            }
    except Exception as e:  # noqa: BLE001
        out["errors"].append(f"{name} wc_sk2d: {str(e)[:120]}")

    try:
        dz = extract_js_obj(get(WC_DINGZHI.format(wcode=wcode), referer="http://www.weather.com.cn/"), f"cityDZ{wcode}")
        if dz:
            wi = dz.get("weatherinfo", {})
            out["wc_today"] = {
                "forecast_time_bjt": wi.get("fctime"),
                "day_temp_c": wi.get("temp"),
                "night_temp_c": wi.get("tempn"),
                "weather": wi.get("weather"),
            }
    except Exception as e:  # noqa: BLE001
        out["errors"].append(f"{name} wc_dingzhi: {str(e)[:120]}")


def fetch_warnings(wcode, out):
    """dingzhi 里的 alarm 字段 = 官方预警（含全文）"""
    try:
        text = get(WC_DINGZHI.format(wcode=wcode), referer="http://www.weather.com.cn/")
        m = re.search(r"alarmDZ" + wcode + r"\s*=\s*", text)
        if not m:
            return
        i = text.find("{", m.end())
        depth = 0
        for j in range(i, len(text)):
            c = text[j]
            if c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0:
                    alarm = json.loads(text[i:j + 1])
                    break
        for w in alarm.get("w", []) or []:
            out.append({
                "region": f"{w.get('w1','')}{w.get('w2','')}{w.get('w3','')}",
                "type": w.get("w5"),
                "level": w.get("w7"),
                "publish_time_bjt": w.get("w8"),
                "text": (w.get("w9") or "")[:400],
            })
    except Exception as e:  # noqa: BLE001
        out.append({"parse_error": f"warnings {wcode}: {str(e)[:120]}"})


def main():
    out = {
        "generated_at_bjt": None,
        "source": "中国气象局 weather.cma.cn(国家站实况/官方预报) + 中国天气网(站点24h雨量/官方预警)",
        "note": "站点实测(海拔3280m/2400m)≠山区河谷，虎跳峡/哈巴雪山一带无国家站，点位间注意海拔差",
        "stations": {},
        "warnings": [],
        "fetch_errors": [],
    }
    from datetime import datetime, timezone, timedelta
    out["generated_at_bjt"] = (datetime.now(timezone(timedelta(hours=8))).strftime("%Y-%m-%d %H:%M"))
    failed = 0
    for key, name, sid, wcode in STATIONS:
        st = {"name": name, "station_id": sid, "wc_code": wcode, "errors": []}
        fetch_cma_station(name, sid, wcode, st)
        if not st.get("now") and not st.get("daily"):
            failed += 1
        out["stations"][key] = st
        fetch_warnings(wcode, out["warnings"])
    print(json.dumps(out, ensure_ascii=False, indent=1))
    if failed == len(STATIONS):
        sys.exit(1)


if __name__ == "__main__":
    main()
