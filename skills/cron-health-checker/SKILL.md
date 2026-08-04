---
name: cron-health-checker
description: "定时任务健康检查 Skill。每天23:30检查全天所有定时任务的运行状态，生成健康报告并推送给用户。如有问题，征求用户意见后协助修复。"
trigger: |
  当用户说以下任意内容时触发：
  - "检查定时任务"
  - "查看任务状态"
  - "健康检查"
  - "任务运行报告"
  - 或用户明确要求检查/查看/报告定时任务状态
---

# 定时任务健康检查 Skill

## 概述

本 Skill 负责每天23:30自动检查全天所有定时任务的运行状态，生成健康报告并推送给用户。

**核心原则**：主动发现问题、清晰报告状态、征求用户意见后协助修复。

---

## 自动发现机制

**无需手动维护任务列表**，脚本会自动发现所有定时任务：

1. **扫描输出目录**: 检查 `~/.hermes/cron/output/` 下的所有子目录
2. **识别任务**: 每个子目录对应一个 job_id，包含该任务的运行记录
3. **提取名称**: 从最新的 `.md` 文件中自动提取任务名称
4. **缓存更新**: 发现的任务信息缓存到 `discovered_jobs.json`，下次直接使用
5. **活跃任务交叉校验**: 调用 `hermes cron list --all` 获取当前活跃任务列表，自动过滤已废弃的旧任务残留

**废弃任务自动清理机制**:
- 调用 `hermes cron list --all` 获取当前所有激活/暂停的任务列表
- 对比 output 目录中的 job_id：如果某个 job_id 不在 cron 列表中且超过 7 天无新记录 → 自动从缓存中移除
- 下次检查不再报告该任务
- 任务后来重新创建 → 重新纳入监控（新 job_id 会被自动发现）

**优势**:
- ✅ 新增定时任务**自动纳入监控**，无需修改脚本
- ✅ 已删除/替换的任务**自动清理**，无需手动维护缓存
- ✅ 任务重命名**自动更新**
- ✅ 支持动态识别，零维护成本

### 预期运行频率估算

脚本根据**最近7天的历史运行记录**自动估算每个任务的预期运行频率：
- 计算平均每天运行次数
- 动态适应不同任务的不同频率（每天1次、每2小时、每天3次等）
- 新任务默认预期1次/天，随着运行记录积累自动调整

---

## 检查维度

### 1. 运行次数检查
- 今日是否运行？
- 运行次数是否符合预期？
- 最后一次运行时间？

### 2. 运行结果检查
- 成功次数 vs 失败次数
- 最新运行状态（成功/失败）
- 错误类型分析

### 3. 错误分类
- **HTTP 402**: API余额不足 → 建议检查账户/切换模型
- **HTTP 404**: API端点错误 → 建议检查配置/.env文件
- **HTTP 503**: API服务过载（Service Too Busy） → 建议重试或切换备用模型。若连续3+次运行均出现，应主动告知用户该API提供商稳定性存在问题
- **Response truncated** (RuntimeError: Response truncated due to output length limit) → 模型输出超过了 max_tokens 限制。建议在任务Prompt中显式要求摘要/精简输出，或检查模型max_tokens配置
- **Missing**: 今日未运行 → 建议检查任务状态/调度
- **Paused**: 任务被暂停 → 建议恢复运行（`hermes cron resume <job_id>`）
- **No Data**: 无运行记录 → 可能是新任务或目录问题

**错误分类注意事项（运行报告解读时）**：

health_checker.py 中的错误检测使用字符串匹配，可能导致**误分类**：
- 脚本对 `"404" in content` 进行全局匹配（不是仅匹配错误段落），如果文件内容中任何地方出现"404"字符串（如URL、数字、教程内容），都会被归类为"HTTP 404"
- 同理，`"RuntimeError" in content` 的匹配相对准确，但不会分类具体的 RuntimeError 类型
- **建议**: 脚本归类后，人工/agent复核文件内容确认真实错误原因。查看输出文件末尾的 `## Error` 段落获取真实错误信息

### 4. 已暂停任务检测（v2 新增）
- 调用 `hermes cron list --all` 精确匹配每个 job_id 的 `[paused]` 状态
- 注意：不能使用 `"[paused]" in cron_out` 这种模糊匹配（当有其他暂停任务时会误判）
- 必须逐行解析，精确匹配 `"  xxxxxxxxxxxx [paused]"`
- 暂停任务使用 ⏸️ 图标（不是 ❌），在建议中给出恢复命令

---

## 完整工作流程

### Step 1: 运行健康检查脚本

```bash
cd ~/.hermes/cron/health_check && python3 health_checker.py
```

脚本输出：
- `HEALTH_CHECK_STATUS: all_healthy` — 全部正常
- `HEALTH_CHECK_STATUS: attention_needed` — 有需要关注的问题

### Step 2: 读取检查结果

脚本生成报告保存到 `~/.hermes/cron/health_check/health_check_YYYYMMDD_HHMMSS.txt`

### Step 3: 组成修正后的报告（写入新文件）

⚠️ **不要直接推送脚本的原始输出**。必须经过人工/agent复核和修正后再推送。

**修正要点**：
1. 排除健康检查任务自身的"假报警"（标记为"正在执行"）
2. 排除非每日任务的"缺失"误报（检查cron表达式中的星期字段）
3. 核验 partial_failure 任务的成功/失败计数是否混入昨日数据
4. "404"标记的任务需确认是否真错误还是URL误匹配
5. 真 404 需区分「配置性问题」与「fallback 瞬时故障」（见下方 Fallback 404 验证小节）

**报告格式**：

将修正后的报告写入一个新文件（如 `health_check_YYYYMMDD_HHMMSS_corrected.txt`），用于 Step 4 推送。格式如下：

```
📊 定时任务健康检查报告
检查时间: YYYY-MM-DD HH:MM:SS

【概览】
总任务数: N
✅ 健康: N
⏸️ 已暂停: N
⚠️ 需关注: N

【详细状态】
✅ 任务名称
   Job ID: xxx
   今日运行: X次
   预期运行: 约N次/天
   最新运行: HH-MM-SS
   状态: 正常

⏸️ 任务名称
   Job ID: xxx
   今日运行: X次
   问题:
     • 任务已被暂停（暂停日期）
   建议操作:
     → hermes cron resume <job_id>

⚠️ 任务名称
   Job ID: xxx
   调度: cron表达式（如 0 21 * * *）
   今日运行: X次
   问题:
     • 错误描述
   建议操作:
     → 具体修复步骤

【需要关注的问题】
...
💡 如需修复问题，请告诉我，我可以帮你处理
```

### Step 4: 推送修正后的飞书报告（使用 lark-cli）

⚠️ 推送的是 Step 3 生成的修正版报告文件，不是 health_checker.py 的原始输出。

**使用 lark-cli 发送**（原生 Feishu post 格式，表格/代码块渲染更漂亮）：

```bash
# 直接推送最新生成的报告
cd ~/.hermes/cron/health_check
cat health_check_$(date +%Y%m%d)*_corrected.txt | \
  lark-cli --as bot im +messages-send \
    --chat-id "oc_4b7bc3b652e8b27c8a3c683fa4b53aa0" \
    --markdown -
```

也可以用 skill 自带的推送脚本（已改成 lark-cli 方式）：
```bash
cd ~/.hermes/cron/health_check
python3 ~/.hermes/skills/cron-health-checker/references/feishu-delivery.py \
  --report health_check_$(date +%Y%m%d)*_corrected.txt
```

**不使用**以下方式（已废弃）：
- ❌ 飞书开放平台 HTTP API（`tenant_access_token` + `requests.post`）— 旧方式
- ❌ `send_message` 工具 — 排版不如 lark-cli
- ❌ Hermes cron 系统 deliver — 排版不如 lark-cli

### Step 5: 如有问题，征求用户意见

如果检测到需要关注的问题，在报告中明确说明：
- 问题是什么
- 建议的修复操作
- 询问用户是否需要修复

**示例**：
```
⚠️ 发现以下问题需要您的关注：

1. FinNovaWiki 每日自动采集 — 今日未运行
   建议：检查任务是否被暂停
   是否需要我帮您检查并修复？【回复"修复"即可】

2. 全网热点深度智能分析V4 — 5次运行失败（API余额不足）
   建议：切换到备用模型
   是否需要我帮您调整配置？【回复"修复"即可】
```

---

## 修复流程

当用户回复"修复"或"帮我修复"时：

### 常见修复操作

1. **任务被暂停**
   ```bash
   hermes cron resume <job_id>
   ```

2. **API余额不足（402）**
   - 检查当前模型配置
   - 切换到备用模型（如kimi-for-coding）
   - 更新cronjob配置移除特定模型指定

3. **API端点错误（404）**
   - 检查 `.env` 文件是否有行内注释污染
   - 检查 `KIMI_BASE_URL` 配置
   - 使用 `repr(os.getenv('KIMI_BASE_URL'))` 诊断
   - ⚠️ 先区分「配置性 404」与「fallback 瞬时 404」（见下）：配置全对 + 直接 API 测试 200 = 瞬时故障，无需改配置，补跑即可

4. **任务配置问题**
   - 检查cron表达式
   - 检查工作目录设置
   - 检查技能加载配置

---

## Report Correction Workflow (companion to Step 3)

The health_checker.py's auto-generated report needs **manual verification and correction** before pushing to the user. The `health-check-correction-workflow` skill has been absorbed into this section. Reference files with concrete verification session examples are in `references/`:
- `references/june-18-verification-examples.md` — Cross-day contamination detection, 404 vs Broken pipe
- `references/june-19-verification-examples.md` — Systemic Broken pipe pattern, false 404 from skill text
- `references/june-23-verification-examples.md` — Timestamp mismatch diagnostics, 4/5 "404" flags false
- `references/june-26-verification-examples.md` — TimeoutError verification, full correction table

### Verification Script (run for each partial_failure/missing task)

```bash
# 1️⃣ List today's files and check each for an ## Error section
for f in ~/.hermes/cron/output/<job_id>/$(date +%Y-%m-%d)_*.md; do
  [ -f "$f" ] || continue
  echo -n "$(basename $f) → "
  grep -q "## Error" "$f" && echo "⚠️ ERROR" || echo "✅ OK"
done

# 2️⃣ View the actual error content (tail end of file)
tail -15 ~/.hermes/cron/output/<job_id>/<filename>.md

# 3️⃣ Cross-day scan: find all files ever with errors
for file in ~/.hermes/cron/output/<job_id>/*.md; do
  if grep -q "## Error" "$file" 2>/dev/null; then
    echo "ERROR: $(basename $file)"
    awk '/## Error/{found=1} found' "$file" 2>/dev/null
  fi
done
```

### Timestamp Ownership Rule

health_checker.py analyzes `today_files + yesterday_files` together. A reported error like `"07-09-43: RuntimeError"` could be from yesterday.

**Check**: Match the timestamp to the filename:
- `2026-06-18_07-09-43.md` → today's error ✅
- `2026-06-17_07-09-43.md` → yesterday's error → do NOT count as today

### 404 Error Verification

The script uses `"404" in content` (global string match), which matches URLs, numbers, markdown table cells — not just errors.

**How to verify**: Check the actual `## Error` paragraph at file tail:
```bash
tail -15 ~/.hermes/cron/output/<job_id>/<file>.md
```

**Real 404**: `## Error` section exists with `HTTP 404` text
**False 404**: No `## Error` section, or `## Error` shows a different error type (e.g. Broken pipe)
→ Reclassify as the actual error type shown in `## Error`

### Fallback 404 验证（2026-08-02 实战新增）

真 404 不一定=配置错误。当主 provider 先故障（stale stream/Broken pipe）触发
fallback 切换时，fallback 的 404 可能是**瞬时故障**。验证三步：

```bash
# 1️⃣ 确认哪个 provider 真正失败（主 or 备）
grep "API call failed after 3 retries" ~/.hermes/logs/agent.log | tail

# 2️⃣ 看完整故障链（主 provider 先 stall → fallback 激活 → fallback 404？）
grep -B5 -A5 "HTTP 404" ~/.hermes/logs/agent.log | tail -40

# 3️⃣ 直接 API 测试 fallback model（Python 优先，勿用 curl 拼接密钥）
cd ~/.hermes && python3 -c "
import os, json, urllib.request, urllib.error
from dotenv import load_dotenv
load_dotenv('.env')
key = os.getenv('KIMI_API_KEY','')
for m in ['kimi-k2.7-code-highspeed','kimi-k2.5','kimi-for-coding']:
    body = json.dumps({'model':m,'max_tokens':5,'messages':[{'role':'user','content':'hi'}]}).encode()
    req = urllib.request.Request('https://api.kimi.com/coding/v1/messages', data=body, method='POST',
          headers={'x-api-key':key,'Content-Type':'application/json','anthropic-version':'2023-06-01'})
    try:
        r = urllib.request.urlopen(req, timeout=20)
        print(f'{m}: HTTP {r.status} OK')
    except urllib.error.HTTPError as e:
        print(f'{m}: HTTP {e.code} {e.read()[:200]}')
    except Exception as e:
        print(f'{m}: {type(e).__name__} {e}')
"
```

**判定规则**：
- 全部 model 200 → **瞬时故障**，无需改配置。报告标注「服务已恢复，建议补跑或等待明日自动运行」
- 单个 model 404 但其他 200 → 配置问题（fallback 模型名不在 provider models 列表），修 fallback_providers
- 全部 404 → URL/注释污染或密钥问题（查 .env 行内注释、KIMI_BASE_URL）

⚠️ curl 用 `$(grep KIMI_API_KEY .env | cut -d= -f2)` 取密钥可能因特殊字符/换行
被 shell 破坏而全部返回 HTTP:000（假阴性）→ 用 Python + load_dotenv 更可靠。

### Recurrence Pattern Recognition

Check if a Broken pipe/404 error is a one-off or an ongoing problem:
```bash
for file in ~/.hermes/cron/output/<job_id>/*.md; do
  if grep -q "## Error" "$file" 2>/dev/null; then
    echo "ERROR: $(basename $file)"
  fi
done
```

- **One date only** → new issue, flag for attention
- **Scattered across dates** → persistent problem, needs active remediation
- **Yesterday error, today clean** → auto-recovered, mark "昨日的X错误，今日已恢复"
- **Today error with retry success** → mark "已通过重试恢复，需排查根因"
- **间歇性（每1-2周一次，同任务）** → 瞬时故障模式，标注「瞬时双提供商故障」而非「配置问题」

### Mapped Correction Table

| Script status | Actual status | Badge | Example |
|:---|:---|:---|:---|
| missing | currently running | 🔄 | health check itself (schedule `30 23 * * *`) |
| missing | weekly schedule | 📅 | movie recommendation (`0 10 * * 0`) |
| missing | weekday-only | 📅 | a-stock report (`0 16 * * 1-5`) |
| partial_failure | yesterday's error only | ✅ | WC2026 tasks (yesterday's failed file mixed in) |
| partial_failure(404) | actually Broken pipe | ⚠️ | skill description text has "404" matches |
| partial_failure | today has real error | ⚠️ | differentiate Broken pipe / 404 / TimeoutError |
| partial_failure(TimeoutError) | yesterday's error, today clean | ✅ | WC2026赛后复盘 (yesterday idle > 600s) |
| partial_failure(404) | fallback provider transient 404 (primary stalled first) | ⚠️→✅ | WC2026赛后复盘 (deepseek stale stream → kimi 404; direct test HTTP 200 hours later) |

### Error Type Differentiation

**TimeoutError** (Cron job idle timeout): The cron job's agent exceeded the idle timeout (default 600s). Common causes:
1. **Long-running browser_navigate**: Browser hanging on slow page load (most common)
2. **Waiting for stream response**: LLM provider stream stalls with no chunks
3. **Complex processing**: Tool producing very large output
4. **Network stall**: Connection drops mid-operation

Diagnosis: Check the error message for the last activity:
- `idle for 1579s — last activity: executing tool: browser_navigate` → Browser hung on page load
- `idle for 1359s — last activity: waiting for stream response (192s, no chunks yet)` → Provider stall

**Broken pipe** (RuntimeError: [Errno 32] Broken pipe): The agent's output pipe was closed before writing completed. Common in cron mode when output is large. Add "精简输出，分段输出，控制在2000字以内" to the task's prompt.

When 3+ different tasks all show Broken pipe on the same day → systemic pipeline timeout, not individual task issues.

**Real HTTP 404**: An API endpoint returned 404. Check `.env` line comment pollution or `KIMI_BASE_URL` config. ⚠️ 先做 Fallback 404 验证（见上）：配置全对 + 直接测试 200 = 瞬时故障。

### Correction Markup (for corrected report)

```
✅ 任务名（脚本误将昨日的X错误计入今日）
✅ 任务名（昨日22:11曾出现404，今日已恢复）
✅ 任务名（fallback瞬时404：主模型流中断→备用模型瞬时404，数小时后直接测试全部恢复）
📅 任务名（按周调度，下次 MM-DD）
⚠️ 任务名 — 非"HTTP 404"（脚本全局匹配404字符串导致的误分类）
⚠️ 任务名 — Broken pipe持续性问题（6/13、6/15、6/18均有发生）
```

### Cross-Task Pattern Detection

When the same error type appears in **multiple unrelated tasks on the same day**:
1. **3+ tasks with Broken pipe on same day** → systemic pipeline timeout. Report as systemic observation.
2. **3+ tasks with HTTP 404 on same day** → API config issue or provider outage.
3. **Multiple tasks missing on same day** → cron scheduler issue. Check Hermes service status.

---

## 注意事项

### DO
- ✅ 每天23:30准时运行检查
- ✅ 生成清晰的报告，区分健康/需关注/失败
- ✅ 对错误进行分类，给出具体修复建议
- ✅ 征求用户意见后再执行修复操作
- ✅ 修复后重新运行检查确认问题已解决
- ✅ 飞书报告使用文本列表格式，避免Markdown表格

### DON'T
- ❌ 不要自动执行修复操作（必须征求用户同意）
- ❌ 不要忽略"无运行记录"的任务
- ❌ 不要在报告中使用Markdown表格
- ❌ 不要遗漏任何监控任务
- ❌ 不要使用模糊匹配检测暂停任务（`"[paused]" in cron_out`），必须逐行正则精确匹配 job_id 的状态
- ❌ **不要悄悄替换正常运行任务的实现方案而不告知用户** — 如果任务依赖的脚本/API出了问题，用了替代方案（如 Python 脚本损坏后改用 curl 采集），必须在下一次报告中或通过即时消息告知用户"什么出了问题 + 替代方案是什么 + 对输出有何影响"。用户宁愿知道问题存在，也不愿被蒙在鼓里。
- ❌ 健康检查自身的"今日未运行"是正常现象（当前正在执行，输出文件尚未生成），不要将其报告为故障
- ❌ 不要把 fallback 瞬时 404 误当配置问题去改配置 — 直接 API 测试返回 200 就说明配置没问题

---

## 文件位置

- **健康检查脚本**: `~/.hermes/cron/health_check/health_checker.py`
- **飞书推送脚本**: `~/.hermes/skills/cron-health-checker/references/feishu-delivery.py`
- **任务缓存**: `~/.hermes/cron/health_check/discovered_jobs.json`
- **报告目录**: `~/.hermes/cron/health_check/`
- **任务日志目录**: `~/.hermes/cron/output/`

---

## 经验教训

### 1. 自动发现优于硬编码

**初始设计**: 硬编码任务列表（MONITORED_JOBS字典）
**问题**: 每次新增/删除/重命名任务都需要修改脚本
**改进**: 自动扫描输出目录，动态发现所有任务
**效果**: 零维护成本，任务变更自动适应

### 2. 预期频率的动态估算

**初始设计**: 硬编码每个任务的预期运行次数
**问题**: 不同任务频率不同（每天1次、每2小时、每天3次等），难以维护
**改进**: 根据最近7天历史记录自动计算平均每天运行次数
**效果**: 自动适应任何频率的任务，无需配置

**已知局限 — 非每日任务（每周任务）的误判**:
脚本基于**最近7天历史**按"平均每天次数"估算。对于**每周运行一次**的任务（如 🎬 每周电影推荐，cron `0 10 * * 0`），7天历史中仅运行1次，估算结果为约1次/天。在非运行日（非周日），脚本会误报为"missing"。

**处理方式**: 报告解读时必须检查任务的实际 cron 表达式。若 c ron 表达式中包含特定星期（如 `* * * * 0` 表示周日），应将该任务标记为"按日/周调度运行"而非"缺失"。在报告中对这类任务标注实际调度周期，例如：`✅ 任务名称 — 今日未运行（每周日运行，下次 MM-DD）`

### 3. 错误分类的重要性

不同错误需要不同的修复策略：
- 402错误 → 模型/余额问题
- 404错误 → 配置问题（⚠️ 先排除 fallback 瞬时 404）
- 无运行 → 调度/暂停问题

### 4. 区分"任务未运行"与"旧任务残留"

自动发现机制扫描的是 `~/.hermes/cron/output/` 目录，该目录可能包含**已删除或已替换的旧任务**的残留输出（例如旧版本的任务目录已多日无新文件）。

**判断方法**：
- 运行 `hermes cron list --all` 查看当前实际激活的 cron 任务
- 对比 output 目录中的 job_id 与激活列表
- 若 output 目录存在但 cron list 中不存在 → 这是**已废弃的旧任务残留**，应在报告中标注为"可能已废弃/被替代"
- 若两者都存在但今日未运行 → 这是**真正缺失运行**，需要关注调度/暂停问题

**报告标注建议**：
- 真正缺失：`❌ 任务名称 — 今日未运行`
- 旧任务残留：`❌ 任务名称 — 今日未运行（最后运行 YYYY-MM-DD，可能已废弃或被替代）`

**v2 改进：自动清理废弃任务**：
- 脚本现在自动调用 `hermes cron list --all` 交叉校验
- 超过 7 天无新文件且不在 cron 列表中的任务自动从发现缓存移除
- 确保报告只展示真正需要关注的活动任务

### 5. 暂停任务检测必须逐行精确匹配

**错误做法**：`if "[paused]" in cron_out and job_id in cron_out`
**问题**：当有多个任务（一个暂停、一个正常）时，`"[paused]" in cron_out` 始终为 True，导致正常任务被误判为暂停

**正确做法**：逐行解析 `hermes cron list --all` 输出，对每行使用正则精确匹配：
```python
match = re.match(r'\s+' + job_id[:12] + r'\s+\[(\w+)\]', line)
if match:
    is_paused = (match.group(1) == 'paused')
```

### 6. 健康检查自身的"假报警"问题

健康检查任务运行在 23:30，与检查时间相同。当检查开始时，当前运行还没创建输出文件，所以健康检查任务自身会显示"今日未运行"。

**处理方式**：这是正常现象。报告或人工处理时应识别出这是正在运行的自身任务，标记为"正在运行"而非"故障"。脚本层面不对其特殊处理（让输出说明实际情况即可），报告解读时人工标注。

### 7. 替代方案必须主动告知（不仅是健康检查，适用于所有cron运行）

**教训场景**：每日热榜精读的 Python 分析脚本（`auto_deep_analysis.py`）因 hotlist 模块损坏无法使用，我在 prompt 中静默切换为 curl 实时采集方案。用户过了较长时间才发现输出格式和质量变了，非常不满。

**规则**：任何正在正常运行的任务，如果其依赖的脚本/API/工具出了问题，即使已找到替代方案继续运行，也必须在**第一时间**告知用户：
- 什么出了问题（具体错误）
- 替代方案是什么
- 对输出有何影响（格式是否变化、质量是否下降、数据源是否不同）
- 是否计划修复原方案

**例外**：临时性/瞬时故障（重试即恢复）不需要报，但持续超过 2 次运行的替代方案必须报。

### 8. 脚本报告解读 — 纠正误报后再推送给用户

health_checker.py 自动生成的报告包含自动分析结果，但直接推送给用户前**必须人工/agent复核**，纠正以下常见误报：

**已知误报模式**：

1. **健康检查任务自身**：脚本运行在23:30，当检查开始时自身输出文件尚未创建，显示"今日未运行"。处理：标记为"正在执行中（当前检查任务）"，从待关注列表中移除
2. **非每日任务（周任务/工作日任务）**：脚本无cron表达式语义理解。每周日运行的任务（如电影推荐）在周一至周六显示为缺失；仅工作日运行的任务（如a股收盘日报，`0 16 * * 1-5`）在周末显示为缺失。处理：用 `hermes cron list --all` 获取实际调度表达式，标注实际周期
3. **昨日失败计入今日**：脚本将昨日文件加入分析（`all_files = today_files + yesterday_files`），因此昨日失败会出现在"今日"的失败计数中。处理：检查失败文件的日期，区分昨日故障与今日故障
4. **"404"误匹配**：脚本的 `"404" in content` 全局匹配可能将文件中的URL、页码等非错误内容归类为HTTP 404。处理：查看输出文件末尾的 `## Error` 段落确认真实错误
5. **fallback 瞬时 404**：真 404 也可能是 fallback provider 瞬时故障（主 provider 先 stall → 切换 → fallback 恰好 404）。处理：grep agent.log 的 `API call failed after 3 retries` 看是哪个 provider，直接 API 测试确认 model 可用，标注「瞬时故障已恢复」而非配置问题

**纠正流程**：
```
1. 运行 health_checker.py → 得到自动报告
2. 用 hermes cron list --all 获取所有任务的 cron 表达式
3. 对每个"missing"任务，检查是否为周任务/工作日任务：
   · `0 16 * * 1-5` → 仅工作日运行（Mon-Fri），周末应标记为"今日无需运行"
   · `0 10 * * 0` → 仅周日运行，其他日子应标记为"按周调度"
   · `0 8 * * *` → 每日运行，缺失时为真实警报
   · `0 9,20 * * *` → 每日2次，需检查是否偏低
4. 对健康检查任务自身（schedule `30 23 * * *`），标记为"正在执行"
5. 对 partial_failure 任务，查看具体文件确认真实错误
6. 对真 404：grep agent.log 区分主/备 provider，直接 API 测试判定瞬时 vs 配置
7. 组成修正后的报告写入新文件，再推送
```

### 9. 脚本设计细节（Agent需要了解的）

- **昨日文件包含**：`_check_single_job` 中 `all_files = today_files + yesterday_files`，目的是捕获凌晨运行的任务，但会导致 ALL 计数（成功和失败）均混入昨日数据。例如任务显示 `今日运行: 1次 (成功2/失败0)` 时，2次成功中包含昨日的1次，非今日真实成功次数。解读报告时需注意成功/失败计数均可能高于今日实际。处理：检查最近两个文件的日期确认今日真实结果
- **错误检测逻辑**：`_analyze_run_file` 首先检查状态（FAILED关键字），然后搜索错误内容。失败的文件即使包含有效输出也被标记为失败
- **暂停检测**：对 `today_runs == 0` 的任务，脚本调用 `hermes cron list --all` 并逐行正则匹配 job_id 的 paused/active 状态

### 10. 必须征求用户同意

自动修复可能导致意外后果，必须：
1. 报告问题
2. 说明修复方案
3. 等待用户确认
4. 执行修复
5. 验证修复结果

### 11. Fallback 瞬时 404（2026-08-02 实战）

**场景**：WC2026赛后复盘（job 24587630598a）12:00 运行失败。agent.log 显示：
主 provider deepseek-v4-flash 流中断（stale stream 180s → Broken pipe，3次重试
失败）→ 自动切换 fallback kimi-k2.7-code-highspeed → 返回 HTTP 404
resource_not_found_error（3次重试均失败）→ job 失败。

**关键洞察**：**不是配置问题**。验证：① `hermes fallback list` 格式正确；
② config.yaml 中 kimi-k2.7-code-highspeed 同时存在于 fallback_providers 和
kimi-coding models 列表；③ .env 无行内注释污染；④ **数小时后直接 API 测试三个
kimi model 全部 HTTP 200** → 判定为双提供商瞬时故障（deepseek 假连 + kimi
恰好同时段 404）。

**历史模式**：该任务间歇性失败（6/14 Broken pipe、6/21 404、6/25 超时、8/2
404），约每1-2周一次，均为瞬时故障 → 报告标注「瞬时故障已恢复，建议补跑或等待
明日自动运行」，**不要**修改配置。

**curl 陷阱**：`curl -H "x-api-key: $(grep KIMI_API_KEY .env | cut -d= -f2)"`
可能因密钥含特殊字符/换行被 shell 破坏而全部返回 HTTP:000（假阴性）→ 用
Python + load_dotenv 测试更可靠（见上方 Fallback 404 验证脚本）。

**附带观察（非 cron）**：gateway 日志持续报 `~/.hermes/kanban.db` 不是有效
SQLite 数据库 → 看板调度暂停。可 `hermes kanban init` 恢复（与 cron 故障无关，
但值得在报告中附带告知用户）。
