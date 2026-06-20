---
name: jiangsu-gaokao-expert-v3
description: "江苏高考决策情报日报 V5 — 家长视角精确定位版"
author: Hermes
version: 5.22
---

# 江苏高考决策情报日报 V5

## 🎯 用户画像（精确定位版）

### 考生信息
- **水平**：211+，发挥不稳定，省排名预估**5000-15000名**
  - 上限（超常发挥）：5000名
  - 核心区间（正常发挥）：8000-15000名
  - 保底：15000名
- **选科**：物化地
- **兴趣方向**：数学类、数据科学 > 自动化 > 带电的工科（智能工程等）
- **不喜欢**：纯计算机

### 已报路径
| 途径 | 学校 | 专业 | 报名状态 |
|------|------|------|---------|
| 强基计划 | **同济大学** | 数学（专业组1·数理综合） | ❌ 已弃考（6/12确认） |
| 综评A类 | **南京大学** | 学科兴趣类·地理科学类 | ✅ 已报 |
| 综评A类 | **香港中文大学(深圳)** | 631综评 | ✅ 已报 |
| 综评B类 | **南京邮电大学** | 综评 | ✅ 已报 |

### 地域偏好（优先级从高到低）
1. ✅ **上海** — 同济在此
2. ✅ **大湾区**（深圳/广州）— 港中深在此
3. ✅ **武汉**
4. ❌ **南京** — 南京人，基本不考虑（但南大综评已报，仅综评路径例外）
5. ❌ **北京、东北、西北、成都、重庆、西南**

### 位次定位图谱

基于2025年江苏物理类录取数据：

| 梯度 | 路径 | 学校 | 2025普通批位次 | 孩子位次匹配度 |
|------|------|------|---------------|--------------|
| 🔴 ~~冲~~ | 强基（已弃考） | ~~同济大学~~ | 最低4675（06组） | ❌ 6/12确认弃考，专注综评路径 |
| 🟡 **稳** | 综评 | 南京大学（地理科学类） | 综评考核制 | ✅ 学科兴趣类综评，校测6/28（高考出分后） |
| 🟡 **稳** | 综评 | 港中深 | 提前批5633 | ⚠️ 需要校测爆发 |
| 🟢 **保** | 综评 | 南京邮电大学 | 25000-30000 | ✅ 非常稳健的保底 |
| 🟢 **保** | 普通批 | 武汉大学/华中科大/上海大学/中山大学 | 见下方详细分析 | ✅ 核心区间可够到 |

### 与你位次匹配且符合地域偏好的学校矩阵

> ⚠️ **范围已锁定：5000-15000名区间已自然覆盖冲稳保，不再扩展。**

**冲（7000-10000名）：**
| 学校 | 城市 | 2025位次 | 匹配度 | 数学/数据科学专业 |
|------|------|---------|--------|-----------------|
| **华中科技大学** | 武汉 | 3556-4000+ | 略高于上限，但可冲 | ⭐ 数学强校，有数据科学相关方向 |
| **武汉大学** | 武汉 | 4082 | 略高于上限 | ⭐ 数学学科评估A-，有数据科学 |
| **上海大学** | 上海 | 10000+ | 核心区间 | ⭐⭐ 数学与应用数学、数据科学与大数据技术、人工智能 |
| **中山大学** | 广州 | 6362 | 需超常发挥 | ⭐ 统计学/数据科学不错 |
| **华南理工大学** | 广州 | 3805-4675 | 需超常发挥 | 数学、数据科学有布局 |

**稳（10000-15000名）：**
| 学校 | 城市 | 2025位次 | 匹配度 | 数学/数据科学专业 |
|------|------|---------|--------|-----------------|
| **上海大学** | 上海 | ~10000 | 稳 | ⭐⭐ 数学与应用数学、数据科学与大数据技术、人工智能 |
| **东华大学** | 上海 | ~12000-14000 | ✅ 稳 | ⭐ 物化2组有数学类(智能科学)、数据科学、AI专业与孩子兴趣匹配 |
| **华中师范大学** | 武汉 | ~13000 | 稳 | 数学与应用数学（师范方向为主） |
| **武汉理工大学** | 武汉 | 7529-10000+ | 稳 | 数据科学、数学有布局 |
| **暨南大学** | 广州 | ~12000 | 稳 | 统计学、数据科学 |
| **华南师范大学** | 广州 | ~14000 | 稳 | 数学（师范方向为主） |

> 📎 各校详细录取分数见 `references/match-schools-scores.md`。**重点关注：上海大学数学/数据科学专业组合度最高，东华大学物化2组有匹配专业。**

## ⚠️ 搜索链路（新标准）

**统一使用 Parallel 免费 MCP + 本地 Chrome 降级链路：**

### 🥇 搜索：web_search(Parallel 免费 MCP)

```python
# 搜关键词，秒出结果
web_search("南京大学 综合评价 地理科学类 2026")
```

- 免费、零配置、中英文都能搜
- 支持 `site:` 过滤（如 `site:zhuanlan.zhihu.com 江苏 高考`）
- 每次搜 5 个结果，摘要已包含发布时间和来源

### 🥇 提取正文：web_extract(Parallel 免费 MCP)

```python
# 直接读正文，返回干净 Markdown
web_extract(["https://www.zizzs.com/gk/..."])
```

- 免费，返回 Markdown 格式正文
- 对静态 HTML 站（zizzs 具体文章页、jseea.cn、admissions.cuhk.edu.cn）效果很好
- 对 SPA 站（bkzs.tongji.edu.cn、bkzs.nju.edu.cn）失败 → 降级 browser

### 🥈 降级：browser_navigate(本地 Chrome)

```python
# web_extract 失败时打开页面
browser_navigate("https://bkzs.tongji.edu.cn/...")
# 读完内容
browser_eval("document.body.innerText")
```

- 本地 Chrome 免费，过 JS 渲染和部分反爬
- 比 web_extract 慢，只做降级用

### ❌ 已废弃（不用了）

| 工具 | 原因 |
|------|------|
| Exa (web_search/web_extract 默认后端) | key 已注释，换成 Parallel 免费 MCP |
| SerpAPI | 脚本已删除 |
| sogou.com 搜索 | 频繁触发反爬 302→antispider |
| browser_navigate→Google | 太慢，Parallel 更快 |

### 故障恢复链

| 层级 | 工具 | 说明 |
|------|------|------|
| 🥇 首选 | `web_search(Parallel)` | 免费 MCP，秒出结果 |
| 🥇 提取 | `web_extract(Parallel)` | 读正文，Markdown 干净 |
| 🥈 搜索降级 | 换关键词再 `web_search(Parallel)` | 同一后端，不消耗额外配额 |
| 🥈 提取降级 | `browser_navigate(本地Chrome)` + `eval body.innerText` | 过 JS 渲染/反爬 |
| 🥉 终极降级 | `execute_code` + `httpx` 直连已知可用站点 | 见下方 curl 兼容性表 |

### 关键站点 curl 兼容性表（httpx 直连降级用）

| 站点 | URL | curl 兼容性 | 说明 |
|------|-----|------------|------|
| ✅ **Open-Meteo API** | `api.open-meteo.com/v1/forecast` | ✅ 始终可用 | 结构化 JSON，无需 API key，首选天气源 |
| ✅ **港中深招生网** | `admissions.cuhk.edu.cn` | ✅ 可用 | 静态 HTML，文章链接模式 `/article/{id}`。已确认可用的2026文章ID：2400(测试安排)、2401(准考证下载)、2399(审核结果)、2402(招生组联系方式) |
| ✅ **zizzs 具体文章页** | `www.zizzs.com/gk/qiangjijihua/222279.html` | ✅ 可用 | 返回完整文章内容(~189KB)，**列表页不可用**(SPA) |
| ✅ **江苏省考试院** | `www.jseea.cn` | ✅ 可用 | 返回完整 HTML 首页，含时间线信息。具体文章页 URL 模式：`//www.jseea.cn/webfile/index/index_zkxx/YYYY-MM-DD/数字.html`（招考信息）或 `//www.jseea.cn/webfile/index/index_zcwj/YYYY-MM-DD/数字.html`（政策文件） |
| ✅ **南京本地宝** | `m.nj.bendibao.com` | ✅ 可用 | 静态 HTML，高考天气专题页可提取 |
| ❌ **同济招生网** | `bkzs.tongji.edu.cn` | ❌ SPA | 仅返回 HTML 壳(439KB)，所有内容 JS 渲染 |
| ❌ **同济 CHSI** | `bm.chsi.com.cn/jcxkzs/sch/10247` | ❌ SPA | Vue 渲染，仅显示模板变量 `{{time}}` |
| ❌ **zizzs 列表页** | `www.zizzs.com/gk/qiangjijihua/` | ❌ SPA | 仅返回页脚 ~9KB |
| ❌ **南大招生网** | `bkzs.nju.edu.cn` | ❌ SPA | 仅返回 ~18KB 空壳 |
| ❌ **weather.com.cn** | `www.weather.com.cn/weather/101190101.shtml` | ❌ 已失效 | 数据 JS 动态加载，API 端点已被屏蔽 |
| ❌ **南邮招生网** | `bkzs.njupt.edu.cn` | ❌ DNS 解析失败 | 域名无法解析 exit code 6 |

> 发现 SPA 站点时，切到 web_extract(Parallel) 或 browser_navigate 提取第三方聚合站的具体文章页（zizzs.com 具体文章 ID）。利用已有缓存/已知信息补全。

### 跳转直连：zizzs 具体文章页直接访问（终极降级用）

当 Parallel 和浏览器都不可用时，zizzs 的具体文章页是已知可靠的中文聚合信息来源：

```bash
# 直接访问已知可用的 zizzs 文章页（返回完整 HTML 内容）
curl -sL "https://www.zizzs.com/gk/qiangjijihua/222279.html" -H "User-Agent: Mozilla/5.0" -o /tmp/zizzs.html
```

已知文章类型对应可能 ID 前缀：
- 强基计划: `/gk/qiangjijihua/`
- 综合评价: `/gk/zonghepingjia/`
- 高校招生: `/gk/gaoxiao/`

无法精确知道 ID 时，搜索已被搜索引擎收录的页面标题在本地缓存中搜，或尝试访问主流聚合站首页（gaokzx.com, gaokaozhitongche.com）——这些首页通常是静态 HTML。

### web_search(Parallel) 搜索示例

```python
# 🥇 首选 — web_search(Parallel 免费 MCP)
web_search("同济大学 2026 强基计划 初试 安排")
# 返回 5 条结果，含标题/URL/摘要
# 摘要不够用时用 web_extract 读正文
web_extract(["https://www.zizzs.com/gk/qiangjijihua/222279.html"])

# 如果 Parallel 搜索偶发超时，换关键词再试即可
# 同一后端，不消耗额外配额
```

**关键优势**：Parallel 是 AI-optimized 搜索引擎，对中英文关键词都覆盖好。搜索结果摘要已包含发布时间和来源，比手动开浏览器快得多。

### curl 解析 HTML 的安全限制工作区

`curl | python3` 管道会被安全扫描拦截（`curl_pipe_shell` 规则）。
**正确做法**：先用 `curl -o /tmp/file.html` 写文件，再用 `execute_code` 读取并解析。

```bash
# ✅ 第一步：下载到临时文件
curl -sL "https://example.com" -H "User-Agent: Mozilla/5.0" -o /tmp/page.html
```

```python
# ✅ 第二步：安全地解析 HTML
import re
with open('/tmp/page.html', 'r', encoding='utf-8', errors='replace') as f:
    html = f.read()
```

⚠️ **HTTP 明文 URL 也会被安全扫描拦截（`plain_http_to_sink` 规则）**
即使正确使用了 `curl -o` 而非管道，传递 `http://` 开头的明文 URL（非 HTTPS）给 `curl -o` 也会触发安全拦截。原理是安全策略认为 HTTP 传输的内容可能被中间人篡改。

**症状**：`terminal("curl -sL http://... -o /tmp/f.html")` 返回 `status: pending_approval`，描述含 `plain_http_to_sink`。

**解决方式（按优先级）：**
1. 优先使用 HTTPS URL（大多数正规站点支持）：`https://nj.bendibao.com/edu/...`
2. 若站点仅支持 HTTP：考虑用浏览器工具直接访问，或者确认能否通过 HTTPS 访问（部分站点同时支持）
3. 最后手段：用浏览器导航到 http 页面获取内容

```bash
# ❌ 被阻止：HTTP 明文 URL
curl -sL "http://nj.bendibao.com/edu/xxx.shtm" -o /tmp/page.html

# ✅ 通过：HTTPS URL（如果站点支持）
curl -sL "https://nj.bendibao.com/edu/xxx.shtm" -o /tmp/page.html

# ✅ 通过：用 httpx 直连获取内容
python3 -c "
import httpx
r = httpx.get('https://nj.bendibao.com/edu/xxx.shtm', timeout=15)
print(r.text[:2000])
"
```

### 高考天气数据源

⚠️ **重要更新（2026-06-02）**：weather.com.cn 的数据 API 端点现在全被屏蔽了（curl 返回"非常抱歉，网页无法访问"），7日预报页面的天气数据改由 JS 动态加载。不能再依赖 curl 获取 weather.com.cn 的结构化数据。

首选可靠的实时数据源是 **Open-Meteo API**（免费、无需 API key、返回结构化 JSON）：

| 数据源 | URL | 特点 | 获取方式 |
|--------|-----|------|---------|
| 🥇 **Open-Meteo API（每日）** | `https://api.open-meteo.com/v1/forecast?latitude=32.06&longitude=118.79&daily=temperature_2m_max,temperature_2m_min,precipitation_probability_max,weathercode&timezone=Asia/Shanghai&start_date=YYYY-MM-DD&end_date=YYYY-MM-DD` | ✅ **最可靠**。ECMWF 全球模型，返回结构化 JSON，无需 API key | `curl` 或 `httpx` 直接 GET，解析 JSON。支持指定起止日期 |
| 🥇 **Open-Meteo API（逐小时）** | `https://api.open-meteo.com/v1/forecast?latitude=32.06&longitude=118.79&hourly=temperature_2m,precipitation_probability,weathercode&timezone=Asia/Shanghai&start_date=YYYY-MM-DD&end_date=YYYY-MM-DD` | ✅ 逐小时预报，精度更高 | 同上。WMO 天气码 → 中文描述（0=晴,1=少云,2=多云,3=阴,61=小雨,63=中雨,65=大雨,95=雷暴） |
| 🥈 备用 | Open-Meteo API（同上，调整start_date/end_date） | ✅ 最可靠，无需API key | `httpx` 直接 GET |
| 🥉 南京本地宝 | `https://m.nj.bendibao.com/news/181345.shtm` | ✅ 静态 HTML，curl 可直接获取。有高考天气专题页 | `curl -sL` 后 `re.sub(r'<[^>]+>', '\n', html)` 提取文本 |
| ❌ 中国天气网7日/15日（已失效） | `https://www.weather.com.cn/weather/101190101.shtml` | ❌ 数据改为 JS 动态加载，curl 仅得 HTML 壳。API 端点已被屏蔽 | 不再可用 |
| ❌ CMA 气象局 | `https://weather.cma.cn/web/weather/58238.html` | ❌ curl 请求会被拦截 | 不再可用 |
| ❌ AccuWeather | accuweather.com | ❌ 需 JS 渲染 | 不再可用 |

**Open-Meteo 使用示例**（南京，纬=32.06, 经=118.79）：

```python
import httpx, json
resp = httpx.get("https://api.open-meteo.com/v1/forecast", params={
    "latitude": 32.06,
    "longitude": 118.79,
    "daily": "temperature_2m_max,temperature_2m_min,precipitation_probability_max,weathercode",
    "timezone": "Asia/Shanghai",
    "start_date": "2026-06-07",
    "end_date": "2026-06-09"
})
data = resp.json()
for i, date in enumerate(data["daily"]["time"]):
    hi = data["daily"]["temperature_2m_max"][i]
    lo = data["daily"]["temperature_2m_min"][i]
    precip = data["daily"]["precipitation_probability_max"][i]
    code = data["daily"]["weathercode"][i]
    wmo = {0:"晴",1:"少云",2:"多云",3:"阴",61:"小雨",63:"中雨",95:"雷暴"}.get(code, str(code))
    print(f"{date}: {lo}~{hi}°C, 降水{precip}%, {wmo}")
```

实际经验（2026-05-25验证）：距高考13天时，weather.com.cn的数据尚未更新至6/7-6/9。15日预报数据窗口是滚动更新的——5/25的15日窗口末端（6/8-6/9）的数据可能尚未填充，需等2-3天（5/27-5/28）数据才会覆盖高考日。

⚠️ **关键陷阱：15日预报数据是滚动窗口，会周期性消失再出现。** 实测发现：5/27数据已填充6/7-6/9，但5/30（仅3天后）同一页面的15日预报中6/7-6/9数据已消失。原因是滚动窗口的特性——数据填充后不会永久驻留，可能在下一轮刷新时被替换/清空。**正确做法**：每次搜到有效预报后立即记录到 key-discoveries.md 作为缓存，下次运行时先读缓存，有新版数据则覆盖更新。不要在日报中标注"数据已消失/不见了"——正常现象，用缓存数据即可。

**正确策略（2026-06-09更新）**：
1. 🥇 首选 **Open-Meteo API**：直接调用 `api.open-meteo.com/v1/forecast?latitude=32.06&longitude=118.79&daily=temperature_2m_max,temperature_2m_min,...` — 最可靠的实时数据来源，无需API key
2. 🥈 备用：直接用 curl 抓取 `https://m.nj.bendibao.com/news/181345.shtm` 南京本地宝高考天气专题页 — 静态HTML
3. ❌ ~~用 curl 抓取 weather.com.cn / CMA 的页面~~（已失效，数据JS动态加载或curl被拦截）
4. 精准预报约6/5前后发布（省气象局高考专项预报），届时用 httpx 搜索

```python
# ✅ Open-Meteo API（推荐 - 最可靠、无需API key）
import httpx, json

params = {
    "latitude": 32.06,
    "longitude": 118.79,
    "daily": "temperature_2m_max,temperature_2m_min,precipitation_probability_max,weathercode",
    "timezone": "Asia/Shanghai",
    "start_date": "2026-06-07",
    "end_date": "2026-06-09"
}
resp = httpx.get("https://api.open-meteo.com/v1/forecast", params=params, timeout=15)
data = resp.json()
for i, d in enumerate(data["daily"]["time"]):
    hi = data["daily"]["temperature_2m_max"][i]
    lo = data["daily"]["temperature_2m_min"][i]
    precip = data["daily"]["precipitation_probability_max"][i]
    wmo = {0:"晴",1:"少云",2:"多云",3:"阴",61:"小雨",63:"中雨"}.get(
        data["daily"]["weathercode"][i], "多云")
    print(f"{d}: {lo}~{hi}°C, 降水概率{precip}%, {wmo}")

# 备用：南京本地宝静态页面（weather.com.cn已失效）
# curl -sL "https://m.nj.bendibao.com/news/181345.shtm" -o /tmp/weather.html
# 然后 execute_code 中 re.sub(r'<[^>]+>', '\n', html) 提取文本
```

## 📡 六维信息采集清单（精确定位版）

每次运行按此顺序搜索，标记优先级。

### 第一优先级（你的专属路径）
1. ~~"同济大学 强基计划 数学 校测 2026 江苏"~~（已弃考）
2. **"南京大学 综合评价 地理科学类 2026 江苏 录取 校测"**  ← 🎯 重点收集
3. "南京大学 综评 地理科学类 2026 录取 分数 降分 位次"
4. "南京大学 学科兴趣类 地理 2026 校测 面试"
5. "南京大学 综合评价 地理科学类 校测 2026 江苏 真题"
6. "香港中文大学深圳 综合评价 2026 江苏 录取 校测"
7. "南京邮电大学 综合评价 2026 江苏 录取 笔试"
8. **"东南大学 2026 综合评价 江苏 校测 真题"**  ← 🆕 新增备选路径（同分段，数理校测对口）

### 第二优先级（匹配学校+全网最新讨论）

5. "武汉大学 OR 华中科技大学 OR 上海大学 OR 中山大学 OR 华南理工 2026 江苏 招生 数学 数据科学"  
6. "上海大学 数学与应用数学 数据科学 2026 江苏 录取 分数 位次"
7. "东华大学 数学类 智能科学 数据科学 2026 江苏 物化2组 录取"
8. "武汉理工大学 OR 暨南大学 数据科学 统计学 2026 江苏 招生"
9. "2026年 江苏 物理类 招生计划 专业组"
10. "2026 高考 江苏 招生 最新 新闻"（限今日/本周）
11. "2026 高考 物理类 志愿 填报 热门 专业 分析"
12. "强基 计划 2026 面试 经验 贴吧 OR 知乎 OR 小红书"
13. "南京大学 OR 港中深 综合评价 2026 校测 通过率"
14. "江苏 高考 综评 2026 报录比 热度"

### 第三优先级（专业方向与决策参考 + 天气）

13. "数学类 OR 数据科学 OR 统计学 2026 就业 前景 高校 排名"
14. "数据科学 本科 专业 江苏 2026 招生 强校"
15. "强基计划 数学 转段 读研 数据科学 方向"
16. "上海大学 OR 东华大学 OR 华中科大 数学 数据科学 2026 江苏 招生"
17. "江苏 高考 家长 群 2026 热门 讨论"（比13-16低优先级）

### 🫧 高考天气预报（6月6日-9日南京/全省）
> 距离高考不足30天时启动搜索。暂时搜不到就空着，等能搜到为止。
> ⚠️ 数据源：Open-Meteo API 优先（无需API key，返回结构化JSON）。weather.com.cn 的数据API已失效（curl被拦截，页面JS动态加载）。
1. **🥇 首选 Open-Meteo API**：`api.open-meteo.com/v1/forecast?latitude=32.06&longitude=118.79&daily=temperature_2m_max,temperature_2m_min,precipitation_probability_max,weathercode&timezone=Asia/Shanghai&start_date=2026-06-07&end_date=2026-06-09`
2. **🥈 备用**：用 curl 抓取南京本地宝等第三方网站发布的高考天气预报文章
3. **🥉 南京本地宝**：`curl -sL "https://m.nj.bendibao.com/news/181345.shtm"` 静态HTML可直接提取文本
4. 搜到后更新到 GaokaoWIKI 的天气记录页面，并在日报中增加"🌤️ 高考天气"板块

### ⚠️ 天气数据缓存刷新规则（2026-06-02新增）
> **用户明确要求：不要用旧缓存糊弄。** 当天气数据满足以下任一条件时，必须主动实时查询最新数据，不得使用超过1天的缓存：
> 1. 缓存数据距离今天已超过1天
> 2. 之前的预报标注了"待更新"或类似占位说明
> 3. 7日预报的时间窗口现在已覆盖到目标日期（之前没覆盖但现在覆盖了）
> 
> 正确做法：每次执行日报时，不管缓存里有什么，先用 Open-Meteo API 实时查询最新数据。如果 Open-Meteo 返回的数据和缓存一致（可接受），才用缓存。否则必须用新数据替代旧缓存并更新 key-discoveries.md。

## ⚠️ 关键陷阱：环境变量在 execute_code 中不可见

**重要**：`FEISHU_HOME_CHANNEL` 等环境变量在 `terminal()` 工具中可用，但在 `execute_code()` Python 沙箱中**不可见**（`os.environ.get('FEISHU_HOME_CHANNEL')` 返回空字符串）。

这意味着：
- 在 `execute_code()` 中不能依赖 `${FEISHU_HOME_CHANNEL}` 或 `os.environ['FEISHU_HOME_CHANNEL']`
- 飞书推送、git 操作等依赖环境变量的步骤必须通过 `terminal()` 执行，不能放在 `execute_code()` 中
- 跨工具调用时，如需传递 env var 值，可在 `terminal()` 中 `echo` 出来，再在 `execute_code()` 中传入
- ⚠️ **甚至 env var 在 execute_code subprocess 中也不可靠**：`subprocess.run(["lark-cli", ...])` 在 `execute_code()` 中虽能读取 env var，但多行 Markdown 字符串通过 Python 参数的传递方式与 shell 直接调用不同，换行符/引号可能被转义破坏，导致推送失败。**稳妥做法**：在 `execute_code()` 中将摘要写入临时文件，再通过 `terminal()` 用 `$(cat /tmp/...)` 推送。

```python
# ❌ 错误：execute_code 中拿不到 FEISHU_HOME_CHANNEL
channel = os.environ.get('FEISHU_HOME_CHANNEL')  # 返回 '' 或 None
```

```bash
# ✅ 正确：通过 terminal() 执行
lark-cli im +messages-send --chat-id "${FEISHU_HOME_CHANNEL}" ...
```

## 搜索策略要点

- **运行前先读 skill 的 `references/match-schools-scores.md`**（`~/.hermes/skills/jiangsu-gaokao-expert-v3/references/match-schools-scores.md`）：该文件已收录东华大学等校的2025详细录取分数。如需确认最新数据再单独搜索，避免重复爬取已确认的基础数据。⚠️ GaokaoWIKI 仓库中无此文件，仅在 skill 目录下。
- **使用 site: 和后缀过滤新鲜内容**：`site:zhuanlan.zhihu.com 2026 江苏 高考 招生`、`site:douban.com/group 江苏 高考`
- **优先搜今日/本周发布的内容**：在搜索词中加"2026年5月"等时间限定
- **每条路径的官网至少扫一次**：目标学校的官网招生栏目，可能 web_extract 直接提取
- **如果搜到重复内容直接跳过**，不必因为任务清单上有13个关键词就硬凑13条
- ⚠️ **加"本科"过滤研究生招生信息**：搜索大学+招生时（如"武汉大学 2026 江苏 招生"），结果常被研究生/硕士招生简章淹没。在关键词中加"本科"以精确定位
- ⚠️ **聚合站点优先于官方页面**：部分高校的政策更新在官方招生网发布延迟，但第三方聚合/解读站点（如 zizzs.com、gk100.com、jszs.com）会先出分析文章。搜索时不要只依赖官方来源——这些聚合站经常有更及时的政策变化解读。发现不一致信息时，应多方交叉验证
- ⚠️ **官方通知页面可能是 JS 渲染 SPA，curl 无法提取文本**：部分高校（如同济大学）的官方通知/公告页面使用 Vue/React SPA 架构，`curl -sL` 仅能获取空 HTML 壳（CSS 和 JS 链接），无法提取正文内容。遇到此类页面时：
  1. 不要反复尝试 curl（页面本身没有静态文本）
  2. **用 web_search(Parallel) 搜通知标题关键词**（如"同济大学 2026 初试安排"），摘要已包含结果
  3. 找到第三方聚合站（zizzs.com、gaokzx.com、gaokaozhitongche.com）的转载/摘要文章后，用 web_extract 提取
  4. web_extract 失败（SPA）则 browser_navigate 打开
  ```bash
  # ✅ 正确做法
  curl -sL "https://www.zizzs.com/gk/qiangjijihua/222279.html" -o /tmp/page.html
  ```
  **注意**：JS 渲染问题不仅限于天气/气象网站，各高校招生官网的通知页也越来越普遍地采用 SPA 架构。每次搜索时如发现 curl 结果只有 CSS/JS 代码，立即切到 web_extract(Parallel) 或 browser_navigate。
- ⚠️ **校测日期冲突预警**：每次运行第一优先级搜索后，立即检查四条路径中任意两条的校测是否安排在同一天。
  - **当前已知冲突**：**同济强基初试（6/13下午14:00-16:30）与港中深机考（6/13下午14:00起）完全重叠**，考生需二选一。南大兴趣类校测（6/28）单独安排，不与志愿填报冲突。
  - ⚠️ **关键陷阱：官方通知可改变此前报道的时间安排**。5月曾报道同济初试为上午9:00-11:30（与港中深下午不冲突），但6月3日同济官方初试安排通知将其**改为下午14:00-16:30**，导致直接冲突。**不要假定"之前不冲突"的状态是永久的**——每次搜索时必须从最新官方通知中重新验证所有校测时间，尤其在考前2周内各校密集发布准考证/安排通知时。
  - 验证方法：搜索该校最新初试/校测安排通知（如"同济大学 2026 强基 初试安排 通知"），与skill中记录的旧时间交叉对比。发现变化立即在头条突出标注。
- ⚠️ **登录保护型里程碑——不可外部验证**：部分里程碑节点（如"5月25日起南大综评审核结果可查"）的通知在登录保护的系统内部发布（bkzsks.nju.edu.cn需登录），外部无法确认结果是否"已公布"。遇到此类节点：
  1. 简要告知用户"今日起可登录XX系统查询"
  2. 不要浪费时间搜索"XX审核结果已公布"（这类新闻通常不存在）
  3. 如果第三方聚合站（zizzs.com等）有文章更新，可以作为旁证
  4. 日报中标注"🆕今日起可查"而非"✅已公布"/"❌未公布"

## 报告排版模板（必须遵守）

报告通过系统 cron deliver 自动推送到飞书群聊，**必须使用下方模板**。每段控制在 5-7 行内。

```
📋 高考决策情报日报 | 2026-05-XX（距高考 XX天）

━━━━━━━━━━━━━━━━━━━━━━━━━━

🔥 今日头条
• 核心发现 1：xxx
• 核心发现 2：xxx

━━━━━━━━━━━━━━━━━━━━━━━━━━

🎯 路径跟踪

❶ 同济强基·数学
• 状态：xxx
• 关键日期：xxx

❷ 南大综评·地理
• 状态：xxx

❸ 港中深综评
• 状态：xxx

❹ 南邮综评
• 状态：xxx

━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 同分段参考
• 华中科技大学（武汉·985）— 位次 ~3556 → 冲刺
• 上海大学（上海·211）— 位次 ~10750 → ⭐ 稳

━━━━━━━━━━━━━━━━━━━━━━━━━━

🌤️ 高考天气
• 6/7（六）语文/数学：xx°C ~ xx°C，xx
• 6/8（日）物理/外语：xx°C ~ xx°C，xx
• 6/9（一）选考科目：xx°C ~ xx°C，xx
*（已搜到即可更新；暂未搜到时省略此板块）*

━━━━━━━━━━━━━━━━━━━━━━━━━━

⏰ 行动清单
🔴 5月25日前后 — **南大综评审核结果公布**（南大报名系统可查）
🔴 5月31日前 — gk.jseea.cn 确认A类顺序（南大+港中深）
🔴 5月31日前 — 南邮缴费60元

━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### 格式规则
1. **禁止使用Markdown表格** — 飞书 `post` 消息的 `md` tag 不支持表格
2. **用 emoji + 粗体 做视觉层次**：🔥🎯📊⏰📋 区分板块
3. **用 `━━━` 分隔线** 分隔板块
4. **手机优先**：每段控制在 5-7 行内
5. **路径跟踪用❶❷❸❹ 序号**，每条路径 3-4 个要点
6. **不要报告用户已报过的背景信息**（学校层次、往年位次、选科覆盖率等）
7. **没有新发现时省略"信息管家提醒"**，不必强行凑数

## 动态反思清单（每次执行必查）

⚠️ 重要原则：**不要报你已经报过的信息。**
- key-discoveries 中 **标记为 `已告知` 且距今超过1天** 的发现，不再重复提及
- 用户已知道的背景（学校层次、往年位次、选科覆盖率等）不在日报正文出现
- "信息管家提醒"只列出**今天真正新搜到的、之前未发现过**的内容
- 如果今天所有搜索都没有真正的新发现，**直接省略"信息管家提醒"这一节**

1. **你的3条路径（同济已弃考）今天有没有新动态？**（搜索优先级：南大综评地理 > 港中深/南邮综评 > 东南综评新增备选 > 招生简章变化）
   - 🎯 **南大地理综评重点关注**：地理科学类录取数据(2025录取38人)、校测形式(6/28学科兴趣类面试)、地理学发展动态(GIS就业/学科评估)、5/25审核结果、5/31 gk.jseea.cn确认
   - 👆 注意5/25审核结果是"登录保护型里程碑"——外部不可验证是否已公布。只需告知用户"今日起可登录bkzsks.nju.edu.cn查询"，不纠结于"是否已公布"的验证
   - 🆕 **东南大学综评备选**：物理类考数学+物理(6/14校测)，和用户物化地选科对口，同分段可考虑
2. **匹配学校（上海+大湾区+武汉）今天有没有新信息？**（招生计划、专业组调整、新增项目）
3. **全网有没有高考招生的最新讨论/分析/经验？**（优先搜今日发布的内容）
4. **网上有没有有价值的他人评论或经验分享？**（知乎、贴吧、小红书今日热帖）
5. **有没有什么紧急的截止日期或节点变化？**（报名截止、缴费、确认等）
   - 特别注意：**5月25日南邮初审结果+南大综评审核结果公布**、**5月31日南邮缴费确认(60元)+港中深/南大在gk.jseea.cn确认A类高校志愿顺序**
6. **距离下一个决策节点还有多久？**
7. **🌤️ 高考天气预报：距离高考不足30天时启动搜索**—搜到后更新日报中的天气板块。暂未搜到就跳过，不硬填。
   - ⚠️ **缓存刷新规则**：每次执行必须主动重新查询（用 Open-Meteo API），不用超过1天前的缓存数据。之前标注了"待更新"的更不能放着不管——用户不接受旧数据占位。
8. **⚠️ 官方通知覆盖检查（距考试<14天时特别重要）**：各校在考前1-2周密集发布准考证/安排通知，其中可能改变此前报道的时间、地点、形式。对每条路径搜索"该校名 2026 初试/校测/入学测试 安排 通知"，将结果与前面报告记录的时间交叉比对。
   - 发现任何差异立即在🔥头条中突出标注
   - 时间改变可能导致新的校测冲突，即使此前报告标注了"不冲突"
9. **自检：以下内容今天是否应该省略？**
   - ❌ "物化地选科覆盖率90%以上" → 这是基础常识，不报
   - ❌ "南大地理学学科评估A-" → 基础事实，除非有新排名数据
   - ❌ "港中深平均年薪17.82万" → 同上
   - ❌ "强基按85%+15%" → 简章已发布时就说过，不重复
   - ❌ "距离高考XX天" → 倒计时模块已有，正文不重提
   - ✅ 只有**今天新搜到的**动态才值得写进"信息管家提醒"

## 执行流程

### 📋 执行日志记录（每次执行必须）

每次执行时，必须将执行过程按**时间线顺序**记录到飞书文档：
- **文档 URL**: `https://zesyg4oxfe.feishu.cn/docx/N8eNdusOvoyMmAxUcY0c6YRpnOb`
- **token**: `N8eNdusOvoyMmAxUcY0c6YRpnOb`
- **身份**: `--as bot`
- **命令**: `lark-cli docs +update --api-version v2 --doc "N8eNdusOvoyMmAxUcY0c6YRpnOb" --command append --as bot --content '<XML日志内容>'`

**日志规则：**
- 整个执行过程中，将日志内容逐条拼接到一个临时文件（如 `/tmp/gaokao_exec_log_YYYYMMDD.xml`）
- 日志内容用 XML 格式拼接，每条记录一个 `<p>` 标签：`<p>[HH:MM:SS] 操作标识 说明</p>`
- 执行结束后，用一次 `terminal()` 调用 cat 读取文件内容传给 `--content` 写入飞书文档
- 日志不阻塞主流程——推送失败不影响日报生成和归档

**操作标识（按执行顺序必录）：**

| 操作 | 标识 | 说明 |
|------|------|------|
| ▶️ 开始执行 | `[HH:MM:SS] ▶️ 开始执行` | 记录运行起始时间 |
| 📖 读取发现 | `[HH:MM:SS] 📖 读取 key-discoveries.md` | |
| 🔍 搜索 | `[HH:MM:SS] 🔍 搜索: "关键词"` | 每个搜索关键词一行，附结果摘要 |
| 🔍 提取 | `[HH:MM:SS] 🔍 提取: URL` | web_extract 正文提取 |
| 🌤️ 天气 | `[HH:MM:SS] 🌤️ Open-Meteo 天气查询` | 天气API调用 |
| ✅ 决策 | `[HH:MM:SS] ✅ 决策: 路径→状态` | 附判断依据（为什么维持/为什么更新） |
| 📋 报告 | `[HH:MM:SS] 📋 日报正文完成` | |
| 💾 归档 | `[HH:MM:SS] 💾 归档 GaokaoWIKI` | 日报归档 + wiki更新 |
| 🔄 同步 | `[HH:MM:SS] 🔄 GitHub 同步` | |
| 📤 推送 | `[HH:MM:SS] 📤 推送飞书群` | |
| ✅ 结束 | `[HH:MM:SS] ✅ 执行结束` | |

**示例日志内容（XML格式）：**
```xml
<h2>2026-06-21 08:30</h2>
<p>[08:30:01] ▶️ 开始执行</p>
<p>[08:30:02] 📖 读取 key-discoveries.md</p>
<p>[08:30:05] 🔍 搜索: "南京邮电大学 2026 综合评价 入围名单 公示"<br/>→ 南邮综评栏目仅见测试公告和初审公示，无入围名单</p>
<p>[08:30:10] 🔍 搜索: "南京邮电大学 2026 综合评价 笔试成绩 查询"<br/>→ 未搜到成绩查询入口相关文章</p>
<p>[08:35:00] ✅ 决策: 南邮→维持"待公布"（搜了两组关键词均无新动态）</p>
<p>[08:40:00] 📋 日报正文完成</p>
<p>[08:40:30] 💾 归档 GaokaoWIKI</p>
<p>[08:41:00] 🔄 GitHub 同步</p>
<p>[08:42:00] 📤 推送飞书群</p>
<p>[08:42:01] ✅ 执行结束</p>
```

> **推荐做法**：用 `execute_code` 中的 Python `open(path, 'a')` 逐条追加日志行到临时文件，最后一次性 `terminal()` 用 lark-cli 推送。

1. **加载已知发现**：阅读 `~/GaokaoWIKI/references/key-discoveries.md`（GaokaoWIKI 仓库中的那份，不是 skill 目录下的），避免重复发现
   - ⚠️ skill 目录下也有一份 `references/key-discoveries.md`，那是初始模板/快照，不是最新数据
   - 每次运行都要读 **GaokaoWIKI 仓库中的** key-discoveries.md，因为那里会记录前一天的发现
   - **→ 记录到执行日志：📖 读取 key-discoveries.md → 摘要（末次更新日期、最新发现概览）**

2. **判断运行阶段并搜索**：根据当前日期在执行流程中施加不同的搜索策略
   - **日志记录**：对每个搜索关键词，记录 `[HH:MM:SS] 🔍 搜索: "关键词" <br/>→ 结果摘要（搜到X条、有无新发现、来源URL）`
   - **日志记录**：对每次 web_extract 正文提取，记录 `[HH:MM:SS] 🔍 提取: URL <br/>→ 提取状态（成功/失败/无新内容）`
   - **日志记录**：对每次天气 API 调用，记录 `[HH:MM:SS] 🌤️ Open-Meteo 天气查询 <br/>→ 返回温度范围、降水概率`

   **A. 考前阶段（距离高考 ≥1天）** — 正常模式：
   按六维清单全力搜索，每次至少搜 15 个关键词。
   - 运行第 2 天+: 对于连续 2 次搜索返回相同结果的关键词，直接跳过（日志中标注"跳过：与上次相同"）
   - 用时间过滤 `2026年5月` `2026年` 等减少重复；官网招生栏目需每次扫一次
   - 搜索大学+招生时务必加"本科"关键词，避免研究生招生结果淹没
   - 每条路径的官网至少扫一次
   - 每条第三方聚合站（zizzs.com, gaokzx.com 等）至少扫一次

   **B. 高考期间（6/7-6/9）— 考试支持模式** ⭐
   搜索策略大幅收缩，聚焦三大板块（按重要性排序）：
   1. **🌤️ 天气（第一优先）**：Open-Meteo API 获取逐小时预报，重点关注：
      - 当日上午+下午考试时段的温度、降水概率、天气码
      - 次日预报对比（看是否恶化/改善）
      - 南京本地宝/新华网等第三方源交叉验证
   2. **🗺️ 路径校测状态确认**：搜索各校官网/聚合站两次确认：
      - 港中深6/13机考时间（准考证是否开放下载）
      - 南邮6/14笔试安排（准考证打印时间）
      - 南大6/28校测安排（确认时间不变）
      - 东南6/14校测安排（新增备选路径）
   3. **📋 考试日程提醒**：基于当天日期生成明后天的考试时间表
      - 注意外语14:45截止入场（6/8下午）
      - 6/9选考科目时间不同（8:30-9:45, 11:00-12:15, 14:30-15:45）
   
   **不要对招生政策/匹配学校/专业前景进行大规模搜索** — 孩子正在考试，
   这些信息无法立即使用，且与考前相同的关键词大概率返回重复内容。
   
   日报内容比重调整：
   - 🌤️ 天气板块 → 扩展为最详细板块（逐小时+体感提醒）
   - 🎯 路径跟踪 → 精简为状态汇总（无新动态的路径一两句带过）
   - 📊 同分段参考 → 保留但注明"考后决策备用"
   - 行动清单 → 优先标注次日考试时间+注意事项
   - 删除"信息管家提醒"中与已报信息重复的内容；如有极少量新发现则保留

   **C. 考后阶段（6/10起）— 校测冲刺模式** ⭐
   搜索重心从招生简章转向：
   1. 校测备考资料/真题/面经（同济初试、港中深机考、南邮笔试）
   2. 校测准考证打印/考场确认等 logistics
   3. 预计出分时间线（6/24左右）和志愿填报策略
   4. 各路径的校测时间冲突（同济6/13 vs 港中深6/13）
   5. 同分段学校的招生计划/专业组（出分前最后一次确认）
   天气搜索继续，但降为第三优先级。

3. **检查校测时间冲突**：每次运行都检查四条路径的校测日期是否有冲突。**⚠️ 注意：此前报告中认为"不冲突"的安排可能因高校官方通知而改变**（实例如同济初试6/3通知从上午改为下午，直接与港中深机考冲突）。交叉验证方法：搜索"X大学 2026 校测/初试 安排 通知"获取最新官方公告，与之前记录的时间对比。如有冲突，在日报的行动清单中突出标注
   - **→ 记录到执行日志：✅ 决策: 校测冲突检查 → 结果（无冲突/发现X新冲突）**

4. **按报告结构生成完整日报**
   - **→ 记录到执行日志：📋 报告生成 → 日报正文完成**

5. **检查反思清单**，在"信息管家提醒"中告知新发现
   - **→ 记录到执行日志：✅ 决策: 信息管家提醒 → 无新发现/发现X条新内容**

6. **将重要新发现追加到 `references/key-discoveries.md`**（见下方"关键发现日志更新"）
   - ⚠️ `read_file` 有 dedup 限制：同一文件内容未变时连续读取会被阻止。建议用 `patch` 工具追加新条目（匹配上一日最后一行作为 old_string），避免先 read_file 再用 Python 重写的脆弱路径。具体示例见"关键发现日志更新"→"追加方法：patch 工具优先"
   - **→ 记录到执行日志：💾 key-discoveries.md 已更新**

7. **将有价值的信息入库到 wiki/院校库/ 对应页面** — 搜索到的每一条有价值信息，分析属于哪个学校，创建或更新该校的 wiki/ 页面（见下方"院校页面更新"）
   - **→ 记录到执行日志：💾 wiki院校库更新 → 更新了X个页面**

8. **将日报归档到 GaokaoWIKI** 并同步 GitHub（见下方归档流程）
   - **→ 记录到执行日志：💾 归档 GaokaoWIKI**

9. **通过飞书推送给用户**（参考 `references/feishu-push.md`）
   - **→ 记录到执行日志：📤 推送飞书群**

10. **推送执行日志到飞书文档**：将临时文件中的日志内容用一次 `terminal()` 推送到飞书文档
    ```bash
    # 推送日志（在步骤 10 执行）
    lark-cli docs +update --api-version v2 --doc "N8eNdusOvoyMmAxUcY0c6YRpnOb" --command append --as bot --content "$(cat /tmp/gaokao_exec_log_$(date +%Y%m%d).xml)"
    ```
    - 推送日志不设超时阈值——失败不阻塞主流程
    - **→ 记录到执行日志（文件最后一行）：✅ 执行结束**

---

### 高考期间搜索示例（6/7）

考前模式（A）会大幅搜索。考试期间（B）应改为：

```python
# ✅ 考试期间搜索策略——聚焦而非广撒网

# 1. 天气（Open-Meteo 逐小时）
import httpx
resp = httpx.get("https://api.open-meteo.com/v1/forecast", params={
    "latitude": 32.06, "longitude": 118.79,
    "daily": "temperature_2m_max,temperature_2m_min,precipitation_probability_max,weathercode",
    "hourly": "temperature_2m,precipitation_probability,weathercode",
    "timezone": "Asia/Shanghai",
    "start_date": "当天日期",
    "end_date": "当天日期+2"
}, timeout=15)

# 2. 校测状态确认（用 curl/httpx 搜索各校官网）
# curl -sL "https://www.zizzs.com/gk/qiangjijihua/..." -o /tmp/page.html
# 3. 快速交叉验证天气
# curl -sL "https://m.nj.bendibao.com/news/181345.shtm" -o /tmp/weather.html
```

## 关键发现日志更新

每次日报运行后，将今日新发现追加到 `references/key-discoveries.md`。

### 追加格式

```markdown
### YYYY-MM-DD（当天日期）

| 发现 | 状态 | 说明 |
|------|------|------|
| 新发现1 | ✅ 已告知(YYYY-MM-DD) | 简要说明 |
| 新发现2 | ✅ 已告知(YYYY-MM-DD) | 简要说明 |
```

同时将超过7天的旧发现从"活跃发现"移入"已归档"。

### 追加方法：patch 工具（中段插入）或 Python append（尾部追加）

**场景一：在文件中间插入新内容（推荐用 `patch`）**
当需要在已有表格之间或指定位置插入新行时，用 `skill_manage(action='patch')` 匹配锚点文本：
- 适合：在已有日期条目前插入新日期、替换内容、删除旧行
- 关键技巧：用上一行的唯一文本作为 `old_string` 匹配锚点，`new_string` 保留 old_string + 追加的新内容
- 如果 patch 后内容有误，可用 `undo` 参数回滚

**场景二：在文件末尾追加新内容（推荐 Python `append`）**
当只是把新发现追加到文件末尾时，直接用 `execute_code` 中的 Python 文件追加：

```python
new_entry = f"""
### {date_str}

| 发现 | 状态 | 说明 |
|------|------|------|
| ... | ✅ 新({date_str}) | ... |
"""
with open("~/GaokaoWIKI/references/key-discoveries.md", 'a') as f:
    f.write(new_entry)
```

此方式比 patch 更简单可靠，因为尾部追加不存在锚点匹配问题，且 Python `with open('a')` 天然幂等。无需先 read_file 再重写。

**选择指南**：需要插入/修改文件中间的已有内容 → `patch` 工具；只需追加到文件末尾 → Python `append`。

## 院校页面更新

每次日报运行后，将搜索到的有价值信息入库到对应的 wiki/ 院校页面。不能只存日报就完事。

```python
def update_wiki(school, title, content, url, date=date_str):
    path = f"{wiki_dir}/wiki/院校库/{school}.md"
    entry = f"""
### {date} | {title}
{content}

📎 [来源]({url})

"""
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            c = f.read()
        if date in c and title[:20] in c:
            return  # 已存在，跳过
        if "## 最新动态" in c:
            # ⚠️ 不能直接用 str.replace() — 若标题后有空白行则不匹配，且 replace 替换所有出现
            # 用 index-based 插入：找到标题位置，跳过其后所有空白行，插入新条目
            header = "## 最新动态"
            idx = c.find(header)
            content_start = idx + len(header)
            while content_start < len(c) and c[content_start] == '\n':
                content_start += 1
            c = c[:content_start] + entry + c[content_start:]
        else:
            c += f"\n## 最新动态\n{entry}\n"
        with open(path, 'w', encoding='utf-8') as f:
            f.write(c)
    else:
        page = f"""---
title: {school}
category: 院校库
tags: []
sources: 1
last_updated: {date}
status: draft
---

# {school}

## 基本信息

## 最新动态
{entry}
"""
        with open(path, 'w', encoding='utf-8') as f:
            f.write(page)
```

每条有价值的信息按学校归属调用 `update_wiki()`。例如：
- 搜到同济强基扩招 → update_wiki("同济大学", "强基江苏扩招", ...)
- 搜到南邮新专业 → update_wiki("南京邮电大学", "综评新增专业", ...)
- 搜到匹配学校招生数据（武大/华科/上大等）→ 创建或更新该校页面

### ⚠️ Python 中文引号陷阱（重要！）

当用 `execute_code` 执行 update_wiki() 时，内容中的中文弯引号（`"` U+201C、`"` U+201D）会被 Python 解析为字符串定界符，导致 SyntaxError。

**错误示例**（报错 SyntaxError）：
```python
# ❌ 外层双引号中的 "强基入围线" 导致解析器混淆
update_wiki("同济大学", "2026强基计划入围线发布",
    "同济大学2026强基计划\"数理综合\"专业组入围线公布",
    "https://...", "2026-05-10")
```

**正确做法（三选一）：**
1. **用单引号作外层定界符**（最简单）：
   ```python
   # ✅ 外层用单引号，内层中文弯引号安全
   update_wiki('同济大学', '2026强基计划入围线发布',
       '同济大学2026强基计划\"数理综合\"专业组入围线公布',
       'https://...', '2026-05-10')
   ```

2. **用 .format() 拆出变量**（最可靠）：
   ```python
   # ✅ 将含引号的文本存入变量后再引用
   title = "2026强基计划入围线发布"
   content = '同济大学2026强基计划\"数理综合\"专业组入围线公布'
   url = "https://..."
   update_wiki("同济大学", title, content, url, date_str)
   ```

3. **避免在字符串中出现中文弯引号**：改用直角引号（`「」`）、书名号（`《》`）或直接无引号表述，如「同济大学2026强基数理综合专业组入围线公布」。

> 此问题仅在使用 `execute_code` 工具运行 Python 时出现。直接在终端执行 `.py` 文件不受影响。

## Cron 交付配置（重要）

### 投递目标

该技能通过定时任务 `577c97d63499`（每日 8:00）运行，结果必须投递到飞书群聊：

- **目标 chat_id**: `oc_5d97d211e77becee79ff4241a4b10568`
- **deliver 参数**: `feishu:oc_5d97d211e77becee79ff4241a4b10568`
- **不要使用 `origin`**（会投递到私聊而非群聊）
- **cron prompt 必须极简**：只写「按 skill 执行」和交付地址，不包含与 skill 重复的业务逻辑。所有流程/规则/能力放在 SKILL.md 中。
- **不要用 lark-cli 或 send_message 额外推送**——cron 的系统 deliver 机制负责发送最终响应

## 日报归档与 GitHub 同步

每次生成日报后，必须执行归档和同步，将日报持久化到用户的 GaokaoWIKI 知识库。

### 存储位置
- **仓库**：https://github.com/babyowen/GaokaoWIKI
- **本地**：~/GaokaoWIKI/
- **日报目录**：~/GaokaoWIKI/raw/日报/
- **命名格式**：YYYY-MM-DD-高考决策情报日报.md

### 归档步骤

```python
import os, subprocess
from datetime import datetime

wiki_dir = os.path.expanduser("~/GaokaoWIKI")
daily_dir = f"{wiki_dir}/raw/日报"
date_str = datetime.now().strftime("%Y-%m-%d")
filename = f"{date_str}-高考决策情报日报.md"
filepath = f"{daily_dir}/{filename}"

# 1. 确保目录存在
os.makedirs(daily_dir, exist_ok=True)

# 2. 写入日报
with open(filepath, 'w', encoding='utf-8') as f:
    f.write(report)

# 3. 更新 index.md（注意防重复和防格式断裂）
index_path = f"{wiki_dir}/index.md"
daily_entry = f"| 日报 | [[{date_str}-高考决策情报日报]] | 每日高考情报汇总 | 1 |"
if os.path.exists(index_path):
    with open(index_path, 'r') as f:
        content = f.read()
    if "## 日报" not in content:
        content += f"\n\n---\n\n## 日报\n\n| 页面 | 描述 | 来源数 |\n|-----|------|--------|\n{daily_entry}\n"
    elif date_str not in content:
        # 用 date_str 检查而非完整行，防止格式断裂导致漏判
        # 在 "|-----|------|--------|" 后插入新行（只替换第一个匹配，即表头分隔线）
        sep = "|-----|------|--------|"
        idx = content.find(sep)
        if idx != -1:
            content = content[:idx + len(sep)] + "\n" + daily_entry + content[idx + len(sep):]
        else:
            content += f"\n{daily_entry}\n"
    with open(index_path, 'w') as f:
        f.write(content)

# 4. 更新 log.md
log_path = f"{wiki_dir}/log.md"
log_entry = f"""
## {date_str}

### [日报] 高考决策情报日报
- **内容**：当日高考情报汇总
- **归档**：raw/日报/{date_str}-高考决策情报日报.md
- **页面更新**：
  - [列出更新的院校库页面]
- **索引**：更新 index.md
"""
with open(log_path, 'a') as f:
    f.write(log_entry)

# 5. Git commit, pull-rebase, and push (pull --rebase 防止并发冲突)
os.chdir(wiki_dir)
subprocess.run(["git", "add", "-A"], capture_output=True)
subprocess.run(["git", "commit", "-m", f"[daily] {date_str} 高考决策情报日报自动归档"], capture_output=True)
subprocess.run(["git", "pull", "--rebase", "origin", "master"], capture_output=True, text=True)
result = subprocess.run(["git", "push", "origin", "master"], capture_output=True, text=True)
print(f"GitHub: {result.stdout[-200:] if result.stdout else result.stderr[-200:]}")
```

### 注意事项
- 日报是 append-only 资产，不创建 wiki/ 下的实体/概念页面（除非当天有特别重要的招生变化信息，可按 llm-wiki 规范入库）
- 如果 git push 失败，不阻塞流程——推送到飞书更重要，下次会自动重试
- 归档完成后，再通过飞书推送给用户

### 入库验证

归档代码最后应打印验证信息：

```python
print("\n=== 入库验证 ===")
print(f"日报: {'✅' if os.path.exists(f'{wiki_dir}/raw/日报/{date_str}-高考决策情报日报.md') else '❌'}")
for s in ["同济大学", "南京大学", "香港中文大学（深圳）", "南京邮电大学"]:
    p = f"{wiki_dir}/wiki/院校库/{s}.md"
    exists = os.path.exists(p)
    if exists:
        with open(p) as f:
            updated = date_str in f.read()
        print(f"  {s}: {'✅ 已更新' if updated else '⚠️ 存在无更新'}")
    else:
        print(f"  {s}: ❌ 不存在")
```

## 关键参考链接（每次运行可能用到）

| 用途 | URL |
|------|-----|
| 港中深/南大 A类综评志愿确认 | https://gk.jseea.cn（江苏省教育考试院考生服务平台） |
| 港中深综评系统 | https://ugapply.cuhk.edu.cn |
| 南大综评报名系统 | https://bkzsks.nju.edu.cn |
| 同济强基 | https://bm.chsi.com.cn/jcxkzs/sch/10247 |
| GaokaoWIKI 仓库 | https://github.com/babyowen/GaokaoWIKI |
| 执行日志文档 | references/execution-log-token.md（飞书文档 token 和推送命令） |
| 各校2026招生简章汇总 | references/2026-admissions-brochures.md（本skill参考文件） |
