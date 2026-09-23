#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
虎跳峡·哈巴雪山 天气数据采集脚本（cron 安全：由 cronjob script 字段在每次 tick 运行，
stdout JSON 注入 agent 会话。仅用 Python 标准库 urllib，无第三方依赖，无需 API key）。

输出：JSON（--json 为默认行为），任一点位全部失败则 exit 1（部分失败仍输出部分数据 + fetch_errors）。
数据源：Open-Meteo（免费、无 key）——网格预报/再分析，非站点实测，仅作趋势参考。

v1.2（2026-09-13）：新增 temp_est 温度块——网格温度按 6.5℃/1000m 直减率校正到**实际点位海拔**，
并给出今日窗口温（清晨/正午/午后/夜间）、未来3天高低温、72h 内 <0℃ 小时数与夜间最低温。
（网格高程与实际海拔差异大：虎跳峡镇网格 3290m vs 实际 1800m，不校正会低约 10℃）
"""
import json
import sys
import math
import urllib.request
import urllib.parse
from datetime import datetime, timedelta

API = "https://api.open-meteo.com/v1/forecast"

# 点位：key, 名称, 纬度, 经度, 海拔说明, **实际海拔(m, 供温度校正)**
# 坐标来源：OSM/Wikipedia 2026-08 核实；实际海拔取该点代表性高度
POINTS = [
    ("tlg_town",      "虎跳峡镇·上虎跳景区", 27.250, 100.060, "约1700-1900m 金沙江河谷", 1800),
    ("haba_village",  "哈巴村(三坝乡)",      27.382, 100.136, "约2700m 徒步起点", 2700),
    ("lanhuaping",    "兰花坪·羊房牧场",     27.365, 100.120, "约3300-3600m 高山牧场", 3450),
    ("heihai",        "黑海营地·垭口(最高关注点)", 27.350, 100.115, "约4100-4200m 上游湖泊(尖山牧场同区,不登顶)", 4150),
    ("xianggelila",   "香格里拉市区(参考)",  27.830,  99.700, "约3280m 迪庆州府", 3280),
    ("lijiang",       "丽江市区(参考)",      26.860, 100.230, "约2400m 毗邻玉龙县", 2400),
    # v1.3：三坝乡（哈巴村所在乡，乡政府·白地村）——只作「哈巴村实况锚点」的网格对照点，不进简报温度行
    ("sanba",         "三坝乡·白地村(锚点对照)", 27.330, 100.030, "约2380m 哈巴村所在乡", 2380),
]

# 简报温度行只报这 4 个路线点位（其余点为锚点/校验用）
ROUTE_POINTS = ["tlg_town", "haba_village", "lanhuaping", "heihai"]

PAST_DAYS = 3
FUTURE_DAYS = 4
TZ = "Asia%2FShanghai"
HOURS = ["precipitation", "precipitation_probability", "temperature_2m",
         "wind_speed_10m", "wind_gusts_10m"]
DAILY = ["precipitation_sum", "precipitation_probability_max",
         "temperature_2m_max", "temperature_2m_min"]

LAPSE_C_PER_KM = 6.5          # 气温直减率，海拔校正用
NIGHT_HOURS = {20, 21, 22, 23, 0, 1, 2, 3, 4, 5, 6}   # 夜间窗口（装备提示用）


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


def summarize(data, elev_actual_m=None):
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

    temp_est = build_temp_est(data, hourly_t, temp, days, anchor_idx, elev_actual_m, now)

    return {
        "grid_elevation_m": data.get("elevation"),
        "past24h_sum_mm": past24,
        "past72h_sum_mm": past72,
        "next24h_sum_mm": next24,
        "next48h_sum_mm": next48,
        "next72h_sum_mm": next72,
        "days": days,
        "short_intense_windows": intense[:20],
        "temp_est": temp_est,
    }


def build_temp_est(data, hourly_t, temp, days, anchor_idx, elev_actual_m, now):
    """网格温度 → 实际点位海拔的温度校正估算（v1.2 新增）。

    T_est = T_grid + 6.5℃/1000m ×(网格高程 − 实际海拔)
    （网格高程高于实际海拔 → 实际点位更暖 → 校正为正；反之更冷。）
    """
    grid_elev = data.get("elevation")
    if grid_elev is None or not elev_actual_m:
        return {"available": False, "reason": "缺少网格高程或实际海拔，未做校正"}
    corr = round(LAPSE_C_PER_KM * (grid_elev - elev_actual_m) / 1000.0, 1)

    def ok(i):
        return 0 <= i < len(temp) and not math.isnan(temp[i])

    def est(i):
        return round(temp[i] + corr, 1)

    today_str = now.strftime("%Y-%m-%d")
    idx_today = [i for i, t in enumerate(hourly_t) if t.startswith(today_str)]

    def win(h_from, h_to):
        vals = [est(i) for i in idx_today if h_from <= int(hourly_t[i][11:13]) < h_to and ok(i)]
        return round(sum(vals) / len(vals), 1) if vals else None

    # 今日逐时最高/最低（含出现时间）
    todays = [(i, est(i)) for i in idx_today if ok(i)]
    tmin_c = tmax_c = tmin_t = tmax_t = None
    if todays:
        i_lo = min(todays, key=lambda x: x[1])
        i_hi = max(todays, key=lambda x: x[1])
        tmin_c, tmin_t = i_lo[1], hourly_t[i_lo[0]][11:16]
        tmax_c, tmax_t = i_hi[1], hourly_t[i_hi[0]][11:16]

    # 未来3天高低温（校正后）
    fut = []
    for d in days:
        if d["date"] >= today_str:
            fut.append({
                "date": d["date"],
                "tmin_c": None if d["tmin_c"] is None else round(d["tmin_c"] + corr, 1),
                "tmax_c": None if d["tmax_c"] is None else round(d["tmax_c"] + corr, 1),
            })
        if len(fut) == 3:
            break

    # 未来72h：<0℃ / <5℃ 小时数 + 最低温 + 夜间最低
    win72 = [i for i in range(anchor_idx + 1, min(anchor_idx + 73, len(hourly_t))) if ok(i)]
    below0 = sum(1 for i in win72 if temp[i] + corr < 0)
    below5 = sum(1 for i in win72 if temp[i] + corr < 5)
    min72 = round(min(temp[i] + corr for i in win72), 1) if win72 else None
    night = [temp[i] + corr for i in win72 if int(hourly_t[i][11:13]) in NIGHT_HOURS]
    night_min3d = round(min(night), 1) if night else None

    # v1.3：今日逐时校正后温度（供 wrapper 做「实况锚定偏差校正」取同一时刻的值）
    hourly_today = []
    for i in idx_today:
        if ok(i):
            hourly_today.append({"time_bjt": hourly_t[i][11:16], "est_c": est(i)})

    # v1.3：过去24h（与乡镇自动站实测同一窗口）的校正后高低温，供 wrapper 量模式偏差
    past = [est(i) for i in range(max(0, anchor_idx - 24), anchor_idx + 1) if ok(i)]
    past24h = {"tmin_c": round(min(past), 1), "tmax_c": round(max(past), 1),
               "n_hours": len(past)} if past else {"tmin_c": None, "tmax_c": None, "n_hours": 0}

    return {
        "available": True,
        "note": ("网格温度按 %s℃/1000m 直减率校正到实际海拔后的**估算值**（山区无国家站，仅供装备/体感参考）；"
                 "校正量 = 网格高程 − 实际海拔" % LAPSE_C_PER_KM),
        "grid_elev_m": grid_elev,
        "actual_elev_m": elev_actual_m,
        "correction_c": corr,
        "today": {
            "tmin_c": tmin_c, "tmin_time_bjt": tmin_t,
            "tmax_c": tmax_c, "tmax_time_bjt": tmax_t,
        },
        "windows_today_c": {
            "dawn_06_08": win(6, 8),
            "noon_12_14": win(12, 14),
            "afternoon_14_16": win(14, 16),
            "night_20_23": win(20, 23),
        },
        "hourly_today": hourly_today,
        "past24h": past24h,
        "days": fut,
        "next72h_hours_below_0c": below0,
        "next72h_hours_below_5c": below5,
        "next72h_min_c": min72,
        "next3d_night_min_c": night_min3d,
    }


def main():
    out = {
        "generated_at_bjt": datetime.now().astimezone().strftime("%Y-%m-%d %H:%M"),
        "data_source": "Open-Meteo best_match(无key,网格数据,非站点实测,仅参考)",
        "unit_note": "雨量mm｜温度℃｜时间均为北京时间｜temp_est 为海拔校正估算值",
        "points": {},
        "fetch_errors": [],
    }
    failed = 0
    for key, name, lat, lon, elev_note, elev_actual in POINTS:
        try:
            data = fetch_point(lat, lon)
            s = summarize(data, elev_actual)
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
