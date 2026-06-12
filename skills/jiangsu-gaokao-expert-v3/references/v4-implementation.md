# V4 实现参考 — 江苏高考信息日报

## 采集策略

### Camofox 高校访问
```python
# 标准采集流程
result = camofox_navigate(url, task_id=task_id)
time.sleep(2)  # 等待渲染
snapshot = camofox_snapshot(full=True, task_id=task_id)
tree = snapshot_dict.get('snapshot', '')
news_list = parse_camofox_snapshot(tree, url, name)
camofox_close(task_id=task_id)
```

### 已知不可达高校
| 高校 | 问题 | 备用方案 |
|------|------|----------|
| 华南理工大学 | SSO 统一认证拦截 | 跳过，靠全网搜索补充 |
| 港中深 | SSL 握手失败 `SSLV3_ALERT_HANDSHAKE_FAILURE` | 尝试更新 CA 证书或用 Camofox |

## 内容清洗

### Jina AI 原生数据的元数据前缀
```python
# fetch_with_jina() 中必须移除
text = re.sub(r'^Title:.*?\n', '', text, flags=re.IGNORECASE)
text = re.sub(r'^URL Source:.*?\n', '', text, flags=re.IGNORECASE)
text = re.sub(r'^Markdown Content:.*?\n', '', text, flags=re.IGNORECASE)
text = re.sub(r'^Here is the extracted content:.*?\n', '', text, flags=re.IGNORECASE)
```

### 摘要提取中的导航 HTML 过滤
```python
# extract_summary() 中过滤
lines = [l.strip() for l in content.split('\n') 
         if len(l.strip()) > 20 
         and not l.strip().startswith('http')
         and not l.strip().startswith('URL')
         and not l.strip().startswith('Source:')
         and not l.strip().startswith('[')]  # 过滤 Markdown 图片链接
```

## DuckDuckGo 搜索实现

```python
def _search_duckduckgo(query: str) -> List[NewsItem]:
    ddg_url = f"https://html.duckduckgo.com/html/?q={quote(query)}"
    headers = {
        'User-Agent': 'Mozilla/5.0 ...',
        'Accept-Language': 'zh-CN,zh;q=0.9',
    }
    resp = requests.get(ddg_url, headers=headers, timeout=15)
    
    # 提取结果（两类 HTML 模式）
    result_blocks = re.findall(
        r'<div class="result[^"]*"[^>]*>.*?<h2[^>]*>.*?<a[^>]+href="([^"]+)"[^>]*>([^<]*)</a>.*?</h2>.*?<a[^>]+class="result__snippet"[^>]*>([^<]*)</a>.*?</div>',
        resp.text, re.DOTALL
    )
    # 备用模式
    result_blocks = re.findall(
        r'<a class="result__a" href="([^"]+)"[^>]*>([^<]+)</a>.*?<a[^>]+class="result__snippet"[^>]*>([^<]*)</a>',
        resp.text, re.DOTALL
    )
    
    # 解析真实 URL
    real_url_match = re.search(r'uddg=([^&]+)', url)
    if real_url_match:
        url = unquote(real_url_match.group(1))
```

## 日期解析

### URL 日期优先
```python
# URL 如 /2026/0428/ → 2026-04-28（比标题中的日期更可靠）
url_date_match = re.search(r'/(\d{4})(\d{2})(\d{2})/', link)
if url_date_match:
    y, m, d = int(...)
    if 2025 <= y <= 2027:
        pub_date = datetime(y, m, d)
```

### 跨年推断
```python
def _infer_year(self, month: int) -> int:
    # 如果新闻月份 > 当前月份 + 3，可能是去年的
    if month > self.today.month + 3:
        return self.today.year - 1
    return self.today.year
```

## 去重策略

双重去重：URL（去参数） + 标题前 15 字符
```python
key = n.url.split('?')[0].split('#')[0]
title_sig = n.title[:15].lower()
```

## 搜索关键词

```python
search_queries = [
    "2026年江苏高考招生最新政策 南京大学 东南大学",
    "2026年强基计划江苏报名 综合评价",
    "江苏高考2026招生变化 新专业 扩招",
]
```

## 不要做的

1. **不要 import `hermes_tools`** — 独立脚本中不可用
2. **不要硬编码 SearXNG 地址** — 环境无 SearXNG，默认 fallback 到 DDG
3. **不要依赖校名+层次输出** — 用户已知信息，不需要
4. **不要输出过时的招生报名通知** — 用 `OUTDATED_KEYWORDS` 过滤
5. **不要在报告里塞入 HTML** — Jina 提取后必须清洗导航栏、图片、超链接
