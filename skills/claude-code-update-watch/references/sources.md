# Claude Code 更新数据源与字段细节

## 1. 官方端点（脚本已内置，人工排查时对照用）

| 用途 | 端点 | 说明 |
|:---|:---|:---|
| 最新版本（轻量） | `https://registry.npmjs.org/@anthropic-ai/claude-code/latest` | 3.3KB，只给 latest 的 manifest |
| **版本表 + 时间 + 通道**（主源） | `https://registry.npmjs.org/@anthropic-ai/claude-code` | packument，实测 1.4MB；`dist-tags` 给三通道，`time{}` 给每个版本的发布时间 |
| **逐版本 changelog**（主源） | `https://api.github.com/repos/anthropics/claude-code/releases?per_page=25` | 每个 release 的 `body` 就是该版 changelog；未认证限流 60 次/小时（脚本一次请求，用 `GITHUB_TOKEN`/`GH_TOKEN` 可提到 5000） |
| 回退 changelog | `https://raw.githubusercontent.com/anthropics/claude-code/main/CHANGELOG.md` | 实测 838KB，全量历史；`## <version>` 分段 |
| 官方文档入口 | `https://docs.claude.com/en/release-notes/claude-code` | ⚠️ 实为 GitHub 页面镜像（返回 HTML，`meta.title` 就是 "claude-code/CHANGELOG.md at main"），不要当独立信源 |

## 2. 三个发布通道（`dist-tags`）

实测 2026-09-29：`{'stable': '2.1.277', 'latest': '2.1.284', 'next': '2.1.284'}`

- `latest` —— `npm i -g @anthropic-ai/claude-code` 装到的就是它，发版最快
- `stable` —— 更保守的通道，实测落后 latest 约 7 个版本（1 周左右的量）
- `next` —— 预发布通道。**不要向用户推荐**；`prerelease=true` 的 release 已在脚本里单独标记

判断用户在哪条通道：`local.version` == `channel.stable` → stable 通道；== `channel.latest` → latest 通道；都不是且低于 latest → 只是没更新。

## 3. 发布节奏（评估"要不要追"的依据）

实测 2026-09-29：近 7 天 5 个版本、近 30 天 26 个版本、中位间隔 **0.98 天**；单版本要点数常见 60~180 条（脚本按 `MAX_BULLETS_PER_VERSION=60` 截断，省略数进 `bullets_omitted`）。

结论：Claude Code 是**日更级**项目，追版本没意义；周报的作用是筛出"有安全/成本/破坏性变化"的那几版。

## 4. 要点分类规则（脚本 `_classify`）

按"开头动词"定主类，避免 `Fixed … are no longer …` 被误判为破坏性：

| 类 | 判定 |
|:---|:---|
| `fix` / `security` | 以 `Fixed/Fixes/Repaired/Resolved/Restored/Corrected` 开头；命中凭据/权限/sandbox/security/CVE 等词归 `security` |
| `breaking` | 命中强信号：`breaking`、`removed`、`remove the`、`deprecat`、`renamed`、`must now`、`now requires`、`migration`、`default changed`、`dropped support`、`no longer supported/accepts/works` |
| `security` | 凭据/密钥/权限/sandbox/CVE/注入类（非 fix 开头） |
| `feature` | `Added`、`New`、`Introduced`、`Support for`、`Can now` |
| `change` | `Improved`、`Changed`、`Updated`、`Reworked`、`Replaced`、`now defaults` |
| `other` | 其余 |

`importance_score = 3×breaking + 2×security + 影响面命中数 + feature`，**只用于排序**，不是结论。

注意：`no longer` 曾被当作破坏性信号，实测误报率极高（大量 `Fixed … are no longer …`），已从标记表移除——只在 `no longer supported/accepts/works` 这类强搭配上算破坏性。

## 5. 本机版本探测（备用，**当前周报不使用**）

⚠️ 用户明确要求：判据只看"本周的更新值不值得升"，**不看本机装了什么版本**。因此 `local` / `behind_latest` / `pending[]` 在周报里一律忽略。以下探测逻辑仅为保留能力，只有用户主动问"我这台落后多少"时才用。

1. `command -v claude && claude --version` → 正则取 `x.y.z`
2. `npm ls -g --depth=0 @anthropic-ai/claude-code --json`（`npm` 与 `~/.hermes/node/bin/npm` 都试）
3. `~/.claude/local/node_modules/@anthropic-ai/claude-code/package.json`（Claude Code 的 local install 布局）
4. `~/.hermes/cache/claude-code-update-watch/local_version.txt`（**跨机覆盖**：用户在别的电脑上用 Claude Code 时，把版本写进去即可）
5. `--local-version X.Y.Z` 命令行覆盖（优先级最高）

实测这台服务器上没有安装 Claude Code（`not_detected`）。**任何情况下都不许编造本机版本号**；周报也不提这件事（铁律 1）。

## 6. 状态文件与防重复

`~/.hermes/cache/claude-code-update-watch/state.json`：

```json
{"reported_versions": [...], "last_report_at": "...", "last_latest": "2.1.284", "last_local": null}
```

- 保留最近 60 个版本（`MAX_VERSIONS_IN_STATE`）
- `state.new_versions_since_last_report` 为空 = 本周没有新版本，报告应写"本周无新版本"而不是重复上一周的内容
- **首次运行**（`reported_versions` 为空）→ `state.first_run=true`，报告给一段盘点
- 想重放历史窗口：`--no-state`（不读写状态）

## 7. 失败与降级

- npm 挂 → `channel` 为空、`behind_latest=null`，但 GitHub 的 changelog 仍可用；报告要写"⚠️ 版本表来源失败"
- GitHub 挂 → 自动回退 raw CHANGELOG.md（此时没有发布时间，`published_at` 取自 npm `time`；两处都没有则 `null`，报告里写"发布时间未知"）
- 三个源全挂 → 脚本 `_run_failed=true` + exit 1，报告只写失败原因
- `errors[]` 非空但 `_run_failed=false`：正常出报，末尾附一行降级说明
