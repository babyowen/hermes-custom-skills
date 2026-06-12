# WC2026 赔率数据源参考

> 世界杯比赛赔率的实时获取方式和可用源。
> 注意：本服务器有 Transport endpoint 网络限制，Python 脚本的 HTTP 请求可能失败。
> 安全的获取手段：web_extract（首选）、web_search（备选），以及 `execute_code` + `httpx`（部分可用）。

---

## 已验证可用的数据源

### 1. Polymarket（预测市场 ✅ 已接入）

| 属性 | 内容 |
|------|------|
| 类型 | 去中心化预测市场（区块链） |
| 数据 | 72场小组赛 + 淘汰赛 + 冠军/分组头名 |
| 获取方式 | `web_search`/`web_extract` 爬体育页面；也可用公开API |
| 格式 | 概率形式（62¢ = 62%隐含概率） |
| 特点 | 信息效率高，对新闻反应快；无需API key |
| 当前状态 | 2026-05-23 已录入24场赔率到match pages |

**公开API（已验证）**：
```python
# 1. Event搜索（赛事级别，如世界杯冠军市场）
GET https://gamma-api.polymarket.com/events?tag=fifa-world-cup&closed=false&limit=100
# 2026 FIFA World Cup Winner — event_id=30615, slug=2026-fifa-world-cup-winner-595

# 2. CLOB市场数据（所有tagged markets）
GET https://clob.polymarket.com/sampling-markets?league=fifa-world-cup&limit=200
# 返回1000+条，含question、condition_id、tokens(含price)
# caution: 这个endpoint返回ALL markets tagged 'fifa-world-cup'，含非体育市场
# 体育单场比赛的match markets在单独的 sports CLOB 系统中

# 3. Simplified markets（不含question字段，仅token价格）
GET https://clob.polymarket.com/sampling-simplified-markets?league=fifa-world-cup&limit=100

# 4. 简化市场列表
GET https://clob.polymarket.com/simplified-markets?tag=sports&limit=100
```

**⚠️ 已知限制**：
- 体育单场比赛市场（如巴西vs摩洛哥胜负盘）不在gamma-api事件系统中，改用 sports CLOB 系统
- sports CLOB的API端点无公开文档，`clob.polymarket.com/sports/*` 返回404
- 稳定的数据提取方式：`web_search`/`web_extract` 抓取体育页面HTML
- 体育页面URL模式：`polymarket.com/sports/fifa-world-cup/fifwc-{t1code}-{t2code}-{date}`
- 示例：`polymarket.com/sports/fifa-world-cup/fifwc-bra-mar-2026-06-13`

### JSON-LD结构化数据提取（Exa断供时的首选备选）

当 `web_extract`/`web_search` 因 Exa API 额度耗尽（HTTP 402）不可用时，**curl直采Polymarket页面 + 提取JSON-LD结构化数据**是获取所有比赛赔率的最可靠方式。

**原理**：Polymarket的 `polymarket.com/sports/fifa-world-cup/games` 页面在HTML的 `<script type="application/ld+json">` 标签中嵌入了完整的比赛赔率数据（CollectionPage schema），包含所有已开盘小组赛的名称、赔率、URL。

**提取脚本**（实测通过 2026-06-01）：
```bash
# Step 1: curl下载页面
curl -sL -o /tmp/polymarket_odds.html \
  "https://polymarket.com/sports/fifa-world-cup/games"

# Step 2: Python解析JSON-LD
python3 -c "
import json, re
with open('/tmp/polymarket_odds.html') as f:
    html = f.read()
pattern = r'<script type=\"application/ld\+json\"[^>]*>(.*?)</script>'
matches = re.findall(pattern, html, re.DOTALL)
for m in matches:
    try:
        data = json.loads(m)
        if data.get('@type') == 'CollectionPage':
            items = data.get('mainEntity', {}).get('itemListElement', [])
            for item in items:
                ev = item.get('item', {})
                name = ev.get('name', 'Unknown')
                offers = ev.get('offers', {})
                if isinstance(offers, list):
                    price = offers[0].get('price', 'N/A') if offers else 'N/A'
                else:
                    price = offers.get('price', 'N/A')
                prob = round(float(price) * 100) if price != 'N/A' else 'N/A'
                print(f'{name}: {prob}%')
    except:
        pass
"
```

**输出示例**（2026-06-01，20场比赛）：
```
Mexico vs. South Africa: 69%
Korea Republic vs. Czechia: 35%
Canada vs. Bosnia and Herzegovina: 54%
United States vs. Paraguay: 49%
Brazil vs. Morocco: 61%
Germany vs. Curaçao: 94%
...
```

**注意事项**：
- Polymarket的JSON-LD输出是**二元预测市场**（胜/负），不含平局赔率。写入match pages时平局列用 `—` 标记
- 页面是Next.js/React渲染，但JSON-LD数据是SSR嵌入的，curl可直接获取（无需浏览器）
- JSON-LD中的 `price` 字段单位为美元（0.69 = 69%概率）
- 一天至少运行一次即可（赔率日内变动不剧烈，每日差值足够）
- 赛前3天内赔率波动加大时，可增加采集频率

**与web_extract的对比**：
| 方法 | Exa 402时可用 | 数据量 | 可靠性 |
|------|:------------:|:------:|:------:|
| web_extract | ❌ | 全文 | — |
| curl + JSON-LD | ✅ | 20条(单页) | ✅ 稳定 |
| SerpAPI + 逐场搜索 | ✅ | 少量 | ⚠️ 慢 |

**推荐**：当 Exa 可用时用 `web_extract` 抓取全部详情；当 Exa 断供时，curl + JSON-LD 作为日常赔率更新的首选备选。

---

**示例请求**（从之前session实际生效的搜索）：
```
web_search(query="Polymarket World Cup 2026 odds group stage matches June 2026")
```

**数据形态**：
```
Brazil vs Morocco: BRA 62¢ (61%) / Draw 24¢ (22%) / MAR 17¢ (16%)
USA vs Paraguay:   USA 51¢ (47%) / Draw 27¢ (25%) / PAR 26¢ (24%)
```

---

### 2. The Odds API（博彩公司赔率综合 ⭐ 强烈推荐）

| 属性 | 内容 |
|------|------|
| URL | https://the-odds-api.com |
| 免费额度 | 1000请求/月（足够每日拉取全部72场） |
| 覆盖 | 80+家博彩公司（Bet365、Pinnacle、DraftKings、FanDuel等） |
| 接入方式 | REST API，注册即得免费API key |
| 数据格式 | 传统赔率（十进制/分数/美式），可转换为隐含概率 |

**关键端点**：
```
GET https://api.the-odds-api.com/v4/sports/{sport_key}/odds/?apiKey={key}&regions=us,uk,eu&markets=h2h
# sport_key for World Cup: soccer_fifa_world_cup (FIFA国际赛)
```

**注册步骤**（一次性的）：
1. 访问 https://the-odds-api.com 注册免费账号
2. 获取 API key
3. 存入 `.env` 文件：`ODDS_API_KEY=your_key_here`

**价值**：提供 Polymarket 之外的独立信号——博彩赔率反映市场深度，预测市场反映信息效率，两者交叉可发现市场分歧点（value bet signals）。

---

### 3. Kalshi（CFTC监管预测市场）

| 属性 | 内容 |
|------|------|
| URL | https://kalshi.com |
| 类型 | 美国合规预测市场 |
| 数据 | 分组头名赔率、冠军赔率、部分淘汰赛 |
| 获取方式 | REST API（需注册账号和API key） |
| 特点 | CFTC监管，美国用户主流选择；分组头名市场成交量高 |

**已知endpoint**：
```
GET https://trading-api.kalshi.com/trade-api/v2/events?status=open&search_term=world+cup
```
需要API key认证。

---

## 赔率数据合并策略

### 比赛页格式
每个match page的 `📈 赔率历史` 表格建议格式：

```
| 日期 | 队名1(Polymarket) | 平局 | 队名2 | 队名1(博彩平均) | 平局 | 队名2 | 来源 |
```

### 两条曲线的分析价值
- **Polymarket** — 信息效率高，大新闻后几分钟内反映
- **博彩赔率** — 市场深度好，受大户资金影响，比Polymarket更稳定
- **信号分歧** → 当Polymarket看好A队而博彩赔率看低A队时，可能存在值得深挖的信息不对称

### 日常采集逻辑
每天的 cron 按以下优先级采集赔率——优先 web_extract，Exa断供时切 curl + JSON-LD：
```
① 从 Polymarket 提取当前所有72场赔率
   - 首选: web_extract(polymarket.com/sports/fifa-world-cup/games)
   - Exa断供备选: curl + JSON-LD提取（见上方 JSON-LD 节）
② 如果 The Odds API key 已配置，提取博彩赔率
③ 两边数据存入对应 match page 的赔率历史表格（追加新行）
④ 标注数据来源日期
```

### 首次批量填充时的注意点
第一次填充72场时，不要逐场提取（太慢）。使用 `execute_code` 在单次调用中批量拉取数据，然后批量更新文件。如果web_search的返回格式包含多个比赛数据，一次性解析所有可用比赛。

---

## 各赔率形式间的转换

| 形式 | 例子 | 概率公式 | 结果 |
|------|------|----------|------|
| Polymarket ¢ | 62¢ | `概率 = ¢/100` | 62% |
| 十进制 (Decimal) | 1.61 | `概率 = 1/赔率` | 62% |
| 美式 (Moneyline) | -164 | `概率 = 赔率/(赔率+100)` 或 `100/(赔率+100)` | 62% |
| 分数 (Fractional) | 5/8 | `概率 = 分母/(分子+分母)` | 61.5% |

**注意**：Polymarket的¢和博彩赔率的隐含概率通常不完全一致，因为：
- Polymarket没有庄家抽水（vig/juice）
- 博彩赔率中包含庄家利润（通常5-10%）
- 因此Polymarket的概率总和接近100%，而博彩赔率概率总和>100%
