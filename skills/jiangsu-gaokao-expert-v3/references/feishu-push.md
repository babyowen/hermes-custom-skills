# 飞书推送参考

## 前置条件

- `lark-cli` 已安装并配置（通过 `npm install -g @larksuite/cli`）
- `~/.hermes/.env` 中包含：
  - `FEISHU_APP_ID` — 应用 ID
  - `FEISHU_APP_SECRET` — 应用密钥
  - `FEISHU_DOMAIN=feishu`
  - `FEISHU_HOME_CHANNEL` — 首页频道 chat_id（`oc_` 开头）

## 发送日报到首页频道

### 方式一：Markdown 消息（推荐）

```bash
CHAT_ID="oc_4b7bc3b652e8b27c8a3c683fa4b53aa0"
lark-cli im +messages-send \
  --chat-id "$CHAT_ID" \
  --markdown "$(cat /tmp/daily_report.md)" \
  --as bot
```

### 方式二：Post（富文本）消息（用于更复杂的排版）

```bash
lark-cli im +messages-send \
  --chat-id "$CHAT_ID" \
  --content '{"zh_cn":{"title":"高考决策情报日报","content":[[{"tag":"text","text":"日报内容"}]]}}' \
  --msg-type post \
  --as bot
```

## Markdown 格式注意事项

### 支持
- 标题 `**粗体**` — 支持
- 列表 `- item` — 支持
- 分隔线 `---` — 支持
- 换行 — 支持（保留原文换行）
- 链接 `[text](url)` — 支持
- 行内代码 — 部分支持

### 不支持
- 表格 `| col | col |` — ❌ 会被渲染成文本
- 代码块 ` ``` ` — ❌ 会被渲染成文本
- 多级嵌套缩进列表 — 不稳定

**建议**：日报中的表格和代码块用纯文本方式呈现（如换行对齐），不要在 Markdown 中使用。

## 身份说明

| 身份 | 何时可用 | 限制 |
|------|----------|------|
| `--as bot` | 始终可用 | 只能发送到 bot 所在的群聊 |
| `--as user` | 用户 token 未过期 | 可发送私聊和其他群 |

当前配置中，bot 身份一直在有效期（tenant token 不设用户级过期），
而 user 身份 token 约 7 天过期。日报发送应始终使用 `--as bot`。

## 验证发送结果

成功响应：
```json
{
  "ok": true,
  "identity": "bot",
  "data": {
    "chat_id": "oc_4b7bc3b652e8b27c8a3c683fa4b53aa0",
    "create_time": "2026-05-06 20:29:56",
    "message_id": "om_x100b50870a884d3cc36d55d1eadf0fe"
  }
}
```

### ⚠️ 已知陷阱：版本更新通知干扰 JSON 解析

当 lark-cli 有新版可用时，`stdout` 中会插入一段版本更新提示（如 `"latest": "1.0.32"`, `"message": "lark-cli 1.0.32 available"`），这会**破坏 JSON 结构**导致 `python3 -m json.tool` 解析失败。

**正确做法**：不要用 python json 解析完整输出，而是用 `grep` 直接检查关键字段：

```bash
# ✅ 稳妥：直接用 grep 检查 ok 字段
lark-cli im +messages-send ... 2>&1 | grep -q '"ok": true' && echo "✅ 成功" || echo "⚠️ 失败"

# ✅ 或者 tail 只看最后几行（避开版本通知）
lark-cli im +messages-send ... 2>&1 | tail -5
```

**错误示范**（会被版本通知破坏）：
```bash
# ❌ 版本通知会使 JSON 解析失败
lark-cli im +messages-send ... 2>&1 | python3 -m json.tool
```

## 故障处理

| 错误 | 原因 | 解决 |
|------|------|------|
| `token expired` | user 身份过期 | 改用 `--as bot` |
| `chat not found` | bot 不在该群聊 | 检查 FEISHU_HOME_CHANNEL，确认 bot 已加入 |
| `permission denied` | 权限不够 | 检查飞书应用权限配置 |

### 排查 bot 可见聊天

如果 bot 身份下 `lark-cli im +messages-send` 返回空结果或找不到聊天：

```bash
# 列出 bot 可见的所有聊天（机器人只能看到自己在的群）
lark-cli im chats list

# 按群名关键词搜索 chat_id
lark-cli im +chat-search --query "高考"

# 搜索返回空列表说明 bot 未加入任何可见群
# 解决方法：在飞书客户端将 bot 拉入目标群
# 之后 lark-cli 会自动刷新 token，无需重启
```

### ⚠️ 已知陷阱：chat-search 不可靠

`lark-cli im +chat-search --query "" | grep -q "$FEISHU_HOME_CHANNEL"` **不能可靠判断 bot 是否能发送消息**。实际测试发现：即便 chat-search 返回空（grep 找不到目标），`messages-send` 仍然可能成功返回 `{"ok": true}`。

**正确做法**：不提前做 chat-search 验证，直接发送 message 并根据返回 JSON 判断。SKILL.md 中的前置检查已移除 chat-search 步骤。

### 检查环境变量

```bash
# 检查 FEISHU_HOME_CHANNEL 是否设置
echo "${FEISHU_HOME_CHANNEL:-未设置}"

# 检查 lark-cli 认证状态
lark-cli im +chat-search --query "" --as bot
```

## 飞书推送不阻塞原则

- 飞书推送失败**不阻塞**日报生成流程
- 日报归档到 GaokaoWIKI 是硬性要求，飞书推送是软性通知
- 推送失败时在 log.md 中记录即可，下次自动重试
