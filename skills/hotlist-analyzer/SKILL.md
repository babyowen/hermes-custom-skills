---
name: hotlist-analyzer
description: "智能追踪全网热点，自动分析热点趋势、跨平台关联、新热点发现，并生成洞察报告。触发词：有什么新热点/热点分析/热点报告/热榜精读/分析热点"
---

# HotList Analyzer 智能热点追踪分析技能 V2

> ⚠️ hotlist 模块永久缺失，所有 Python 脚本不可用。交互模式用 `execute_code` + `httpx` 实时采集。
> ⚠️ **Cron模式限制**：`execute_code` 在 cron 模式下被完全阻止。须用 `curl -s --max-time 15` 逐平台采集 JSON 到 `/tmp/`，再用 `python3 -c` 或独立 `.py` 脚本通过 `terminal()` 解析。详见坑点#8。

## Cron 执行流程

| 步骤 | 操作 | 说明 | ⚠️ 失败降级 |
|:----:|:----|:----|:-----------|
| 1 | 采集8平台 | 交互模式：httpx并行；cron模式：curl逐平台。API: `https://hot-api.vhan.eu.org/v2?type={key}`，`d['data']`是列表。注意 `hot` 值可能是字符串（如 `"5098.1万"`）而非数值 | 某平台超时→重试1次→仍失败则跳过→**⚠️降级运行**标注。douyinHot间歇性报 `error code: 1101`（服务端错误），出错才跳过 |
| 2 | 筛选TOP 3-4条 | 优先跨平台热点 → 高热度新热点 → 类型多样 | 数据不足时仅按热度排，仍不足则减少条数（最少2条） |
| 🔴 | **交互模式确认** | **展示筛选结果给用户，确认后再进深度分析** | **Cron模式自动跳过此步** |
| 3 | 深度分析 | delegate_task并行子代理，每条≤400字。搜索链路: web_search→web_extract→browser降级 | web_search失败→web_extract→browser→仍不行则基于已有摘要分析，标注⚠️ |
| 4 | 固定追踪项 | 查看 `references/fixed-tracking-items.md`。**当前无活跃追踪项**（刚果（金）埃博拉已于 2026-08-04 停止追踪，仅存档）。文件中有未划掉的活跃项时才需搜索 | 无需追踪则跳过本步 |
| 🔴 | **推送确认** | **交互模式：确认后推送报告** | **Cron模式自动推送origin** |
| 5 | 报告生成 | **≤2000字**，推送origin | 生成失败→输出文本到本地文件 `~/.hermes/cron/output/` 备用 |

**cron限制：** 总报告≤2000字，最多5条热点，每条≤400字。

### 飞书格式规则
- ✅ **粗体** + emoji 做标题（`**🔥 标题**`）
- ✅ `-` 列表、`[链接](url)`、`━━━` 分隔线
- ❌ 禁止Markdown表格（`|`）、标题（`# ##`）

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
| 8 | cron模式下用 `execute_code` 采集 | **execute_code被cron模式阻止**。改用 `curl -s --max-time 15 "https://hot-api.vhan.eu.org/v2?type={key}" -o /tmp/hot_{key}.json` 逐平台采集，再 `python3 -c` 或独立 `.py` 脚本文件解析 |
| 9 | `xargs -n1 -P8 -I{}` 并行curl；终端前台用 `&` 后台 | xargs 的 `-I{}` 会把**整行**当参数替换导致URL拼接错乱（-n1 与 -I 互斥被忽略）；终端前台禁 `&`。**最优解：write_file 写一个自包含 `.py`（urllib + 15s超时 + 失败重试1次，逐平台拉取→解析→打印TOP），terminal 单次执行 `python3 /tmp/x.py`**——采集与解析原子完成，避免跨 terminal 调用交接 /tmp 文件（沙箱 /tmp 可能在调用间被清空，glob 返回空） |

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

---

## 触发条件
- 用户问"有什么新热点"/"分析热点"/"热点报告"
- cron定时任务自动触发（每天 09:00 和 20:00 北京时间）

## 用户偏好
- **使用替代方案时必须告知用户**：不可悄悄换掉方案不通知
