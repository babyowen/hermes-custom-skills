---
name: wc2026-review
description: "WC2026世界杯赛后复盘系统。每天中午自动查询前一天比赛结果，对比系统预测，分析偏差原因，自动迭代预测方法论。"
version: 1.2.0
tags: [wc2026, world-cup, review, post-match, iteration]
---

# WC2026 赛后复盘与自动迭代系统

## 概述

在 `wc2026-predictor` skill 生成赛前预测的基础上，在**比赛结束后随时**对已结束的比赛进行**结果确认 → 预测对比 → 偏差分析 → 方法论迭代**的完整闭环。

**核心原则**：已结束的比赛随时可复盘，不需要等定时 cron。用户告知比赛已结束、或手动触发时立即执行。cron 12:00 只是每日例行跑。

**⚠️ Cron 安全须知**：本 skill 在 cron 模式下执行，**禁止使用 `execute_code` 和 `terminal`（调 curl/wget 等）**，这些工具在 cron 模式会被 blocked。所有数据获取必须用 **`web_search` → `web_extract` → `browser_navigate`** 链路。

## 核心流程

```text
① 获取赛果 — Odds API via web_extract / web_search(比分) / FotMob browser
①.5 赛后新闻采集 — web_search + web_extract + browser_navigate
② 对比预测 — 将实际结果与系统预测进行逐场对比
③ 偏差分析 — 按10维度逐一排查
④ 方法论迭代 — 写入 accuracy-tracking 和 lessons-learned
⑤ 输出复盘报告
```

## 数据存储

赛后复盘数据存储在 `~/wc2026/reviews/` 目录：

```
wc2026/reviews/
├── accuracy-tracking.md    ← 累计准确率追踪（逐轮更新表格）
├── lessons-learned.md      ← 偏差教训库（每条偏差一个条目）
└── match-reports/          ← 每场比赛的详细复盘
    ├── 2026-06-12_墨西哥-vs-南非.md
    └── ...
```

## 执行步骤（详细）

### 第一步：获取赛果

获取前一天已结束比赛的比分。所有工具必须 cron 安全。

**工具优先级（全部 cron 安全）**：
1. 🥇 **The Odds API via web_extract** — `web_extract("https://api.the-odds-api.com/v4/sports/soccer_fifa_world_cup/scores/?apiKey=e957983e5449073eedc1e6fafc619a74&daysFrom=1")` 返回已完成比赛的最终比分。⚠️ 返回的 `scores` 是 `[{"name": "Mexico", "score": "2"}, {"name": "South Africa", "score": "0"}]` 格式的列表，不是字典。从返回的 markdown 文本中解析比分。
2. 🥈 **web_search** — 搜 `"{队A} vs {队B} 2026 World Cup score result"`，Parallel 免费 MCP 的结果摘要通常已包含比分
3. 🥉 **FotMob browser** — `browser_navigate("fotmob.com/leagues/77/fixtures/world-cup")` 查看已完成比赛的最终比分

**获取进球详情**：
- 用 `web_search("{队A} vs {队B} 2026 World Cup goal scorers")`
- Parallel 免费 MCP 的搜索结果摘要通常直接包含进球者和时间
- 摘要不足时 `web_extract` 读正文
- 都失败再 `browser_navigate` → Google 体育知识面板

### ①.5 赛后新闻采集（每场 100 篇，为偏差分析提供依据）

用 web_search(Parallel) 批量搜索每场已结束比赛的赛后新闻，按以下维度分布：

| 维度 | 篇数 | 目的 |
|:----|:----|:----|
| 赛后战报/比赛回顾 | 12 篇 | 比赛全貌、转折点、关键事件 |
| 战术复盘分析 | 12 篇 | 阵型变化、战术调整、攻防数据 |
| 教练/球员赛后采访 | 12 篇 | 赛后感言、对战术的解释、更衣室信号 |
| 数据统计（xG/控球率） | 10 篇 | Opta/WhoScored 深度数据 |
| 媒体评分/舆论 | 10 篇 | 各方评价、赛后评级 |
| 进球/精彩瞬间分析 | 8 篇 | 每个进球的过程拆解 |
| 伤病更新 | 8 篇 | 比赛中受伤球员的伤情确认 |
| 红黄牌/纪律 | 8 篇 | 停赛风险、下一场缺席 |
| 出线形势分析 | 10 篇 | 本场结果对小组排名的影响 |
| 赔率变动回顾 | 5 篇 | 赛前赔率 vs 赛后复盘 |
| 双方球迷/社媒反应 | 5 篇 | 情绪面、士气面评估 |

**搜索关键词示例**：
```
web_search("{队A} vs {队B} 2026 World Cup match report post-match analysis")
web_search("{队A} vs {队B} tactics review formation change")
web_search("{教练名} post-match press conference {队A}")
web_search("{队A} {球员} injury update after match")
web_search("{队A} xG stats expected goals {比赛名}")
web_search("{队A} vs {队B} player ratings man of the match")
web_search("{比赛名} World Cup 2026 group standings after match")
```

提取链路：`web_extract(Parallel)` → 失败降级 `browser_navigate(本地Chrome)`。全部免费 cron 安全。

### 第二步：对比预测

将实际结果与赛前预测进行对比。需要读取之前输出的预测记录。

**预测来源查找**：
- 通过 `session_search(query="WC2026 赛前预测 {日期}")` 查找之前生成的预测报告
- 提取每场比赛的预测胜率、推荐比分、推理链

**对比维度**：

| 维度 | 对比内容 |
|:----|:--------|
| 胜负方向 | 预测胜者 vs 实际胜者 → ✅/❌ |
| 概率精度 | 预测概率 vs 实际发生频率 |
| 比分精度 | 推荐比分 vs 实际比分 |
| 关键推理 | 推理链中的核心论点是否成立 |

### 第三步：偏差分析（核心）

对每个错误的预测或偏差较大的预测，进行**10维度回溯分析**：

```yaml
比赛: 墨西哥 vs 南非
预测: 墨西哥胜(78%) 2-0
实际: ?-?
偏差维度: 
  - 实力评估: ✅ 正确
  - 近期状态: ✅ 正确
  - 阵容完整性: ✅ 正确
  - 战术对位: ⚠️ 不完全
  - 历史交锋: N/A (无)
  - 外部因素(海拔/天气): ❌ 低估/高估了？
  - 关键球员: ✅ 正确
  - 大赛心理: ✅ 正确
  - 名宿观点: N/A
  - 深层数据: ❌ 遗漏了什么？
关键教训: ...
修正方案: ...
```

**偏差类型分类**：

| 类型 | 描述 | 处理方法 |
|:----|:-----|:--------|
| 🔬 **数据缺失** | 我们没有某个关键信息 | 下次赛前采集增加该维度 |
| ⚖️ **权重偏差** | 某个维度权重设高了/低了 | 调整10维度评分权重 |
| 🌪️ **黑天鹅** | 意外红牌、重伤、极端天气 | 记录但不调整模型 |
| 🧠 **认知偏差** | 我方思维定势导致的误判 | 记录到 lessons-learned |
| 📊 **赔率误导** | Sharp赔率方向错了 | 记录但不过度修正 |

### 第四步：方法论迭代

将偏差分析的结论写入两个文件：

#### accuracy-tracking.md

累计准确率表格，追加新行：

```markdown
## 小组赛第1轮（2026-06-12 ~ 2026-06-14）

| 日期 | 比赛 | 预测方 | 实际结果 | 预测概率 | 胜负✅❌ | 比分✅❌ |
|:---|:----|:------|:--------|:--------|:--------|:--------|
| 6/12 | 墨西哥vs南非 | 墨西哥胜 | ?-? | 78% | ? | ? |
| 6/12 | 韩国vs捷克 | 韩国胜 | ?-? | 45% | ? | ? |

### 累计统计
- 总预测场次: X
- 胜负方向正确: X (XX%)
- 比分正确: X (XX%)
- 平均概率校准: ±XX%
```

#### lessons-learned.md

每个教训一个条目，按时间排序：

```markdown
## 2026-06-12 | 墨西哥 vs 南非
- **偏差维度**: 外部因素(海拔)
- **预测**: 墨西哥胜2-0(78%)
- **实际**: ?-?
- **偏差描述**: ...
- **根因**: ...
- **修正措施**: ...
```

### 第五步：更新文件（赛后数据同步）

每场已结束的比赛，按以下流程更新所有相关文件。文件操作使用 `patch` 或 `write_file`（cron 安全）。

**① 更新 match page**（用 patch 修改 YAML frontmatter）
- 修改 frontmatter: `status: finished`, 添加 `result: X-Y`, `goals_home: ...`, `goals_away: ...`, `red_cards: ...`
- 追加赛后复盘区块（预测vs实际对比、进球详情、比赛回顾、出线形势影响）

**② 更新伤病追踪总表（concepts/伤病追踪总表.md）**
- 🟥 **红牌球员** → 标记 ❌（至少停赛1场），记录停赛场次
- 🏥 **受伤球员** → 标记 ❌/⚠️，记录伤情详情
- ✅ **已恢复球员** → 从❌/⚠️改为✅
- 来源：赛后新闻报道 + 比赛记录

**③ 更新出线形势**
- 在复盘报告中更新小组积分榜
- 标注关键缺阵对下一场的影响

### 第六步：输出复盘报告

报告格式统一如下：

```
⚽ WC2026 赛后复盘 | 6月XX日

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 昨日战果

🇲🇽 墨西哥 ?-? 🇿🇦 南非
  → 预测: 墨西哥胜(78%) 推荐2-0
  → 判断: ✅/❌

🇰🇷 韩国 ?-? 🇨🇿 捷克
  → 预测: 韩国胜(45%) 推荐1-0
  → 判断: ✅/❌

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📈 累计准确率
- 胜负方向: X/X (XX%)
- 推荐比分: X/X (XX%)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔬 偏差分析

1. [比赛名] — [偏差类型]
   偏差描述: ...
   根因: ...
   修正: ...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔄 方法论更新
- [更新的维度/权重/规则]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📋 lessons-learned 已更新
📋 accuracy-tracking 已更新
```

## Cron 配置

每天 12:00（北京时间）运行，只加载 `wc2026-review` 一个 skill（不加载 wc2026-predictor，避免 context 过大导致 Broken pipe）。

```yaml
定时: 0 12 * * *
技能: [wc2026-review]
投递: origin
```

## Pitfalls

- **🚫 禁止使用 execute_code 和 terminal（curl）**：这两个工具在 cron 模式下会返回 `pending_approval` 或 `BLOCKED`，导致 agent 卡死。所有数据获取必须用 `web_search` → `web_extract` → `browser_navigate` 链路。
- **Odds API 使用 web_extract 调用**：`web_extract("https://api.the-odds-api.com/...")` 是 cron 安全的，返回文本中可直接解析比分。注意 API 返回的 `scores` 是 `[{"name": "Mexico", "score": "2"}]` 数组格式，不是 `{"home": "2", "away": "0"}` 字典。
- **Parallel 免费 MCP 获取进球详情**：搜比赛名+goal scorers，Parallel 摘要通常已有比分/进球者+时间，不足则 web_extract 读，再不行 browser→Google
- **SerpAPI/Exa 均已废弃**：SerpAPI 脚本已删除，Exa key 已注释。搜和提取全部走 Parallel 免费 MCP 降级 browser 链路。
- **赛后必须同步伤病追踪表**：红牌球员必须在 `concepts/伤病追踪总表.md` 中标记为 ❌ 停赛。这是复盘流程中容易遗漏的步骤。
- **预测记录查找**：`session_search` 可能找不到之前的赛前预测输出。备选方案是直接读 match pages 中的「系统预测」区块（每个 match page 的 🤖 部分包含完整评分+预测概率+推荐比分）。
- **accuracy-scoring nuance**：当预测同时包含首选（如 1-1）和次选（如 2-1 韩国），实际为次选结果时 → 胜负方向✅，推荐比分❌，在备注中标注"次选正确"。
- **FotMob 时间差**：美洲西海岸的晚场比赛（北京时间凌晨）在12:00北京运行时可能结果已出但尚未被所有来源索引。Google 体育知识面板是最快的信息来源。
- **时区陷阱**：比赛日期以北京时间为准。前一天 = 北京时间昨天。注意 FotMob 显示的是当地 US 时间，需换算。
