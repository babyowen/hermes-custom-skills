---
name: wc2026-news-review
description: WC2026世界杯赛后新闻搜集与复盘学习——收集前一天比赛的新闻报道、专家分析、市场反应，提取可复用的预测经验，同步更新到 wc2026-predictor 技能中。
version: 1.1.0
metadata:
  hermes:
    tags: [wc2026, world-cup, news, review, learning, sports]
---

# WC2026 赛后新闻搜集与复盘学习

## 概述

专注搜集比赛日的赛后新闻，提取**可复用的预测经验**回写到预测技能。这是 wc2026-predictor 的**学习闭环**——每场比赛都是一次校准模型的机会。

## 执行流程

### ① 确认当天已结束的比赛

用 browser_navigate 访问 FotMob，确认最近 24h 内（北京时间）结束的比赛：

```
fotmob.com/leagues/77/fixtures/world-cup
```

查看 "today" 和 "yesterday" 标签下的比赛，记录：
- 比分（准确赛果）
- 组别
- 开球时间（UTC + 北京时间）

**⚠️ FotMob 相对时间标签偏移陷阱**：FotMob fixture 列表显示的是 PT (Pacific Time, UTC-7)。"yesterday"、"today"、"tomorrow" 等相对时间标签基于 PT 时区计算，**不一定等于北京时间的"昨天"**。例如 2026-06-15 北京时间的运行时，FotMob 可能仍将 6月11日的比赛归类在"yesterday"标签下。确认方法：点击具体比赛进入详情页，查看 `<h1>` 标题中的 ISO 8601 UTC 时间戳（如 `Mexico vs South Africa (2026-06-11T19:00:00.000Z)`），这是最精确的开球时间。

### ①.5 检查是否已被前序 cron 处理（避免重复工作）

**wc2026-review skill** 可能在 12:00（北京时间）已运行过并处理了相同比赛。在采集新闻前先快速检查：

```bash
# 检查 match page 状态
grep -l "status: finished" ~/wc2026/matches/小组赛/{潜在比赛名}.md
# 检查是否已有复盘报告
ls ~/wc2026/reviews/match-reports/ | grep {日期}
```

如果比赛页已标记 `status: finished` 且 `reviews/match-reports/` 中已有对应复盘文件 → 跳过「对比预测」步骤（直接进入④提取经验）。

### ② 逐场搜集赛后新闻

对每场已结束的比赛，用 web_search(Parallel) 搜以下关键词，然后用 web_extract(Parallel) 读正文（提取失败降级 browser_navigate→eval innerText）：

**每场比赛采集 100 篇赛后新闻**，按以下维度分布：

| 维度 | 篇数 | 目的 |
|:----|:----|:----|
| 赛后战报/比赛回顾 | 12 篇 | 比赛全貌、转折点、关键事件 |
| 战术复盘分析 | 12 篇 | 阵型变化、战术调整 |
| 教练/球员赛后采访 | 12 篇 | 赛后感言、更衣室信号 |
| 数据统计（xG/控球率） | 10 篇 | Opta/WhoScored 深度数据 |
| 媒体评分/舆论 | 10 篇 | 各方评价、赛后评级 |
| 进球/精彩瞬间分析 | 8 篇 | 每个进球的过程拆解 |
| 伤病更新 | 8 篇 | 比赛中受伤球员的伤情确认 |
| 红黄牌/纪律 | 8 篇 | 停赛风险、下一场缺席 |
| 出线形势分析 | 10 篇 | 本场结果对小组排名的影响 |
| 赔率变动回顾 | 5 篇 | 赛前赔率 vs 赛后复盘 |
| 双方球迷/社媒反应 | 5 篇 | 情绪面、士气面评估 |

搜索关键词示例：

| 关键词组合 | 目的 |
|-----------|------|
| `{队A} vs {队B} World Cup 2026 match report post-match analysis` | 赛后战报 |
| `{队A} vs {队B} tactics review formation change` | 战术复盘 |
| `{教练名} post-match press conference` | 赛后发布会 |
| `{队A} {球员} injury update` | 伤病更新 |
| `{队A} {球员} red card suspension` | 红牌停赛 |
| `{比赛} odds movement post-match` | 赔率变动 |
| `{队A} xG stats expected goals` | 深度数据 |

**提取方式**：`web_extract(Parallel)` → 失败降级 `browser_navigate(本地Chrome)` + eval body.innerText。全部免费，采集一场约 5 分钟。

### ③ 对比预测 vs 实际

查找本次比赛之前是否有过系统预测（session_search 或用 wc2026-predictor 的预测记录），对比：

| 维度 | 预测 | 实际 | 偏差分析 |
|------|:----:|:----:|:---------|
| 胜负 | ? | ? | ? |
| 比分 | ? | ? | ? |
| 进球数 | ? | ? | ? |
| 红牌/点球等 | ? | ? | ? |

> 如果步骤 ①.5 确认该比赛已被前序 cron 处理过（match page 已有赛后复盘区块），可以跳过此步骤，直接进入④。

### ④ 提取可复用的经验

每次跑完至少回答以下 3 个问题：

1. **什么预测对了？** 原因是什么？（强化正确逻辑）
2. **什么预测错了？** 为什么错？遗漏了什么信息？（修正模型）
3. **这个比赛有什么可复用的规律？** （比如：某队主场优势被低估了、红牌在揭幕战特别多、etc.）

### ⑤ 更新 wc2026-predictor 技能

将有价值的经验写入 wc2026-predictor，包括但不限于：

**场景 A：发现了新的特殊情景修正**
```patch
在「特殊情景修正」表中新增一行：
| 🆕 新发现情景 | 说明 | 修正值 |
```
用 `skill_manage(action='patch')` 更新 wc2026-predictor 的 SKILL.md。

**场景 B：某队战术模式发现**
更新对应 entities/{队名}.md 中的战术分析或 entities 数据。

**场景 C：赔率/市场行为规律**
追加到 wc2026-predictor 的「赔率分析」或「特殊情景」章节。

**场景 D：重大伤病/停赛**
更新 伤病追踪总表 concepts/伤病追踪总表.md

#### ⚠️ 多 cron 并发写冲突（sibling subagent 警告）

当 wc2026-news-review 和 wc2026-predictor 或 wc2026-review 同时运行时，多个 cron 可能同时调用 `skill_manage(action='patch')` 修改 wc2026-predictor 的 SKILL.md。Hermes 会发出 "modified by sibling subagent" 警告。

**处理规则**：
1. patch 操作通常能成功（fuzzy matching）——检查 diff 输出确认变更已应用
2. 如果 patch 返回失败（旧文本未找到），先重读 SKILL.md 再重试
3. 不要在同一运行中多次 patch 同一个文件的同一区域——一次性准备完整 old_string→new_string
4. 如果变更有冲突风险，优先追加到文件尾部（新增段落）而非修改已有内容

### ⑥ 输出日报摘要 → lark-cli 推送

生成日报摘要后，写入临时文件并用 lark-cli --markdown 推送，回复简短确认。格式如下：

```
📰 WC2026 赛后新闻速览 | 6月XX日
━━━━━━━━━━━━━━━━━━━━━━━━

🇲🇽 墨西哥 2-0 🇿🇦 南非  |  A组
✅ 预测: 墨西哥胜 2-0 → 命中！
💡 启示：揭幕战红牌多发——3张红牌创纪录，预测时应加入"大赛首场情绪因子"

🇰🇷 韩国 vs 🇨🇿 捷克  |  A组
结果：进行中/待确认

━━━━━━━━━━━━━━━━━━━━━━━━
📊 累计预测准确率: X%
🔄 本次更新：新增「揭幕战情绪因子」修正，下轮预测生效
━━━━━━━━━━━━━━━━━━━━━━━━
```

## 时间选择逻辑

| 时间段 | 覆盖的比赛 | 说明 |
|--------|-----------|------|
| 15:00 北京 | 美洲时区前晚比赛 + 亚洲/澳洲早场 | 美洲比赛通常在北京凌晨结束，15:00 已出报道 |
| 22:00 北京 | 欧洲/非洲当天比赛 | 欧洲晚间黄金档比赛，22:00 已有完整复盘 |

## 特殊注意事项

### 关于"写入预测技能"的边界

⚠️ 只写**可复用的通用规律**，不写单场比赛的孤立事实。判断标准：
- ✅ 写："东道主揭幕战红牌概率高（近3届2场有红牌）" 
- ❌ 不写："墨西哥的蒙铁斯红牌了"
- ✅ 写："高温露天场馆（30°C+）对北欧球队下半场体能影响明显"
- ❌ 不写："今天多伦多27°C不算高温"

### 更新 wc2026-predictor 的方法

使用 `skill_manage(action='patch')`：

```yaml
skill_manage(
  action='patch',
  name='wc2026-predictor',
  old_string='...完整的旧文本...',
  new_string='...更新后的文本...'
)
```

需要先 `skill_view(name='wc2026-predictor')` 获取最新 SKILL.md 内容，找到要修改的精确位置。
