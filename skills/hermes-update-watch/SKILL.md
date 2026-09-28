---
name: hermes-update-watch
description: "盯 Hermes Agent 官方更新并给升级建议。触发词：hermes更新/hermes升级/hermes周报/官方更新了什么/要不要升级"
version: 1.0.0
metadata:
  hermes:
    tags: [hermes, release-watch, upgrade, weekly, devops]
    related_skills: [hermes-agent, hermes-maintenance]
---

# Hermes 官方更新周报 + 升级建议

## 概述

每周核对 **Hermes Agent 官方仓库**（`NousResearch/hermes-agent`）的发布动态，输出一份「本周更新 + 升级建议」的周报。
数据只有一个来源：官方 GitHub Releases API（附 `compare/...` 完整 changelog 链接）。

**铁律：只给建议和现成命令，绝不自动执行升级。** 用户点头后才动手，且按 `references/upgrade-checklist.md` 走。

## 何时用

- cron 每周六 10:00（BJT）自动触发
- 用户说："hermes 这周更新了啥" / "要不要升级" / "给我升级建议" / "盯一下官方更新"

## 核心流程

### ① 采集（脚本是唯一数据源，别自己 curl）

```bash
python3 ~/.hermes/skills/hermes-update-watch/scripts/fetch_hermes_updates.py --days 7 --json
```

- **cron 模式**：脚本输出已作为 context 注入 prompt，直接读 JSON，不要再跑一次
- **交互模式**：跑上面这条命令拿 JSON
- 脚本自己维护 `~/.hermes/cache/hermes-update-watch/state.json`（已报过的 tag），无需手工处理
- 脚本退出码非 0 / `_run_failed` → 报告里标注 **⚠️ 采集失败**，只报错误原因，不编内容

### ② 判读版本差

| JSON 字段 | 含义 |
|:---|:---|
| `local.version` / `local.commit_date` | 本机版本（git 安装：`~/.hermes/hermes-agent`）与最后更新时间 |
| `latest.tag` / `latest.published_at` | 官方最新 tag |
| `pending_releases[]` | **本机没装上的** release（周报主体） |
| `releases_in_window[]` | 最近 7 天官方发的（可能本机已装） |
| `impact_for_local[]` | 命中你环境关键字的条目（gateway/cron/feishu/provider/skill/state.db…） |
| `state.new_tags_since_last_report[]` | 上次报过之后新增的 tag（防重复） |
| `behind.total_commits` / `behind.impact_commits[]` | 落后区间的官方 compare 数据（**唯一权威的 commit 数**）+ 相关提交样本 |

**数字纪律（硬性）**：报告里出现的任何数量（commit 数、PR 数、文件数、天数、版本数）**只能来自 JSON**。
`behind.capped=true` 时 `total_commits`/`files_changed` 是 GitHub compare 的**封顶值**（10000/300），只能写成"≥10000"；
`behind.impact_commits` 只是**最近 250 个提交里的样本**，不是全量。**不许自行推算或估算**任何数字。

### ③ 出报告（中等详细度，≤40 行，决策优先）

```
📦 Hermes 更新周报 | YYYY-MM-DD（周六）

**结论：<建议升 / 可暂缓 / 先别升>** — 一句话理由
本机 v0.20.6 → 最新 v2026.9.24（落后 N 天 / N 个 tag，<待升 N 个>）

━━━ 本周官方发布 ━━━
- `vXXXX`（M/D）：一句要点 [+N PR]
  - 亮点：…
  - ⚠️ 破坏性/需注意：…（无则省略）

━━━ ⚠️ 影响你本机的 ━━━
- gateway/cron/feishu/provider/技能 相关条目（没有就写"无"）

━━━ 🔧 升级建议 ━━━
- 目标版本 + 一条命令
- 前置检查：…（备份清单）
- 升级后验证：…（hermes doctor / 跑一次关键 cron）
- 回滚点：…

━━━ 其他值得关注的更新 ━━━
- 3-5 条（不逐条罗列全部 release）

完整 changelog：<compare 链接>
```

- 飞书格式：`**粗体**` + emoji 小标题、`-` 列表、`[链接](url)`、`━━━` 分隔线；**禁** Markdown 表格与 `#` 标题
- 首次运行（`state.first_run=true`）时，额外给一段「本机落后情况盘点」

### ④ 升级建议的三档口径

| 档 | 什么时候这么写 |
|:---|:---|
| **建议升** | 含本机相关修复（gateway/feishu/cron/provider/state.db）或安全修复 |
| **可暂缓** | 只有边缘功能（desktop/TUI/新平台）、且无本机相关项 |
| **先别升** | release notes 里有破坏性变更且本机正踩在受影响配置上（例：改过 provider/model、跑着 cron 的 state.db 相关修复未验证） |

跨大版本（如 v0.21→v0.22）必须给**分步方案**：备份 → 升级 → 装回 venv 第三方包 → 验证 → 重启 gateway。

## Pitfalls

| # | ❌ 坑 | ✅ 正确做法 |
|:-:|:---|:---|
| 1 | 把第三方同名仓当官方（`hermes-agent-us`、`hermes-agent-org/hermes`、`hermes-ai.net` 都是社区/山寨） | 只认 `NousResearch/hermes-agent` + 官方文档域 `hermes-agent.nousresearch.com` |
| 2 | 拿 release 的 "rolls up N PRs" 当更新内容吹 | patch release 常只写一句；细节看 body 的 `compare/vX...vY` 链接 |
| 3 | 自己拼 tag / compare URL | 用脚本给的 `compare_url`（tag 命名是 `vYYYY.M.D` 形式，会变） |
| 4 | 用 pyproject 的版本当权威 | `hermes --version` 权威；pyproject 可能滞后于实际 checkout |
| 5 | 把 draft / prerelease 报成"已发布" | 脚本已过滤，别自己再挑 |
| 6 | 忘了用户环境特有的升级坑 | 见 `references/upgrade-checklist.md`（uv 重建丢包、cron model_snapshot、必须 /restart） |
| 7 | 自动执行 `hermes update` | **禁止**。只输出命令与检查项，用户确认后再执行 |
| 8 | 自己推算"落后 N 个 PR / N 个 commit" | 只用 `behind.*`；`capped=true` 时写"≥10000（GitHub 上限）"；不要拿 release body 的 "rolls up N PRs" 凑数 |
| 9 | release notes 太空就写"本周无内容" | 改用 `behind.impact_commits`（按你环境关键词筛出的真实提交）+ release 的 `highlights` |
| 10 | 升级后 `uv sync --locked` 报"锁需要更新"就以为锁坏了 | 是**索引源不一致**：pip.conf 的镜像被 pm 桥接成 `UV_INDEX_URL`，与 `pm/uv.lock` 里的 `registry` 不同 → 用 `UV_INDEX_URL=<锁里的 registry> hermes config check` 跑收尾（详见 `references/upgrade-checklist.md` §7；`upgrade_risks[]` 会提前预警） |

## References

| 文件 | 内容 |
|:---|:---|
| `references/sources.md` | 官方源清单、API 端点与限流、山寨源识别 |
| `references/upgrade-checklist.md` | 本机（git 安装 + uv venv + 多 cron）升级 SOP、回滚、验证 |

