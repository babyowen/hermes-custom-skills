# 高考日报执行日志 - 飞书文档 Token

> 每次 cron 执行日报时，将关键过程按时间线写入此文档。
> 用 `lark-cli docs +update --api-version v2 --doc <token> --command append --content '...'` 追加日志。

## 文档信息

- **document_id**: `N8eNdusOvoyMmAxUcY0c6YRpnOb`
- **URL**: https://zesyg4oxfe.feishu.cn/docx/N8eNdusOvoyMmAxUcY0c6YRpnOb
- **身份**: `--as bot`

## 日志格式

每次执行追加一个新章节，按时间线排列：

```xml
<h2>YYYY-MM-DD HH:mm</h2>
<p>[HH:MM:SS] ▶️ 开始执行</p>
<p>[HH:MM:SS] 📖 读取 key-discoveries.md</p>
<p>[HH:MM:SS] 🔍 搜索: "关键词1"<br/>→ 结果摘要</p>
<p>[HH:MM:SS] 🔍 搜索: "关键词2"<br/>→ 结果摘要</p>
<p>[HH:MM:SS] ✅ 决策: 南邮状态→ ...</p>
<p>[HH:MM:SS] 📋 报告正文完成</p>
<p>[HH:MM:SS] 💾 归档 GaokaoWIKI</p>
<p>[HH:MM:SS] 🔄 GitHub 同步</p>
<p>[HH:MM:SS] ✅ 执行结束</p>
```

## 注意事项

- 用 `append` 追加当天章节（在文档末尾），不用修改已有内容
- 每条搜索记录包含：关键词 + 搜索结果摘要（搜到几条、有无新发现）
- 每条决策记录包含：判断依据（为什么维持旧状态/为什么更新）
- 日志不阻塞主流程——append 失败不影响日报生成和推送
- 追加内容不宜过细（每条搜索一句就行），也不宜过粗（不能只写"搜了"不写结果）
