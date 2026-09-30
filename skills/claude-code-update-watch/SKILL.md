---
name: claude-code-update-watch
description: "盯 Claude Code 官方更新给周报+升级建议。触发词：claude code 更新/cc 更新/cc 周报/claude code 要不要升级/官方 release notes"
version: 1.1.0
author: Hermes Agent
metadata:
  hermes:
    tags: [claude-code, release-watch, upgrade, weekly, devops]
    related_skills: [hermes-update-watch, hermes-maintenance]
---

# Claude Code 更新周报 + 升级建议

## 概述

每周核对 **Claude Code**（npm 包 `@anthropic-ai/claude-code` / GitHub `anthropics/claude-code`）的发布动态，输出一份「本周更新了什么 + 哪些重要 + **值不值得升级**」的周报。

数据源只有官方两处：**npm registry**（权威版本表 + 每版发布时间 + 三个发布通道）与 **GitHub Releases**（逐版本 changelog 正文，失败时回退 raw CHANGELOG.md）。全部由脚本采集，人工不碰原始 API。

**三条铁律**
1. **只判"本周的更新值不值得升"** —— 判据只有本周变化本身 + 发版节奏。**完全不考虑用户本机装了什么版本**：不做落后计算、不做安装盘点、不写"你落后 N 个版本"。JSON 里的 `local` / `behind_latest` / `pending[]` **一律忽略**。
2. **只给建议和现成命令，绝不代跑升级**（不许 `claude update` / `npm i -g` / 改自动更新开关）。用户点头后才动手。
3. **报告里任何数字只能来自脚本 JSON**（版本数、条目数、天数、间隔）；不许自行推算或脑补。

## 何时用

- cron **每周六 10:30（BJT）** 自动触发（与 Hermes 周报 10:00 错峰）
- 用户说："claude code 更新了什么" / "cc 最近改了啥" / "claude code 要不要升级" / "看下官方 release notes"

## 核心流程

### ① 采集（脚本是唯一数据源，别自己 curl）

```bash
python3 ~/.hermes/skills/claude-code-update-watch/scripts/fetch_claude_code_updates.py --days 7 --json
```

- **cron 模式**：脚本 JSON 已作为 context 注入 prompt，直接读，不要再跑一次（GitHub 未认证限流 60 次/小时）
- **交互模式**：跑上面这条命令；加 `--no-state` 可调试（不写状态）
- 脚本自己维护 `~/.hermes/cache/claude-code-update-watch/state.json`（已报过的版本），无需手工处理
- 退出码非 0 / `_run_failed` → 报告里只写 **⚠️ 采集失败 + 原因**，不编内容
- 脚本会顺带探测本机版本，**但周报不使用**（见铁律 1）；只有用户主动问"我这台落后多少"时才看 `references/sources.md` 第 5 节

### ② 判读 JSON

| 字段 | 含义 |
|:---|:---|
| `channel.latest / stable / next` | 三个发布通道的版本号（`latest`=最新发布、`stable`=更保守可能落后、`next`=预发布）。只用于说明"本周发到了哪"，**不用于说用户在哪儿** |
| `released_in_window[]` | **周报主体**：窗口内每个版本 → `counts`（breaking/security/feature/change/fix/other）、`breaking[]`、`security[]`、`features[]`、`changes[]`、`fixes[]`、`bullet_total`、`bullets_omitted`、`importance_score`、`changelog_source`、`url` |
| `top_versions_by_importance[]` | 脚本按 `importance_score`（破坏性×3 + 安全×2 + 影响面 + 新功能）排序的前 5，用于挑"本周重点" |
| `cadence` | 近 7 天/30 天版本数、中位发版间隔天数 —— 判"该不该追版本"的依据 |
| `impact_for_local[]` | 命中「MCP/hook/子代理/权限/模型/限额/成本/npm/安装/IDE」等关键词的条目（字段名带 local 只是历史命名，与"你的机器"无关） |
| `state.new_versions_since_last_report[]` | 上次报过之后新增的版本（防重复）；为空 = 本周无新版本，直接写"本周无新版本" |
| `local` / `behind_latest` / `pending[]` | ⛔ **忽略**（铁律 1） |
| `errors[]` | 某个源失败时会出现在这里（部分可用仍算成功） |

**数字纪律**：`bullet_total` 是**截断后**的条目数，被省略的数量在 `bullets_omitted`；严禁把"要点 60 条"写成"修复了 60 个 bug"。节奏类结论只能引用 `cadence`。

### ③ 出报告（决策优先，≤30 行）

**读者是技术爱好者**：懂概念、爱折腾，但不做技术工作。所以报告要"讲人话"，**不要写成 changelog 的中文摘要**。

**语言风格（硬性）**
- **内部词汇不上报告**：不出现 JSON 字段名（`counts`/`breaking`/`cadence`/`window`）、不出现"条目/窗口/降级/采集"这类工程词
- **术语第一次出现必须跟一句人话解释**：MCP（让 Claude 连外部工具/数据源的机制）、compact 或"压缩"（长对话被自动总结、腾出上下文）、沙箱（限制 Claude 能碰哪些文件的隔离环境）、OTel（运行数据上报）、审批（改文件前的权限确认）
- **用场景说话，别抄 changelog 措辞**：把"修复 resume 时 MCP 工具调用报 No such tool available"写成"恢复昨天的长会话时，外部工具插件以前会加载失败，现在最多等 10 秒就能用"
- **数字只留有用的**：版本数、发版间隔、价格/上下文的量级；不要每行堆"安全 6｜新功能 8｜修复 37"
- **结论和命令必须精确**：结论要一眼可读，命令/版本号要能直接复制（不许口语化改写）
- 允许打比方、举"这对你意味着什么"；不要制造紧迫感

```
🤖 Claude Code 更新周报 | 9月29日

**这周值得升吗？值得。** — 一句话说清为什么（人话，别堆术语）
本周发了 N 个版本（vA → vB），最新 vX｜近 30 天共 M 个，差不多每 D 天就发一版

━━━ 为什么值得升（挑 2-4 条，讲人话）━━━
- 💰 更聪明也更便宜：默认模型换成 Sonnet 5.5，一次能读进约 100 万 token（≈一整本长篇小说的量）
- 🩹 修了真会遇到的毛病：以前长对话压完还报"提示太长"，现在会自动再压一次；恢复旧会话时外部工具插件加载失败，现在最多等 10 秒
- 🔒 用起来更安全：插件不能再给自己偷偷开权限；Linux 沙箱下写被拒目录不再启动失败
- ⚠️ 会不会破坏我的用法：不会 —— 这批版本没有删功能、也没有要改配置的地方

━━━ 各版本一句话 ━━━
- `2.1.284`（9/28）：默认模型升级 + MCP 一键重连（`/mcp reconnect all`）
- （窗口内每个版本一行；条目少的可两版合一行）

━━━ 想升就这么做 ━━━
- 一条命令：`npm i -g @anthropic-ai/claude-code@latest`（或内置 `claude update`）｜想稳一点用 `@<channel.stable>`
- 后悔了能退：`npm i -g @anthropic-ai/claude-code@<旧版本>`｜升完要 `/exit` 重开会话才生效
- 一句时机建议（结合 `cadence`：几乎天天发版，不必每版都追；刚发版不到一天且改动大，可以等一个补丁版）

完整 changelog：<links.releases>
```

- 飞书格式：`**粗体**` + emoji 小标题、`-` 列表、`[链接](url)`、`━━━` 分隔线；**禁** Markdown 表格与 `#` 标题
- 报告里**不出现**"本机 / 你落后 / 你装的是 / 安装盘点"这类字眼
- `state.first_run=true` 时补一句"本周为首次采集，已记录 N 个版本作基线"，**不涉及本机**

### ④ "值不值得升"三档口径

| 档 | 判据（引用 JSON 字段/条目） |
|:---|:---|
| **值得升** | `counts.security>0` 且涉及凭据/权限/sandbox/审批绕过；或修了日常会踩的坑（compact 后仍报 "Prompt is too long"、响应流损坏、resume 会话丢消息/MCP 工具调用失败、崩溃重试死循环）；或模型/限额/成本有实质变化（新默认模型、1M 上下文、计价变动） |
| **可暂缓** | 条目集中在 IDE/终端 UI/遥测/企业托管设置（managed settings、Claude apps gateway、OTel）这类与个人终端无关的方向；或纯内部重构与小体验优化 |
| **先别升** | `counts.breaking>0`（设置项被移除/改名、需要迁移配置）；或刚发版 <24h 且改动面很大 —— 先等一个补丁版 |

**默认基线**：Claude Code 是日更级项目（用 `cadence.median_gap_days_last30d` 佐证），**不必每版都追**。除非命中"值得升"，否则给命令 + "你想升的时候跑一下"就行，**不要制造紧迫感**。

### ⑤ 通道语义（只说"发到哪儿"，不说"你在哪儿"）

- 报告里可以写 `latest=vX｜stable=vY`，用来提示"想稳可以停在 stable 通道"
- ⛔ 不要写"你在 stable 通道 / 你落后 N 个版本 / 你的版本是" —— 本技能不看用户装了什么
- `next` 是预发布，**不要在报告里推荐**，只在用户问起时说明

## Pitfalls

| # | ❌ 坑 | ✅ 正确做法 |
|:-:|:---|:---|
| 1 | 把本机版本当判据 | 判据只有本周变化 + `cadence`；`local`/`behind_latest`/`pending[]` 一律忽略，报告里不出现"落后/本机/安装盘点"字眼 |
| 2 | 认错包/认错仓 | 只认 npm scoped 包 `@anthropic-ai/claude-code` + 官方 repo `anthropics/claude-code`；`claude-code-cli`、`@anthropic/claude-code`、各类镜像站一律不算 |
| 3 | 三个通道混着用 | `latest` 用于报"本周最新"，`stable` 用于给"想稳一点"的替代命令，`next` 不推荐 |
| 4 | release body 为空就写"本周无内容" | 脚本已回退 CHANGELOG.md，`changelog_source` 会标明；两源都空才写"只有版本号" |
| 5 | 把 `## Unreleased` 段当已发布 | 脚本只取 npm 版本表里的真实版本，天然规避；人工核对时也别引 Unreleased |
| 6 | 拿文档站当独立信源 | `docs.claude.com/en/release-notes/claude-code` 实际是 GitHub 页面镜像，引用时指向 `links.releases` / `links.changelog` |
| 7 | 把截断的条目数当全量 | `bullet_total` 是截断后数量，`bullets_omitted` 是被省略数；不许加总成"本周 N 个修复" |
| 8 | 自己再 curl 一遍 npm/GitHub | 脚本已打这两个源；重复请求会吃 GitHub 未认证限流（60/h），失败时报告会缺 changelog |
| 9 | 代跑升级 | **禁止**。只输出命令与回滚方式 |
| 10 | 拿 `importance_score` 当结论 | 它只是排序用的启发式（破坏性×3+安全×2+影响面+新功能），最终判断要读条目内容 |
| 11 | 判据只堆形容词 | "为什么值得升"每条都要挂具体变化（如"修了压缩后仍报提示太长"），不许写"改进很多、体验更好" |
| 12 | 把 changelog 措辞直接搬进报告 | 必须翻译成**场景语言** + 术语带一句人话解释（见 ③ 语言风格）；读起来像给工程师看的内部文档 = 失败 |

## References

| 文件 | 内容 |
|:---|:---|
| `references/sources.md` | 官方端点、字段细节、通道语义、真伪识别、限流与回退链、本机版本探测（备用，当前不用于周报） |
