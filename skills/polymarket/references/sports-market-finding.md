# Sports Market Finding on Polymarket

## The Slug Problem

EPL match markets use a specific slug format that **keyword search cannot find**.
Pattern: `epl-{home_abbr}-{away_abbr}-YYYY-MM-DD`

Examples:
- Tottenham vs Everton: `epl-tot-eve-2026-05-24`
- Liverpool vs Man City: `epl-liv-mci-YYYY-MM-DD`
- Arsenal vs Chelsea: `epl-ars-che-YYYY-MM-DD`

Abbreviations follow standard 3-letter EPL codes (TOT, EVE, LIV, MCI, ARS, CHE, MUN, etc.).

## Correct Finding Method

### Method 1: Exact slug via events API (preferred when URL known)

```bash
curl -s "https://gamma-api.polymarket.com/events?slug=epl-tot-eve-2026-05-24"
```

Returns a single event with three sub-markets:
- "Will {Home} FC win on YYYY-MM-DD?" → Home Win
- "Will {Home} vs {Away} end in a draw?" → Draw
- "Will {Away} FC win on YYYY-MM-DD?" → Away Win

### Method 2: Search by tag (sports category)

```bash
curl -s "https://gamma-api.polymarket.com/events?active=true&closed=false&limit=20&tag=sports"
curl -s "https://gamma-api.polymarket.com/events?active=true&closed=false&limit=20&tag=football"
```

Note: `tag=football` may return political events like Super Bowl bets.
`sports` tag is more reliable for league matches.

### Method 3: URL extraction (when user provides link)

User URL: `https://polymarket.com/zh/sports/epl/epl-tot-eve-2026-05-24`
→ Extract slug: `epl-tot-eve-2026-05-24`
→ Query: `/events?slug=epl-tot-eve-2026-05-24`

The path segments give clues: `/sports/epl/` indicates category/league.

## Extracting Market Details

Once you have the event, extract per-market data:

```python
import json

event = data[0]  # single event
for m in event['markets']:
    prices = json.loads(m['outcomePrices'])
    clob_tokens = json.loads(m['clobTokenIds'])
    condition_id = m['conditionId']
    
    print(f"Question: {m['question']}")
    print(f"  Yes: {float(prices[0]):.3f} / No: {float(prices[1]):.3f}")
    print(f"  Volume: ${float(m.get('volume',0)):,.0f}")
    print(f"  Best Bid/Ask: {m.get('bestBid')}/{m.get('bestAsk')}")
    print(f"  Spread: {m.get('spread')}")
    print(f"  1W Change: {m.get('oneWeekPriceChange')}")
    print(f"  ConditionID: {condition_id}")
    print(f"  Yes TokenID: {clob_tokens[0]}")
```

## Common Pitfalls

- ❌ Searching by team name in `/markets` — Gamma API doesn't index sports market questions well
- ❌ Filtering by `tag=epl` — the tag likely doesn't exist; use `tag=sports`
- ✅ Search by **event slug** — always works when you know the match
- ✅ **Ask the user for the URL** if initial search fails — they likely already have it
