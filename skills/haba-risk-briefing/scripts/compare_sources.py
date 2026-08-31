#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""双源对比：Open-Meteo(网格/国外) vs 中国气象局/中国天气网(站点实测/官方) —— 一次性诊断+日常自查用"""
import json
import subprocess
import sys
import os

HERE = os.path.dirname(os.path.abspath(__file__))


def run(name):
    r = subprocess.run([sys.executable, os.path.join(HERE, name)], capture_output=True, text=True, timeout=300)
    try:
        return json.loads(r.stdout)
    except Exception:  # noqa: BLE001
        return {"_run_failed": True, "stderr": r.stderr[:500], "stdout_tail": r.stdout[-300:]}


def d(x, unit="", nd=1):
    if x is None:
        return "N/A"
    try:
        return f"{float(x):.{nd}f}{unit}"
    except (TypeError, ValueError):
        return str(x)


def main():
    om = run("fetch_haba_weather.py")
    cma = run("fetch_cma.py")
    print("=" * 70)
    print("双源对比 ｜ Open-Meteo(网格) vs 中国气象局/中国天气网(官方)")
    print(f"生成时间: OM={om.get('generated_at_bjt')} | CMA={cma.get('generated_at_bjt')}")
    print("=" * 70)

    # 站点对比
    for key, label, om_key in [("xianggelila", "香格里拉(3280m)", "xianggelila"),
                               ("lijiang", "丽江(2400m)", "lijiang")]:
        st = cma.get("stations", {}).get(key, {})
        om_pt = om.get("points", {}).get(om_key, {})
        print(f"\n--- {label} ---")
        print(f"  OM 网格 过去24h雨量: {d(om_pt.get('past24h_sum_mm'))}mm | "
              f"站点实测24h雨量(wc_obs.rain24h): {d(st.get('wc_obs',{}).get('rain24h_mm'))}mm")
        print(f"  OM 过去72h: {d(om_pt.get('past72h_sum_mm'))}mm | "
              f"OM未来24/48/72h: {d(om_pt.get('next24h_sum_mm'))}/{d(om_pt.get('next48h_sum_mm'))}/{d(om_pt.get('next72h_sum_mm'))}mm")
        print(f"  官方预报(CMA): " + " | ".join(
            f"{x['date'][5:]} {x['day']} {x['high_c']}/{x['low_c']}℃"
            for x in st.get("daily", [])[:3]) or "N/A")
        now = st.get("now", {})
        print(f"  官方实况(08:10): {d(now.get('temperature_c'),'℃')} {now.get('wind','')} "
              f"湿度{d(now.get('humidity_pct'),'%',0)} {now.get('obs_time_bjt')}")

    print("\n--- 官方预警(dingzhi alarm / 国家预警信息发布中心) ---")
    for w in cma.get("warnings", []):
        print(f"  [{w.get('level')}]{w.get('type')}预警 {w.get('region')} {w.get('publish_time_bjt')}")
        print(f"    {w.get('text','')[:150]}")

    print("\n--- 山地点位 OM 趋势(无国家站，仅网格) ---")
    for k in ["tlg_town", "haba_village", "lanhuaping", "heihai", "haba_summit"]:
        p = om.get("points", {}).get(k, {})
        if not p:
            continue
        nxt = [x for x in p.get("days", []) if x.get("date", "") > (om.get("generated_at_bjt", "")[:10])]
        nxt_s = " | ".join(f"{x['date'][5:]} {x['sum_mm']}mm" for x in nxt[:3])
        print(f"  {p.get('name')}: 24h={d(p.get('past24h_sum_mm'))}mm 72h={d(p.get('past72h_sum_mm'))}mm "
              f"未来3天: {nxt_s} 短时强降水窗口={len(p.get('short_intense_windows', []))}")

    om_err = om.get("fetch_errors", [])
    cma_err = cma.get("fetch_errors", [])
    print("\nfetch_errors: OM:", om_err, " CMA:", cma_err)
    if not om_err and not cma_err and cma.get("warnings"):
        print("\n✅ 双源均正常，官方预警已捕获")


if __name__ == "__main__":
    main()
