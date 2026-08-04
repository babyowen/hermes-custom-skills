# June 19 Verification Session — Concrete Examples

## Systemic Pattern: Cross-Task Broken Pipe

**Date**: June 19, 2026
**Observation**: 4 different cron tasks hit `RuntimeError: [Errno 32] Broken pipe` on or around this date.

| Task | Job ID | When | Frequency |
|:-----|:-------|:-----|:----------|
| WC2026赛后新闻复盘·15:00版 | 02f873a85b82 | June 19 15:09 (today) | Only failure today |
| 江苏高考决策情报日报V5.3 | 577c97d63499 | June 19 08:09 (today) | 1 of 3 runs failed |
| 短线选股策略知识库自动采集 | 0ad6eb0e87af | June 19 12:09 (today) | 1 of 3 runs failed |
| WC2026赛前预测·晚间版 | 8a8c783a853a | June 18 20:09 (yesterday) | Yesterday, recovered today |
| 每日热榜精读 | fda1ae624d71 | June 18 20:09 (yesterday) | Persistent on some dates |

**Correction applied**: Flag as systemic ⚠️ rather than individual task issues. Report observation in "需要关注的问题汇总" section.

---

## False 404 Verification Results

### 每日热榜精读 (fda1ae624d71) — FALSE 404

**Script claimed**: HTTP 404 at 09:08 and 20:23
**Actual verification**:
```bash
# Search for "404" in today's files
grep -n "404" ~/.hermes/cron/output/fda1ae624d71/2026-06-19_*.md
```
**Result**: Matches found at:
- Line 28 in skill description: `DON新编号404→降回上期数据`

This is skill instruction text, NOT an error. Both files had **no `## Error` section** → SUCCESS ✅
**Correction**: ✅ All healthy today. Remove from needs-attention list.

### 江苏高考决策情报日报V5.3 (577c97d63499) — YESTERDAY'S 404

**Script claimed**: HTTP 404 at 08-10-00 AND 08-09-51
**Actual verification**: Checked which files have "404":
```bash
grep -rn "404" ~/.hermes/cron/output/577c97d63499/2026-06-19_*.md
# → No matches!
grep -rn "404" ~/.hermes/cron/output/577c97d63499/2026-06-18_*.md
# → 2026-06-18_08-10-00.md  line 855: RuntimeError: HTTP 404
```
**Result**: The 404 is from yesterday (June 18), NOT today. Today's files have no 404.
**Correction**: Today's real issue is only Broken pipe on 1st run (08:09). 2nd/3rd runs succeeded.

---

## Partial Failure: Real Today vs Yesterday's Data

### WC2026赛后新闻复盘·15:00版 (02f873a85b82) — REAL FAILURE TODAY

**Script said**: partial_failure, 1 success + 1 failure (Broken pipe at 15-09-54)
**Verification**: ✅ This is a real today failure. The `## Error` section exists in today's file (2026-06-19_15-09-54.md):
```
## Error
RuntimeError: [Errno 32] Broken pipe
```
File header says `(FAILED)` too.
**Duration**: This task has been running successfully on June 12-17. June 18 and 19 both failed. Possibly a new issue.

### WC2026赛前预测·晚间版 (8a8c783a853a) — YESTERDAY'S FAILURE ONLY

**Script said**: partial_failure, 1 success + 1 failure (Broken pipe at 20-09-49)
**Verification**: Today's file (2026-06-19_20-10-39.md) is 359 lines, has full prediction output, NO `## Error` section, NOT marked FAILED. Only the yesterday file (2026-06-18_20-09-49.md) has FAILED.
**Correction**: ✅ Healthy today. Remove from needs-attention list.

---

## Verification Checklist Used

```
For each partial_failure/missing task:
☐ 1. List today's files: ls -lt ~/.hermes/cron/output/<job_id>/ | head -5
☐ 2. Check FAILED header: grep -l "FAILED" ~/.hermes/cron/output/<job_id>/2026-06-19_*.md
☐ 3. Check ## Error section in today's files
☐ 4. If "404" claimed: grep -rn "404" all files → determine if real 404 or false match
☐ 5. If Broken pipe claimed: check which date the file is from
☐ 6. Cross-check: does same error affect other tasks? → systemic or individual?
```
