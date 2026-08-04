# June 23 Verification Session — Concrete Examples

## New Pattern: Timestamp Mismatch as Diagnostic Signal

When the script reports an error at a specific time, but that time doesn't match any today filename, it's a strong signal of **yesterday-file contamination**.

**How to check**: Compare the error timestamp from the script output against the actual file listing timestamps.

### Case: FinNovaWiki 每日自动采集 (33f7272665cc)

```
Script reported:  "21-09-33: API请求失败 (HTTP 404)"
Today's files:    2026-06-23_21-05-33.md  ✅ (no Error section)
Yesterday's file: 2026-06-22_21-09-33.md  ← the "21-09-33" matches THIS file
```

**Rule**: When script's error timestamp doesn't match any today file's timestamp but matches a yesterday file → the error is from yesterday. Mark task as healthy for today.

---

## All Three "404" Cases Were False — No `## Error` Section Pattern

This session had **5 total partial_failure tasks** flagged with "404". After verification:

| Task | Script claimed | File has `## Error`? | Verdict |
|:-----|:--------------|:--------------------|:--------|
| FinNovaWiki 每日自动采集 | HTTP 404 at 21-09-33 | ❌ No | ✅ False — yesterday's file contamination |
| WC2026赛前预测·晚间版 | HTTP 404 at 20-13-02 | ❌ No | ✅ False — successful prediction report |
| 短线选股策略知识库自动采集 | HTTP 404 at 12-13-13 | ❌ No | ✅ False — normal template output |
| 每日热榜精读 | HTTP 404 at 09-09-28 | ❌ No (today's file) | ✅ False — yesterday's real 404 file contaminated count |
| WC2026赛后新闻复盘·15:00版 | HTTP 404 at 15-10-13 | ✅ Yes | ⚠️ REAL 404 |

**Takeaway**: In THIS session, 4 out of 5 "404" flags were false. The only real 404 had a `## Error` section. The other 4 had zero error indicators.

---

## Verification Commands Used (June 23)

```bash
# 1. Get cron expressions for all tasks — enables weekly/weekday detection
hermes cron list --all

# 2. For each partial_failure task, check TODAY's files for errors
#    (replace job_id and date)
for f in ~/.hermes/cron/output/<job_id>/2026-06-23_*.md; do
  echo -n "$(basename $f) → "
  grep -q "## Error" "$f" && echo "⚠️ ERROR" || echo "✅ OK"
done

# 3. Cross-day scan: all files with errors in this task
grep -l "## Error" ~/.hermes/cron/output/<job_id>/*.md 2>/dev/null

# 4. View the actual error content
awk '/## Error/{found=1} found' ~/.hermes/cron/output/<job_id>/<file>.md
```

---

## Correction Table (June 23)

| Script status | After correction | Notes |
|:--------------|:----------------|:------|
| 10 ❌ partial_failure/missing | ✅ 11 healthy, ⏸️ 2 paused, ⚠️ 2 real issues | 8 false alarms corrected |
| 3x "HTTP 404" misclassification | All false — file content matched "404" string | No `## Error` section in any |
| 1x "missing" — 健康检查 | 🔄 Currently executing (23:30 cron) | Schedule `30 23 * * *` |
| 1x "missing" — 🎬 每周电影推荐 | 📅 Weekly schedule (Sundays only) | Cron `0 10 * * 0`, today is Tuesday |
| 1x "partial_failure" — 每日热榜精读 | ✅ Both today runs successful | Failure was from yesterday's file |
| 1x "partial_failure"(404) — WC2026晚间预测 | ✅ Complete successful report | Prediction tables or URLs triggered `"404" in content` |
| 1x real 404 — WC2026赛后新闻复盘·15:00版 | ⚠️ Real error | Has `## Error: HTTP 404` |
| 1x scheduling issue — WC2026情报采集19:00 | ⚠️ Mode confusion | Tried Mode A (morning) at 19:00 instead of Mode D |
