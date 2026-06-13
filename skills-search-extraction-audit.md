# Skills 搜索/提取方式审计清单

审计日期：2026-06-13
审计范围：~/hermes-custom/skills/ 下 7 个 skill 子目录

---

## 1. hotlist-analyzer/

### 使用了哪些搜索/提取方式
| 工具 | 用途 | 优先级 |
|------|------|--------|
| `web_search` | 深度分析背景搜索 | 🥇 主方案（依赖 Exa） |
| `web_extract` | 提取热点详情正文 | 🥇 主方案（依赖 Exa） |
| `execute_code` + `httpx` | 采集8平台热点数据（hot-api.vhan.eu.org）+ 直连新闻站提取正文 | 🥇 主方案（绕过Exa）|
| `execute_code` + `urllib.request` | 文章提取降级方案 | 🥈 回退 |
| `browser_navigate` | WHO DON 页面完整读取、Baidu 浏览器搜索 | 🥈 回退 |
| `browser_snapshot` / `browser_console` / `browser_click` | Baidu 搜索结果提取、WHO 页面数据提取 | 🥉 回退 |
| `curl` → `python3`（分步） | 新闻站直连、采集 hot-api | 🥉 回退 |
| `requests` | SKILL.md 有代码示例 | 仅示例 |
| DuckDuckGo Lite / Bing News / Google News | 搜索回退（通过 curl/httpx） | 多层回退链 |

### Exa / SerpAPI 引用
- **Exa**: ⚠️ 重度依赖。SKILL.md 全篇围绕 Exa 建立，降级回退链所有层级都围绕 Exa 402 设计。`web_search` 和 `web_extract` 共享 Exa 配额。
- **SerpAPI**: ⚠️ 引用。`references/bing-news-fallback.md` 中列为 🥇 首选回退（`serpapi-search` 技能）。

### 是否需要修改
**是**。整个 SKILL.md 的降级策略围绕 Exa 402 构建，包含大量针对 Exa 的上下文优化逻辑（如子代理 context 告知 Exa 降级状态）。切换到新标准链路后：
- Exa 不再返回 402（使用 Parallel MCP 免费链路）
- web_search / web_extract 恢复可用
- 大量降级回退链文档需要精简
- 但当前 `httpx` 直连新闻站的做法实际上与新标准不冲突

### 修改复杂程度：**复杂**
- 8个参考文件中有大量针对 Exa 降级的详细描述
- SKILL.md 中 ~30+ 处涉及 Exa/降级逻辑
- 需重新设计整个回退链（可将多层降级简化为 1-2 层）

---

## 2. jiangsu-gaokao-expert-v3/

### 使用了哪些搜索/提取方式
| 工具 | 用途 | 优先级 |
|------|------|--------|
| `web_search` (Exa) | 高考信息搜索 | 🥇 主方案 |
| `web_extract` (Exa) | 页面内容提取 | 🥇 主方案（与 web_search 同池）|
| `execute_code` + `httpx` → sogou.com | 搜狗搜索（中文高考关键词） | 🥈 首选回退 |
| `execute_code` + `httpx` → baidu.com | 百度搜索 | 🥉 回退 |
| `browser_navigate` → Google | 浏览器 Google 搜索（首选备选） | 🥈 首选备选 |
| `curl` → 学校官网/聚合站 | 直连静态 HTML 站点 | 🥉 回退 |
| Open-Meteo API (curl/httpx) | 高考天气数据 | 🥇 天气源 |
| `browser_navigate` → Baidu | 极限降级 | 🥉 极限降级 |

### Exa / SerpAPI 引用
- **Exa**: ⚠️ 依赖。SKILL.md 中"搜索工具故障链"完全围绕 Exa 配额耗尽（402）设计。故障恢复链表第一行就是 `web_search (Exa)`。
- **SerpAPI**: 未发现引用。

### 是否需要修改
**是**。主要影响：
1. Exa 不再返回 402，因此整个"搜索工具故障链"需要重写
2. `browser_navigate → Google` 作为"首选备选"被新标准禁止
3. 搜狗搜索（sogou.com）的 antispider 问题仍然存在，但 httpx 直连仍可用

### 修改复杂程度：**中等**
- SKILL.md 中"⚠️ 搜索工具故障链"章节需全面更新
- 故障恢复链表的 Exa 条目可以移除或标注为已修复
- `browser_navigate → Google` 的做法需删除
- 但 httpx→sogou/baidu 的回退逻辑与新标准不冲突，可保留

---

## 3. movie-watchlist/

### 使用了哪些搜索/提取方式
| 工具 | 用途 | 优先级 |
|------|------|--------|
| `web_search` | 搜索豆瓣榜单（方法A） | 🥇 主方案 |
| `browser_navigate` | 访问豆瓣 Explore 页面、豆瓣详情页（方法A） | 🥇 主方案 |
| Camofox 浏览器 | 豆瓣详情页提取（方法B 回退）+ 迅雷云盘登录 | 🥈 回退 |
| `browser_click` | 点击"加载更多" | 🥇 配合 browser_navigate |

注意：curl 被标记为**不可用**（豆瓣有 SHA-512 安全验证）。

### Exa / SerpAPI 引用
**无**。未发现任何 Exa 或 SerpAPI 引用。

### 是否需要修改
**可能不需要或极少量修改**。该 skill 主要依赖 `browser_navigate`（新标准允许的）和 `web_search`（新标准下走 Parallel MCP）。Camofox 是独立的本地工具，与新标准不冲突。

### 修改复杂程度：**简单**
- 如需确保 `web_search` 在新后端下正常工作，可能需要极小调整
- 主要工作流程不变

---

## 4. drone-weather/

### 使用了哪些搜索/提取方式
| 工具 | 用途 | 优先级 |
|------|------|--------|
| `curl` | NOAA FTP / AWC API / OGIMET 获取 METAR/TAF | 🥇 主方案 |
| `urllib.request` | nanjing_cloud_check.py 中获取 Moji 天气 + Open-Meteo API | 🥇 主方案 |
| `web_extract` | **明确标记为不可用**（Exa 拦截 aviationweather.gov） | ❌ 不使用 |

**关键发现**：该 skill 的 SKILL.md 明确写着：
> "Important: use curl, not web_extract — The web_extract tool routes through Exa which can block aviationweather.gov URLs."
> "Do NOT use web_extract for METAR fetching — Exa may have exhausted credits or block the URL"

### Exa / SerpAPI 引用
**无直接 Exa 引用**。但 SKILL.md 提及 web_extract 底层路由到 Exa，且 Exa 可能额度耗尽。

### 是否需要修改
**不需要**。该 skill 完全使用 curl 和 urllib.request 直连气象数据源（NOAA、AWC、Open-Meteo），不依赖 web_search 或 web_extract。现有的工作流与新标准完全兼容。

### 修改复杂程度：**无需修改**

---

## 5. football-prediction/

### 使用了哪些搜索/提取方式
| 工具 | 用途 | 优先级 |
|------|------|--------|
| `curl` | The Odds API / SerpAPI / Polymarket CLOB API / Polymarket book | 🥇 主方案 |
| `web_search` | 搜索比赛背景信息（新闻、伤病、H2H） | 🥇 主方案（Phase 2） |
| `web_extract` | 页面提取 | 🥇（提及但标注 Exa 配额问题）|
| SerpAPI | X/Twitter 搜索（API key 已配置） | 🥈 回退搜索 |
| Python（urllib.request 隐式） | 通过 curl 管道到 Python 解析 | 数据处理 |

### Exa / SerpAPI 引用
- **Exa**: ⚠️ 引用。Pitfalls 中标注："Exa credits can run out. Fall back to SerpAPI for search, direct curl for page scraping."
- **SerpAPI**: ⚠️ 重度依赖。SKILL.md 明确使用 SERPAPI_API_KEY、`serpapi.com/search.json` 端点、`data.get('organic_results',[])` 等。SerpAPI 被列为 Exa 失效后的首选回退。

### 是否需要修改
**是**。主要问题：
1. SerpAPI 已废弃，需要将搜索回退链路改为 web_search (Parallel MCP)
2. SKILL.md 中所有 SerpAPI 调用示例需要移除或替换
3. `SERPAPI_API_KEY` 环境变量引用需要移除

### 修改复杂程度：**中等**
- SKILL.md 中 Phase 2b 有 SerpAPI 完整调用示例（含 `curl -s "https://serpapi.com/search.json?...&api_key=***"`）
- 需替换为 `web_search` 工具调用
- The Odds API 和 Polymarket API 的 curl 调用不受影响

---

## 6. gaokao-essay-predictor/

### 使用了哪些搜索/提取方式
| 工具 | 用途 | 优先级 |
|------|------|--------|
| `web_search` | 搜索高考热点、模拟考作文题、年度事件 | 🥇 主方案 |
| `execute_code` + `httpx` | Exa 降级时直连源站或 Wikipedia API | 🥈 回退 |
| `browser_navigate` | WAF 拦截时用浏览器渲染 | 🥉 回退 |
| `curl` | 少量提及（被 WAF 拦截时） | 🥉 极限回退 |
| `lark-cli docs +fetch/+update` | 飞书文档读取/更新 | 知识库管理 |

### Exa / SerpAPI 引用
- **Exa**: ⚠️ 引用。SKILL.md pitfalls 明确标注："⚠️ Exa API 额度耗尽→百度/Wikipedia/httpx 搜索回退"。`web_search`/`web_extract` 共享 Exa 后端。
- **SerpAPI**: 未引用。

### 是否需要修改
**可能不需要或少量修改**。该 skill 的搜索策略已经以 httpx 直连为回退方案，且核心工作流围绕本地飞书文档和参考文件。切换到新标准后：
- web_search 使用 Parallel MCP（不再 402），主搜索链路恢复
- 现有的 httpx 回退方案可作为增强而非必须

### 修改复杂程度：**简单**
- 主要更新：SKILL.md 中的陷阱提示（移除 Exa 402 相关描述）
- 现有的 httpx 直连逻辑可保留作为备用

---

## 7. polymarket/

### 使用了哪些搜索/提取方式
| 工具 | 用途 | 优先级 |
|------|------|--------|
| `curl` | Gamma API / CLOB API / Data API 查询 | 🥇 主方案 |
| `urllib.request` | scripts/polymarket.py 中所有 API 调用 | 🥇 主方案 |
| **无** web_search / web_extract / browser_navigate | 不涉及外部搜索或网页提取 | — |

该 skill 完全通过 Polymarket 官方公开 REST API 获取数据，**不依赖**任何搜索引擎或网页内容提取工具。API 端点包括：
- `gamma-api.polymarket.com`（搜索/浏览）
- `clob.polymarket.com`（实时价格/订单簿）
- `data-api.polymarket.com`（交易/持仓）

### Exa / SerpAPI 引用
**无**。完全独立于 Exa 和 SerpAPI。

### 是否需要修改
**不需要**。该 skill 不涉及网页搜索或内容提取工具，全部使用 REST API 调用，与新标准链路无关。

### 修改复杂程度：**无需修改**

---

## 汇总表

| Skill | 主要搜索方式 | 主要提取方式 | Exa? | SerpAPI? | 需修改? | 复杂度 |
|-------|-------------|-------------|------|----------|---------|--------|
| **hotlist-analyzer** | `web_search`, `httpx`→新闻站, DDG/Bing/Google | `web_extract`, `httpx`, `urllib`, `browser_navigate`, `curl` | ✅ 重度 | ✅ 引用 | ✅ 是 | 🔴 **复杂** |
| **jiangsu-gaokao-expert-v3** | `web_search`, `httpx`→sogou/baidu, `browser_navigate`→Google | `web_extract`, `httpx`→直连, `curl` | ✅ 依赖 | 无 | ✅ 是 | 🟡 **中等** |
| **movie-watchlist** | `browser_navigate`→豆瓣, `web_search` | `browser_navigate`→豆瓣详情, Camofox | 无 | 无 | ⚠️ 极小 | 🟢 **简单** |
| **drone-weather** | `curl`→NOAA/AWC/OGIMET | `curl`, `urllib.request`→Open-Meteo/Moji | 无(刻意规避) | 无 | ❌ 否 | — |
| **football-prediction** | `web_search`, SerpAPI | `curl`→Odds API, Polymarket API | ✅ 提及 | ✅ 重度 | ✅ 是 | 🟡 **中等** |
| **gaokao-essay-predictor** | `web_search` | `httpx`→源站/Wikipedia | ✅ 提及 | 无 | ⚠️ 少量 | 🟢 **简单** |
| **polymarket** | `curl`/`urllib`→Polymarket API | `curl`/`urllib`→Polymarket API | 无 | 无 | ❌ 否 | — |

## 优先级建议

1. 🔴 **高优先级**（需立即修改，否则功能受影响）：
   - **hotlist-analyzer** — 最复杂，Exa 降级逻辑是整个 SKILL.md 的核心骨架
   - **football-prediction** — SerpAPI 已废弃，搜索回退链断裂

2. 🟡 **中优先级**（建议尽快更新）：
   - **jiangsu-gaokao-expert-v3** — 需要更新故障恢复链和删除 `browser_navigate→Google`

3. 🟢 **低优先级**（可改可不改）：
   - **gaokao-essay-predictor** — 更新陷阱提示即可
   - **movie-watchlist** — 极小调整

4. ✅ **无需修改**：
   - **drone-weather** — 已独立于 Exa/SerpAPI
   - **polymarket** — 纯 REST API，不涉及搜索/提取工具
