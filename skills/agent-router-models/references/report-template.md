# 报告模板与推送命令

## 图标字典
| 图标 | 语义 |
|:--|:--|
| 🟢 | 与基线一致，无变化 |
| 🟡 | 有变化（新增/下线/能力变更） |
| 🔴 | 在用配置受影响（主模型/fallback 已不在架） |
| ⚪ | 已建立基线（首次运行，无对比） |
| ⛔ | 取数失败，监测受阻 |
| 🆕 / ❌ / 📈 / ➖ | 新增 / 下线 / 字段变化 / 无变化 |
| 📌 | 需处理（无则整行省略） |
| 🧭 | 边界说明 |

## 模板（填占位符，不许留 `{}`）

### 1. 有变化（changed）
```
<【agent-router 模型清单｜{{date}}】> 🟡 有变化
📊 当前 {{total}} 个（text {{n}} ｜ image {{n}}）｜ 对比基线 {{baseline}}（{{age}} 天前）
🆕 新增 {{n}}：{{id1、id2}}            ← 无则整行写「无」
❌ 下线 {{n}}：{{id1、id2}}            ← 无则整行写「无」
📈 能力变更 {{n}}：
 · {{id}} {{字段中文}} {{旧值}} → {{新值}}
📌 需处理：{{哪个在用模型不在架 + 建议换哪个在架模型}}   ← 无则整行省略
🧭 边界：仅对比网关 /v1/models 返回值，未做真实调用连通性测试
```
每段超过 5 个条目时写「等 N 个」，不要堆满整屏。

### 2. 无变化（unchanged）
```
<【agent-router 模型清单｜{{date}}】> 🟢 无变化
📊 {{total}} 个（text {{n}} ｜ image {{n}}）｜ 与基线 {{baseline}} 完全一致
✅ 在用主模型 {{model}} 在架 ｜ fallback {{fallback}} 在架
🧭 边界：仅对比 /v1/models 返回值
```

### 3. 首次运行（baseline）
```
<【agent-router 模型清单｜{{date}}】> ⚪ 已建基线
📊 当前 {{total}} 个（text {{n}} ｜ image {{n}}），快照已落盘
ℹ️ 无历史快照可比，明日起报变化
```

### 4. 取数失败（_run_failed）
```
<【agent-router 模型清单｜{{date}}】> ⛔ 监测受阻
❌ {{error}}           ← 例：HTTP 401（Key 无效或已停用）
📌 建议：{{401→检查 ~/.hermes/secrets/agent-router.env 的 Key；402→控制台充值；429→次日重试；网络/超时→稍后手动补跑}}
（未取到数据，本次不报清单变化）
```

## 推送命令（**可选**）
默认路径是**系统投递**（把报告正文作为最终回复发出，cron 的 `deliver` 负责投递）——单条消息、不依赖 terminal，是当前 cron job 的配置。
只有需要幂等防重（会被手动补跑）或原生 post 排版时，才改用下面这条；此时最终回复只写一句确认语，**不要**再同时回复全文。
cron 环境变量可能未导出，先从 `~/.hermes/.env` 取：
```bash
export FEISHU_HOME_CHANNEL=$(grep '^FEISHU_HOME_CHANNEL=' ~/.hermes/.env | cut -d= -f2-)
lark-cli im +messages-send --chat-id "$FEISHU_HOME_CHANNEL" --as bot \
  --markdown "$(cat /tmp/agent_router_models_{{date}}.md)" \
  --idempotency-key "agent-router-models-{{date}}"
```
- 核对返回 `ok:true` ＋ `message_id` 才算「已通知」；状态不明不盲目重发（同 key 防重）。
- 内容超 400 字用 `lark-cli im +messages-edit --as bot --message-id <om_> --markdown …` **原地压缩**，不要发第二条。
- 飞书不渲染 Markdown 表格 → 一律「｜」分隔的一行式。
