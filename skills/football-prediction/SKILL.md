---
name: football-prediction
description: "Football match prediction workflow: fetch odds from 40+ bookmakers via The Odds API, research context (injuries/form/H2H/stakes) via web search, analyze sharp vs retail discrepancies, produce multi-factor prediction."
version: 2.0.0
tags: [football, soccer, prediction, odds, betting, premier-league, sports]
---

# Football Match Prediction

Predict football matches using a three-phase workflow: **Odds → Research → Synthesis**.

## When to Use

- User asks "who will win X vs Y?"
- User asks about odds, betting markets, or prediction markets for a football match
- User wants analysis of sharp vs retail betting discrepancies
- Any football match prediction request (league, cup, international)

## Phase 1: Fetch Odds via The Odds API

The API key is documented in the `wc2026-predictor` skill's SKILL.md (search for "The Odds API博彩赔率").

### 1a. Find the sport key

```bash
curl -s "https://api.the-odds-api.com/v4/sports?apiKey=KEY" | python3 -c "
import sys,json
for s in json.load(sys.stdin):
    if s.get('active'):
        print(f'{s[\"title\"]}: {s[\"key\"]}')
"
```

Active EPL key: `soccer_epl`

### 1b. Get odds for specific match

```bash
curl -s "https://api.the-odds-api.com/v4/sports/{sport_key}/odds?apiKey=KEY&regions=uk,us,eu&markets=h2h,spreads,totals&oddsFormat=decimal"
```

Filter for the specific teams using Python. The response includes `home_team`, `away_team`, `commence_time`, and `bookmakers[]` array.

### 1c. Identify Sharp bookmakers

The most reliable "sharp" (smart money) books to focus on:

| Bookmaker | Profile | Notes |
|:---|:---|:---|
| **Pinnacle** | Sharpest | Low margin, no limits, industry benchmark |
| **Betfair Exchange** | Sharp | Peer-to-peer exchange, real supply/demand |
| **Coolbet** | Sharp | Low margin, aggressive lines |
| **Smarkets** | Sharp | Exchange platform |
| **LowVig.ag** | Semi-sharp | Low juice operations |

Retail (public-facing) books for comparison: Bet365, Sky Bet, Paddy Power, William Hill, DraftKings, FanDuel, etc.

### 1d. Analyze Sharp vs Retail divergence

Compute implied probabilities from decimal odds: `probability = 1/odds`.

Key signal: when sharp books and retail books diverge by **>3%** on the same outcome, sharp money is usually right. The direction of divergence tells you which way the smart money leans.

## Phase 2: Research Context

### 2a. Search match context via web_search(Parallel)

Search for match context using Parallel 免费 MCP. Essential search queries:

```python
# All queries use web_search(Parallel) — free, fast
web_search("{team1} vs {team2} preview May 2026")       # match previews
web_search("{team1} injury news {team2} team news")      # injury/suspension
web_search("{team1} form last 5 games")                  # recent results
web_search("{team1} {team2} head to head")               # H2H record
web_search("{league} table standings relegation")        # league context
web_search("{manager} press conference {team}")          # pre-match quotes
```

### 2b. Search X/Twitter for breaking news (crucial!)

Press conferences, lineup leaks, and last-minute stories often break on X first.
Use the `x_search` tool (auto-enabled when XAI_API_KEY is configured):

```python
x_search("{manager} {team} {keyword} site:x.com")
```

Or use web_search(Parallel) with `site:x.com` prefix:

```python
web_search("site:x.com {manager} {team} press conference")
```

Look for:
- **Press conference quotes** (manager's actual words about tactics, injuries)
- **Captain/star player controversies** (Romero flying to Argentina before relegation decider — massive morale signal)
- **Squad selection surprises** (Spence earning last-minute World Cup call-up → confidence boost)
- **Fan sentiment** (backlash, protests, support)

### Key research dimensions

| Dimension | What to look for |
|:---|:---|
| Injuries | Which starters are out? Are returning players match-fit? |
| Form | Win/loss streaks, scoring trends, clean sheets |
| H2H | Recent meetings, home/away splits, score patterns |
| Stakes | Relegation battle? Title race? European qualification? |
| Motivation | Is one team already safe? Playing for nothing? |
| Manager news | New manager bounce? Pressure from board? Quotes from presser? |
| X sentiment | Breaking stories, lineup speculation, fan mood |

## Phase 2b: Check Polymarket (Three-Source Cross-Reference)

Polymarket **does** cover regular-season league matches (EPL, etc.) — not just major tournaments. See the
`polymarket` skill's `references/sports-market-finding.md` for the correct search method
(slug-based: `epl-tot-eve-YYYY-MM-DD`, not keyword search).

Each match event contains three sub-markets:
- Home Win (e.g. "Will Tottenham Hotspur FC win on 2026-05-24?")
- Draw (e.g. "Will ... end in a draw?")
- Away Win (e.g. "Will Everton FC win on 2026-05-24?")

Use the Gamma API to get prices and the Gamma API's `oneDayPriceChange` / `oneWeekPriceChange`
/ `oneMonthPriceChange` fields for **capital flow trend detection**:

| Value | Meaning |
|:---|:---|
| Tottenham +5.5% in 1w, Everton -7.5% | Strong rotation INTO Tottenham — money flow |
| All three within 2% change | No clear directional bias |
| Large move without matching news | Potential overreaction → fade opportunity |

- **Polymarket fee structure (Sports category)**: Taker 3%, Maker 0% + 25% rebate.
  Always prefer limit (Maker) orders to avoid fees on small edges (<5%).
See the `polymarket` skill's `references/odds-analysis-framework.md` for the full three-source
comparison methodology (Sharp de-vig + Retail + Polymarket).

## Phase 3: Multi-Factor Synthesis

Use a 10-dimension scoring framework (adapted from `wc2026-predictor` skill):

```
 1. Quality assessment (squad value, league position)
 2. Recent form (last 5-6 matches, scoring/defensive trends)
 3. Squad availability (injuries, suspensions, returns)
 4. Tactical matchup (style clash, formation advantages)
 5. H2H record (psychological edge, score patterns)
 6. External factors (home/away, weather, rest days)
 7. Key player factor (star individual vs opponent weakness)
 8. Pressure psychology (must-win vs nothing-to-lose)
 9. Expert/preview consensus (weighted by credibility)
10. Odds divergence (sharp/retail spread as signal)
```

## Phase 4: Present Results

The user wants a **final result prediction** — not just probability analysis. Lead with the answer,
then back it up with evidence.

Desired output structure:

```
## ⚽ Team A vs Team B | Match Name

### 📋 Basic Info
- Venue, kickoff time (user's timezone), competition, stakes

### 🔥 Background
- League context, form, narrative (1-2 paragraphs)

### 🏥 Team News
- Key injuries/returns for both sides
- X-derived info: press conference quotes, lineup speculation

### 📈 Odds Analysis (Sharp vs Retail vs Polymarket)
- Table: outcome | Sharp odds | Retail avg | Polymarket | Sharp implied %
- Divergence signals (>3% = noteworthy) and trend detection (1-week money flow)
- Over/Under and spread analysis

### 🎯 Prediction (LEAD WITH THIS)
- **Most likely outcome** and scoreline (e.g. "1-1 draw — 35% probability")
- Secondary outcomes and their probabilities
- Brief reasoning (2-3 sentences tying odds + fundamentals + game-state logic together)
```

## Phase 5: Game-State Logic (Critical)

When predicting a football match, the **current score + points situation** fundamentally
changes how teams play. Always consider:

| Scenario | Impact on behavior |
|:---|:---|
| Team needs **1 point** to survive/qualify | Will NOT push for winner in final 15 min — will protect the draw. Assume ~80% chance they sit deep. |
| Team **must win** to survive | Will take risks, push numbers forward — leaves defensive gaps. |
| Team is **already safe** | Motivation drops 30-50%. Intensity likely lower. |
| Team is playing for **nothing** | Risk of "holiday mode" — intensity may be down, more defensive errors. |
| Team chasing a **record/milestone** | Extra motivation — striker chasing golden boot, manager milestone, etc. |

**Never assume a closed game stays open** — if the score hits the team's minimum
requirement (e.g. 1-1 when 1 point is enough), the game dynamic shifts radically.

## Pitfalls

- **API key month limit**: The Odds API free tier has 500 requests/month. Track usage. WC2026 cron jobs consume ~60/month.
- **搜索链路（Parallel 免费 MCP）**：搜索用 web_search(Parallel)，提取用 web_extract(Parallel)，提取失败降级 browser_navigate(本地Chrome) + eval body.innerText。全部免费。
- **Polymarket DOES have EPL matches** — don't skip it. Use slug-based event search (`epl-tot-eve-YYYY-MM-DD`),
  not keyword search. See `polymarket` skill's `references/sports-market-finding.md`.
- **Polymarket orderbook depth** — before recommending a trade, verify liquidity:
  ```bash
  curl -s "https://clob.polymarket.com/book?token_id={YES_TOKEN_ID}"
  # Check: spread < 0.02, top-5 depth > $10K
  ```
  A great price is useless if the orderbook can't absorb the trade.
- **Odds format**: Always use `oddsFormat=decimal` for calculation ease. Convert to implied probability with `1/price`.
- **Betting margins**: Sum of implied probs typically ~103-107% (the vig/juice). Always de-vig before comparing sources.
- **Sharp doesn't mean correct**: Sharp books have better information flow but still get it wrong. Use as a signal, not an oracle.
- **Game-state logic trumps odds**: A Sharp 55% favorite with nothing to play for at 1-1 is not really 55%.
  Account for motivation in your final prediction, especially in the final 15 minutes.
- **Press conference quotes > media speculation**: Manager's actual words (from X/transcripts) are more reliable
  than pundit predictions. Search for the official press conference transcript or X clips.
- **Trend does not equal value**: A 1-week +5.5% move may already be fully priced in.
  Compare the magnitude against fundamentals — if news doesn't justify the move, the fade is the value.
