---
name: hotlist-analyzer
description: "智能追踪全网热点，自动分析热点趋势、跨平台关联、新热点发现，并生成洞察报告。触发词：有什么新热点/热点分析/热点报告/热榜精读/分析热点"
---

# HotList Analyzer 智能热点追踪分析技能 V2

> ⚠️ hotlist 旧模块（目录下的 analyzer.py / cli.py 等）依赖永久缺失，不可用。**采集一律走 `scripts/hot_collect.py`**（纯标准库，cron 与交互通用；交互模式下不必再用 execute_code + httpx）。
> ⚠️ **Cron模式限制**：`execute_code` 在 cron 模式下被完全阻止 → 用 `python3 ~/.hermes/skills/hotlist-analyzer/scripts/hot_collect.py` 一次完成 8 平台采集与解析。详见坑点#8。

## Cron 执行流程

| 步骤 | 操作 | 说明 | ⚠️ 失败降级 |
|:----:|:----|:----|:-----------|
| 1 | 采集8平台 | **直接跑技能自带脚本**：`python3 ~/.hermes/skills/hotlist-analyzer/scripts/hot_collect.py`（一次调用完成 8 平台采集+解析，逐平台打印 TOP20）；可选 `--json` / `--top 30` / `--timeout 20` / `--platforms …`；原始快照自动落 `~/.hermes/cache/hotlist/raw_<时间戳>.json`。API 与字段名维护在脚本内（`hot` 可能是字符串如 `"5098.1万"`，脚本已统一转 str） | 脚本退出码：**0=全正常 ｜ 2=部分平台失败→报告标 ⚠️ 降级运行 ｜ 1=全部失败**。douyinHot 间歇性报 `error code: 1101`（服务端错误），出错才跳过 |
| 2 | **聚类筛选** | ① **按事件/实体聚类**：同一事件的多平台/多角度报道合成一条**主线**（取最权威链接为主链，其余作**支线**＝一句话+链接）；② 排序：跨平台出现次数 → 热度值 → 与近 48h 已报不重复；③ **时效核验**：事件日期 >48h 或无法确认（旧文再流传）**不进主区**，最多降级到快讯区；④ 产出 **主区 4-5 条 + ⚡快讯 6-8 条** | 数据不足时仅按热度排，主区最少 2 条 |
| 🔴 | **交互模式确认** | **展示筛选结果给用户，确认后再进深度分析** | **Cron模式自动跳过此步** |
| 3 | 深度分析 | 主区每条 **250-400 字（硬上限 400）**（主题簇：主线 ≤400 字 + 每支线 1 句）；**⚡快讯区零抓取** —— 直接用榜单标题+摘要字段+链接，每条 ≤60 字。搜索链路: web_search→web_extract→browser降级 | web_search失败→web_extract→browser→仍不行则基于已有摘要分析，标注⚠️ |
| 4 | 固定追踪项 | 查看 `references/fixed-tracking-items.md`。**当前无活跃追踪项**（刚果（金）埃博拉已于 2026-08-04 停止追踪，仅存档）。文件中有未划掉的活跃项时才需搜索 | 无需追踪则跳过本步 |
| 🔴 | **推送确认** | **交互模式：确认后推送报告** | **Cron模式自动推送origin** |
| 5 | 报告生成 | **≤4000字**（主区 4-5 条 + ⚡快讯 6-8 条），推送origin | 生成失败→输出文本到本地文件 `~/.hermes/cron/output/` 备用 |

**cron限制（字数预算）：** 总报告 **≤4000 字**（2026-09-29 用户确认：~3900 字量级可接受）—— 主区 5 条 × ≤400 字 ＝ ≤2000｜⚡快讯 ≤8 条 × ≤60 字 ＝ ≤480｜标题/分隔线/链接行 ≤500。
**写完自检字符数**（`python3 -c "print(len(open('/tmp/hot_report.txt').read()))"`）；超 4000 的处理顺序：① 快讯砍到 6 条 → ② 主区压到 300 字/条 → ③ 仍超则主区减到 4 条。
（2026-09-29 实测：不加自检，模型自然产出 ~3900 字；该量级已获用户确认。）

### 飞书格式规则
- ✅ **粗体** + emoji 做标题（`**🔥 标题**`）
- ✅ `-` 列表、`[链接](url)`、`━━━` 分隔线
- ❌ 禁止Markdown表格（`|`）、标题（`# ##`）

### 报告结构（cron 固定骨架）
```
🌐 **每日热榜精读 | 日期**
━━━
**🔥 热点精选**
**【#N 主线标题】**（跨平台 N 榜）
为什么值得看：一句话
• 要点 1（含硬数据/日期）
• 要点 2
└ 支线：[标题](链接) — 一句话        ← 同主题的其他角度，一条一句
[主链链接]
（主区重复 4-5 条）
━━━
**⚡ 快讯**
- 标题 — 一句为什么 [链接]          ← 6-8 条，每条一行，零抓取
━━━
📊 采集状态 / ⚠️ 降级说明（如有）
```

### 早晚两期去重（状态文件）
- 状态文件：`~/.hermes/cache/hotlist/state.json`（**48h 窗口**，超期自动清理；不要手工编辑）
- **采集后过滤候选**：
  `python3 ~/.hermes/skills/hotlist-analyzer/scripts/hotlist_dedupe.py --check /tmp/hot_candidates.json`
  → 输出 JSON 的 `new[]` 才能进候选，`duplicates[]` 本期弃用（同一件事早晚不重复报）
- **报告发出后登记**：
  `python3 ~/.hermes/skills/hotlist-analyzer/scripts/hotlist_dedupe.py --mark /tmp/hot_reported.json`
- 脚本失败（exit 1）**不阻塞出报**：按未去重处理并在报告里标注 ⚠️ 降级

### 搜索链路（全部免费）
`web_search(Parallel)` → `web_extract(Parallel)` → 失败降级 `browser_navigate(本地Chrome)` + `eval body.innerText`

---

## 关键坑点

| # | ❌ 不要做 | ✅ 正确做法 |
|:-:|:---------|:------------|
| 1 | 读本地缓存 `data/latest_analysis.json` | 每次httpx实时采集 |
| 2 | `curl \| python3` 管道 | `curl -o /tmp/file` 再 `python3` 读文件 |
| 3 | `execute_code` 内 `terminal()` 嵌多层引号 | `write_file` 写独立`.py` → `terminal('python3 /tmp/script.py')` |
| 4 | 用 `__import__('urllib.parse').quote` | `from urllib.parse import quote` |
| 5 | 切换替代方案不告知用户 | 报告中标注 **⚠️ 降级运行** + 原因 |
| 6 | 报告超2000字 | 严格控制在≤2000字 |
| 7 | `--as user` 发飞书缺scope | 降级 `--as bot`，无需重新auth |
| 8 | cron模式下用 `execute_code` 采集 | **execute_code被cron模式阻止**。改用技能自带脚本 `python3 ~/.hermes/skills/hotlist-analyzer/scripts/hot_collect.py`（纯标准库 urllib，8 平台一次性采集+解析），不要再走 `curl -o /tmp/hot_{key}.json` 逐平台拼装 |
| 9 | `xargs -n1 -P8 -I{}` 并行curl；终端前台用 `&` 后台 | xargs 的 `-I{}` 会把**整行**当参数替换导致URL拼接错乱（-n1 与 -I 互斥被忽略）；终端前台禁 `&`。**正解：直接用技能自带 `scripts/hot_collect.py`**（内置 15s 超时 + 失败重试 1 次 + 逐平台容错），**不要再让 LLM 现写一次性 `.py` 到 /tmp** —— 那是文件名撞车 / 旧文件写保护 / 跨 terminal 交接丢文件的根源（见坑点#13） |
| 10 | 榜单里混进**旧文再流传**（2026-09-29 实例：虎嗅"微信将上线AI助手"实为 6/3 旧文） | Step 2 加**时效核验**：事件日期 >48h 或无法确认 → 不进主区（最多降级到快讯区）；必要时报告末尾加一行纠偏 |
| 11 | 早晚两期报同一件事 | 用 `scripts/hotlist_dedupe.py --check` 过滤候选、报告发出后 `--mark` 登记（48h 窗口）；脚本失败不阻塞出报 |
| 12 | ⚡快讯区被写成"第二份报告" | 快讯每条**严格 ≤60 字、一行**：`标题 — 一句为什么 [链接]`；不做抓取、不写要点 |
| 13 | `write_file` 写**已存在且本次未读过**的文件被拒 → 报文尾部多一段 ⚠️ File-mutation verifier 噪音 | 这是 Hermes 的**陈旧写保护**（防误盖不了解内容的旧文件），不是崩溃、不阻塞出报。2026-10-06 实例：采集脚本名 `/tmp/hot_collect_100500.py` 撞上 10-03 的残留 → 写盘失败 + 一次无效重试。**根治：采集不再写临时文件**（用 `scripts/hot_collect.py`）；其余跨运行复用的数据文件一律带时间戳（`/tmp/hot_cand_<YYYYMMDD_HHMM>.json`、`/tmp/hot_report_<YYYYMMDD>.txt`、`/tmp/hot_reported_<YYYYMMDD>.json`），或先 `read_file` 再覆盖 |

---

## 已知平台异常

| 平台 | 异常模式 | 处理 |
|:----|:---------|:-----|
| douyinHot | **间歇性**：有时返回 `error code: 1101`（服务端错误），有时正常返回30条（2026-08-01即正常） | 出错则跳过并标注 **⚠️ 降级运行**；正常则直接使用，不必预设失败 |
| toutiao等 | `hot` 字段是字符串如 `"5098.1万"`，非数值 | 解析时用 `str(hot)` 而非 `int(hot)` |

---

## 固定追踪项

查看 `references/fixed-tracking-items.md` 获取完整追踪数据和数据提取方法。

当前活跃追踪：
- **无**（刚果（金）埃博拉疫情已于 **2026-08-04 应指示停止追踪**，数据存档在 fixed-tracking-items.md；未来如新增追踪项，在此登记）

⛔ **无活跃追踪项时**：跳过 Step 4，**不得**在报告中出现任何“追踪”板块，**不得**搜索已停止项（埃博拉/Ebola/Bundibugyo、洪迪厄斯号等）；即使它们出现在平台榜单里，也只按普通热点规则正常处理，不做专项跟读。

---

## 触发条件
- 用户问"有什么新热点"/"分析热点"/"热点报告"
- cron定时任务自动触发（每天 09:00 和 20:00 北京时间）

## 用户偏好
- **使用替代方案时必须告知用户**：不可悄悄换掉方案不通知
