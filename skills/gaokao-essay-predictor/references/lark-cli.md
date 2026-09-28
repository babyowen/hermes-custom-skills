# gaokao-essay-predictor · 细节全文（由 SKILL.md 拆出 2026-09-28）

> 按需读取；SKILL.md 保留判据与索引。

### lark-cli 维护

lark-cli 需要保持最新，否则 `docs +fetch` / `docs +update` 等命令会出现 `[deprecated] using v1 API` 警告。

- 检查更新：`lark-cli update --check`
- 执行升级：`lark-cli update`
- 当前已升级至 **1.0.47**（2026-06-04）
- **⚠️ v1 警告的实际情况**：`[deprecated] using the v1 API` 警告仍然存在。来自 lark-doc skill 版本而非 lark-cli 本身。功能不受影响。
  - **这不是功能阻塞**：v1 兼容模式下命令仍然正常运行（返回 `"ok": true` 和正确的文档更新结果），警告只是提示信息。
  - **实操建议**：每次 cron 运行开始时执行 `lark-cli update` 保持最新，但不要假设升级后警告会消失。检查 lark-doc skill 是否有 v2 版本：`lark-cli skill view lark-doc`。如果仍有警告，正常执行命令即可，功能不受影响。
- **⚠️ lark-table HTML 标签被剥离（5月30日发现）**：lark-cli 1.0.44 + 同步升级后的 lark-doc skill，在执行 `docs +update` 时不再保留 `<lark-table>`/`<lark-tr>`/`<lark-td>` 标记。更新返回的 `warnings` 中会提示 `[WARNING:UNSUPPORTED_HTML_TAG] unsupported HTML tag removed`。文档内容（文字）仍然完整更新，但表格格式丢失——表格变成纯文本/列表格式。
  - **排查经过**：升级 1.0.43→1.0.44 时 skills 同步更新（26 official, 26 updated），新版 lark-doc skill 不再支持这些私有 HTML 标签。
  - **影响范围**：热点素材库.md 中的「外部预测趋势追踪」表格（lark-table 格式）在更新后失去表格排版，变为纯文本。
  - **当前评估**：内容完整保留（功能不受阻），仅表格视觉效果变差。如果后续 Feishu 文档的表格排版对用户阅读体验至关重要，需关注 lark-doc skill 后续版本是否会恢复 lark-table 支持，或在本地维护两份格式（markdown 版提交飞书，表格版留本地缓存供 agent 读取）。
