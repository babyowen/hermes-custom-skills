# 数据源与检索参考（虎跳峡·哈巴雪山风险简报）

## 〇、三源架构（2026-09-23 v1.6 起；v1.1~v1.5 为双源）

- **国内官方腿**（权威优先，`scripts/fetch_cma.py`）：中国气象局国家站实况/官方预报 + 中国天气网站点24h雨量 + **官方预警 JSON（国家预警信息发布中心原文）**
- **乡镇实况腿**（**温度打底/锚定**，`scripts/fetch_town_obs.py`）：中国天气网乡镇预报页内嵌的**乡镇自动站逐时实测**（虎跳峡镇/三坝乡/建塘镇/金江镇）+ 该镇官方乡镇预报高低温
- **国外网格腿**（趋势参考，`scripts/fetch_haba_weather.py`）：Open-Meteo 7 个山地点位逐时降水/气温/阵风
- 合并脚本：**算法本体在技能目录 `scripts/merge_legs.py`（进 git，唯一真源）**；系统里 `~/.hermes/scripts/fetch_haba_weather.py` 只是 3 行 shim（cron 的 script 字段指向它），runpy 技能目录那份。**改算法只改技能目录那份**。注入 `{"open_meteo":…,"domestic_cma":…,"town_obs":…,"temp_obs_corrected":…}`；最后一项=**实况锚定偏差校正**（两点法，分别校高温/低温 + 不确定度）
- 对比验证：`scripts/compare_sources.py`（手动跑，双源并排输出）

### 乡镇自动站接口（v1.6 关键）

| 站点 | 站点号 | 海拔 | 用途 |
|:--|:--|--:|:--|
| 虎跳峡镇 | 101291301003 | 1853m | 河谷点锚点（镇政府·下桥头） |
| 三坝乡 | 101291301008 | 2380m | 哈巴村锚点（乡政府·白地村） |
| 建塘镇（香格里拉城区） | 101291301004 | 3280m | 兰花坪/黑海/香格里拉锚点 |
| 金江镇 | 101291301005 | 1900m | 河谷交叉校验 |

页面 `https://forecast.weather.com.cn/town/weather1dn/{站点号}.shtml` 内嵌（静态 HTML，可直接正则取）：

- `var forecast_default = {"time":"08:00","temp":14.9,"weather":"雾","humidity":96,"wind":"北风 1级","maxTemp":19,"minTemp":8}` → 最新实况 + 该镇官方乡镇预报高低温
- `var observe24h_data = {"od":{"od0":"101291301003","od2":[{"od21":"07","od22":14.8,"od26":0,"od27":96},…]}}` → 过去24h逐时实测（od21=时次 od22=气温 od26=降水 od27=湿度）；**od0=站点号，页面还内嵌 2 个北京默认块，必须匹配 od0 才算对**

> ⚠️ 该站 WAF 会 403 掉「完整 Chrome UA + Accept/Accept-Language」组合，**用短 UA `Mozilla/5.0 (Windows NT 10.0; Win64; x64)` + Referer 才通**（2026-09 实测）。
> ⚠️ 官方**乡镇预报**（`cma_town_forecast`）对虎跳峡镇是错的：8~19℃ 其实是香格里拉(3280m)的数，该镇自动站实测 14.6~25.4℃（差 6~7℃）。**手机天气（华为/中国天气网）查"虎跳峡镇"看到的也是这个数**，别跟着走。
> ⚠️ 香格里拉乡镇站对比（2026-09-23 07:50 实测）：建塘镇 8.1℃ / 格咱乡 8.6 / 三坝乡 12.6 / 上江乡 14.0 / 五境乡 14.1 / **虎跳峡镇 14.9** / 金江镇 15.7 / 东旺乡 16.9 / 尼西乡 18.1——河谷镇普遍比城区高 6~9℃。

## 一、国内官方接口（fetch_cma.py 已封装，web_extract 降级模板）

| 接口 | URL | 说明 |
|:--|:--|:--|
| CMA 国家站实况 | `https://weather.cma.cn/api/now/{站号}` | 香格里拉=56543，丽江=56651；温度/降水/湿度/气压/风力/体感，lastUpdate |
| CMA 官方逐日预报 | `https://weather.cma.cn/api/weather/{站号}` | data.daily[] 7天：高低温/白天夜间天气/风 |
| 中国天气网站点实况 | `https://d1.weather.com.cn/sk_2d/{城市码}.html` | **rain24h 字段=站点24h实测雨量**；香格里拉=101291301，丽江=101291401；需 Referer: http://www.weather.com.cn |
| 中国天气网预警 JSON | `https://d1.weather.com.cn/dingzhi/{城市码}.html` | 解析 `alarmDZ{城市码}` 对象：w1省/w2州/w3市/w5类型/w7级别/w8发布时间/w9全文——**第一手官方预警，置顶用**。城市码（2026-08-31 已实测核实）：香格里拉=101291301、丽江=101291401、迪庆州=101291305、德钦=101291302、维西=101291303（101291306 无效、101291304=中甸旧码）；州/县码无独立国家站，仅用于抓预警 |

> 注意：国家站只在香格里拉市区(3280m)/丽江(2400m)，**虎跳峡、哈巴雪山山区无国家站**——山区数值用 Open-Meteo 网格趋势，官方站用于校准量级与预警。

## 二、Open-Meteo 直调模板（web_extract 降级用，无 key）

格式：`https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&timezone=Asia%2FShanghai&past_days=3&forecast_days=4&hourly=precipitation,precipitation_probability,temperature_2m,wind_speed_10m,wind_gusts_10m&daily=precipitation_sum,precipitation_probability_max,temperature_2m_max,temperature_2m_min&models=best_match`

点位坐标（2026-08 核实）：

| 点位 | 纬度 | 经度 | 海拔(约) |
|:--|--:|--:|--:|
| 虎跳峡镇·上虎跳 | 27.250 | 100.060 | 1700-1900m |
| 哈巴村 | 27.382 | 100.136 | 2700m |
| 兰花坪·羊房牧场 | 27.365 | 100.120 | 3300-3600m |
| 黑海营地·垭口（最高关注点，不登顶） | 27.350 | 100.115 | 4100-4200m |
| 香格里拉市区 | 27.830 | 99.700 | 3280m |
| 丽江市区 | 26.860 | 100.230 | 2400m |

## 三、官方源清单（优先级从高到低）

### 预警类
1. **国家突发事件预警信息发布网** http://www.12379.cn/ — 全国官方预警总入口，按区域检索（迪庆/香格里拉/玉龙）
2. **中央气象台** https://www.nmc.cn/ — 首页"预警"栏目 + 云南预警列表；香格里拉预报页 https://www.nmc.cn/publish/forecast/AYN/xianggelila.html
3. **中国天气网** https://www.weather.com.cn/ — 预警列表 https://www.weather.com.cn/alarm/ ；香格里拉 https://www.weather.com.cn/weather/101291301.shtml ；丽江 https://www.weather.com.cn/weather/101291401.shtml ；**虎跳峡风景区** https://www.weather.com.cn/weather1d/10129130106A.shtml
4. **山洪灾害气象预警**（水利部+中国气象局联合发布）— nmc.cn/中国天气网新闻页检索，级别：黄/橙/红
5. **地质灾害气象风险预警**（自然资源部+中国气象局联合发布）— 检索"地质灾害气象风险预警 云南"；级别：蓝(4级有一定风险)/黄(3级较高)/橙(2级高)/红(1级很高)
6. 云南省气象局/迪庆州气象台/香格里拉市气象局 — 官网或官方微博/微信（"迪庆气象""香格里拉气象"），web_search 检索最新发布

### 突发/管制类
7. **应急管理部** https://www.mem.gov.cn/ 、云南省应急管理厅 — 灾害事故通报
8. 交通：迪庆州/香格里拉交警、交通运输局 — 道路中断/管制（搜索"香格里拉 道路中断 塌方"）
9. **景区**：虎跳峡景区公告、香格里拉文旅局、哈巴雪山登山管制公告（迪庆州教体局/登山协会）— 搜索"虎跳峡 景区 关闭/暂停""哈巴雪山 登山 管制/封山"

### 高海拔参考
10. **Mountain-Forecast**（哈巴雪山各海拔温/风/降雪专业预报，英文）https://www.mountain-forecast.com/peaks/Haba-Xue-Shan-Haba-Snow-Mountain/forecasts/5396
11. 香格里拉雷达回波 https://products.weather.com.cn/product/radar1/index/procode/JC_RADAR_AZ9888_JB_V3.shtml

## 四、web_search 关键词模板

- `香格里拉 暴雨预警 迪庆 气象台` / `迪庆州 雷电 大风 冰雹 预警`
- `云南 山洪灾害气象预警` / `云南 地质灾害气象风险预警 迪庆`
- `三坝乡 山洪 泥石流` / `哈巴村 塌方`
- `虎跳峡 景区 关闭 公告` / `虎跳峡 道路 中断`
- `哈巴雪山 登山 管制 封山`
- `香格里拉 降水实况 24小时 降雨量`（实况核验）

检索后**点开官方原文读全文**（5-8篇/源，多源交叉），禁止只看摘要。

## 五、网页打不开时的降级

```bash
# Scrapling stealthy-fetch（venv 已装）
~/.scrapling-venv/bin/scrapling stealthy-fetch "<URL>" --keep-html
```
详见 scrapling skill。仍失败 → 用 web_search 摘要+标注"未能读取原文"。

## 六、预警级别速查（发布单位现行标准）

- **暴雨预警**：蓝(12h≥50mm)/黄(6h≥50mm)/橙(3h≥50mm)/红(3h≥100mm)
- **山洪灾害气象预警**：黄(可能发生)/橙(可能性较大)/红(可能性大)
- **地质灾害气象风险**：蓝=4级(有一定风险)/黄=3级(风险较高)/橙=2级(风险高)/红=1级(风险很高)
- **强对流/雷电/大风/冰雹预警**：蓝/黄/橙/红
- 判级时"地灾蓝=风险较低≠无风险"，雨季连续降雨后即便蓝色也要在简报中提示。

## 七、其他

- 时间统一北京时间；雨量 mm；风速 km/h（脚本）或 m/s（官方，换算 ×3.6）
- 官方页面常含验证码/JS 渲染：优先 web_extract，失败走 scrapling，再失败换搜索引擎缓存
- **水利部全国水雨情网（xxfb.mwr.cn）数据接口做了混淆加密（OTMursapkc 前缀），未接入**；如需真实雨量计数据可后续再攻或用 12379 发布的站点实况替代
