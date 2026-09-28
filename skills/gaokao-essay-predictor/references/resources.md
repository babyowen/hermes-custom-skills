# gaokao-essay-predictor · 细节全文（由 SKILL.md 拆出 2026-09-28）

> 按需读取；SKILL.md 保留判据与索引。

### 参考资料库

| 文件 | 说明 |
|:----|:------|
| `references/历年作文题汇编.md` | 2016-2025年完整作文题原文（多源交叉验证） |
| `references/jiangsu_gaokao_essay_analysis_2016_2020.md` | 江苏卷时期权威解析+高分作文特点 |
| `references/gaokao_essay_analysis_2021_2025.md` | 新高考I卷时期官方评析+高分作文特点 |
| `references/2025-2026年度热点综述.md` | 全年28个热点事件+作文切入角度 |
| `references/2026趋势分析与预测方向.md` | 10年规律→4个预测方向+低概率方向（更新于2026-05-22） |
| `references/命题特点与规则.md` | 高考命题原则+注意事项（2026年更新） |
| **`references/教育部命题方向.md`** | **⚠️ 预测依据：教学〔2026〕1号原文+三大核心要求+官方命题原则** |
| `references/热点素材库.md` | 按可考性排序的动态热点库 — **⚠️ 已迁移至飞书，以此为缓存** |
| `references/作文素材库.md` | 可复用素材库（金句+人物+事件+适用度速查） — **⚠️ 已迁移至飞书，以此为缓存** |
| `references/各方向最低保障思路.md` | 考场上时间不够时的保底方案 — **⚠️ 已迁移至飞书，以此为缓存** |
| **`references/2025-2026整数纪念年清单.md`** | **✅ 新增 — 整数纪念年起点数据：已确认+待验证的周年事件+思辨角度速查** |


### 飞书文档映射

每天动态更新的三个文档已迁移到飞书，用户可通过链接直接查看。cron 运行时使用飞书 CLI 读取和更新。

| 文档 | doc_token | 飞书链接 |
|:----|:----------|:---------|
| 📂 高考作文预测（文件夹） | U8DUfCMCelQxXBdy0CLcFHOhnN8 | https://www.feishu.cn/drive/folder/U8DUfCMCelQxXBdy0CLcFHOhnN8 |
| 📊 热点素材库 | LBVKdoNRYoXk62xreFucshXNnUe | 在文件夹中 |
| 📝 作文素材库 | NrOLd6DQoo8tv6xF6VQcOFQ6npg | 在文件夹中 |
| 🛡️ 保障思路 | Ss40dKnasoh6OVxhXiTcJaKZnme | 在文件夹中 |

操作方法：
- **读取**：`lark-cli docs +fetch --doc <token> --format pretty`
- **更新（全量覆盖）**：`cat <file> | lark-cli docs +update --doc <token> --markdown - --mode overwrite`
  ⚠️ **必须加 `--mode overwrite`，否则报错 `--mode is required`！** 后续如需追加/部分替换，改用 `--mode append` 或 `--mode replace_range`。
- **读取后保存本地缓存**：`lark-cli docs +fetch --doc <token> --format pretty > references/<文件名>`
  （飞书更新后务必同步保存本地缓存文件，保持两者一致）
- ⏱ **每次更新素材库内容时，必须在对应条目末尾或文档顶部标注更新日期**，如 `（更新于2026-05-22）`，让用户知道内容的新鲜程度

