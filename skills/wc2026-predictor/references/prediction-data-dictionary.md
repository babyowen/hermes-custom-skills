# 预测数据词典

WC2026 wiki 中可用于比赛预测的数据文件和字段说明。

## 📂 数据文件索引

| 数据类别 | 路径 | 格式 | 说明 |
|---------|------|------|------|
| 球队基础信息 | `entities/{队名}.md` | Markdown + YAML frontmatter | 阵容动态、伤病情况、战术分析、FIFA排名 |
| 历史交锋 | `comparisons/{队名1}-vs-{队名2}.md` | Markdown + YAML | 总场次、胜负平分布、最近5次交锋、大赛记录 |
| 近期状态 | `comparisons/recent-form/{队名}.md` | Markdown + YAML | 近6场正式比赛结果表格 |
| 小组分组 | `concepts/2026世界杯小组赛分组.md` | Markdown | 12小组48队分组明细 |
| 裁判数据 | `wiki/concepts/裁判名单与执法风格.md` | Markdown | 52名主裁名单+执法风格评分 |
| 场地数据 | `wiki/concepts/比赛场地与环境数据.md` | Markdown | 16座场馆容量/海拔/气候 |
| 概念分析 | `concepts/世界杯历史模式分析.md` | Markdown | 历史数据规律总结 |
| 伤病总览 | `concepts/伤病追踪总表.md` | Markdown | 48队伤病全景（❌确认缺席/⚠️存疑/✅恢复），2026-05-23创建 |
| 热身赛追踪 | `warmup/` 全套（README + schedule + results/） | Markdown | 赛程+已录结果+模板，2026-05-23创建 |

## 📊 8维度评分说明

| 维度 | 数据来源 | 权重建议 |
|:----|:---------|:---------|
| 1. 实力评估 | entities/ (FIFA排名 + 球员总身价 + 大赛经验评分) | 高 |
| 2. 近期状态 | comparisons/recent-form/ (近6场胜率 + 进球/失球趋势) | 高 |
| 3. 阵容完整性 | entities/ + SerpAPI搜索 (伤病缺阵影响程度) | 高 |
| 4. 战术对位 | entities/ (阵型相克 + 风格克制分析) | 中 |
| 5. 历史交锋 | comparisons/ (心理优势 + 比分模式) | 中 |
| 6. 外部因素 | concepts/ + weather-collection (主客场 + 海拔高度 + 天气温度+湿度 + 休息天数) 详见 references/weather-collection-workflow.md | 中 |
| 7. 关键球员 | entities/ + SerpAPI搜索 (球星个人能力 + 对位优势) | 中 |
| 8. 大赛心理 | entities/ (历史大赛表现 + 淘汰赛经验) | 低 |
| 9. 名宿观点 | matches/ (多名名宿加权预测) | 低 |
| 10. 深层数据 | matches/ (xG, 控球率, 射门转化率) | 低 |

## 🔍 赛前搜索模板

赛前2-4小时，用 SerpAPI 搜索以下情报：
```bash
python3 ~/.hermes/skills/serpapi-search/scripts/search.py "{队名} {队名} 2026 World Cup lineup injury latest" --country cn --lang zh-CN --limit 5 --json
python3 ~/.hermes/skills/serpapi-search/scripts/search.py "{队名} vs {队名} 2026 match preview" --limit 5 --json
```

## 📤 预测输出格式

```
⚽ WC2026 比赛预测 | YYYY-MM-DD

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🇧🇷 巴西 vs 🇷🇸 塞尔维亚  |  C组  |  6月13日
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 综合评估
  巴西: 8.5/10  |  塞尔维亚: 6.2/10
  预测胜率: 62% - 20% - 18%（胜平负）

🔍 关键对位
  • 维尼修斯 vs 帕夫洛维奇 — 速度优势明显
  • 中场控制权: 巴西 65% vs 塞尔维亚 35%

⚠️ 风险因素
  • 内马尔刚复出，体能存疑
  • 巴西近3场热身赛仅1胜

💡 比分预测: 巴西 2-1 塞尔维亚
```
