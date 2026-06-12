# 百度搜索提取参考

> 当 Exa (402)、Sogou (antispider) 均不可用时，百度搜索可作为备选。
> 实测返回 ~895KB HTML，含19条搜索结果（2026-06-12验证）。

## 调用方式

```python
import httpx, re

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept-Language": "zh-CN,zh;q=0.9",
}

resp = httpx.get("https://www.baidu.com/s", params={"wd": "搜索关键词"},
    headers=headers, timeout=15, follow_redirects=True)
```

## HTML 结构特征

百度搜索结果用 `<div class="result ...">` 包裹。每条结果包含：
- `<h3>` 标题（含 `<a>` 链接）
- 摘要文本

### 结果数量提取

```python
results = re.findall(r'<div class="result[^"]*"[^>]*>(.*?)</div>', resp.text, re.DOTALL)
print(f"Found {len(results)} results")
```

### 标题提取（⚠️ 注意：标题外层可能有 em 加粗等格式化标签）

```python
for r in results:
    title_match = re.search(r'<h3[^>]*>(.*?)</h3>', r, re.DOTALL)
    if title_match:
        title = re.sub(r'<[^>]+>', '', title_match.group(1)).strip()
```

⚠️ 实测时 `re.findall(r'<div class="result...')` 找到了19个结果容器，但 `<h3>` 内的标题提取因嵌套格式化标签导致空结果。
**兜底做法**：用 `re.findall(r'百度快照', resp.text)` 等特征词验证结果存在后，直接提取纯文本摘要。

## 已知限制

| 问题 | 说明 |
|------|------|
| HTML 结构复杂 | 百度搜索结果页含大量 JS/CSS，标题提取 regex 可能不匹配 |
| 语言偏好 | 需要 `Accept-Language: zh-CN` 头 |
| 重定向 | 有时会 302 到 https://www.baidu.com/ 的其它路径 |
| 无 site: 过滤确认 | 搜索结果的 site: 过滤功能未验证 |

## 适用场景

- Sogou 反爬（antispider）且 Exa 额度耗尽时
- 需要验证已知关键词的搜索结果是否存在
- 作为直接 curl 到已知站点前的快速验证
