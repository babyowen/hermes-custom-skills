# Changelog

## v2.0.0 (2026-06-12) — SKILL.md 大瘦身
- SKILL.md 从 777行/52KB 精简至 ~110行/5.6KB（90%缩减）
- 搬出：详细采集流程 → references/workflow-details.md
- 搬出：版本历史 → references/changelog.md
- 移除：DuckDuckGo/SerpAPI 引用（统一 browser→Google）
- 新增：「揭幕战情绪因子」特殊情景修正

## v1.10.0 (2026-06-12) — SerpAPI全面退役
- SerpAPI skill 已删除，默认搜索改为 browser_navigate→Google
- 采集工具优先级：web_extract → browser→Google → DuckDuckGo → curl

## v1.9.0 (2026-06-12) — DuckDuckGo + ussoccer.com + subagent效率
- 新增 DuckDuckGo Search 作为免费备用
- 新增 ussoccer.com 至 site accessibility 表
- 新增 subagent 效率 pitfall 与 context 模板

## v1.8.0 (2026-06-11) — FotMob 时区修正
- 确认 FotMob fixture 列表显示 PT 而非 ET
- 新增 mexico-venue-coordinates.md
- 新增 delegate_task 批量采集模式

## v1.7.0 (2026-06-10) — 合并 football-prediction
- X/社媒情报采集、Polymarket 资金流向检测

## v1.6.0 (2026-06-10) — 赛程数据紧急审计
- 发现模板生成 match pages 对阵/日期全错
- 新增 FotMob 赛程验证流程

## v1.5.0 (2026-06-06) — 天气维度全面升级
- weather-collection-workflow.md + 球队气候适应性分析.md
- 特殊情景修正表新增4行高温/高海拔

## v1.4.0 (2026-06-04) — 热身赛日程偏移
- 热身赛日期偏移处理、Pending赛果不在 schedule 中处理

## v1.3.0 (2026-05-27~31) — 采集体系建立
- bulk-wikipedia-squad-scan、pipe-to-interpreter pitfall、Eix 断供工作流

## v1.0.0 (2026-05-20) — 初始版本
