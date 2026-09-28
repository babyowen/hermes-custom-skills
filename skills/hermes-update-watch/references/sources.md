# 官方源清单 & 山寨源识别

> 最后核对：2026-09-28（实测可用）

## ✅ 官方源（只信这些）

| 用途 | 地址 |
|:---|:---|
| 代码仓库 | `https://github.com/NousResearch/hermes-agent` |
| 发布说明 | `https://api.github.com/repos/NousResearch/hermes-agent/releases?per_page=N` |
| 两个 tag 之间的全部提交 | `https://github.com/NousResearch/hermes-agent/compare/vX...vY`（`/compare/vX...vY.diff` 更省 token） |
| 官方文档 | `https://hermes-agent.nousresearch.com/docs/` |
| 文档 LLM 入口 | `/docs/llms.txt`（~17KB 全站索引）、`/docs/llms-full.txt`（~1.8MB 全文） |
| 远程 tag 列表 | `https://api.github.com/repos/NousResearch/hermes-agent/tags?per_page=N` |
| 安装脚本 | `https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh` |

## 🚫 山寨/社区源（不要采信）

搜索引擎首页会混进同名仓，都是**第三方**，内容可能滞后或改写：

- `github.com/hermes-agent-us/hermes-agent`
- `github.com/hermes-agent-org/hermes`
- `hermes-ai.net`（自称"非官方社区指南"，release 摘要可作交叉参考，**不作为数据源**）

判断法：**owner 必须是 `NousResearch`，文档域必须是 `hermes-agent.nousresearch.com`**。

## API 限流与请求预算

- 未认证：**60 次/小时/IP**；带 `GITHUB_TOKEN` / `GH_TOKEN` 环境变量则 5000 次/小时（脚本自动识别，没有 token 也能跑）
- 本技能每次运行只用 **2 个请求**（`/releases` + `/tags`），不会触限流
- 403 + `rate limit` → 脚本会在 `errors[]` 里写明原因；报告里标注 ⚠️ 并跳过本周，不编内容

## 发布节奏（用于判断"周报有没有货"）

- **周级 patch tag**：形如 `v2026.9.7` → `v2026.9.11` → `v2026.9.14` → `v2026.9.21` → `v2026.9.24`
- 版本号是双轨的：语义版本（`v0.21.4`）+ 日期 tag（`v2026.9.21`），**别拿两套号直接比大小**
- patch release 的 body 常常只写"rolls up ~N PRs since vX"——真实内容在 `compare/vX...vY` 里
- **策展版发布说明**（highlights / feature areas / 完整贡献者名单）随大版本一起发（如 v0.22.0 覆盖 v0.21.0 起全部内容）。若某周只有 patch tag，报告不必硬凑要点
- Docker / Hermes Cloud 用同一 tag 构建：`nousresearch/hermes-agent:vYYYY.M.D`

## 备用取数（API 全挂时）

1. `https://raw.githubusercontent.com/NousResearch/hermes-agent/main/pyproject.toml` → `version` 字段（粗判最新版本号）
2. release 页 HTML：`https://github.com/NousResearch/hermes-agent/releases`（web_extract 可读）
3. 官方文档站 release/更新相关页（`/docs/` 首页 Quick Links）

> 备用源只用于确认"有没有新版本"，要点仍以官方 API body 为准。
