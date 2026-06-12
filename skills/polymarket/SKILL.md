---
name: polymarket
description: "Query Polymarket: markets, prices, orderbooks, history."
version: 1.0.0
author: Hermes Agent + Teknium
tags: [polymarket, prediction-markets, market-data, trading]
platforms: [linux, macos, windows]
---

# Polymarket — Prediction Market Data

Query prediction market data from Polymarket using their public REST APIs.
All endpoints are read-only and require zero authentication.

See `references/api-endpoints.md` for the full endpoint reference with curl examples.

## When to Use

- User asks about prediction markets, betting odds, or event probabilities
- User wants to know "what are the odds of X happening?"
- User asks about Polymarket specifically
- User wants market prices, orderbook data, or price history
- User asks to monitor or track prediction market movements

## Key Concepts

- **Events** contain one or more **Markets** (1:many relationship)
- **Markets** are binary outcomes with Yes/No prices between 0.00 and 1.00
- Prices ARE probabilities: price 0.65 means the market thinks 65% likely
- `outcomePrices` field: JSON-encoded array like `["0.80", "0.20"]`
- `clobTokenIds` field: JSON-encoded array of two token IDs [Yes, No] for price/book queries
- `conditionId` field: hex string used for price history queries
- Volume is in USDC (US dollars)

## Three Public APIs

1. **Gamma API** at `gamma-api.polymarket.com` — Discovery, search, browsing
2. **CLOB API** at `clob.polymarket.com` — Real-time prices, orderbooks, history
3. **Data API** at `data-api.polymarket.com` — Trades, open interest

## ⚠️ Search Pitfall: Sports Markets (EPL, etc.)

EPL and other sports match markets use a **slug-based** event pattern like `epl-{home_abbr}-{away_abbr}-YYYY-MM-DD`
(e.g. `epl-tot-eve-2026-05-24`). **Keyword searching** for team names ("Tottenham", "Everton") in the Gamma
`/markets` or `/events` endpoints often **returns no results** because the questions are formatted as
"Will Tottenham Hotspur FC win on 2026-05-24?" — which the Gamma search doesn't index well.

**Correct approach**:
1. Use **`events?slug={slug}`** with the event-level slug string for exact match
2. Filter by **`tag=sports`** or **related tags** rather than relying on text search
3. If the user provides a **Polymarket URL**, extract the slug from the path (e.g. `/sports/epl/epl-tot-eve-2026-05-24` → `epl-tot-eve-2026-05-24`)
4. The event contains **three sub-markets** for a match: Home Win, Draw, Away Win — each with its own `conditionId` and `clobTokenIds`

See `references/sports-market-finding.md` for the exact curl commands.

## Three-Source Odds Analysis Framework

When a user asks about betting value or whether to trade on Polymarket, cross-reference
**three independent sources**:

| Source | What it represents | How to use |
|--------|-------------------|------------|
| **Sharp (Pinnacle / Betfair)** | Professional bettors' consensus — most accurate public probability signal | De-vig (remove ~3% fee) to get "true probability" benchmark |
| **Retail (William Hill, Ladbrokes, etc.)** | Casual bettors, higher vig, slower to react | Compare vs Sharp to identify where retail public money is driving mispricing |
| **Polymarket price** | On-chain market consensus | Directly comparable to Sharp/Retail probabilities (same 0-1 scale) |

### Value Detection Formula

```
Value = P(Sharp de-vig) - P(Polymarket) - Friction
```

Where **Friction** = taker fee (Sports: 0.03%) + slippage (bid-ask spread × order size) + gas.

| Value > 0 | Polymarket underpriced → buy Yes |
| Value < 0 | Polymarket overpriced → buy No or skip |
| |Value| > 5% | Strong signal — Sharp money disagrees with prediction market |

### Money Flow Signal (Trend)

Use `oneDayPriceChange`, `oneWeekPriceChange`, `oneMonthPriceChange` from Gamma API
market fields to detect **capital flows**:

- A +5% weekly change on Tottenham but -7% on Everton suggests money is rotating INTO Tottenham
- Compare trend magnitude vs fundamentals (injury news, lineups) — if trend overshoots, the fade has value
- **Empty price history** is common for new markets — in that case rely on Gamma API's
  `oneDayPriceChange` / `oneWeekPriceChange` fields instead

### Orderbook Depth Check (Before Trading)

Before suggesting a trade, verify **liquidity**:

```python
# Use CLOB /book endpoint
curl -s "https://clob.polymarket.com/book?token_id={YES_TOKEN_ID}"
```

Key metrics:
- **Spread < 0.02** (2 cents) — tight market, safe to trade
- **Total depth on best 5 levels** — if < $10K on your side, slippage will eat profits
- **Polymarket fee structure**: Sports = 3% taker / 0% maker + 25% maker rebate
  → **Always prefer limit (Maker) orders** to avoid fees and earn rebates

See `references/odds-analysis-framework.md` for the full de-vig formula, worked examples,
and a Python code snippet for automated comparison.

## Typical Workflow

When a user asks about prediction market odds or betting value:

1. **Identify the market** — use search (with slug approach for sports) or ask for the URL
2. **Gather Sharp odds** — query The Odds API or Pinnacle directly for the same event
3. **Gather Polymarket data** — prices, orderbook depth, weekly trends
4. **Cross-reference** — compute de-vig Sharp probabilities, compare to Polymarket
5. **Check friction** — spread, fees, depth — can you actually execute at these prices?
6. **Present analysis** — highlight discrepancies, money flow trends, and concrete trade suggestions
7. **Give a clear final prediction** when asked — use team news, form, H2H, and market data:
   - Combine odds with **match context** (injuries, stakes, home/away, H2H record)
   - Sharp odds give the probability; fundamentals tell you **which outcome feels right**

## Presenting Results

Format prices as percentages for readability:
- outcomePrices `["0.652", "0.348"]` becomes "Yes: 65.2%, No: 34.8%"
- Always show the market question and probability
- Include volume when available

Example: `"Will X happen?" — 65.2% Yes ($1.2M volume)`

## Parsing Double-Encoded Fields

The Gamma API returns `outcomePrices`, `outcomes`, and `clobTokenIds` as JSON strings
inside JSON responses (double-encoded). When processing with Python, parse them with
`json.loads(market['outcomePrices'])` to get the actual array.

## Rate Limits

Generous — unlikely to hit for normal usage:
- Gamma: 4,000 requests per 10 seconds (general)
- CLOB: 9,000 requests per 10 seconds (general)
- Data: 1,000 requests per 10 seconds (general)

## Limitations

- This skill is read-only — it does not support placing trades
- Trading requires wallet-based crypto authentication (EIP-712 signatures)
- Some new markets may have empty price history
- Geographic restrictions apply to trading but read-only data is globally accessible

## Extended Resources

- `references/sharp-odds-framework.md` — Three-source value betting framework: Sharp (Pinnacle) de-vig probabilities vs Polymarket prices vs Retail odds. Includes orderbook depth checks, weekly money flow signals, and lineup-calibrated adjustments.


