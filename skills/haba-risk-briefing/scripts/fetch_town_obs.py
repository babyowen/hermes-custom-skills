#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
虎跳峡·哈巴雪山 简报数据腿 3：乡镇自动站**实测**（打底/校正用）

数据源：中国天气网 乡镇预报页内嵌数据（中央气象台 乡镇自动站）
  https://forecast.weather.com.cn/town/weather1dn/<code>.shtml
  页面内嵌 `var forecast_default = {...}`  → 最新实况(时次/温度/天气/湿度/风) + 该镇官方乡镇预报高低温
  页面内嵌 `var observe24h_data = {...}`   → 过去24h**逐时实测**（必须匹配 od0 == 该站号，页面还嵌了北京默认块）

用途：给「网格估算温度」做锚定校正（偏差 = 实况 − 同点位网格估算@同一时刻），
      虎跳峡镇河谷点网格高程 3290m vs 实际 1853m，官方乡镇预报又锚在香格里拉(3280m)，
      只有该镇自己的自动站实测能反映河谷真实温度。

仅用 Python 标准库，无 API key。全部站点失败才 exit 1（单站失败保留 errors 字段）。
"""
import json
import re
import sys
import urllib.request
from datetime import datetime

# 注意：该站 WAF 会 403 掉"完整 Chrome UA + Accept/Accept-Language"组合，用这个短 UA 才通（2026-09 实测）
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
HEADERS = {"User-Agent": UA, "Referer": "https://www.weather.com.cn/"}

# key, 站点号, 名称, 海拔(m), 用途
TOWNS = [
    ("tlg_town", "101291301003", "虎跳峡镇", 1853,
     "河谷点锚点（镇政府·下桥头 1853m）"),
    ("sanba", "101291301008", "三坝乡", 2380,
     "哈巴村锚点（乡政府·白地村约2380m，哈巴村再高约300m）"),
    ("jiantang", "101291301004", "建塘镇(香格里拉城区)", 3280,
     "兰花坪/黑海锚点（香格里拉城区 3280m）"),
    ("jinjiang", "101291301005", "金江镇", 1900,
     "河谷交叉校验（金沙江边 ~1900m）"),
]

URL = "https://forecast.weather.com.cn/town/weather1dn/%s.shtml"
RE_DEFAULT = re.compile(r"var\s+forecast_default\s*=\s*(\{.*?\});", re.S)
RE_OBS24 = re.compile(r"var\s+observe24h_data\s*=\s*(\{.*?\});", re.S)


def fetch_html(code):
    req = urllib.request.Request(URL % code, headers=HEADERS)
    last = None
    for attempt in (1, 2, 3):
        try:
            with urllib.request.urlopen(req, timeout=25) as r:
                return r.read().decode("utf-8", "ignore")
        except Exception as e:  # noqa: BLE001
            last = f"attempt{attempt}: {e}"
    raise RuntimeError(last)


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def parse_town(code):
    html = fetch_html(code)

    m = RE_DEFAULT.search(html)
    if not m:
        raise RuntimeError("未找到 forecast_default（页面结构可能变化）")
    d = json.loads(m.group(1))
    obs = {
        "time_bjt": d.get("time"),
        "temp_c": _num(d.get("temp")),
        "weather": d.get("weather"),
        "humidity_pct": _num(d.get("humidity")),
        "wind": d.get("wind"),
    }
    town_fc = {"tmax_c": _num(d.get("maxTemp")), "tmin_c": _num(d.get("minTemp"))}

    hours = []
    for mm in RE_OBS24.finditer(html):
        try:
            blk = json.loads(mm.group(1))
        except Exception:  # noqa: BLE001
            continue
        od = blk.get("od") or {}
        if od.get("od0") != code:          # 跳过页面内嵌的北京默认块
            continue
        for row in od.get("od2") or []:
            hours.append({
                "hour": row.get("od21"),
                "temp_c": _num(row.get("od22")),
                "rain_mm": _num(row.get("od26")),
                "humidity_pct": _num(row.get("od27")),
            })
        break

    temps = [h["temp_c"] for h in hours if h["temp_c"] is not None]
    rain = [h["rain_mm"] for h in hours if h["rain_mm"] is not None]
    past24 = {
        "hours": hours,
        "tmax_c": round(max(temps), 1) if temps else None,
        "tmin_c": round(min(temps), 1) if temps else None,
        "rain24h_mm": round(sum(rain), 1) if rain else None,
        "n_hours": len(hours),
    }
    return {"obs": obs, "cma_town_forecast": town_fc, "past24h": past24}


def main():
    out = {
        "generated_at_bjt": datetime.now().astimezone().strftime("%Y-%m-%d %H:%M"),
        "source": "中国天气网乡镇预报页内嵌乡镇自动站实测(中央气象台) + 该镇官方乡镇预报高低温",
        "note": ("乡镇自动站**逐时实测**，非模型网格；obs.time_bjt 为该站最新观测时次；"
                 "past24h.hours 为过去24h逐时实测（用于校验当日高低温是否合理）"),
        "towns": {},
        "fetch_errors": [],
    }
    failed = 0
    for key, code, name, elev, purpose in TOWNS:
        try:
            t = parse_town(code)
            t.update({"code": code, "name": name, "elev_m": elev, "purpose": purpose})
            out["towns"][key] = t
        except Exception as e:  # noqa: BLE001
            failed += 1
            out["fetch_errors"].append({"key": key, "name": name, "error": str(e)[:200]})
    print(json.dumps(out, ensure_ascii=False, indent=1))
    if failed == len(TOWNS):
        sys.exit(1)


if __name__ == "__main__":
    main()
