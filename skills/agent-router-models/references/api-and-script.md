# 接口与脚本手册（agent-router 模型清单）

## 1. 接口

```
GET http://api.agent-router.cn/v1/models
Authorization: Bearer $AGENT_ROUTER_KEY
```
- 返回结构同 OpenAI：`{"object":"list","data":[{...}]}`，`data[].id` 是模型 ID（**大小写敏感**）。
- 文档：https://www.agent-router.cn/docs （"模型列表"章节）；文档明确要求以该接口为准，不要在客户端硬编码清单。
- 单条目字段（2026-09-22 实测）：`id / object / created / owned_by / mode / max_input_tokens / max_output_tokens / category`。
  - `mode` 部分条目缺失（值为 null）；`category` 恒有（如 `text` / `image`）。
- 实测耗时约 7s（明文 HTTP 聚合网关），脚本超时设 90s。
- 错误码：400 未知模型或参数（核对大小写）/ 401 Key 无效或停用 / 402 余额不足 / 429 限流 / 500·502·504 上游不可用。

凭据文件（600，**不要**把 Key 写进命令行或报告）：
```
~/.hermes/secrets/agent-router.env
AGENT_ROUTER_KEY=sk-...            # 必填
AGENT_ROUTER_BASE=http://api.agent-router.cn/v1
AGENT_ROUTER_DOCS=https://www.agent-router.cn/docs
```

## 2. 脚本 CLI

`scripts/check_models.py`（纯标准库，无第三方依赖，无 pip 需求）

| 参数 | 说明 |
|:--|:--|
| （无参数） | 拉取今日清单 → 写快照 → 与「今天之前最近一次」快照对比 → 输出 JSON |
| `--list` | 仅输出当前清单（含 `models` 明细），不写快照、不对比 |
| `--history` | 列出已有快照日期 |
| `--baseline YYYY-MM-DD` | 强制与指定日期快照对比（测试/补比对用） |
| `--keep N` | 快照保留天数，默认 30 |
| `--cache-dir DIR` | 覆盖缓存目录（测试用，隔离真实快照） |
| `--json` / `--compact` | JSON 输出（默认）/ 单行 JSON |

退出码：`0` 成功；`1` 失败（缺 Key、Key 格式异常、网络错误、HTTP 非 200、响应非 JSON、`data[]` 空、指定基线快照不存在或损坏）。失败时输出 `{"_run_failed": true, "error": ..., "hint": ...}`。

## 3. 输出 JSON 契约

```json
{
  "date": "2026-09-22", "fetched_at": "2026-09-22T22:52:25+08:00",
  "base_url": "http://api.agent-router.cn/v1",
  "total": 31, "by_category": {"image": 4, "text": 27},
  "snapshot_path": ".../snapshots/2026-09-22.json",
  "retention_days": 30, "pruned_snapshots": [],
  "baseline": "2026-09-21", "baseline_age_days": 1, "baseline_count": 31,
  "added": ["glm-5.2"], "removed": ["gpt-7-test"],
  "changed": [{"id": "kimi-k3",
               "fields": {"max_output_tokens": {"from": 128000, "to": 1000000, "label": "输出上限"}}}],
  "unchanged_count": 28,
  "verdict": "changed"
}
```
- `verdict` ∈ `baseline`（首次，附 `models` 明细与 `note`）/ `changed` / `unchanged`。
- 对比字段（`TRACKED`）：`category / mode / owned_by / max_input_tokens / max_output_tokens`。要加字段就改脚本顶部 `TRACKED` 与 `FIELD_CN`，**不要**在 SKILL.md 里另行枚举。
- 快照文件：`{"date","fetched_at","base_url","count","models":{id:{...}}}`，同日重跑覆盖。

## 4. 验收测试

```bash
python3 ~/.hermes/skills/agent-router-models/scripts/selftest.py
```
覆盖 6 项：① 不变场景 verdict=unchanged ② 错误 Key → 401 → exit 1 ③ 主机不可达 → exit 1 ④ 基线快照缺失 → exit 1（不抛裸异常）⑤ `--history`/`--list` 可用 ⑥ `--keep` 生效。全部只读接口、只写 `/tmp`。
> 注意：变更场景（新增/下线/字段变更）无法用真实接口复现，测试用「人工改造的快照」验证；如需再验，令快照基线缺少某个 id、或把某字段改成不同值后重跑即可。

## 5. cron 配置

```yaml
script: agent_router_models.py        # ~/.hermes/scripts/ 下，实体薄包装（cron 拒绝绝对路径/symlink）
skills: [agent-router-models]
schedule: "30 22 * * *"               # 每日 22:30（北京时间）
deliver: "origin"
```
薄包装内容：转调 `~/.hermes/skills/agent-router-models/scripts/check_models.py`，透传 argv 与退出码。技能更新脚本时包装器无需改动。

## 6. 排障
| 症状 | 处理 |
|:--|:--|
| `_run_failed` + `HTTP 401` | Key 失效/被轮换 → 更新 `~/.hermes/secrets/agent-router.env` |
| `HTTP 402` | 网关账户余额不足 |
| `URLError` / 超时 | 网关或网络抖动 → 稍后手动补跑，别重试风暴 |
| 快照目录为空 → 每次都 baseline | 检查 `--cache-dir` 是否被误改 |
| cron 输出里出现 `⚠️ Skill(s) not found` | 同名 skill 冲突（备份目录别放 `~/.hermes/skills/`） |
