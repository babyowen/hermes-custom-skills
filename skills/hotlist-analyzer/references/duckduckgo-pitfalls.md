# DuckDuckGo HTML Search as Fallback — Pitfalls

> Added: 2026-05-30
> Context: session where web_search (Exa) returned 402 credit limit; DuckDuckGo was used as fallback but gave inconsistent results.

## How to Use

```python
from urllib.parse import quote
import subprocess, re

url = f"https://html.duckduckgo.com/html/?q={quote(query)}"
result = subprocess.run(['curl', '-s', '-L', '--max-time', '20',
    '-H', 'User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',
    url], capture_output=True, text=True, timeout=25)
html = result.stdout

# Extract results using the result__body pattern
blocks = re.findall(r'class="result__body">(.*?)</div>\s*</div>', html, re.DOTALL)
for block in blocks[:5]:
    title_m = re.search(r'class="result__a"[^>]*>(.*?)</a>', block, re.DOTALL)
    snippet_m = re.search(r'class="result__snippet"[^>]*>(.*?)</(?:a|span)>', block, re.DOTALL)
    url_m = re.search(r'href="//duckduckgo\.com/l/\?uddg=([^&"]+)"', block)
```

## Pitfalls

### ⚠️ Inconsistent Results
DuckDuckGo HTML search **does not return results for all queries**. In testing:
- `"Hondius" virus outbreak hantavirus 2026` → ✅ Good results (WHO, Wikipedia, ECDC)
- `Ebola DRC Uganda Bundibugyo 2026 outbreak` → ❌ Empty results
- `Blue Origin New Glenn rocket explosion 2026` → ❌ Empty results

Likely causes: query language (English works better than Chinese on this endpoint), query "hotness"/popularity, or rate-limiting/throttling.

### ⚠️ No Regex Safety Net
Unlike Google News or Wikipedia API which have predictable HTML/JSON structure, DuckDuckGo's HTML varies. The regex patterns above may break if DuckDuckGo changes their HTML structure.

### ⚠️ URL Extraction
DuckDuckGo wraps result URLs in redirect links (`//duckduckgo.com/l/?uddg=<encoded_url>`). These need URL-decoding. The `url_m` regex above handles this.

## When to Use
Use DuckDuckGo after SerpAPI, before Google News httpx fallback. It is a tier-4 option (after SerpAPI, Wikipedia API, Google News).

## When NOT to Use
- If Wikipedia API can answer the query directly (Ebola stats, disease outbreaks, known events)
- If the query is in Chinese (DuckDuckGo HTML endpoint has poor Chinese search performance)
