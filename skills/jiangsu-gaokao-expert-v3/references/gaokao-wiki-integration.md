# GaokaoWIKI 知识库集成参考

## 仓库信息
- **URL**: https://github.com/babyowen/GaokaoWIKI
- **本地路径**: ~/GaokaoWIKI/
- **分支**: master
- **认证方式**: HTTPS + .netrc（已配置 PAT）
- **CLAUDE.md**: 遵循 Karpathy 风格的三层架构（raw/ + wiki/ + CLAUDE.md）

## 目录结构
```
GaokaoWIKI/
├── CLAUDE.md           # Schema 文件，定义入库规则
├── index.md            # 内容索引
├── log.md              # 操作日志（append-only）
├── raw/
│   ├── 日报/           # <-- 日报归档位置
│   ├── inbox/          # 人工投放入口
│   ├── 政策文件/
│   ├── 院校资料/
│   ├── 录取数据/
│   └── 经验分享/
├── wiki/
│   ├── 升学路径/       # 强基计划、综合评价等
│   ├── 院校库/         # 各大学页面
│   ├── 专业百科/
│   ├── 省份政策/
│   └── 填报策略/
```

## 日报归档规则
- 文件名：`YYYY-MM-DD-高考决策情报日报.md`
- 存放到：`raw/日报/`
- 更新 index.md（添加日报章节索引）
- 追加 log.md（记录归档操作）
- git add/commit/push 到 master 分支

## Git 操作注意事项
- 使用 subprocess.run() 执行 git 命令
- commit message 格式: `[daily] YYYY-MM-DD 高考决策情报日报自动归档`
- push 失败不阻塞，下次自动重试
- .netrc 已配置在 ~/.netrc，无需额外认证

## 已存在的相关 wiki 页面
以下页面与高考日报重叠，日报中的关键信息可以考虑更新它们（但不是强制要求，日报优先）：
- wiki/院校库/南方科技大学.md
- wiki/院校库/香港中文大学（深圳）.md
- wiki/院校库/南京邮电大学.md
- wiki/升学路径/强基计划.md
- wiki/升学路径/综合评价.md
- wiki/省份政策/江苏省.md

## 与 llm-wiki 技能的关系
本知识库遵循 Karpathy's LLM Wiki 模式（见 research/llm-wiki skill）。
日报只做归档，不创建实体/概念页面。如果日报中发现了值得长期留存的信息
（如某校最新招生计划、位次变化），可参考 llm-wiki 的 Ingest 流程入库。
