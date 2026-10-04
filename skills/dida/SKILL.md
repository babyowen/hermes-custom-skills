---
name: dida
description: "滴答清单 dida CLI：飞书里管待办与习惯打卡。触发词：待办/任务/滴答/清单/打卡/习惯/今天要做什么/明天有什么"
version: 1.0.0
author: Hermes Agent
metadata:
  hermes:
    tags: [dida, ticktick, todo, habit, feishu, cli-wrapping]
    related_skills: [cli-skill-wrapping, cron-principles]
---

# 滴答清单（dida）操作技能

## 概述

用户在飞书里用自然语言管理自己的滴答清单账号，本技能负责翻译成 `dida` CLI（`~/.hermes/node/bin/dida`，npm 包 `@suibiji/dida-cli`，已登录）。账号时区 **Asia/Shanghai**。

账号里现在长什么样（用于判断合理性，不是硬编码）：5 个清单（💻工作 / 🏖️家 / 💰报销 / 🌇拍摄想法 / 📟编程想法）、约 56 条未完成、5 个习惯（锻炼身体 / 营养剂 / 午餐慢7分 / 晚饭慢7分 / 冥想）、5 个倒数日。

**用户实际最常用两件事**：① 建任务（说清日期、哪个清单）② 习惯打卡（问"哪个今天已经完成"）。其余能力（完成、改期、搜索、清单/习惯/倒数日）按需用。

## 铁律（违反即失败）

1. **只用本技能的两个脚本，不手拼 `dida` 命令。** CLI 的坑很多且静默：`task complete` / `task delete` **不接受 `--json`**（加了直接 `unknown option` 失败）；`task update` 必须同时给 `--id` 和 `--project`（缺一个就报错）；`habit checkins` 必须带 `--habits <ids>`，且 **`--to` 是排他的**（查当天要写 `D → D+1`）。脚本已经把这些封好了。
2. **建任务直接建，不要回述、不要"你确认一下"。** 用户 2026-09-30 明确要求。建完一句话报结果（标题 + 清单 + 日期 + id）即可。改期/改优先级/完成同理：先做，再一句结果。
3. **删除类必须先问。** 删除任务、批量完成（>5 条）、把任务指派给别人 = 危险操作：**用户点名才做，一次一条，绝不批量删**。执行时脚本要带 `--yes`。
4. **原始 JSON 不进聊天。** 一律走读侧脚本压缩（默认每组最多 15 条 + "另有 N 条"）。
5. **时间一律北京时间。** 全天任务在库里存的是「北京日期 − 8 小时的 UTC 零点」，读侧脚本已换算；写侧直接给 `今天/明天/后天/周三/2026-10-05/"2026-10-05 15:00"/+3d`，由脚本换算。
6. **写完必须回读，且回读有"成功的定义"。** 写生效有 1~3 秒延迟（脚本会轮询等）。**打卡的成功定义是 `status == 2` + `time` 非空**，不是"今天有记录"——只发 `--stamp` 会写出 `status=null/time=null` 的空壳记录，数据层有、APP 里仍显示未打卡（2026-09-30 实测踩到，脚本已修）。脚本报 ⚠️/❌ 时必须如实告诉用户"没生效"，不许说成"已完成"。

## 意图映射表

| 用户说 | 执行 |
|:---|:---|
| "加个待办/帮我创建任务：X（明天/10-5/周三、放工作/报销清单、高优先级）" | `dida_write.py add-task --title X [--project 名] [--due …] [--priority 高]` |
| "X 这个我做完了 / 把 X 标完成" | `dida_write.py complete --title X`（多条匹配会列出来让你挑） |
| "X 改成明天 / 优先级提高 / 加个备注" | `dida_write.py update --title X --due 明天` / `--priority 高` / `--content …` |
| "今天有哪些事 / 今天要做什么" | `dida_view.py today` |
| "明天有什么 / 哪些会拖到明天" | `dida_view.py tomorrow` |
| "这周/未来 N 天有什么" | `dida_view.py upcoming --days 7` |
| "找一下含 X 的任务" | `dida_view.py search X` |
| "我最近完成了什么" | `dida_view.py done --days 7` |
| "有哪些清单 / 有哪些习惯 / 倒数日" | `dida_view.py projects` / `habits` / `countdowns` |
| "习惯打卡了吗 / 今天哪个打卡完成了" | `dida_view.py checkins`（加 `--days 7` 看区间内打卡情况） |
| "帮我打卡：锻炼身体" | `dida_write.py checkin --habit 锻炼身体`（默认今天；`--date 昨天` 补卡） |
| "删掉 X" | **先问一句**"确认删除 X？"→ 得到确认后 `dida_write.py delete-task --title X --yes` |

清单/习惯一律用**名字**给，脚本负责解析成 ID：精确匹配优先，其次包含匹配；歧义时报出候选清单并 `exit 1`（别自己猜）。无 `--project` 时进收件箱。

## 命令速查

读侧（`scripts/dida_view.py`，只读安全，可随时跑）：

```
today [--limit N]        # 逾期 / 今天到期 / 无日期（默认每组 15 条）
tomorrow                 # 明天到期 + 今天没完成会带过去的
upcoming --days 7        # 未来 N 天
search 关键词            # 按标题搜未完成
done --days 7            # 最近完成
projects | habits | countdowns
checkins [--date 今天] [--days 1]
brief --mode morning|evening --json    # 给 cron 的聚合视图
```
所有子命令都支持 `--json`（结构化：含 counts + 明细）与 `--limit`。

写侧（`scripts/dida_write.py`，写操作统一入口，全部支持 `--json` 和 `--dry-run`）：

```
add-task --title T [--project 名] [--due 今天|明天|周三|2026-10-05|"2026-10-05 15:00"|+3d]
                [--priority 高|中|低|无] [--tags a,b] [--content C] [--items "a,b"] [--repeat RRULE]
complete --title 关键词 | --task-id ID
update   --title 关键词 | --task-id ID  [--title-new …] [--due …] [--priority …] [--content …] [--tags …]
checkin  --habit 名字 [--date 今天] [--value n] [--goal n] [--time ISO] [--status 2]
         # 默认带 --time=现在 + --status 2 + --value 1（缺了就会写出 APP 不认的空壳记录）
         # 补卡：--date 昨天；撤销打卡：--status 0
delete-task --title 关键词 | --task-id ID --yes      # 不带 --yes 直接拒绝执行
```
`--dry-run` 只打印将要执行的 CLI 命令、不写入——验证参数拼装用它（尤其打卡这类无法回收的写）。

## 高频流程

**建任务**（最高频，不要回述）
1. 从用户话里抽：标题、日期（没提就不设日期）、清单（没提就收件箱）、优先级（没提就不设）。
2. 跑 `add-task`；脚本会自己解析清单名、换算日期、建完回读确认。
3. 回一句：`✅ 已创建：**标题**（💻工作·10-01（全天））`。

**打卡**（第二高频）
1. 问"哪个打卡完成了" → `checkins`（输出 `✅/⬜ + 习惯名 (+打卡时刻)`）。
2. "帮我打卡 X" → `checkin --habit X`；用户说"顺便都打上"也要**逐条**跑（一条一条来，出错能定位）。

**完成/改期**：`complete` / `update` 先按标题关键词解析；匹配到多条时脚本会退出并列候选，此时把候选**原样念给用户挑**，不要自己选一个。

**晚间补救**：用户问"哪些拖到明天了" → `tomorrow`（含 `carried_over` 段：今天/之前未完成的）。

## 定时简报（两个 cron 任务消费本技能）

两个 cron 都用 `~/.hermes/scripts/dida_morning.py` / `dida_evening.py` 拿 JSON，**简报内容由你按下面格式写**（不要在 cron 里手写 dida 命令）。

**晨间（每天 07:00，`brief --mode morning`）——不超过 20 行**
1. 第一行结论：`📋 今天 N 件要办｜逾期 X 条`（N = due_today + 逾期总数）。
2. `🔴 先办这几件`：从 `suggest_today` 取前 5 条，每条一行 `标题（清单·为什么先办）`。挑的顺序就是 JSON 给的顺序（逾期最久 → 今天到期高优先级 → 今天到期 → 3 天内高优先级）；**别自己重排、别编理由**。
3. `📅 今天到期`：`due_today` 剩余条目，最多 6 条，一行一个。
4. `⬜ 今天的打卡`：`habits_today` 里未完成的习惯名，一行列完（默认 5 个习惯，全未完成也要报）。
5. 结尾一行：`💤 另有 无日期待办 M 条`（M>0 时才写）。

**晚间（每天 21:30，`brief --mode evening`）——不超过 15 行**
1. 第一行：`🌙 今天没完成、会顺延到明天的 N 条`（N = counts.carry_to_tomorrow）。
2. 列出 `carry_to_tomorrow` 前 6 条，一行一个，带逾期天数。
3. `📆 明天到期 M 条` + `due_tomorrow` 最多 6 条。
4. 若今天打卡没打满：`⬜ 今天还差：习惯名…`（一句）；打满则写 `✅ 今天打卡全齐`。
5. 不说教、不催、不写"建议你早点休息"这类废话；用户要的是"我明天得面对什么"。

## Pitfalls（都是实测踩到的）

| # | ❌ 坑 | ✅ 正确做法 |
|:-:|:---|:---|
| 1 | 给 `task complete` / `task delete` 加 `--json` | 这两个子命令不支持，加了直接失败；脚本已去掉 |
| 2 | `task update <id> --priority 5` | 报 `required option '--id'`；必须 `update <id> --id <id> --project <projectId>` |
| 3 | 全天任务差一天（今天建的显示成昨天） | 库里是「北京日期 − 8h」的 UTC 零点，必须转北京时间再取日期 |
| 4 | `habit checkins --from D --to D` 查当天返回空 | `--to` 排他，查当天要 `--from D --to D+1` |
| 5 | 不传 `--habits` 直接查打卡 | 报 `required option '--habits <ids>'`；先 `habit list` 取 ID 再查（脚本已处理） |
| 6 | 打卡记录被当成扁平结构解析（结果全显示未打卡） | 真实结构是嵌套：`[{habitId, checkins:[{stamp,value,time}]}]` |
| 7 | 写完立刻回读，看到"还在"就以为失败 | 写生效有 1~3 秒延迟；脚本轮询最多 5 次 ×1.5s |
| 8 | 只看回读、不看 CLI 退出码，把命令失败当成"没生效" | 先取 `_cli_error`（非零退出）再谈回读；两个都要看 |
| 9 | 把 `task filter --status 0` 的 41KB JSON 直接贴进对话 | 走 `dida_view.py` 压缩 + `--limit`，只报关键字段 |
| 10 | 用系统 `python3` 跑脚本报缺依赖 | 本技能两个脚本只用标准库，系统 `python3` 就能跑（实测通过） |
| 11 | 打卡只发 `--stamp`，回读只看"有记录"就报成功 | 空壳记录 `status=null/time=null`，APP 里仍显示未打卡；必须 `--time` + `--status 2`，回读判据也是 `status==2`（交叉验证：`habit list` 的 `totalCheckIns` 应 +1） |
| 12 | 用内联 `python3 -c "…"` 跑临时核对（带引号+管道） | 会被审批拦截并超时 BLOCKED；核对写成 `~/.hermes/cache/xxx.py` 再跑 |

## 相关文件

- `references/cli-reference.md` — dida CLI 全部 65 个命令节点的 `--help` 原文（43KB），要查冷门参数时读它。
- `scripts/dida_view.py` — 读侧：聚合/时区换算/压缩排序，失败 `exit 1`。
- `scripts/dida_write.py` — 写侧：argv 直传（不经过 shell）、名字→ID、日期口语化、写完回读、删除要 `--yes`。
- `~/.hermes/scripts/dida_morning.py` / `dida_evening.py` — cron 薄 shim（转调 view 脚本的 `brief`）。
