#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
虎跳峡·哈巴雪山 天气数据采集脚本（cron 安全：由 cronjob script 字段在每次 tick 运行，
stdout JSON 注入 agent 会话。仅用 Python 标准库 urllib，无第三方依赖，无需 API key）。

输出：JSON（--json 为默认行为），任一点位全部失败则 exit 1（部分失败仍输出部分数据 + fetch_errors）。
数据源：Open-Meteo（免费、无 key）——网格预报/再分析，非站点实测，仅作趋势参考。
"""
import json
import sys
import urllib.request
import urllib.parse
from datetime import datetime, timedelta

API = "https://api.open-meteo.com/v1/forecast"

# 点位：名称, 纬度, 经度, 海拔说明（坐标来源：OSM/Wikipedia 2026-08 核实）
POINTS = [
    ("tlg_town",      "虎跳峡镇·上虎跳景区", 27.250, 100.060, "约1700-1900m 金沙江河谷"),
    ("haba_village",  "哈巴村(三坝乡)",      27.382, 100.136, "约2700m 徒步起点"),
    ("lanhuaping",    "兰花坪·羊房牧场",     27.365, 100.120, "约3300-3600m 高山牧场"),
    ("heihai",        "黑海营地·垭口",       27.350, 100.115, "约4100-4200m 上游湖泊"),
    ("haba_summit",   "哈巴雪山顶峰",        27.320, 100.100, "5396m 雪线约4900m"),
    ("xianggelila",   "香格里拉市区(参考)",  27.830,  99.700, "约3280m 迪庆州府"),
    ("lijiang",       "丽江市区(参考)",      26.860, 100.230, "约2400m 毗邻玉龙县"),
]

PAST_DAYS = 3
FUTURE_DAYS = 4
TZ = "Asia%2FShanghai"
HOURS = ["precipitation", "precipitation_probability", "temperature_2m",
         "wind_speed_10m", "wind_gusts_10m"]
DAILY = ["precipitation_sum", "precipitation_probability_max",
         "temperature_2m_max", "temperature_2m_min"]


def fetch_point(lat, lon):
    params = urllib.parse.urlencode({
        "latitude": f"{lat:.4f}", "longitude": f"{lon:.4f}",
        "timezone": "Asia/Shanghai",
        "past_days": PAST_DAYS, "forecast_days": FUTURE_DAYS,
        "hourly": ",".join(HOURS), "daily": ",".join(DAILY),
        "models": "best_match",
    })
    url = f"{API}?{params}"
    last_err = None
    for attempt in (1, 2):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "hermes-haba-briefing/1.0"})
            with urllib.request.urlopen(req, timeout=25) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception as e:  # noqa: BLE001
            last_err = f"attempt{attempt}: {e}"
    raise RuntimeError(f"fetch failed: {last_err}")


def _safe(v, default=0.0):
    return v if v is not None else default


def summarize(data):
    now = datetime.now().astimezone()
    hourly_t = data["hourly"]["time"]
    precip = [_safe(x) for x in data["hourly"]["precipitation"]]
    prob = [_safe(x) for x in data["hourly"]["precipitation_probability"]]
    temp = [_safe(x, float("nan")) for x in data["hourly"]["temperature_2m"]]
    gust = [_safe(x) for x in data["hourly"]["wind_gusts_10m"]]

    # 以"当前整点"为锚点
    anchor_idx = None
    anchor_str = now.strftime("%Y-%m-%dT%H:00")
    for i, t in enumerate(hourly_t):
        if t >= anchor_str:
            anchor_idx = i
            break
    if anchor_idx is None:
        anchor_idx = len(hourly_t) - 1

    def sum_window(start, end):
        s = 0.0
        for i in range(start, end):
            if 0 <= i < len(precip):
                s += precip[i]
        return round(s, 1)

    # 过去24h / 过去72h
    past24 = sum_window(anchor_idx - 24, anchor_idx)
    past72 = sum_window(anchor_idx - 72, anchor_idx)

    # 未来窗口
    next24 = sum_window(anchor_idx + 1, anchor_idx + 25)
    next48 = sum_window(anchor_idx + 1, anchor_idx + 49)
    next72 = sum_window(anchor_idx + 1, anchor_idx + 73)

    # 逐日汇总（过去3天 + 未来4天）
    days = []
    daily_t = data.get("daily", {}).get("time", [])
    daily_sum = data.get("daily", {}).get("precipitation_sum", [])
    daily_prob = data.get("daily", {}).get("precipitation_probability_max", [])
    daily_tmax = data.get("daily", {}).get("temperature_2m_max", [])
    daily_tmin = data.get("daily", {}).get("temperature_2m_min", [])
    for d in range(len(daily_t)):
        day = daily_t[d][:10]
        hours = [i for i, t in enumerate(hourly_t) if t.startswith(day)]
        if not hours:
            continue
        day_precip = [precip[i] for i in hours]
        day_gust = [gust[i] for i in hours]
        max_h = max(day_precip)
        max_h_time = hourly_t[hours[day_precip.index(max_h)]][11:16] if max_h > 0 else "-"
        days.append({
            "date": day,
            "sum_mm": round(sum(day_precip), 1),
            "prob_max_pct": int(_safe(daily_prob[d])) if d < len(daily_prob) else None,
            "tmax_c": round(_safe(daily_tmax[d]), 1) if d < len(daily_tmax) else None,
            "tmin_c": round(_safe(daily_tmin[d]), 1) if d < len(daily_tmin) else None,
            "max_hourly_mm": round(max_h, 1),
            "max_hourly_time_bjt": max_h_time,
            "hours_ge1mm": sum(1 for x in day_precip if x >= 1),
            "hours_ge10mm": sum(1 for x in day_precip if x >= 10),
            "gust_max_kmh": round(max(day_gust), 0),
        })

    # 未来72h内短时强降水信号（逐小时 >=10mm）
    intense = []
    for i in range(anchor_idx + 1, min(anchor_idx + 73, len(hourly_t))):
        if precip[i] >= 10:
            intense.append({"time_bjt": hourly_t[i][5:16], "mm": round(precip[i], 1)})

    return {
        "grid_elevation_m": data.get("elevation"),
        "past24h_sum_mm": past24,
        "past72h_sum_mm": past72,
        "next24h_sum_mm": next24,
        "next48h_sum_mm": next48,
        "next72h_sum_mm": next72,
        "days": days,
        "short_intense_windows": intense[:20],
    }


def main():
    out = {
        "generated_at_bjt": datetime.now().astimezone().strftime("%Y-%m-%d %H:%M"),
        "data_source": "Open-Meteo best_match(无key,网格数据,非站点实测,仅参考)",
        "unit_note": "雨量mm｜时间均为北京时间",
        "points": {},
        "fetch_errors": [],
    }
    failed = 0
    for key, name, lat, lon, elev_note in POINTS:
        try:
            data = fetch_point(lat, lon)
            s = summarize(data)
            s["name"] = name
            s["lat"] = lat
            s["lon"] = lon
            s["elev_note"] = elev_note
            out["points"][key] = s
        except Exception as e:  # noqa: BLE001
            failed += 1
            out["fetch_errors"].append({"point": key, "name": name, "error": str(e)[:200]})
    print(json.dumps(out, ensure_ascii=False, indent=1))
    if failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
