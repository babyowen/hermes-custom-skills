# Bing News Search Fallback（搜索降级方案）

> 当 web_search（Exa）或 web_extract（Firecrawl）因额度耗尽、API 故障而失败时，使用 Bing News 作为替代搜索引擎。

## 适用场景

- `web_search` 返回 402 "You have exceeded your credits limit"
- `web_extract` 返回同样 402 错误
- DuckDuckGo `lite` endpoint **部分可用**（见下方 DuckDuckGo lite 方案），不同查询成功率不同
- Google News 返回 JS-heavy 页面但可通过 `execute_code` 解析（见下方 Google News 方案）

## 多层级降级策略（Exa 额度耗尽时的完整回退链）

当 Exa 信用额度耗尽（402错误）时，按以下优先级尝试：

### 第1层：DuckDuckGo Lite（轻量、快速、无需API key）
✅ 适用于简单关键词搜索（英文查询成功率 > 中文）
❌ 某些查询返回0结果（无明显错误，页面干净但无链接）

### 第2层：Bing News（次选，结构化好）
✅ 英文和中文均表现稳定
✅ HTML结构规整，正则解析可靠

### 第3层：Google News（稳定但需要更多解析）
✅ 适用于任何查询，结果全面
⚠️ HTML可达2.5MB，需使用 `execute_code` 解析

### 第4层：源站直连（CDC、WHO、Wikipedia等）
✅ 已知 URL 时最直接
✅ 用 curl 下载全文 → execute_code 正则提取正文

## DuckDuckGo Lite 搜索

```bash
# 英文搜索（查询词用空格分隔即可）
curl -s --max-time 15 "https://lite.duckduckgo.com/lite/?q=Hondius+virus+outbreak+quarantine+2026" \
  -H "User-Agent: Mozilla/5.0" -o /tmp/ddg_results.html

# 中文搜索
curl -s --max-time 15 "https://lite.duckduckgo.com/lite/?q=%E7%94%98%E8%82%83+%E5%9C%B0%E9%9C%87+2026" \
  -H "User-Agent: Mozilla/5.0" -o /tmp/ddg_results.html
```

### 解析 DuckDuckGo Lite 结果

DuckDuckGo Lite 返回的是纯HTML，搜索结果URL通过 `uddg=` 参数编码：

```python
import re, urllib.parse

with open('/tmp/ddg_results.html') as f:
    html = f.read()

# 提取所有链接
links = re.findall(r'uddg=([^&"\']+)', html)
for l in links[:10]:
    decoded = urllib.parse.unquote(l)
    print(decoded)

# 提取标题文本
titles = re.findall(r'uddg=[^&"\']+[^>]*>([^<]+)<', html)
```

**注意事项**：
- 部分查询可能被 DuckDuckGo 限制（返回空白页但无错误码），此时换用 Bing 或 Google News
- DuckDuckGo Lite 没有中文界面参数，中英文结果取决于查询词

## Bing News 搜索命令

```bash
# 英文搜索
curl -s --max-time 15 -H "User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36" \
  'https://www.bing.com/news/search?q=Hondius+ship+virus+outbreak+2026&FORM=HDRSC7' \
  -o /tmp/bing_results.html

# 中文搜索
curl -s --max-time 15 -H "User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36" \
  'https://www.bing.com/news/search?q=山西+煤矿+爆炸+82死+2026&FORM=HDRSC7&setlang=zh-Hans' \
  -o /tmp/bing_results.html
```

**关键**：必须设置 `User-Agent` 头部，否则 Bing 可能拒绝请求。

## 解析搜索结果

Bing News 返回结构化 HTML，可直接使用正则提取标题 + URL + 摘要：

```python
import re

def parse_bing_news(html):
    """从 Bing News HTML 中提取文章信息"""
    results = []
    # 提取文章卡片
    article_blocks = re.findall(
        r'<a[^>]*class="[^"]*title[^"]*"[^>]*href="(https?://[^"]+)"[^>]*>(.*?)</a>',
        html, re.DOTALL
    )
    for url, title in article_blocks[:10]:
        clean = re.sub(r'<[^>]+>', '', title).strip()
        results.append({'title': clean, 'url': url})
    
    # 如果上述模式未命中，尝试更宽松的匹配
    if not results:
        all_links = re.findall(
            r'<a[^>]*href="(https?://[^"]+)"[^>]*>(.*?)</a>',
            html, re.DOTALL
        )
        seen = set()
        for url, text in all_links:
            clean = re.sub(r'<[^>]+>', '', text).strip()
            if len(clean) > 15 and clean not in seen and 'bing.com' not in url:
                seen.add(clean)
                results.append({'title': clean[:120], 'url': url})
    
    return results
```

## 提取文章正文

从搜索结果中获得文章 URL 后，可直接用 curl 下载并用 Python 提取正文：

```bash
curl -s --max-time 15 -H "User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36" \
  'https://example.com/article' -o /tmp/article.html
```

```python
import re

def extract_article_text(html):
    """简单的 HTML 正文提取（不使用任何外部库）"""
    # 移除脚本、样式、noscript
    for tag in ['script', 'style', 'noscript']:
        html = re.sub(rf'<{tag}[^>]*>.*?</{tag}>', '', html, flags=re.DOTALL)
    # 去标签
    text = re.sub(r'<[^>]+>', '\n', html)
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    # 去重连续行
    result = []
    for line in lines:
        if not result or result[-1] != line:
            result.append(line)
    return '\n'.join(result)
```

## 能成功提取正文的新闻站点（已验证）

以下站点可通过上述方法提取正文内容（已验证）：

### 通用提取策略

对于不同新闻站点，使用不同的容器选择器：

| 站点 | 容器模式 | 说明 |
|------|----------|------|
| chinanews.com（中新网） | `class="left_zw"` | 正文在 left_zw div 内 |
| sina.com.cn（新浪） | `<p>` 标签过滤 | 直接取所有 `<p>` 标签文本，去掉短行 |
| qq.com（腾讯新闻） | `<p>` 标签 | 常规 `<p>` 提取 |
| sohu.com（搜狐） | `<p>` 标签 | 常规 `<p>` 提取 |
| ifeng.com（凤凰网） | `class="article"` 或 `<p>` | article 容器效果最佳 |
| apnews.com (AP News) | JavaScript 渲染，不推荐 curl | 需浏览器或 RSS |
| thestar.com.my | `<p>` 标签 + 清理导航 | 含较多导航噪音需过滤 |
| globaltimes.cn (环球网) | `<p>` 标签 | 常规 `<p>` 提取 |
| ithome.com (IT之家) | `<p>` 标签 | 常规 `<p>` 提取 |
| **thepaper.cn (澎湃新闻)** | **`<p>` 标签** | **2026-05-26 验证：正文在 `<p>` 标签内，抽取效果很好** |
| **view.inews.qq.com (腾讯新闻)** | **`<p>` 标签** | **2026-05-26 验证：常规 `<p>` 提取，新闻正文完整** |
| **www.thepaper.cn/newsDetail_forward_XXX** | **`<p>` 标签** | **2026-05-26 验证：深度报道图文混排，`<p>` 提取效果稳定** |

### 通用提取代码

```python
def extract_from_ps(html):
    \"\"\"通用方法：取所有<p>标签，过滤短行\"\"\"
    paragraphs = re.findall(r'<p[^>]*>(.*?)</p>', html, re.DOTALL)
    texts = []
    for p in paragraphs:
        t = re.sub(r'<[^>]+>', '', p).strip()
        t = html.unescape(t)
        if len(t) > 30:  # 过滤导航/广告等短行
            texts.append(t)
    return texts

def extract_from_container(html, class_name):
    \"\"\"从指定class的容器中提取\"\"\"
    m = re.search(r'class="[^"]*' + class_name + r'[^"]*"[^>]*>(.*?)</div>', html, re.DOTALL)
    if m:
        return re.sub(r'<[^>]+>', '', m.group(1)).strip()
    return ""
```



## 安全扫描器注意事项

- ⚠️ **禁止** `curl ... | python3 -c "..."` 管道模式 — 被 tirith 安全扫描器拦截
- ✅ **正确做法（方案一）**：`curl -o /tmp/file` 然后 `python3 file.py` 或 `execute_code` 块
- ✅ **更优做法（方案二）**：在 `execute_code` 块内直接用 **httpx** 完成搜索和文章提取，完全避免终端管道操作。httpx 是 Hermes venv 内预装的，无需额外安装。适用于：Bing News HTML 搜索、单个文章页面提取。

### 推荐：execute_code + httpx 方案

```python
import httpx, re, html

# 搜索
resp = httpx.get(
    "https://www.bing.com/news/search?q=your+search+query",
    headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"},
    timeout=15
)
# 提取结果
results = re.findall(r'<a[^>]*class="title"[^>]*href="([^"]+)"[^>]*>(.*?)</a>', resp.text, re.DOTALL)

# 提取文章正文
resp2 = httpx.get(url, headers=..., timeout=15)
paragraphs = re.findall(r'<p>(.*?)</p>', resp2.text, re.DOTALL)
```

**优点**：无需 tmp 文件、无管道安全拦截、一键完成、输出直接返回。

**httpx 已知可成功提取的新闻站点**：chinanews.com（中新网）、sina.com.cn、qq.com、sohu.com、thestar.com.my、ifeng.com — 用正则匹配 `<p>` 标签或 `class="article"` / `class="content"` / `class="left_zw"` 容器效果最佳。

## Google News 搜索（DuckDuckGo 和 Bing 都不行时的可靠备选）

Google News 的 HTML 很庞大但结构清晰，可用 `execute_code` 解析。**注意：不能用管道 `curl | python`，必须分步：curl 下载 → execute_code 解析。**

```bash
curl -s --max-time 15 "https://news.google.com/search?q=Ebola+Bundibugyo+DRC+2026&hl=en-US&gl=US&ceid=US:en" \
  -H "User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36" \
  -o /tmp/google_news.html
```

### 解析 Google News 结果

```python
import re
from hermes_tools import read_file  # 或直接用 open

with open('/tmp/google_news.html') as f:
    html = f.read()

# 去 script/style
html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL)
html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL)

# 提取文章链接和标题
articles = re.findall(r'<a[^>]*href="([^"]*)"[^>]*>([^<]*)</a>', html)

# 按关键词筛选（用 Python 过滤相关结果）
for url, title in articles:
    title_clean = title.strip()
    if any(kw in title_clean for kw in ['Ebola', 'Bundibugyo', 'CDC', 'WHO']):
        print(f"{title_clean} -> {url}")
```

### 完整的 Google News 分析流程（已验证）

```python
import httpx, re

resp = httpx.get(
    "https://news.google.com/search?q=Ebola+DRC+Bundibugyo+2026&hl=en-US&gl=US&ceid=US:en",
    headers={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"},
    timeout=15
)

html = re.sub(r'<script[^>]*>.*?</script>', '', resp.text, flags=re.DOTALL)
html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL)
articles = re.findall(r'<a[^>]*href="([^"]*)"[^>]*>([^<]*)</a>', html)

# 打印所有相关文章
for url, title in articles:
    t = title.strip()
    if len(t) > 10:  # 过滤无关短链接
        print(f"• {t}")
```

**Google News 优势**：几乎不会被限流，结果丰富全面，时效性好。

## 源站直连（有具体 URL 时最有效）

当追踪特定事件（如洪迪厄斯号、埃博拉）时，不要依赖搜索引擎，直接去权威来源获取最新数据：

### Al Jazeera 新闻列表页（验证：2026-05-26）

Al Jazeera 的标签/主题页（如 `/tag/ebola/`）是获取国际突发公共卫生事件最新进展的可靠来源——无需搜索，直接访问聚合页即可获取最新标题列表。

```bash
curl -s --max-time 15 -L "https://www.aljazeera.com/tag/ebola/" \
  -A "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36" -o /tmp/aj_ebola.html
```

**解析策略**：HTML 含大量 CSS-in-JS 和 styled-components，但文章标题可通过正则从原始 HTML 提取。去 script/style 后，扫描 `<a>` 标签中含义关键字的文本：

```python
import re
with open('/tmp/aj_ebola.html') as f:
    html = f.read()
html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL)
html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL)
text = re.sub(r'<[^>]+>', '\n', html)
lines = [l.strip() for l in text.split('\n') if l.strip() and len(l.strip()) > 30]
# 过滤含关键词的行
for l in lines[:60]:
    if any(kw in l for kw in ['Ebola', 'case', 'death', 'outbreak', 'WHO', 'Tedros', 'vaccine', 'DRC', 'Uganda', 'Bundibugyo']):
        print(l[:200])
```

**已验证内容**：返回 WHO 总干事谭德塞评论、病例数更新、乌干达输入病例、治疗中心纵火事件等——覆盖完整。

### CDC Newsroom（特定事件）
# WHO Disease Outbreak News
curl -s --max-time 15 -L "https://www.who.int/emergencies/disease-outbreak-news/item/2026-DON601" \
  -H "User-Agent: Mozilla/5.0" -o /tmp/who_page.html

# CDC Newsroom（特定事件）
curl -s --max-time 15 -L "https://www.cdc.gov/media/releases/2026/cdc-provides-update-on-hantavirus-outbreak-linked-to-m-v-hondius-cruise-ship.html" \
  -H "User-Agent: Mozilla/5.0" -o /tmp/cdc_page.html

# Wikipedia（事件背景+时间线）
curl -s --max-time 15 -L "https://en.wikipedia.org/wiki/MV_Hondius_hantavirus_outbreak" \
  -H "User-Agent: Mozilla/5.0" -o /tmp/wiki_page.html
```

解析时先用 `execute_code` 去 script/style，然后搜索关键词定位最新信息。

**安全扫描器坑点**：⚠️ 禁止 `curl | python3` 管道模式。必须：
1. ✅ `curl -o /tmp/file` 下载到文件
2. ✅ 用 `execute_code`（或 `open()` + 正则解析）读取文件
3. ✅ 或者在 `execute_code` 里使用 `httpx` 直接获取

## 完整工作流模板

```python
from hermes_tools import terminal
import re

# Step 1: 搜索
query = '山西+煤矿+爆炸+2026'
r = terminal(
    f"""curl -s --max-time 15 -H 'User-Agent: Mozilla/5.0' \
    'https://www.bing.com/news/search?q={query}&FORM=HDRSC7&setlang=zh-Hans' \
    -o /tmp/bing_results.html && echo OK""",
    timeout=15
)

# Step 2: 解析结果（在 execute_code 内或后续步骤）
with open('/tmp/bing_results.html') as f:
    html = f.read()
articles = parse_bing_news(html)

# Step 3: 提取具体文章
for article in articles[:3]:
    r = terminal(
        f"curl -s --max-time 15 -H 'User-Agent: Mozilla/5.0' '{article['url']}' -o /tmp/article.html",
        timeout=15
    )
    with open('/tmp/article.html') as f:
        text = extract_article_text(f.read())
    # 找到文章相关部分
    if article['title'][:20] in text:
        idx = text.find(article['title'][:20])
        content = text[idx:idx+2000]
    else:
        content = text[:2000]
    print(content)
---

## 🏆 最佳回退链总结（按优先级）

当 Exa / Firecrawl 不可用时，按以下顺序尝试：

```
① 🥇 SerpAPI → serpapi-search 技能（`python3 scripts/search.py`，已配 API key，无 CAPTCHA，中英文均可，推荐首选）
② 已知 URL 时 → 源站直连（WHO/CDC/Wikipedia 等，最快）
③ Wikipedia API → 已知主题时首选（结构化 JSON，无速率限制）
④ Google News RSS → 新闻类查询（简单 XML，几乎不受限）
⑤ DuckDuckGo HTML → 通用搜索（轻量，但每 IP 约 2-3 次后限流）
⑥ Baidu 搜索 → 仅限中文查询（HTML 复杂但可用）
⑦ Bing News → 全面但易触发验证码，见上方
⑧ Google News 全页 → 最重但最全面
⑨ Session Search → 所有外部搜索均失效时的终极内部缓存（仅恢复已知状态，不产生新数据）
```

---

## 新增回退通道（2026-05-25 验证）

### Wikipedia API（结构化 JSON，推荐用于已知主题）

Wikipedia 的 JSON API 是追踪已知事件（如 Hondius、Ebola）的**最佳回退方案**——无速率限制、结构化响应、直接返回纯文本。

```bash
# 标准 API 查询（获取概述）
curl -s "https://en.wikipedia.org/w/api.php?action=query&titles=MV_Hondius_hantavirus_outbreak&prop=extracts&exintro=true&explaintext=true&format=json"

# 完整文本（不含 exintro 限制）
curl -s "https://en.wikipedia.org/w/api.php?action=query&titles=2026_Ituri_Province_Ebola_epidemic&prop=extracts&explaintext=true&format=json"

# 搜索 Wikipedia 页面
curl -s "https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch=Ebola+Bundibugyo+outbreak+2026&format=json"
```

**解析方式**（Python，无需 urllib.parse 等复杂库）：
```python
import json, subprocess
result = subprocess.run(['curl', '-s', url], capture_output=True, text=True)
data = json.loads(result.stdout)
pages = data.get('query', {}).get('pages', {})
for pid, pdata in pages.items():
    extract = pdata.get('extract', '')
    # extract 已为纯文本，直接使用
```

**经验证可用的 Wikipedia 主题**：
- `MV_Hondius_hantavirus_outbreak` — 全面时间线、病例数、WHO/CDC 响应
- `2026_Ituri_Province_Ebola_epidemic` — 病例数、传播路径、疫苗状况
- `Bundibugyo_ebolavirus` — 病毒学背景、历史爆发

**优势**：零配置、JSON 响应、无限流（合理使用下）、纯文本无需 HTML 解析。

### ⚠️ Google 主搜索 CAPTCHA 陷阱（2026-05-27 新增）

**危险**：Google 主搜索（`www.google.com/search?q=...`）返回 HTTP **200 OK** + ~90KB HTML，但实际不是搜索结果——而是隐藏的插入页。

**识别特征**：
- HTTP 200（看起来正常）
- 搜索结果 `<a>` 标签几乎为零
- 页面含文本：`"If you're having trouble accessing Google Search, please&nbsp; click here"`
- 比正常 Google 搜索结果小得多（~90KB vs 500KB+）

**为什么危险**：
- 因为返回 200，容易误认为请求成功
- 正则匹配 `<h3>` 或 `class="g"` 结果容器返回空——但不会报错
- 不像 DuckDuckGo 那样明确弹出 CAPTCHA

**对策**：Google 主搜索仅作最后手段。优先用 Wikipedia API、WHO/CDC/AFRO 源站直连、Google News RSS、Bing News。

---

### Google News RSS（比全页 Google News 轻量 50 倍）

Google News HTML 页面可达 2.5MB，但 RSS 版本仅 ~50KB 且直接可用：

```bash
curl -s "https://news.google.com/rss/search?q=China+Japan+rare+earth+export+ban+2026&hl=en-US&gl=US"
```

**解析方式**（简单正则）：
```python
import re, subprocess
result = subprocess.run(['curl', '-s', url], capture_output=True, text=True)
titles = re.findall(r'<title>(.*?)</title>', result.stdout, re.DOTALL)
for t in titles[1:]:  # 第 0 条是 "Google News" 标题
    clean = t.replace('<![CDATA[', '').replace(']]>', '').strip()
    print(f"  {clean}")
```

**已验证查询**：
- `China+Japan+rare+earth+export+ban+2026` — 返回路透社、NYT、CSIS 等主流媒体
- 传参：`hl=en-US&gl=US` 控制语言和地区。中文用 `hl=zh-CN&gl=CN`

---

### DuckDuckGo HTML 搜索（通用备选，注意限流）

`html.duckduckgo.com/html/?q=...` 对中文和英文查询都可用，但**每 IP 约 2-3 次查询后即触限流**（返回空白搜索页，无错误码）。

```bash
curl -s -L --max-time 10 \
  -H "User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36" \
  "https://html.duckduckgo.com/html/?q=Hondius+cruise+ship+virus+outbreak+2026"
```

**解析**：
```python
links = re.findall(r'class="result__a"[^>]*href="([^"]+)"[^>]*>(.*?)</a>', html, re.DOTALL)
snippets = re.findall(r'class="result__snippet"[^>]*>(.*?)</(?:a|td)>', html, re.DOTALL)
```

**限流行为**：成功返回第 1-2 次 → 第 3 次后返回无结果的空白页。无错误码，只能通过 `result__snippet` 的出现次数 0 来判断。

### Session Search 回退（所有搜索引擎均失败时的终极方案）

当所有搜索引擎（DuckDuckGo、Bing、Google、Baidu）均因 CAPTCHA、限流或额度耗尽而无法使用时，**session_search 工具**可以检索本地历史会话数据库，重建追踪事件的最新已知状态。

**适用场景**：
- web_search 402 额度耗尽
- DuckDuckGo/Bing/Google 全部触发 CAPTCHA 或限流
- 追踪特定事件（如洪迪厄斯号、埃博拉疫情）需要"目前已知的最新状态"
- 不需要"最新新闻"时（因为 session_search 不能产生新的外部数据）

**使用方法**：
```python
from hermes_tools import session_search

# 搜索历史会话中关于追踪事件的最新状态
results = session_search(
    query="洪迪厄斯号 Hondius 已解决 追踪",
    limit=5
)
# 返回的 results 中包含每个匹配会话的：
# - bookend_end: 会话最后的用户+助手消息（含最终结论/状态更新）
# - bookend_start: 会话开始时的目标设定
# - messages: 匹配消息前后各 5 条，含锚点标记
```

**输出解读**：
- `bookend_end` 中的最后一条助手消息通常包含该次运行的最新追踪结论
- `match_message_id` 可 paired 配合 `around_message_id` + `window` 参数做滚动查看更多上下文
- 按 `sort='newest'` 返回最近的会话优先

**局限性**：
- ❌ 不能获取外部世界的最新数据——只能恢复"最近一次 cron 运行时该状态的快照"
- ❌ 若追踪事件有重大进展但发生在两次 cron 运行之间，session_search 不会知道
- ✅ 适合判断"上次我们追踪到哪里了"——用于构建连续追踪报告
- ✅ 比完全不报好得多——至少能维持追踪的连续性

**实战示例**（2026-05-27 每日热榜精读）：
当 web_search/web_extract 全部失败、DuckDuckGo 触发 CAPTCHA、Google 返回插入页时，使用：
```
session_search(query="洪迪厄斯号 刚果 埃博拉 每日热榜精读", limit=3, sort='newest')
```
成功回收到 2026-05-26 晚（约12小时前）的追踪数据：洪迪厄斯号10确诊+2疑似、3死、船员全阴；埃博拉超900疑似、三国部长会议等——足以维持报告质量。

---

### WHO AFRO 官网直连（追踪埃博拉等非洲疫情的最佳回退）

当搜索埃博拉疫情但所有搜索引擎均失效时，**WHO 非洲区域办公室官网**是获取最新官方数据的可靠来源。URL 结构稳定，HTML 响应友好。

**已知可用 URL 模式**：
```
# 新闻列表页
https://www.afro.who.int/news

# 具体新闻页（可预测 slug 模式）
https://www.afro.who.int/countries/uganda/news/intensifying-cross-border-collaboration-curb-ebola-outbreak
https://www.afro.who.int/news/high-level-ministerial-meeting-cross-border-coordination-ebola-disease-outbreak-caused
```

**提取策略**：
```python
import httpx, re

resp = httpx.get(url, headers={"User-Agent": "..."}, timeout=15)
html = resp.text
html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL)
html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL)

# WHO AFRO 的内容在 <meta> description 和 <div class="field--name-body"> 中
text = re.sub(r'<[^>]+>', '\n', html)

# 寻找 COMMUNIQUÉ / PREAMBLE / 关键词
idx = text.find('COMMUNIQUÉ')
if idx < 0:
    idx = text.find('PREAMBLE')
```

**已验证提取内容**（2026-05-27）：
- 三国部长级会议联合公报全文（DRC、Uganda、South Sudan）
- 流行病学数据："截至5月20日，伊图里省和北基伍省确认传播"
- 具体承诺：加强跨境监测、入境点协调、社区动员等6点行动计划
- 发布时间：2026-05-23
- 更新日期标记：`<meta property="article:modified_time" content="Mon, 25/05/2026 - 11:49" />`

**WHO AFRO 提取注意事项**：
- ⚠️ Drupal 10 架构，正文在 `field--name-body` div 中
- ⚠️ 元描述中包含文章前 200 字（含关键数据），适合快速获取摘要
- ⚠️ 有法语版（`/fr/` 路径），如英文页面 404 可尝试移除 URL 中不匹配的部分
- ✅ 无 CAPTCHA，无速率限制
- ✅ 发布日期和修改日期均在 HTML head 的 meta 标签中

### 🚨 DuckDuckGo CAPTCHA 挑战（2026-05-26 新增）

某些查询（尤其是中文、敏感主题如"Ebola"）会触发 DuckDuckGo 的 CAPTCHA 挑战——显示 "Select all squares containing a duck" 图片验证码，而非无结果空白页。

**识别特征**：返回的 HTML 中包含以下字符串：
```html
Please complete the following challenge to confirm this search was made by a human.
Select all squares containing a duck:
```

**CAPTCHA 触发场景**（实测）：
- 中文关键词 → 通常 OK
- 英文关键词 + 敏感/健康话题 → 高概率触发（如 `Ebola DRC Uganda Bundibugyo 2026`）
- 查询频率：第 1 次正常 → 第 2 次 CAPTCHA

**对策**：一旦检测到 CAPTCHA HTML（含 "duck" / "challenge" / "squares" 等特征词），**立即放弃 DuckDuckGo** 并升级到下一层回退：Google News RSS 或 Wikipedia API。

---

### Baidu 搜索（仅限中文查询，2026-05-25 验证）

Baidu 搜索从中国服务器可直接访问，返回 HTML 约 900KB。适用于中文关键词搜索。

```bash
# 中文搜索（无需预编码，curl 自动处理）
curl -s -L --max-time 10 \
  -H "User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36" \
  -H "Accept-Language: zh-CN,zh;q=0.9" \
  "https://www.baidu.com/s?wd=印度+热浪+50度+2026"
```

**已验证的解析模式**：
```python
titles = re.findall(r'<h3[^>]*>(.*?)</h3>', html, re.DOTALL)
for t in titles[:5]:
    clean = re.sub(r'<.*?>', '', t).strip()
    # clean 就是搜索结果的标题
```

**局限**：
- 结果链接 URL 被百度重定向包装，`<a href="...">` 中的 URL 是百度内部跳转链接，不是直链
- 无法直接获取摘要（`c-abstract` 等 class 名会变化）
- 仅标题可用于判断结果相关性
- 无法绕过百度内容审查

---

## 注意事项

1. **Bing 频率限制**：不要高频连续搜索，每次搜索间隔至少 2-3 秒
2. **结果数量**：Bing News 通常返回 10-15 条结果，足够使用
3. **中文搜索**：使用 `&setlang=zh-Hans` 参数可获得中文搜索结果
4. **CJK 编码**：URL 中的中文词需先做 URL 编码，或直接使用 curl 的自动编码能力
5. **文章提取限制**：部分站点有付费墙/弹窗，需额外处理
6. **AP News 限制**：AP News 页面高度 JavaScript 渲染，curl 正则提取效果差。改用其 RSS feed 或 browser 工具
7. **Wikipedia API 限制**：对敏感/争议性主题，Wikipedia API 可能被墙或限流。建议作为首选而非唯一来源
8. **DuckDuckGo 限流**：约 2-3 次查询后即触限流。换用 Google News RSS 或 Wikipedia API 绕过。限流无错误码，需检测 result 数量是否为 0
