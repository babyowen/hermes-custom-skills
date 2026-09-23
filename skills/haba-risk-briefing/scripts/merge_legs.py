#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
虎跳峡·哈巴雪山简报 **合并脚本（算法本体，唯一真源）** v1.6

位置约定（2026-09-23 起）：
  本文件 = 技能目录 `skills/haba-risk-briefing/scripts/merge_legs.py`（进 git，受版本控制）
  系统里 `~/.hermes/scripts/fetch_haba_weather.py` 只是 3 行 shim（cron 的 script 字段指向它），
  它 runpy 本文件。改算法只改这里，不要改系统那份。

跑三条数据腿，合并为一个 JSON 注入 agent 会话：
  腿1 open_meteo   = Open-Meteo 网格（无 key，趋势参考，非实测）
  腿2 domestic_cma = 中国气象局/中国天气网 国家站实测 + 官方预报 + 官方预警（权威优先）
  腿3 town_obs     = 中国天气网 乡镇自动站**逐时实测**（打底/锚定用）

并算出 `temp_obs_corrected`：**实况锚定偏差校正**
  低温偏差 = 锚点站过去24h实测最低 − 该锚点网格同期估算最低
  高温偏差 = 锚点站过去24h实测最高 − 该锚点网格同期估算最高
  校正后 = 网格估算 + 偏差（分别平移当日高温/低温，既修偏移也修日振幅）
理由：虎跳峡镇河谷点网格高程 3290m vs 实际 1853m，固定 6.5℃/1000m 直减率会高估约 2~3℃；
      官方乡镇预报又把该镇锚在香格里拉(3280m)（实测偏低 5~7℃），两边都不可直接信。
      该镇自动站实测才是河谷真值 → 用「实测 − 模式同期估算」的差把当日预报拉回来。

三条腿全失败才 exit 1（单腿失败保留其 fetch_errors 供 agent 降级）。
"""
import json
import os
import subprocess
import sys
from datetime import datetime

HERE_CANDIDATES = [
    os.path.dirname(os.path.abspath(__file__)),          # 本文件所在目录（技能目录，三条腿脚本都在这里）
    os.path.expanduser("~/.hermes/skills/haba-risk-briefing/scripts"),
    os.path.expanduser("~/hermes-custom/skills/haba-risk-briefing/scripts"),
]
HERE = next((p for p in HERE_CANDIDATES if os.path.isdir(p)), os.path.dirname(os.path.abspath(__file__)))

# 锚点定义：station=("town", key) 乡镇自动站 | ("cma", key) 国家站；model_point=用来量偏差的网格点位
ANCHORS = {
    "tlg_town":  {"station": ("town", "tlg_town"), "name": "虎跳峡镇乡镇自动站",
                  "elev_m": 1853, "model_point": "tlg_town"},
    "sanba":     {"station": ("town", "sanba"), "name": "三坝乡乡镇自动站",
                  "elev_m": 2380, "model_point": "sanba"},
    "jiantang":  {"station": ("town", "jiantang"), "name": "建塘镇(香格里拉城区)乡镇自动站",
                  "elev_m": 3280, "model_point": "xianggelila"},
    "lijiang_st": {"station": ("cma", "lijiang"), "name": "丽江国家站",
                   "elev_m": 2400, "model_point": "lijiang"},
}

# 路线点位 → 锚点
POINT_ANCHOR = {
    "tlg_town": "tlg_town",
    "haba_village": "sanba",
    "lanhuaping": "jiantang",
    "heihai": "jiantang",
    "xianggelila": "jiantang",
    "lijiang": "lijiang_st",
}
ROUTE_POINTS = ["tlg_town", "haba_village", "lanhuaping", "heihai"]


def run_leg(name):
    try:
        r = subprocess.run([sys.executable, os.path.join(HERE, name)],
                           capture_output=True, text=True, timeout=300)
        data = json.loads(r.stdout)
        if r.returncode != 0:
            data.setdefault("fetch_errors", []).append("script exit=%s" % r.returncode)
        return data, r.returncode != 0
    except Exception as e:  # noqa: BLE001
        return {"_run_failed": True, "error": str(e)[:300]}, True


def _est_at_time(point, hour, minute=0):
    """把某点位今日逐时网格估算线性插值到指定时刻（观测时次多为 :50）。"""
    te = (point or {}).get("temp_est") or {}
    series = te.get("hourly_today") or []
    vals = {}
    for h in series:
        try:
            vals[int(str(h.get("time_bjt", ""))[:2])] = h.get("est_c")
        except (TypeError, ValueError):
            continue
    if not vals:
        return None
    if hour in vals:
        base = vals[hour]
        nxt = vals.get(hour + 1)
        if minute and nxt is not None:
            return round(base + (nxt - base) * minute / 60.0, 1)
        return base
    return min(vals.items(), key=lambda kv: abs(kv[0] - hour))[1]


def _shift(v, b):
    return None if v is None else round(v + b, 1)


def _station_obs(anchor, town_obs, cma):
    kind, key = anchor["station"]
    if kind == "town":
        t = ((town_obs or {}).get("towns") or {}).get(key) or {}
        obs = t.get("obs") or {}
        return {"temp_c": obs.get("temp_c"), "time_bjt": obs.get("time_bjt"),
                "weather": obs.get("weather"), "code": t.get("code"),
                "source": "乡镇自动站实测(中国天气网/中央气象台)",
                "cma_town_forecast_c": t.get("cma_town_forecast"),
                "obs_past24h_c": [(t.get("past24h") or {}).get("tmin_c"),
                                  (t.get("past24h") or {}).get("tmax_c")]}
    st = ((cma or {}).get("stations") or {}).get(key) or {}
    obs = st.get("now") or {}
    return {"temp_c": obs.get("temperature_c"), "time_bjt": obs.get("obs_time_bjt"),
            "weather": None, "code": st.get("station_id"),
            "source": "国家站实测(weather.cma.cn)",
            "cma_town_forecast_c": None, "obs_past24h_c": None}


def build_correction(om, town_obs, cma):
    """实况锚定偏差校正（两点法：分别校高温/低温）。

    b_lo = 锚点站过去24h实测最低 − 该锚点网格过去24h估算最低
    b_hi = 锚点站过去24h实测最高 − 该锚点网格过去24h估算最高
    今日 tmin += b_lo、tmax += b_hi；窗口温按其在模式日振幅中的相对位置线性插值偏差。
    这样既修偏移也修日振幅误差（河谷点网格高程偏差大，日振幅常被高估）。
    """
    warnings = []
    points = (om or {}).get("points") or {}
    now = datetime.now().astimezone()

    anchors, point_bias = {}, {}
    for aid, adef in ANCHORS.items():
        info = {"anchor": adef["name"], "anchor_elev_m": adef["elev_m"],
                "model_point": adef["model_point"]}
        obs = _station_obs(adef, town_obs, cma)
        info.update({"source": obs["source"], "anchor_code": obs["code"],
                     "obs_time_bjt": obs["time_bjt"], "obs_c": obs["temp_c"],
                     "weather": obs["weather"],
                     "cma_town_forecast_c": obs["cma_town_forecast_c"],
                     "obs_past24h_c": obs["obs_past24h_c"]})
        hour = minute = 0
        try:
            parts = [p for p in str(obs["time_bjt"]).replace("/", " ").split() if ":" in p]
            hh, mm = parts[-1].split(":")[:2]
            hour, minute = int(hh), int(mm)
        except (TypeError, ValueError, IndexError):
            hour, minute = now.hour, 0
        mpoint = points.get(adef["model_point"]) or {}
        mte = mpoint.get("temp_est") or {}
        model_est = _est_at_time(mpoint, hour, minute)
        info["model_est_at_obs_c"] = model_est
        if obs["temp_c"] is not None and model_est is not None:
            info["bias_obs_time_c"] = round(obs["temp_c"] - model_est, 1)

        obs24 = obs["obs_past24h_c"] or [None, None]
        mp24 = mte.get("past24h") or {}
        b_lo = b_hi = None
        if obs24[0] is not None and mp24.get("tmin_c") is not None:
            b_lo = round(obs24[0] - mp24["tmin_c"], 1)
        if obs24[1] is not None and mp24.get("tmax_c") is not None:
            b_hi = round(obs24[1] - mp24["tmax_c"], 1)
        if b_lo is None or b_hi is None:                       # 退化为单点偏移
            b = info.get("bias_obs_time_c")
            b_lo = b_hi = b
            info["method"] = "单点偏移(缺过去24h实测或网格同期值)"
        else:
            info["method"] = "两点法(高低温分别校正)"
            info["model_past24h_c"] = [mp24.get("tmin_c"), mp24.get("tmax_c")]
        info["bias_low_c"], info["bias_high_c"] = b_lo, b_hi
        if b_lo is not None and abs(b_lo) > 8:
            warnings.append(f"{adef['name']} 低温偏差 {b_lo}℃ 过大，核对实况时次是否新鲜")
        if b_hi is not None and abs(b_hi) > 8:
            warnings.append(f"{adef['name']} 高温偏差 {b_hi}℃ 过大，核对实况时次是否新鲜")
        if (info.get("bias_obs_time_c") is not None and b_lo is not None and b_hi is not None
                and abs(info["bias_obs_time_c"] - (b_lo + b_hi) / 2) > 3):
            warnings.append(f"{adef['name']} 观测时次偏差 {info['bias_obs_time_c']}℃ 与日高低温偏差 "
                            f"({b_lo}/{b_hi}) 差>3℃，模式日振幅可能异常")
        try:
            obs_dt = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            info["obs_lag_h"] = round((now - obs_dt).total_seconds() / 3600.0, 1)
            if info["obs_lag_h"] > 4:
                warnings.append(f"{adef['name']} 实况时次 {obs['time_bjt']} 距当前 {info['obs_lag_h']}h，可能偏旧")
        except (TypeError, ValueError):
            pass
        anchors[aid] = info
        point_bias[aid] = (b_lo, b_hi)

    pts_out = {}
    for pkey, aid in POINT_ANCHOR.items():
        info = anchors.get(aid) or {}
        bias = point_bias.get(aid) or (None, None)
        b_lo, b_hi = bias
        te = (points.get(pkey) or {}).get("temp_est") or {}
        if b_lo is None or not te.get("available"):
            pts_out[pkey] = {"available": False,
                             "reason": info.get("error") or "锚点偏差或 temp_est 不可用"}
            continue

        def corr_any(v, t_lo, t_hi):
            """按模式日振幅中的相对位置插值偏差（低点用 b_lo、高点用 b_hi）。"""
            if v is None:
                return None
            if b_lo == b_hi or t_lo is None or t_hi is None or t_hi == t_lo:
                return round(v + b_lo, 1)
            frac = (v - t_lo) / (t_hi - t_lo)
            frac = max(0.0, min(1.0, frac))
            return round(v + b_lo + (b_hi - b_lo) * frac, 1)

        today = te.get("today") or {}
        t_lo, t_hi = today.get("tmin_c"), today.get("tmax_c")
        wins = te.get("windows_today_c") or {}
        item = {
            "available": True,
            "anchor": info.get("anchor"),
            "bias_low_c": b_lo,
            "bias_high_c": b_hi,
            "bias_obs_time_c": info.get("bias_obs_time_c"),
            "today": {
                "tmin_c": _shift(t_lo, b_lo),
                "tmax_c": _shift(t_hi, b_hi),
            },
            "windows_today_c": {k: corr_any(v, t_lo, t_hi) for k, v in wins.items()},
            "days": [{"date": d.get("date"), "tmin_c": _shift(d.get("tmin_c"), b_lo),
                      "tmax_c": _shift(d.get("tmax_c"), b_hi)} for d in (te.get("days") or [])],
            "next3d_night_min_c": _shift(te.get("next3d_night_min_c"), b_lo),
            "next72h_min_c": _shift(te.get("next72h_min_c"), b_lo),
        }
        obs24 = info.get("obs_past24h_c")
        a_elev = info.get("anchor_elev_m")
        p_elev = te.get("actual_elev_m")
        if obs24 and obs24[0] is not None and obs24[1] is not None:
            # 期望区间：锚点实测 + 标准直减率外推到目标点位海拔（锚点与目标点海拔不同时必须换算）
            exp_lo = exp_hi = None
            if a_elev and p_elev:
                d = 6.5 * (a_elev - p_elev) / 1000.0
                exp_lo, exp_hi = round(obs24[0] + d, 1), round(obs24[1] + d, 1)
            item["check"] = {"anchor_obs_past24h_c": obs24,
                             "expected_at_point_elev_c": [exp_lo, exp_hi],
                             "note": "期望区间=锚点实测按6.5℃/1000m外推到本点位海拔；校正值偏离>4℃ 说明模式日振幅异常"}
            tmax, tmin = item["today"].get("tmax_c"), item["today"].get("tmin_c")
            if exp_hi is not None and tmax is not None and abs(tmax - exp_hi) > 4:
                warnings.append(f"{pkey} 校正后高温 {tmax}℃ 偏离期望 {exp_hi}℃ 超4℃（锚点 {info.get('anchor')}）")
            if exp_lo is not None and tmin is not None and abs(tmin - exp_lo) > 4:
                warnings.append(f"{pkey} 校正后低温 {tmin}℃ 偏离期望 {exp_lo}℃ 超4℃（锚点 {info.get('anchor')}）")

            # 不确定度：锚点与目标点海拔差 >300m 时模式的高度衰减不可靠，取两法(偏差校正/实测外推)的并集
            elev_gap = abs((a_elev or 0) - (p_elev or 0))
            unc = 0.0
            if elev_gap > 300:
                unc = max(unc, 2.0)
            bracket = {}
            for k, val, exp in (("tmin_c", tmin, exp_lo), ("tmax_c", tmax, exp_hi)):
                if val is None:
                    bracket[k] = None
                    continue
                if exp is None:
                    bracket[k] = [val, val]
                else:
                    bracket[k] = [round(min(val, exp), 1), round(max(val, exp), 1)]
                    spread = abs(val - exp)
                    if spread > 1.5:
                        unc = max(unc, round(spread, 1))
            item["elevation_gap_m"] = elev_gap
            item["uncertainty_c"] = unc or 0.0
            item["today_bracket"] = bracket
        pts_out[pkey] = item

    block = {
        "available": any(v.get("available") for v in pts_out.values()),
        "method": ("实况锚定偏差校正(两点法)：低温偏差=锚点站过去24h实测最低−该锚点网格同期估算最低；"
                   "高温偏差=实测最高−网格同期估算最高；再分别平移今日高温/低温与未来3天，"
                   "窗口温按其在模式日振幅中的相对位置插值偏差。"
                   "虎跳峡镇用本镇自动站；哈巴村用三坝乡站；兰花坪/黑海/香格里拉用建塘镇(城区)站；丽江用国家站。"
                   "偏差含「模式误差+网格高程误差」，故不要再叠加 temp_est 的固定直减率结果。"),
        "anchors": anchors,
        "points": pts_out,
        "route_points": ROUTE_POINTS,
        "warnings": warnings,
    }
    if not block["available"]:
        block["reason"] = "乡镇实况腿或网格腿不可用，无法校正，退回 temp_est"
    return block


def main():
    om, om_fail = run_leg("fetch_haba_weather.py")
    cma, cma_fail = run_leg("fetch_cma.py")
    town, town_fail = run_leg("fetch_town_obs.py")
    merged = {
        "merge_note": ("三条数据腿: open_meteo=国外网格(无key,趋势参考,非实测) / "
                       "domestic_cma=中国气象局+中国天气网(国家站实测+官方预报+官方预警,权威优先) / "
                       "town_obs=中国天气网乡镇自动站逐时实测(打底锚定)"),
        "open_meteo": om,
        "domestic_cma": cma,
        "town_obs": town,
        "temp_obs_corrected": build_correction(om, town, cma),
    }
    print(json.dumps(merged, ensure_ascii=False, indent=1))
    sys.exit(1 if (om_fail and cma_fail and town_fail) else 0)


if __name__ == "__main__":
    main()
