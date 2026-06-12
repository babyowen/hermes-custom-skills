# Hermes Custom Skills

本仓库托管我个人设计的 Hermes Agent 技能。通过 symlink 链接到 `~/.hermes/skills/` 使用。

## 技能列表

| 技能 | 说明 | 领域 |
|:----|:-----|:-----|
| wc2026-predictor | 世界杯比赛预测（10维度评分+特殊情景修正） | ⚽ 体育 |
| wc2026-news-review | 赛后新闻搜集与复盘学习 | ⚽ 体育 |
| wc2026-review | 赛后复盘与准确率追踪 | ⚽ 体育 |
| gaokao-essay-predictor | 2026江苏高考作文题预测 | 📚 高考 |
| jiangsu-gaokao-expert-v3 | 江苏高考决策情报日报 | 📚 高考 |
| a-stock-closing-analysis | A股收盘日报自动生成 | 📈 金融 |
| hotlist-analyzer | 全网热点智能追踪分析 | 🔥 热点 |
| cron-health-checker | 定时任务健康检查 | 🔧 运维 |
| polymarket | Polymarket 预测市场查询 | 🏛️ 预测市场 |
| football-prediction | 足球预测工作流 | ⚽ 体育 |
| movie-watchlist | 电影推荐与观影管理 | 🎬 娱乐 |
| drone-weather | 无人机航拍天气评估 | 🛸 航拍 |

## 使用方式

### 服务端（Hermes Agent）

所有技能通过 symlink 引用到 `~/.hermes/skills/`：

```bash
ln -sf ~/hermes-custom/skills/<技能名> ~/.hermes/skills/<技能名>
```

### 本地 AI Agent

```bash
ln -sf ~/hermes-custom/skills/<技能名> ~/.agent/skills/<技能名>
```

## 工作流

1. **服务端**：通过对话修改技能 → 自动 `git commit + push`
2. **本地**：`git pull` 同步 → 用本地 AI review diff → 有修改则 `push` 回来
3. **同步**：服务端 `git pull` 拉取本地修改
