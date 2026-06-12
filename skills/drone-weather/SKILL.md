---
name: drone-weather
description: "Check weather conditions for drone aerial photography — METAR/TAF cloud layer analysis, 穿云 (cloud-penetrating) suitability scoring"
triggers:
  - "check drone weather"
  - "南京云层"
  - "穿云拍摄"
  - "cloud conditions for drone"
  - "drone flying weather"
  - "能不能飞无人机"
  - "现在能拍穿云吗"
---

# Drone Weather — Cloud Layer Analysis for Aerial Photography

## Overview
Analyze aviation weather reports (METAR/TAF) to determine if current or forecast conditions are suitable for drone-based 穿云 (cloud-penetrating) photography. The key question: is there a low cloud deck below the drone's max altitude, with a clear air gap above it so the drone can fly between layers?

## Key Criteria for 穿云 Suitability
The ideal condition for drone cloud-penetrating shots (drone takes off at ~30m, flies to ~500m):
1. **Low cloud layer** exists below **500 m (1,640 ft)** — the drone flies above this layer
2. **Clear air gap** at **500-600 m** — no cloud layer in this band (next layer is well above)
3. **Clouds above 600 m** don't matter

| Score | Condition |
|-------|-----------|
| ✅ Ideal | Low clouds < 500m AND gap clear at 500-600m |
| ⚠️ Marginal | Low clouds exist but gap unclear or thin |
| ❌ Unsuitable | No low clouds / clouds blocking 500-600m gap |

**Cross-validation principle**: use multiple data sources (METAR + TAF + trend) for comprehensive judgment, not a single snapshot.

## Data Sources (all free, no API keys)

### Primary: NOAA FTP (latest METAR)
```
curl -s "https://tgftp.nws.noaa.gov/data/observations/metar/stations/<ICAO>.TXT"
```
Returns the most recent hourly observation. E.g. for Nanjing: ZSNJ.

### Secondary: AWC API (METAR + TAF forecast)
```
curl -s "https://aviationweather.gov/api/data/metar?ids=<ICAO>&format=raw&taf=true"
```
Adding `&taf=true` gets the 24h forecast alongside current conditions.

### Historical trend: OGIMET (last ~24h)
```
https://www.ogimet.com/display_metars2.php?lang=en&lugar=<ICAO>&tipo=SA&ord=REV&nil=SI&fmt=txt&send=send
```
Then grep for the ICAO code lines to extract observations. Use this to determine if cloud base is **rising** (improving) or **lowering** (worsening).

### Important: use curl, not web_extract
The web_extract tool routes through Exa which can block aviationweather.gov URLs. Always use `terminal(command="curl ...")` for METAR/TAF fetching.

## METAR Decoding Guide

### Cloud layer format
`<cover><height_in_hundreds_of_ft>`

| Code | Meaning | Coverage |
|------|---------|----------|
| FEW | Few | 1-2/8 of sky |
| SCT | Scattered | 3-4/8 |
| BKN | Broken | 5-7/8 |
| OVC | Overcast | 8/8 |

**Example**: `BKN012` = Broken clouds at 1,200 ft AGL.

### Feet to Meters conversion
| Feet | Meters | Significance |
|------|--------|--------------|
| 500 | 152 | very low |
| 1,000 | 305 | low |
| 1,500 | 457 | approaching threshold |
| **1,640** | **500** | **key threshold for drone** |
| 2,000 | 610 | upper gap boundary |

Formula: `meters = feet × 0.3048`

### Other useful METAR fields
- **9999** = visibility ≥ 10 km (good)
- **3000-5000** = visibility 3-5 km (mist/haze)
- **Temp = Dewpoint** = 100% humidity, saturated air, likely fog/low clouds
- **Q1004** = QNH pressure in hPa
- **-RA** = light rain, **BR** = mist, **SHRA** = rain showers

### TAF forecast key patterns
- `TEMPO` = temporary changes (usually showers, visibility drop)
- `BECMG TL<HHMM>` = becoming by time (gradual change)
- `NOSIG` = no significant change
- `FM<HHMM>` = from time (more definitive change)

## Workflow

### Step 1: Identify the nearest ICAO airport code
- Nanjing (南京中心城区): ZSNJ (禄口机场, ~35km from city center — close enough for cloud layer approximation)
- For other Chinese cities, search "ICAO code <city name> airport"
- METAR cloud data is representative within ~50km radius

### Step 2: Fetch current METAR
Use curl with the AWC API to get METAR + TAF in one call.

### Step 3: Parse cloud layers
Extract BKN/OVC/SCT/FEW entries, convert feet to meters.

### Step 4: Get historical trend (OGIMET)
Fetch last 4-6h of METARs to see cloud base trajectory.

### Step 5: Score suitability
Apply the 3-tier scoring system above.

### Step 6: Output human-readable assessment
Include: current cloud structure (numbered layers with m/ft), suitability score, recommended shooting window (if TAF shows improvement).

## Pitfalls
- METAR is updated hourly (~:00 past the hour) — conditions can change between reports
- Cloud base heights are rounded to nearest 100 ft
- Airport-level data may differ from specific neighborhood conditions, especially if terrain varies
- The AWC API endpoint has changed in the past; if it 404s, check aviationweather.gov for current docs
- Do NOT use web_extract for METAR fetching — Exa may have exhausted credits or block the URL
- Always check the full TAF, not just the current METAR — conditions may improve/deteriorate within hours

## City-Specific Implementations

### Nanjing (南京) — `references/nanjing-cloud-check.md` + `scripts/nanjing_cloud_check.py`

A full Nanjing-specific implementation with **5-source cross-validation** and **dual-model (ECMWF + GFS) tomorrow-morning prediction**.

Key differences from the general workflow:
- **5 sources**: METAR (ZSNJ), Moji Weather (市区 humidity/temp), ECMWF cloud base via dew point, GFS cross-validation, confidence scoring
- **Tomorrow forecast**: ECMWF + GFS dual-model comparison for 05:00-09:00 CST
- **One-click**: `python3 scripts/nanjing_cloud_check.py` — runs all sources independently
- **Ideal for**: Any Nanjing-based drone shooter checking conditions the night before and morning of

The script adds direct dew-point cloud base calculation (`LCL ≈ (T - Td) × 125m`) as a secondary check alongside the METAR cloud layer heights. This is particularly useful when METAR is stale (hourly updates only) and you want a real-time estimate from local weather station data.

## Adapting to Other Cities

To create a city-specific variant:
1. Find the nearest ICAO airport code (search "ICAO code <city name> airport")
2. Find the city's lat/lon coordinates for Open-Meteo API
3. Replace `ZSNJ`, `32.06/118.79` in the script template
4. If available, add a local weather station URL for real-time temp/humidity

## References
- `references/nanjing-drone-weather-20260524.md` — Worked example with real data from Nanjing on May 24, 2026.
- `references/nanjing-cloud-check.md` — Full Nanjing implementation details with code comments.
- `scripts/nanjing_cloud_check.py` — Standalone Python script for Nanjing 穿云 conditions.
