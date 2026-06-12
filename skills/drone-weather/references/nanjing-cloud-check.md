# Nanjing Cloud Check — City-Specific Implementation

> Absorbed from `nanjing-cloud-check` skill into drone-weather umbrella.

## Overview

Nanjing-specific implementation of the drone-weather methodology. Adds **dual-model (ECMWF + GFS) cloud base prediction** and a **5-source cross-validation** architecture.

## Architecture (5 Sources + Tomorrow Prediction)

| Source | Role |
|--------|------|
| **METAR (ZSNJ Lukou Airport)** | Actual cloud layer heights from aviation report |
| **Moji Weather (市区)** | Real-time temperature/humidity → independent cloud base estimate via dew point formula |
| **ECMWF (Open-Meteo)** | Current cloud base + tomorrow 05:00-09:00 hourly forecast |
| **GFS (Open-Meteo)** | Cross-validation + precipitation probability |
| **Confidence Score** | Multi-source consistency check |

## Ideal Conditions for Nanjing 穿云

| Condition | Requirement |
|-----------|-------------|
| Cloud base | **< 500m** (200m ideal) |
| Low cloud coverage | **≥ 30%** |
| Precipitation | **< 0.5mm/h** |
| Best window | Morning 05:00-07:00 (lowest base + good light) |

## One-Click Run

```bash
python3 ~/.hermes/skills/drone-weather/scripts/nanjing_cloud_check.py
```

Run in evening for tomorrow morning's prediction, then again after waking to confirm actual conditions.

## Key Data Sources

### METAR Decoding
| Code | Coverage |
|------|----------|
| SKC/CLR | Clear sky |
| FEW | 1-2/8 |
| SCT | 3-4/8 |
| BKN | 5-7/8 |
| OVC | 8/8 |

1 ft = 0.3048 m. Cloud base formula: (T - Td) × 125m (LCL approximation).

### Open-Meteo Models
- **ECMWF** (European): `api.open-meteo.com/v1/ecmwf` — slightly wet bias
- **GFS** (American): `api.open-meteo.com/v1/gfs` — slightly dry bias
- Free, no API key, returns structured JSON

## Notes
- Models have ~1-3h latency; tomorrow forecast is directional
- ECMWF precipitation bias: wetter than reality; GFS: drier
- Take actual midpoint between the two models
- ⚠️ For reference only — always confirm visually before takeoff
