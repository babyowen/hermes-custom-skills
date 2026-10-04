#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""上海大师赛 · 天气（旗忠网球中心，闵行马桥）。

数据源：Open-Meteo（免费、无需密钥）。只用标准库，系统 python3 直接跑。

用法：
  masters_weather.py                     # 默认 2026-10-18 决赛日
  masters_weather.py --date 2026-10-17
  masters_weather.py --json

⚠️ 时效边界：Open-Meteo 逐日预报最多 16 天。今天 10/4 时 10/18 正好在窗口边缘，
   预报值偏差大——脚本会自动标注"距今天数"，≥7 天的一律标为「仅供趋势参考」。
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.parse
import urllib.request
from datetime import date, datetime, timedelta, timezone
from typing import NoReturn

CST = timezone(timedelta(hours=8))
QIZHONG = (31.0456, 121.3645)   # 旗忠网球中心（闵行区马桥镇元江路5500号）
DEFAULT_DATE = "2026-10-18"      # 决赛日
WEEKDAY = "一二三四五六日"
WMO = {
    0: "晴", 1: "晴间多云", 2: "多云", 3: "阴", 45: "有雾", 48: "雾凇",
    51: "小毛毛雨", 53: "毛毛雨", 55: "大毛毛雨", 56: "冻毛毛雨", 57: "强冻毛毛雨",
    61: "小雨", 63: "中雨", 65: "大雨", 66: "冻雨", 67: "强冻雨",
    71: "小雪", 73: "中雪", 75: "大雪", 77: "米雪",
    80: "阵雨", 81: "中阵雨", 82: "强阵雨", 85: "阵雪", 86: "强阵雪",
    95: "雷阵雨", 96: "雷阵雨伴冰雹", 99: "强雷暴伴冰雹",
}


def die(msg: str) -> NoReturn:
    print(json.dumps({"_run_failed": True, "error": msg}, ensure_ascii=False))
    sys.exit(1)


def fetch(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": "curl/8"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))


def wmo(code) -> str:
    """WMO 天气码 → 中文（容错：非数字返回『未知』）。"""
    return WMO.get(int(code), "未知(%s)" % code) if isinstance(code, (int, float)) else "未知"


def main() -> int:
    ap = argparse.ArgumentParser(description="旗忠网球中心天气（Open-Meteo）")
    ap.add_argument("--date", default=DEFAULT_DATE, help="目标日期 YYYY-MM-DD（默认决赛日 2026-10-18）")
    ap.add_argument("--lat", type=float, default=QIZHONG[0])
    ap.add_argument("--lon", type=float, default=QIZHONG[1])
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    try:
        target = datetime.strptime(a.date, "%Y-%m-%d").date()
    except ValueError:
        die("日期格式应为 YYYY-MM-DD，收到：%s" % a.date)

    today = datetime.now(CST).date()
    days = (target - today).days
    if days < 0:
        die("目标日期 %s 已过去" % a.date)

    q = urllib.parse.urlencode({
        "latitude": a.lat, "longitude": a.lon,
        "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max,"
                 "precipitation_sum,wind_speed_10m_max,wind_gusts_10m_max,uv_index_max,sunrise,sunset",
        "hourly": "temperature_2m,precipitation_probability,precipitation,wind_speed_10m,weather_code",
        "timezone": "Asia/Shanghai",
        "forecast_days": 16,
    })
    try:
        d = fetch("https://api.open-meteo.com/v1/forecast?" + q)
    except Exception as e:  # noqa: BLE001
        die("Open-Meteo 请求失败：%s" % e)

    daily = d.get("daily") or {}
    times = daily.get("time") or []
    if a.date not in times:
        die("目标日期 %s 不在预报窗口内（当前窗口 %s ~ %s）。逐日预报最多 16 天，临近再查。"
            % (a.date, times[0] if times else "?", times[-1] if times else "?"))

    i = times.index(a.date)
    code = (daily.get("weather_code") or [None])[i]
    rec = {
        "date": a.date,
        "weekday": "周" + WEEKDAY[target.weekday()],
        "days_ahead": days,
        "place": "旗忠网球中心（上海闵行马桥）",
        "lat_lon": [a.lat, a.lon],
        "source": "open-meteo.com",
        "condition": wmo(code),
        "temp_max": (daily.get("temperature_2m_max") or [None])[i],
        "temp_min": (daily.get("temperature_2m_min") or [None])[i],
        "precip_prob_max": (daily.get("precipitation_probability_max") or [None])[i],
        "precip_sum_mm": (daily.get("precipitation_sum") or [None])[i],
        "wind_max_kmh": (daily.get("wind_speed_10m_max") or [None])[i],
        "wind_gust_kmh": (daily.get("wind_gusts_10m_max") or [None])[i],
        "uv_max": (daily.get("uv_index_max") or [None])[i],
        "sunrise": (daily.get("sunrise") or [None])[i],
        "sunset": (daily.get("sunset") or [None])[i],
        "window": "%s ~ %s" % (times[0], times[-1]),
    }
    # 逐时（只留 11:00-23:00，看球时段）
    h = d.get("hourly") or {}
    ht = h.get("time") or []
    hours = []
    for j, ts in enumerate(ht):
        if not ts.startswith(a.date):
            continue
        hh = int(ts[11:13])
        if 11 <= hh <= 23:
            hours.append({
                "time": ts[11:16],
                "temp": (h.get("temperature_2m") or [None])[j],
                "precip_prob": (h.get("precipitation_probability") or [None])[j],
                "precip_mm": (h.get("precipitation") or [None])[j],
                "wind_kmh": (h.get("wind_speed_10m") or [None])[j],
                "condition": wmo((h.get("weather_code") or [None])[j]),
            })
    rec["hours"] = hours
    rec["reliability"] = ("仅供趋势参考（距今天 %d 天，临近 3 天内才准）" % days) if days >= 7 else \
                         ("参考（距今天 %d 天）" % days if days >= 3 else "较可信（距今天 %d 天）" % days)

    if a.json:
        print(json.dumps(rec, ensure_ascii=False, indent=1))
        return 0

    lines = ["🌦 **%s（%s）旗忠网球中心天气** — 距今天 %d 天｜%s"
             % (rec["date"], rec["weekday"], days, rec["reliability"]),
             "- 天气：%s｜气温 %s~%s℃｜降水概率 %s%%｜降水量 %s mm"
             % (rec["condition"], rec["temp_min"], rec["temp_max"],
                rec["precip_prob_max"], rec["precip_sum_mm"]),
             "- 风：最大 %s km/h（阵风 %s）｜紫外线指数 %s｜日出 %s / 日落 %s"
             % (rec["wind_max_kmh"], rec["wind_gust_kmh"], rec["uv_max"],
                (rec["sunrise"] or "")[11:16], (rec["sunset"] or "")[11:16])]
    if hours:
        wet = [x for x in hours if (x["precip_prob"] or 0) >= 40]
        lines.append("- 逐时（11:00-23:00）：%s" % "、".join(
            "%s %s℃/%s%%" % (x["time"], x["temp"], x["precip_prob"]) for x in hours[::2]))
        lines.append("- 观赛提示：%s" % ("降水概率 ≥40%% 的时段：" + "、".join(x["time"] for x in wet) +
                                     "（带雨具，露天场可能暂停/推迟）" if wet else "全场次无高降水时段"))
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    sys.exit(main())
