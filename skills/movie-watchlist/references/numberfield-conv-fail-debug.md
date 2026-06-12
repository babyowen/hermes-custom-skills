# NumberFieldConvFail (code 1254061) 排查指南

## 症状

POST 记录到飞书多维表格时返回：

```json
{
  "code": 1254061,
  "message": "NumberFieldConvFail"
}
```

## 排查方法

### Step 1: 检查现有记录的实际字段类型

用 Python 读取现有记录的字段值类型：

```python
import json
data = json.load(open('feishu_movies.json'))
first = data['data']['items'][0]['fields']
for k, v in first.items():
    print(f"  {k}: {type(v).__name__} = {repr(v)}")
```

> ⚠️ GET 返回的字段值类型不总是等于 POST 要求的类型。数字字段 GET 可能返回字符串 `'8.5'`，但 POST 仍需传数字 `8.5`。

### Step 2: 逐一测试每个字段

用最小 payload 逐个字段测试，找出有问题的字段：

```python
from hermes_tools import terminal
import json

base = {"电影名称": "test-field"}
fields_to_test = {"评分": 8.5, "年份": 2025, "类型": "剧情", ...}

for field, value in fields_to_test.items():
    payload = {"fields": {**base, field: value}}
    r = terminal(f"echo '{json.dumps(payload, ensure_ascii=False)}' | lark-cli api POST ... --data -")
    if '"code": 0' in r.get('output', ''):
        print(f"  {field} OK")
    else:
        print(f"  {field} FAILED: {r['output'][:200]}")
```

### Step 3: 已知的 NumberFieldConvFail 原因

| 字段 | 正确类型 | 错误类型 |
|:----|:---------|:---------|
| 评分 | 数字 (`8.5`) | 字符串 (`"8.5"`) |
| 年份 | 整数 (`2025`) | 字符串 (`"2025"`) |

## 规律

此飞书表格中有两个数字类型的字段（评分、年份）。其他字段（地区、导演、主演等）都是文本类型。

添加新记录时记住：
- **评分**: 传数字，如 `8.7`
- **年份**: 传整数，如 `2025`
