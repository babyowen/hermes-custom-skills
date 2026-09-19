# 库结构笔记（2026-09-19 实测）

库 `serp_news`，生产表 `scored_news`（约 14.3 万行；**不要**用 `scored_news_test`）。历史数据从 2026-09 起保留在库内，实测 2026-09-01～09-18 连续有数据。

## 字段（SHOW COLUMNS 实测）
| 字段 | 类型 | 说明 |
|:----|:----|:----|
| id | int | 主键，按天递增 |
| date | varchar(64) | 新闻自身日期，**统计不用它** |
| title | varchar(255) | 标题 |
| link | text | 原文链接 |
| source | varchar(255) | 来源站点 |
| fetchdate | date | **统计口径字段**（业务日期） |
| sourceapi | varchar(255) | 采集通道：`serp_googlenews` / `serp_bingnews` / `serp_baidunews` / `serp_duckduckgo_news` / `官网抓取`；可能为 NULL |
| thumbnail | text | 缩略图 |
| keyword | varchar(255) | 主题（养老/公积金/烟草服务银行/政府基金/中国烟草/机关事务/零基预算/数字政务） |
| content | longtext | 正文 |
| wordcount | int | 字数（实测 = `CHAR_LENGTH(content)`，仍以 CHAR_LENGTH 为准） |
| custom_grab | tinyint(1) | 自定义抓取标记 |
| score | int | 0–5；NULL = 未评分 |
| import_batch_id | varchar(50) | 导入批次 |
| content_hash | varchar(32) | 去重哈希 |
| search_keyword | varchar(255) | 检索关键词 |
| short_summary | text | 摘要 |
| region | varchar(255) | 地域（公积金用，可空） |
| business_types | json | 公积金业务类型，多数为 NULL |

**没有入库时间字段** → 无法从库内判断任务完成时刻，报告里不要假装知道。

## 实测基线（2026-09-11～09-17，7 天）
- 日均总量 ≈260 条；日均高分 ≈43 条。
- 当日量级参考：2026-09-18 = 372 条（官网 1 条），高分 82 条。
- 各来源占比量级：serp_googlenews > serp_bingnews > serp_baidunews > serp_duckduckgo_news ≫ 官网抓取。
- 官网抓取量级很低（每天 0–4 条），多天无记录属常见 → 不要按天告警。

## 常见坑
- `fetchdate` 是 date 类型，比较用 `%s` 传 `datetime.date`，不要传字符串拼接。
- MySQL 里 `sourceapi<>'官网抓取'` 会把 NULL 行滤掉 → 必须写 `(sourceapi IS NULL OR sourceapi<>'官网抓取')`。
- `TRIM()` 默认只去空格；判断纯空白正文用 `content<>'' AND TRIM(content)=''`。
- `AVG(score)` 自动忽略 NULL，报告里注明「不含 NULL」。
- 脚本 `q()` 会拒绝非 SELECT 语句、包含 `scored_news_test` 的语句、以及未引用生产表的语句。
