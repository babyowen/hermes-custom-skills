---
name: wc2026-review
description: "WC2026世界杯赛后复盘系统。每天中午自动查询前一天比赛结果，对比系统预测，分析偏差原因，自动迭代预测方法论。"
version: 1.1.0
tags: [wc2026, world-cup, review, post-match, iteration]
---

# WC2026 赛后复盘与自动迭代系统

## 概述

在 `wc2026-predictor` skill 生成赛前预测的基础上，每天中午运行，对前一天已结束的比赛进行**结果确认 → 预测对比 → 偏差分析 → 方法论迭代**的完整闭环。

## 核心流程

```
① 获取前一天赛果 — FotMob browser / The Odds API / Football365 curl
② 对比预测 — 将实际结果与系统预测进行逐场对比
③ 偏差分析 — 按10维度逐一排查：哪个维度看错了？
④ 方法论迭代 — 将发现的偏差写入 accuracy-tracking 和 lessons-learned
⑤ 输出复盘报告 — 推送到飞书
```

## 数据存储

赛后复盘数据存储在 `~/wc2026/reviews/` 目录。**首次运行时需先创建该目录**（`mkdir -p ~/wc2026/reviews/match-reports`）：

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

从 FotMob fixtures 页面或 The Odds API 获取前一天已结束比赛的比分。

**工具优先级**：
1. 🥇 **The Odds API**（`soccer_fifa_world_cup`）— 返回已完成比赛的最终比分（`completed`状态）
2. 🥈 **browser→Google 搜索** — 搜索比赛名+goal scorers，Google体育知识面板直接显示进球者+时间
3. 🥉 **FotMob browser** — 逐个检查比赛详情页的最终比分

```python
# 示例：从 The Odds API 获取已结束比赛
# ⚠️ 注意：scores 是 [{"name": team, "score": "X"}] 列表，不是字典！
import httpx
resp = httpx.get("https://api.the-odds-api.com/v4/sports/soccer_fifa_world_cup/scores/?apiKey=e957983e5449073eedc1e6fafc619a74&daysFrom=1", timeout=15)
scores = resp.json()
for m in scores:
    if m.get('completed'):
        score_list = m.get('scores', [])
        hs = score_list[0]['score'] if len(score_list) > 0 else '?'
        as_ = score_list[1]['score'] if len(score_list) > 1 else '?'
        print(f"{m['home_team']} {hs} - {as_} {m['away_team']}")
```

### 获取进球详情

The Odds API 只返回比分，不返回进球者/时间。获取详情的方法：

**browser→Google 搜索（最可靠，Exa断供时唯一可用）**：
```python
# 搜索 "[主队] vs [客队] goal scorers" → Google体育知识面板直接显示
# 返回格式：Ladislav Krejčí 59', Hwang In-beom 67', Oh Hyeon-gyu 80'
browser_navigate("https://www.google.com/search?q=South+Korea+vs+Czech+goal+scorers")
# 从 snapshot 中的"Sports results"或"Videos"分组提取
```
**实测效果**（2026-06-12）：Google搜索结果页的体育知识面板直接包含进球者、时间、比赛回顾链接，无需点击任何文章。这是 Exa/SerpAPI 均不可用时获取进球详情的唯一可靠方法。

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

每场已结束的比赛，按以下流程更新所有相关文件：

**① 更新 match page**
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

每天 12:00（北京时间）运行，加载 `wc2026-predictor` + `wc2026-review` 两个 skill。

```yaml
定时: 0 12 * * *
技能: [wc2026-predictor, wc2026-review]
投递: origin
```

## Pitfalls

- **Odds API scores 是列表而非字典**：`m.get('scores')` 返回的是 `[{"name": "Mexico", "score": "2"}, {"name": "South Africa", "score": "0"}]` 格式的列表，不是 `{"home": "2", "away": "0"}` 字典。示例代码中的 `.get('home')` 会抛出 AttributeError。正确写法：`score_list = m.get('scores', []); hs = score_list[0]['score'] if len(score_list) > 0 else '?'`
- **Exa API 耗尽时获取进球详情**：web_extract 返回 402，web_search 也返回 402。此时用 browser_navigate→Google 搜索比赛名+"goal scorers"，Google 体育知识面板直接显示进球者+时间，无需点击任何文章。这是最可靠的进球详情来源。
- **SerpAPI 脚本已删除**：`~/.hermes/skills/serpapi-search/scripts/search.py` 已随 v1.10.0 更新被移除。不要尝试调用这个路径，直接用 browser_navigate→Google。
- **赛后必须同步伤病追踪表**：红牌球员必须在 `concepts/伤病追踪总表.md` 中标记为 ❌ 停赛。这是复盘流程中容易遗漏的步骤。
- **预测记录查找**：`session_search` 可能找不到之前的赛前预测输出。备选方案是直接读 match pages 中的「系统预测」区块（每个 match page 的 🤖 部分包含完整评分+预测概率+推荐比分）。
- **accuracy-scoring nuance**：当预测同时包含首选（如 1-1）和次选（如 2-1 韩国），实际为次选结果时 → 胜负方向✅，推荐比分❌，在备注中标注"次选正确"。
- **FotMob 时间差**：美洲西海岸的晚场比赛（北京时间凌晨）在12:00北京运行时可能结果已出但尚未被所有来源索引。Google 体育知识面板是最快的信息来源。
- **时区陷阱**：比赛日期以北京时间为准。前一天 = 北京时间昨天。注意 FotMob 显示的是当地 US 时间，需换算。
