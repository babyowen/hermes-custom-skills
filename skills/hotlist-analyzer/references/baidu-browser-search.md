# Baidu 浏览器搜索降级方案（当 Exa/SerpAPI 均不可用时）

## 适用场景

当以下所有方案均不可用时：
- `web_search` → 402（Exa 额度耗尽）
- `web_extract` → 402（同一套 Exa 额度）
- `serpapi-search` → 无结果或配额用完
- `httpx` 直连 → 目标站不可达

此时使用 **browser_navigate + browser_console** 走 Baidu 搜索，通过浏览器渲染引擎绕过 API 限制。

## 工作流程

### Step 1：Baidu 搜索（关键步骤）

直接导航到 Baidu 搜索 URL（不要依赖搜索框输入，容易 CAPTCHA）：

```python
# 直接构造搜索 URL 导航
browser_navigate(url="https://www.baidu.com/s?wd=<URL编码搜索词>&ie=utf-8")
```

### Step 2：用 browser_console 提取搜索结果

Baidu 搜索结果的 DOM 结构特点：
- 结果标题在 `<h3>` 标签内的 `<a>` 中
- 每个结果在 `<div class="result">` 或 `<div class="c-result">` 容器中
- 摘要文本在 `<div class="c-abstract">` 或 `<span class="c-span-last">` 中

**提取标题和链接**：
```javascript
// 获取所有搜索结果标题和链接
Array.from(document.querySelectorAll('h3 a')).map(a => ({
    title: a.textContent.trim(),
    href: a.href
}))
```

**提取带摘要的完整结果**：
```javascript
Array.from(document.querySelectorAll('.result, .c-result, .result-op')).slice(0, 10).map(div => {
    const link = div.querySelector('h3 a');
    const abs = div.querySelector('.c-abstract, .c-summary, .c-span-last');
    return {
        title: link ? link.textContent.trim() : '',
        href: link ? link.href : '',
        summary: abs ? abs.textContent.trim().substring(0, 200) : ''
    };
}).filter(x => x.title)
```

### Step 3：利用百度热搜侧边栏获取热门话题

当直接搜索结果不理想时，Baidu 页面右侧的**热搜榜**（热点趋势面板）非常有价值。它在页面中以表格形式呈现，可通过以下方式提取：

```javascript
// 观察页面侧边栏的热搜内容
// 注意：热搜数据通常以表格中的链接形式呈现
Array.from(document.querySelectorAll('h3')).slice(0, 20).map(h => h.textContent.trim()).join('\n')
```

热搜侧边栏会显示：
- 排名（数字 1-15）
- 热门话题标题
- 热度标记（🔥爆 = 最热，💥沸 = 沸腾，🔥热 = 热门，🆕新 = 最新）

### Step 4：点击具体搜索结果

找到相关结果后，使用 `browser_click(ref)` 点击链接。如果链接是 Baidu 重定向 URL，浏览器会自动跟随到目标站。

### Step 5：提取目标页面内容

到达目标页面后：
```javascript
// 提取文章正文
document.querySelector('.content, .article-content, .article, #content, .main-content, .detail-content, .art-content, .text')?.innerText || document.body.innerText
```

## 注意事项

### ⚠️ 搜索词 URL 编码
Baidu 搜索词必须 URL 编码。直接在 URL 中用 `?wd=` 参数，不要用 `?word=`。建议直接使用中文（浏览器会自动编码）。

### ⚠️ 页面内容截断问题
`browser_snapshot` 返回的 accessibility tree 对长页面会**大幅截断**（显示 "N more lines truncated"）。解决：
1. 先用 `browser_scroll(direction='down')` 滚动到关键区域
2. 用 `browser_console` + JavaScript DOM 查询提取精确数据
3. 用 `browser_console` + `expression` 执行 `document.body.innerText.substring(0, 5000)` 提取正文

### ⚠️ Baidu 重定向链接
Baidu 搜索结果中的链接是 `http://www.baidu.com/link?url=...` 格式。浏览器导航到这些链接时会自动跟随跳转到真实目标页。也可以用 `browser_click` 点击，浏览器会自动跟随。

### ⚠️ CAPTCHA 拦截
高频请求 Baidu 可能触发 CAPTCHA。如果 `browser_navigate` 后看到验证码页面，可能是请求太频繁。此时先做其他操作稍后再试。

### ⚠️ 无法使用 fetch() 跨站请求
在 browser_console 中执行 `fetch(url).then(r => r.text())` 会被 CORS 策略拦截，返回 `NetworkError: NetworkError when attempting to fetch resource.`。必须通过 `browser_navigate` 直接导航到目标站。

### ⚠️ browser_vision 可能不可用
在本环境中 `browser_vision` 返回 404。无法通过截图分析页面。必须通过 accessibility tree + JavaScript DOM 查询来理解页面内容。

## 适用场景案例

| 场景 | 做法 |
|:----|:----|
| 搜索中文新闻/热点 | Baidu 搜索（`browser_navigate`）→ 提取 h3 标题 → 点击阅读 |
| 获取热搜趋势 | 观察 Baidu 页面的右侧热搜榜 sidebar |
| 搜索考试/政策类信息 | 使用精确关键词，利用 Baidu 索引优势 |
| 对比不同来源的信息 | 搜索后提取多个结果标题，对比不同来源 |
| 搜索失效/老数据 | Baidu 的索引对中文老数据保留更好 |

## 与其他降级方案的配合

```
web_search/web_extract 402
  ├─ 🥇 SerpAPI (~/.hermes/skills/serpapi-search/)
  ├─ 🥈 httpx 直连目标站（thepaper.cn / news.cn 等）
  ├─ 🥉 Baidu 浏览器搜索（本文档）
  └─ ❹ Wikipedia API / 其他
```
