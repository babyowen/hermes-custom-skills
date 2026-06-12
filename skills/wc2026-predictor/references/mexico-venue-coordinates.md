# 墨西哥比赛场馆坐标 & Open-Meteo 天气查询

## 用途
每次赛前采集露天场馆当地天气预报时，直接用以下坐标 + Open-Meteo API 获取数据。

## 墨西哥场馆

| 场馆 | 城市 | 纬度 | 经度 | 海拔 | 屋顶 | 空调 |
|------|------|:----:|:----:|:----:|:----:|:----:|
| Estadio Azteca (阿兹特克) | 墨西哥城 | 19.3028 | -99.1504 | 2,200m | 露天 | 无 |
| Estadio Akron (艾克朗) | 瓜达拉哈拉 | 20.6818 | -103.4626 | 1,560m | 露天 | 无 |
| Estadio BBVA (BBVA) | 蒙特雷 | 25.6697 | -100.2444 | 530m | 露天 | 无 |

## 美国/加拿大场馆

| 场馆 | 城市 | 纬度 | 经度 | 屋顶 | 空调 |
|------|------|:----:|:----:|:----:|:----:|
| AT&T Stadium | 阿灵顿 | 32.7473 | -97.0945 | 封闭 | ✅ |
| Mercedes-Benz Stadium | 亚特兰大 | 33.7554 | -84.4008 | 封闭 | ✅ |
| NRG Stadium | 休斯顿 | 29.6847 | -95.4107 | 封闭 | ✅ |
| BMO Field | 多伦多 | 43.6333 | -79.4186 | 76m | 露天 | 无 |
| BC Place | 温哥华 | 49.2767 | -123.1120 | 4m | 封闭 | ✅ |
| SoFi Stadium | 洛杉矶 | 33.9533 | -118.3392 | 封闭 | ✅ |
| Rose Bowl | 帕萨迪纳 | 34.1614 | -118.1676 | 露天 | 无 |
| Levi's Stadium | 圣克拉拉 | 37.4033 | -121.9699 | 露天 | 无 |
| Hard Rock Stadium | 迈阿密 | 25.9580 | -80.2389 | 露天 | 无 |
| MetLife Stadium | 东卢瑟福 | 40.8135 | -74.0745 | 露天 | 无 |
| Arrowhead Stadium | 堪萨斯城 | 39.0489 | -94.4839 | 露天 | 无 |
| Lincoln Financial Field | 费城 | 39.9008 | -75.1675 | 露天 | 无 |
| Gillette Stadium | 福克斯堡 | 42.0909 | -71.2643 | 露天 | 无 |
| Lumen Field | 西雅图 | 47.5952 | -122.3316 | 露天 | 无 |

## Open-Meteo 查询模板

```bash
# 墨西哥城 (阿兹特克) — 开球19:00 UTC = 14:00 CDT
curl -s -o /tmp/weather.json \
  "https://api.open-meteo.com/v1/forecast?latitude=19.3028&longitude=-99.1504&hourly=temperature_2m,relative_humidity_2m,apparent_temperature,precipitation_probability,weather_code&timezone=auto&start_date=YYYY-MM-DD&end_date=YYYY-MM-DD"

# 解析：找到开球小时
python3 -c "
import json
with open('/tmp/weather.json') as f:
    data = json.load(f)
times = data['hourly']['time']
# 找指定小时的天气
for i, t in enumerate(times):
    if '14:00' in t:  # CDT local hour
        print(f'{t}: temp={data[\"hourly\"][\"temperature_2m\"][i]}°C, feels={data[\"hourly\"][\"apparent_temperature\"][i]}°C, RH={data[\"hourly\"][\"relative_humidity_2m\"][i]}%, rain={data[\"hourly\"][\"precipitation_probability\"][i]}%')
"
```

## 注意事项
- 封闭/空调场馆（AT&T/梅赛德斯/NRG/BC Place/SoFi）无需采集天气
- Open-Meteo 数据更新于UTC 00:00左右，当天预报精度尚可
- 开球时间用 19:00 UTC 统一换算当地小时：
  - 墨西哥城 (CDT, UTC-5): 14:00 local
  - 瓜达拉哈拉 (CST, UTC-6): 13:00 local
  - 蒙特雷 (CDT, UTC-5): 14:00 local
  - 洛杉矶 (PDT, UTC-7): 12:00 local
