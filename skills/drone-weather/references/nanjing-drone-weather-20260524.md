# Nanjing (南京) Drone Weather — Worked Example
## Date: May 24, 2026 (Sunday) — 17:00 CST

## Current METAR
```
ZSNJ 240900Z 13004MPS 9999 BKN012 BKN033 26/26 Q1004 BECMG TL1030 SCT015
```

- Station: ZSNJ (南京禄口国际机场)
- Time: 09:00 UTC = 17:00 CST
- Wind: 130° at 4 m/s
- Visibility: 9999 (≥10 km, excellent)
- **Cloud layer 1: BKN012** = 1,200 ft = **366 m** (broken, 5-7/8 coverage)
- **Cloud layer 2: BKN033** = 3,300 ft = **1,006 m** (broken, 5-7/8 coverage)
- Temp/Dew: 26°C / 26°C (100% humidity — saturated air)
- Pressure: Q1004 hPa
- Trend: BECMG TL1030 SCT015 — by 10:30 UTC (18:30 CST), scattered at 1,500 ft

## Today's Full Cloud Trend (all times CST)

| Time | Low Layer | Mid Layer | Trend |
|------|-----------|-----------|-------|
| 13:00 | BKN @ 500ft (152m) | OVC @ 2,300ft (701m) | Low, dense |
| 14:00 | BKN @ 700ft (213m) | OVC @ 4,000ft (1,219m) | Lifting |
| 15:00 | BKN @ 900ft (274m) | BKN @ 4,000ft (1,219m) | Lifting, some showers |
| 16:00 | BKN @ 1,000ft (305m) | BKN @ 3,300ft (1,006m) | Improving |
| 17:00 | **BKN @ 1,200ft (366m)** | BKN @ 3,300ft (1,006m) | ✅ Best of day |

## Suitability Assessment

**Criteria applied:**
1. Low clouds < 500m? → Yes, BKN at **366m** ✓
2. Gap at 500-600m clear? → Next layer at **1,006m** → gap clear ✓
3. Clouds above 600m? → Present but irrelevant ✓

**Score: ✅ Ideal** — Low clouds at 366m with a wide gap up to 1,006m. Drone can fly above the 366m deck and still be well below the next layer.

**Caveats:**
- Temp = Dewpoint → 100% humidity, fog potential
- BKN = 5-7/8 coverage → not a solid overcast, some breaks exist
- Wind is light (4 m/s) — very flyable

## TAF Forecast (Next 24h)
```
TAF AMD ZSNJ 240619Z 2406/2506 12004MPS 3000 -RA BR BKN010 BKN030
  TEMPO 2420/2424 SHRA BKN010 FEW030CB BKN030
```

- Tonight 20:00-00:00 UTC (04:00-08:00 CST Mon): TEMPO showers + CB clouds → **unsuitable**
- Tomorrow (May 25): BKN010 @ 305m + BKN030 @ 914m, light rain/mist, visibility 3km → marginal at best

## Key Takeaway
The afternoon window (15:00-18:00 CST) was the best for 穿云 on May 24. Conditions were marginal in the morning and early afternoon (cloud base too low), improved through the day, and will worsen tonight with rain.
