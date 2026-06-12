# 独立脚本提取模式（规避 execute_code 引号陷阱）

> 当 `execute_code` 中的 `terminal()` 调用因多层嵌套引号导致 SyntaxError 时，将复杂脚本写入临时文件再执行。

## 触发条件

在以下情况使用此模式替代在 `execute_code`/`terminal()` 中嵌入长命令：

- 命令含 `python3 -c "..."` 内嵌 Python 代码，且 Python 代码本身有引号
- 命令含 shell 管道 `|` + 多个参数
- 命令需要 `urllib.parse.quote()` 等 Python 标准库
- 命令跨多行，字符串拼接容易出错
- 需要在脚本中 import 多个标准库模块

## 标准工作流

```python
from hermes_tools import write_file, terminal

# Step 1: 写独立 Python 脚本到 /tmp
write_file(path='/tmp/fetch_articles.py', content='''
import subprocess, re, json, html, urllib.parse

# 所有搜索词和 URL 在这里定义
searches = {
    "荷兰军机 驱离": "荷兰 军机 解放军 驱离 南海 2026",
    "中俄 天然气 管道": "中俄 天然气 管道 普京 2026",
}

for label, query in searches.items():
    encoded = urllib.parse.quote(query)
    result = subprocess.run(
        ["curl", "-s", f"https://www.bing.com/news/search?q={encoded}&setlang=zh-cn",
         "-H", "User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"],
        capture_output=True, text=True, timeout=15
    )
    html_content = result.stdout
    # 提取标题
    for m in re.findall(r\'<a[^>]*class="title"[^>]*>.*?</a>\', html_content, re.DOTALL):
        text = re.sub(r\'<[^>]+>\', \'\', m).strip()
        print(f"  {text}")
''')

# Step 2: 运行脚本（无引号问题）
r = terminal('python3 /tmp/fetch_articles.py', timeout=30)
print(r["output"])
```

## 对中文新闻站点的优势

1. **Bing News 对中文搜索友好**：`setlang=zh-cn` 参数返回简体中文结果，标题完整准确
2. **无需 API key**：完全免费，无速率限制（合理频率下）
3. **无 CAPTCHA**：Bing News 接口（非主搜索）通常不触发验证码
4. **提取多篇文章**：在脚本内循环处理搜索结果，批量提取新闻标题

## 已验证的解析模式

```python
# Bing News 标题提取（class="title"）
for m in re.findall(r'<a[^>]*class="title"[^>]*>.*?</a>', html, re.DOTALL):
    text = re.sub(r'<[^>]+>', '', m).strip()
    print(f"TITLE: {text}")

# Bing News 来源提取（data-author attribute）
sources = re.findall(r'data-author="([^"]+)"', html)
for s in sources:
    print(f"SOURCE: {s}")

# Bing News URL 提取（来自文章链接）
urls = re.findall(r'<a[^>]*class="title"[^>]*href="([^\"]+)"', html)
```

## 已知局限

- Bing News 返回的不含文章摘要/正文——只能获取标题和来源
- 若要获取正文，需额外抓取每篇文章的 URL（使用 `urllib.request` 或 `httpx`）
- 部分文章 URL 被 Bing 的 `ck/a` 重定向包装，需提取实际 URL（可通过两次 curl 或检查 `href` 参数）
- `subprocess.run(["curl", ...])` 中参数分开写避免 shell 注入，但不能用 `|` 管道——如需管道则用 `shell=True` 或 Python 内处理
