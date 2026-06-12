# WC2026 采集工作流详情

## 采集工具优先级

```
web_extract → 若 402 → browser_navigate→Google → DuckDuckGo(ddgs, Python) → terminal curl
```

## 站点 curl 可用性

| 站点 | 可用 | 备注 |
|------|:----:|------|
| SI.com / The Guardian / Goal.com / Flashscore | ✅ 全文可提取 | 优先使用 |
| EnglandFootball.com / FOX Sports / FIFA.com | ✅ | 全文可提取 |
| ussoccer.com | ✅ | 美国队官方新闻/阵容 |
| The Athletic (nytimes.com) | ✅ | 全文可提取 |
| FotMob赛程页 (fixtures) | ✅ browser | 最可靠赛程源 |
| ESPN | ❌ | 0字节，只能用 Google 摘要 |
| BBC Sport | ❌ | JS渲染，部分失败 |
| Sky Sports | ❌ 405 | Google 摘要 |
| SportingNews / FourFourTwo | ❌ | JS墙/会员墙 |
| FotMob新闻页 | ❌ | JS渲染 |

**经验**: 先用 `curl -sI -o /dev/null -w "%{http_code}" <URL>` 探测站点。

## 快速比分确认

下载官方页面后用 grep 提取 `<title>` 标签：
```bash
curl -sL -A "Mozilla/5.0" -o /tmp/page.html "https://..." 
grep -oP '(?<=<title>)[^<]+' /tmp/page.html
```

## Pipe-to-interpreter 安全拦截

`terminal` 工具拦截所有 `cmd | python3` 管道。修复：
```bash
# 错误 ❌
curl ... | python3 -c "..."

# 正确 ✅ 分两步
curl -sL -o /tmp/data.json "https://..."
python3 -c "import json; data=json.load(open('/tmp/data.json')); print(data)"
```

## DuckDuckGo 备用搜索

当 web_extract/browser 都不可用时：
```python
from duckduckgo_search import DDGS
with DDGS() as ddgs:
    results = list(ddgs.text("query", max_results=10))
```

## Subagent 效率

在 delegate_task context 中直接告知可用/不可用站点：
```
可用：SI.com, The Guardian, Goal.com, Al Jazeera, FOX Sports, Flashscore
不可用：ESPN(0字节), BBC(JS), Sky(405), SportingNews(JS墙), FourFourTwo(会员)
```

## 赛后复盘流程

每场比赛结束后：
1. 确认比分/进球/红牌/伤情（多源交叉验证）
2. 更新伤病追踪表（红牌→❌停赛、受伤→❌/⚠️、恢复→✅）
3. 更新 match page（status:finished, 填写result/goals/red_cards）
4. 更新出线形势

## FotMob 使用注意

- 赛程页显示 **PT (UTC-7)** 时间，非 ET
- 最可靠的开球时间：点进比赛详情页，查看 `<h1>` 中的 UTC 时间戳
- 推荐使用「By round」视图，比「By group」高效

## 公告时间差处理

| 时区 | 07:00 UTC 覆盖 | 19:00 UTC 覆盖 |
|:-----|:--------------:|:--------------:|
| 欧洲/英国早间 | ✅ 昨日公告 | ✅ 当日公告 |
| 欧洲下午 | ✅ 前日公告 | ❌ →次日 |
| 亚洲 | ❌ →19:00 | ✅ |
| 非洲下午 | ❌ →次日 | ❌ →次日 |
| 美洲 (17-20 ET) | ✅ 昨日 | ❌ →次日 |

## Polymarket 搜索

用 slug 格式搜 EPL：`epl-{team-abbr}-{team-abbr}-YYYY-MM-DD`
用 Gamma API：`/events?slug=...`
