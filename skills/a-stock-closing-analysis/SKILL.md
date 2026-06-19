---
name: a-stock-closing-analysis
display_name: A股收盘日报
title: A股收盘日报分析
description: 每日16:00自动生成A股收盘日报，覆盖大盘指数、涨跌分布、涨停聚焦、资金成交额、异动扫描（涨跌幅/换手/量能/极值）、特别关注、市场要闻、盘后小结。基于东方财富妙想mx系列技能提供实时数据。
author: Hermes
version: 1.4.0
required_env_vars:
  - MX_APIKEY
credentials:
  - type: api_key
    name: MX_APIKEY
    description: 东方财富妙想 API Key
---

# A股收盘日报技能

## 概述

每日收盘后自动生成A股市场综合日报。

**核心原则：不堆数据，讲人话。** 目标是让任何一个普通人都能：
1. 一眼看懂今天市场发生了什么
2. 看到涨跌分布和资金聚集方向
3. 关注到值得注意的异动和新闻
4. 得到一个情绪判断

### 数据源变更

**2026-06-09：新闻查询从 SerpAPI 切回 mx-search（零成本）**
- 原因：用户控成本，SerpAPI 月费不划算
- 新闻查询：`q_news()` → mx-search "A股大盘收盘 今日行情 市场热点 资金流向 板块涨跌"
- 特别关注：`q_special()` → mx-search "A股股价突破历史新高 新股暴涨 创纪录 股王 科创板异动"
- 回退：DuckDuckGo `region='cn-zh'`（仅 mx-search 失败时）
- **⚠️ 注意**：DuckDuckGo 在腾讯云服务器上返回质量极差（中文结果为空/不相关）+ 容易触发验证码，仅做 fallback，不要依赖
- 行情数据（mx-data）和选股数据（mx-xuangu）仍使用 mx 系列

### 模块结构（实际产出）

脚本实际生成以下模块，按报告顺序排列：

| Step | 模块 | 数据源 | 说明 |
|:----:|:----|:-------|:-----|
| 1 | **大盘指数+涨跌分布** | mx-data + mx-xuangu | 5大指数涨跌幅 + 涨停/跌停/涨跌幅>5%统计 |
| 2 | **涨停聚焦+资金聚焦** | mx-xuangu | 涨停个股列表 + 成交额TOP3 |
| 3 | **异动扫描** | mx-xuangu + 极值缓存 | 涨跌幅/换手/量能TOP5 + 市值/市盈极值 |
| 4 | **特别关注** | mx-search | 突破新高/新股暴涨/创纪录等独立搜索 |
| 5 | **其他要闻** | mx-search | 当日市场重要资讯 |
| 6 | **盘后小结** | 模板 | 情绪判断+明日关注 |

> **关于缺失模块**：板块热力图、北向资金/融资融券/龙虎榜（聪明钱）、指数估值体检、异常信号检测等模块因依赖 lixinger API 集成，当前脚本尚未实现。如需增加请告知。

## 依赖

### 行情数据源（mx 三件套）

- mx-data — 行情数据（指数、个股）
- mx-xuangu — 条件选股（涨跌分布、异动、极值）
- MX_APIKEY 环境变量（已配置）

### 新闻数据源（mx-search — 零成本）

- `mx-search` skill — 提供要闻和特别关注（东方财富金融信源，比 Google 通用搜索更精准）
- 搜索词见 `closing_report.py` 中 `q_news()` 和 `q_special()`
- 用量：每交易日2次，mx 共用同一配额（日报总计 ~18次/日，远低于50次限额）
- 回退方案：DuckDuckGo（`region='cn-zh'`），但腾讯云上中文结果质量差，仅做备胎

## 输出格式要点

**用户偏好（硬性要求，必须遵守）：**
- 版面要**清爽紧凑**，拒绝大段文字和冗余装饰符号
- 每个区块使用一个**图标前缀**（见 `references/report-styles.md` 图标表）
- 数据用 **竖线 `｜`** 分隔，一行展示多个条目
- 不要为每个项目开新行或使用列表符号，紧凑排列优先
- 涨跌幅统一用 `+/-X.XX%` 格式
- 大盘指数两行排列（每行2-3个），不逐个换行
- 极值变化用 `←新入榜: XX` 标注，不单独拆行
- 要闻用 `📰 标题（来源）` 格式，不加多余装饰
- 盘后小结保持1-2句话，附带 `📝` 和 `⚠️` 图标
- 拒绝表格（飞书不支持）、拒绝长段落、拒绝啰嗦
- 完整报告模板见 `references/report-styles.md`

## 数据采集流程

详见 `references/report-workflow.md`

**特别关注查询**（独立于常规要闻）：
- 用 mx-search 搜"A股股价突破历史新高 新股暴涨 创纪录 股王 科创板异动"
- 结果展示在报告"🔥 今日特别关注"板块，排在常规要闻之前
- 无结果时整块隐藏，不会出现空 section

**新闻查询**：
- 用 mx-search 搜"A股大盘收盘 今日行情 市场热点 资金流向 板块涨跌"
- 展示在"📢 其他要闻"板块

## API JSON 解析

两个 mx 技能的实际返回结构**与官方文档不同**，详情见各技能的 `references/api-json-structure.md`：
- `mx-data` → `data.data.searchDataResultDTO.dataTableDTOList`
- `mx-xuangu` → `data.data.allResults.result.dataList`
- `mx-xuangu` 总数 → `data.data.allResults.result.total`
- `mx-search` 资讯 → `data.data.llmSearchResponse.data`（每个 item 含 `title`, `content`, `date`, `source`, `jumpUrl`）

## 使用方式

### 手动运行
```bash
~/hermes/hermes-agent/venv/bin/python3 \
  ~/.hermes/skills/a-stock-closing-analysis/scripts/closing_report.py
```

### 定时运行（cron）
已配置 cron ID `0ecce809a17b`，交易日 16:00 自动运行。

**cron 推送方式**：运行脚本生成报告后，用 lark-cli --markdown 推送到飞书，回复简短确认。避免让系统 deliver 完整报告。

## 数据文件

- `~/.hermes/cache/a-stock-closing/reports/closing_report_{date}.md` — 每日报告
- `~/.hermes/cache/a-stock-closing/_extremes.json` — 极端值缓存（次日对比用）

## 注意事项

- mx 系列 API 限流：每次调用需间隔 ≥1.2 秒，错误码 112 表示频率过高
- mx 系列每日限额 50 次，日报用约 18 次（含 mx-search 新闻/特别关注 2 次），在安全范围内
- 飞书不支持 Markdown 表格，所有数据用紧凑文字展示（`｜` 分隔）

## 已知陷阱

### 1. mx-xuangu 字段键含日期后缀 — 禁止硬编码

mx-xuangu 返回的字段键包含当日日期，如 `010000_TRADING_VOLUMES<70>{2026-05-27}`、`010000_TOAL_MARKET_VALUE<70>{2026-05-27}`、`010000_TURNOVER_RATE<70>{2026-05-27}`、`010000_PE_D{2026-05-27}`。

**错误做法**：硬编码日期字符串
```python
# ❌ 次日会失效
a = item.get('010000_TRADING_VOLUMES<70>{2026-05-21}')
```

**正确做法**：使用子串模糊匹配
```python
def _val(item, *ks):
    # 精确匹配优先
    for k in ks:
        v = item.get(k)
        if v is not None and v!='': return v
    # 子串匹配回退：找包含 ks 中任一关键字的键
    for k in ks:
        for item_k, item_v in item.items():
            if k in item_k and item_v is not None and item_v!='':
                return item_v
    return ''
```
调用时传入简短子串即可：
```python
_val(item, 'TRADING_VOLUMES', 'AMOUNT', '成交额')
```
这会匹配到 `010000_TRADING_VOLUMES<70>{当前日期}`。

### 2. 脚本超时风险

脚本依次调用约 18 次 API（5 指数 + 4 涨跌分布 + 7 异动/极值 + 2 新闻/特别关注），每次间隔 1.2 秒避让限流，合计约需 20-30 秒 + 网络延迟。若某项 API 响应慢（超时 25 秒），总耗时可能超过 160 秒。确保 terminal timeout ≥ 180 秒。

### 3. 数据聚合路径深度

| 数据 | 路径 |
|:----|:-----|
| mx-data 行情 | `data.data.searchDataResultDTO.dataTableDTOList` |
| mx-search 资讯 | `data.data.llmSearchResponse.data` |
| mx-xuangu 选股 | `data.data.allResults.result.dataList` |
| mx-xuangu 总数 | `data.data.allResults.result.total` |

### 4. 特别关注与常规要闻可能重复

`q_special()` 和 `q_news()` 是两次独立的 mx-search 搜索，返回结果可能有重叠（同一篇新闻两轮都搜到）。generate() 中对两个循环分别用 `seen` 去重，但跨循环不排重。

当前影响不大（特别关注最多 4 条，常规最多 4 条，重叠概率低），暂不处理。
