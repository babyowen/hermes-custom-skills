# WHO DON 浏览器提取指南

> 创建：2026-06-10 | 验证版本：DON #605（5/29）和 #606（6/8）

## 为何需要此指南

Exa 额度耗尽时 `web_search`/`web_extract` 返回402。WHO DON 页面是追踪埃博拉等疫情的最佳数据源，但 httpx 直连可能因JS渲染截断内容。`browser_navigate` 可完整读取。

## 步骤

### 1. 找到最新 DON 条目 ID

导航到 DON 列表页查看最新条目：

```python
# 通过 browser_navigate 打开列表页
browser_navigate("https://www.who.int/emergencies/disease-outbreak-news")
# snapshot 中可看到最近条目列表，例如：
# "8 June 2026 | Ebola disease caused by Bundibugyo virus, DRC & Uganda"
# "29 May 2026 | Ebola disease caused by Bundibugyo virus, DRC & Uganda"
```

### 2. 直接导航到详情页

WHO DON 的 URL 模式为：`https://www.who.int/emergencies/disease-outbreak-news/item/2026-DON6xx`

```python
browser_navigate("https://www.who.int/emergencies/disease-outbreak-news/item/2026-DON606")
```

递增DON编号试探：DON605 → DON606 → DON607...

### 3. 提取数据

browser_navigate 返回的snapshot中包含 `"Situation at a glance"` 区块下的完整文本，包含：
- 确诊/死亡/疑似数字
- 地理分布（省份/卫生区）
- 接触者追踪数据
- 医护人员感染数据
- 国际扩散信息

**关键数据字段搜索**：
- `confirmed cases` + 数字
- `deaths` + 数字
- `suspected cases` + 数字
- `health and care workers` + 数字
- `contacts` + 数字
- `CFR` （病死率）
- `recovered`

### 4. 如需更完整数据

用 `browser_snapshot(full=True)` 获取完整页面内容。

## 验证结果

| DON编号 | 发布日期 | 数据截止日 | 访问方式 | 完整性 |
|---------|---------|-----------|---------|-------|
| #605 | 5/29 | 5/27-5/29 | browser_navigate | ✅完整 |
| #606 | 6/8 | 6/6 | browser_navigate | ✅完整 |

## 已知限制

- WHO 列表页（/disease-outbreak-news）的条目标题是 heading 元素而非 link 元素，无法直接点击。需通过 URL 模式直接导航到详情页。
- 页面内容段落用 `<article>` 标签包裹，browser_snapshot 会截断超长页面（超过~250行），此时用 `browser_snapshot(full=True)` 获取完整内容。
- WHO 页面无 CAPTCHA、无 paywall、无需登录。
