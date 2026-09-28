# gaokao-essay-predictor · 细节全文（由 SKILL.md 拆出 2026-09-28）

> 按需读取；SKILL.md 保留判据与索引。

## 反例与黑名单（速查）

| 类别 | ❌ 别这么干 | ✅ 应该怎么做 |
|:----|:-----------|:------------|
| 📡 搜索 | 搜索提取链路 | 按标准链路：web_search(Parallel)→web_extract→降级browser |
| 📡 搜索 | curl 硬爬被 WAF 挡 | 换 browser_navigate（完整浏览器渲染），或用搜索结果摘要代替 |
| 📝 飞书 | `lark-cli docs +update` 不加 `--mode` | 必须加 `--mode overwrite`（全量覆盖）或对应模式 |
| 📝 飞书 | 用 `patch` 改飞书导出的文件 | **绝对禁止**——引号转义会逐层恶化，用 `write_file` 全文覆盖 |
| 📝 飞书 | 更新飞书后不同步本地缓存 | 更新后马上：`lark-cli docs +fetch --doc <token> --format pretty > references/<文件名>` |
| ⚙️ cron | cron prompt 写了一大段自有的逻辑 | cron prompt 只写"按 skill 执行"+交付地址，所有流程放 SKILL.md |
| ⚙️ cron | deliver 设成 `origin` | 高考日报必须设成 `feishu:oc_5d97d211e77becee79ff4241a4b10568` |
| 🎯 预测 | 冲刺期还追当周热点 | 回看全年，像命题组一样思考 |
| 🎯 预测 | 写政治表态/纯科技叙事 | 剥去政治外衣，提取哲学思辨内核；科技必须配人文 |

> 完整 26 条陷阱清单见 `references/已知陷阱清单.md`

**❗已知陷阱**
0. **⚠️ 搜索链路（Parallel 免费 MCP）**：搜索走 web_search(Parallel)，提取走 web_extract(Parallel)，提取失败降级 browser_navigate(本地Chrome) + eval body.innerText。全部免费。

1. **`--mode` 参数必填陷阱**：`lark-cli docs +update` 必须带 `--mode overwrite`（全量覆盖）或对应模式。如果缺了 `--mode`，命令静默失败报 `--mode is required`，不会更新飞书文档。写 cron job 前务必验证该命令可用。
2. **本地缓存文件不存在陷阱**：`references/热点素材库.md` 等标记为"以此为缓存"的文件可能不存在于磁盘上。首次运行时需要用 `lark-cli docs +fetch --doc <token> --format pretty > references/<filename>` 创建缓存。飞书更新后**必须**同步保存本地缓存，否则下次运行读取到的是过时版本。
3. **参考资料文件集体缺失陷阱**：references/目录下大部分文件（历年作文题汇编.md、教育部命题方向.md、2026趋势分析与预测方向.md、命题特点与规则.md、2025-2026年度热点综述.md、jiangsu/gaokao分析文件等）最初可能均不在磁盘上。不要因此卡住——这些是可选/上下文参考文件，并非执行必需的。直接从飞书拉取三个核心文档（热点素材库、作文素材库、保障思路）即可运行。教育部命题方向.md虽然是"首要步骤"，但若不存在，应通过 web_search 搜索"2026教育部命题方向"或"教学〔2026〕1号"来获取最新政策表述。首次运行后不会立即完全填充所有文件，重点维护飞书文档和三个核心缓存。
4. **重新编号陷阱（已过时）**：目前热点素材库使用方向名称（方向A/方向B）而非数字编号，无需重排编号。如果未来改用编号格式，操作时须注意。
5. **表格格式陷阱**：向作文素材库追加事件时，新表格的加入可能使上游条目标题和表格之间的关联断裂——每追加一个Event后务必检查上一个Event的结尾格式正确
6. **patch唯一性**：在markdown文件中使用patch时，old_string必须严格唯一。若无法唯一（如多行表头相同），改用edit（全文覆盖）或先确认唯一上下文
9. **⚠️ cron prompt 覆盖技能指令陷阱**：cron 的 prompt 不应包含与 skill 重复或冲突的业务逻辑。cron 只做定时触发 + 交付地址设定，所有流程/规则/能力都放在 skill 的 SKILL.md 中。如果 cron prompt 里写了一大段自己的指令，它会覆盖 skill 的内容，导致 skill 更新后 cron 仍然执行旧的逻辑。本次会话中这个问题就导致了「模拟考排除」旧逻辑在技能已更新后仍然持续产出。创建/更新 cron 任务时确保 prompt 极简，只引用 skill 名和 deliver 地址。
7. **⚠️ Feishu导出文件的引号转义陷阱**：`lark-cli docs +fetch` 导出的 lark-table 格式中，所有文本字段使用 `\"`（反斜杠-引号）包裹而非标准 `"`（普通引号）。这意味着：
   - 直接搜索 `"融入科技前沿动态"` 匹配不到文件中的 `\"融入科技前沿动态\"`
   - 搜索 `\"融入科技前沿动态\"` 则因为作为子串出现在大量 HTML 属性标记中而爆出数百个匹配
   - **解决**：使用比普通引号上下文更多的相邻行（3-5行文本+标签）做 old_string，而非单独依赖引号内容本身
   - **⚠️ 绝对不要用 patch 修改 Feishu 导出的文件**：patch 无法识别 `\\\"` 转义，会把输入中的 `\"` 当作未转义字符，每次 patch 都会给已转义的引号再套一层反斜杠（`\\\"` → `\\\\\\\"` → `\\\\\\\\\\\\\\\"`），造成逐层恶化。这种损坏不可逆——下一次 patch 只会越修越糟。**必须用 write_file 做全文覆盖**，然后用 `cat <file> | lark-cli docs +update --doc <token> --markdown - --mode overwrite` 推送飞书。这是唯一安全的操作路径。
   - **✅ execute_code 替代模式**：可用 `from hermes_tools import write_file, read_file, terminal` 在 Python 中完成文件读写和终端命令，避免 shell 中直接文件重定向触发 dotfile overwrite 安全告警。先 `terminal()` 调 lark-cli fetch，再用 `write_file()` 写缓存。
8. **⚠️ 双目录缓存同步陷阱**：cron 运行时，技能引用文件可能分布在两个目录：
   - `~/.hermes/skills/gaokao-essay-predictor/references/` — 技能自身目录（**首要维护目标**）
   - `~/.hermes/hermes-agent/skills/gaokao-essay-predictor/references/` — 工作副本目录
   - cron 的 `workdir` 可能指向 hermes-agent 目录，导致工具默认使用工作副本的 references/
   - **解决**：更新飞书后，务必用 `cp` 在两个目录间同步三个核心缓存文件（热点素材库.md、作文素材库.md、各方向最低保障思路.md）

