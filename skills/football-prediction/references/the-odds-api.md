# The Odds API Reference

**Base URL**: `https://api.the-odds-api.com/v4`
**API Key**: `e957983e5449073eedc1e6fafc619a74` (500 req/month free tier, shared with WC2026)

## Available Sports (active)

```bash
curl -s "https://api.the-odds-api.com/v4/sports?apiKey=KEY" | jq '[.[] | select(.active==true) | {title, key, group}]'
```

## Key Football Sport Keys

| League | Key |
|:---|:---|
| English Premier League | `soccer_epl` |
| UEFA Champions League | `soccer_uefa_champions_league` |
| UEFA Europa League | `soccer_uefa_europa_league` |
| La Liga | `soccer_spain_la_liga` |
| Serie A | `soccer_italy_serie_a` |
| Bundesliga | `soccer_germany_bundesliga` |
| Ligue 1 | `soccer_france_ligue_one` |
| FIFA World Cup | `soccer_fifa_world_cup` |

## Get Odds for a Match

```bash
curl -s "https://api.the-odds-api.com/v4/sports/{sport_key}/odds?apiKey=KEY&regions=uk,us,eu&markets=h2h,spreads,totals&oddsFormat=decimal"
```

### Parameters

| Param | Values | Description |
|:---|:---|:---|
| `regions` | `uk`, `us`, `eu`, `au` | Geographic bookmaker pools |
| `markets` | `h2h`, `spreads`, `totals` | Market types (comma-separated) |
| `oddsFormat` | `decimal`, `american` | Display format |

### Response Structure

```json
[
  {
    "id": "match_id",
    "sport_key": "soccer_epl",
    "sport_title": "EPL",
    "commence_time": "2026-05-24T15:00:00Z",
    "home_team": "Tottenham Hotspur",
    "away_team": "Everton",
    "bookmakers": [
      {
        "title": "Pinnacle",
        "markets": [
          {
            "key": "h2h",
            "outcomes": [
              {"name": "Tottenham Hotspur", "price": 1.97},
              {"name": "Draw", "price": 3.57},
              {"name": "Everton", "price": 4.14}
            ]
          },
          {
            "key": "spreads",
            "outcomes": [
              {"name": "Everton", "point": 0.5, "price": 1.94},
              {"name": "Tottenham Hotspur", "point": -0.5, "price": 1.98}
            ]
          },
          {
            "key": "totals",
            "outcomes": [
              {"name": "Over", "point": 2.5, "price": 1.94},
              {"name": "Under", "point": 2.5, "price": 1.96}
            ]
          }
        ]
      }
    ]
  }
]
```

## Sharp Bookmaker Identification

These are widely considered the sharpest books (lowest margins, smartest money):

| Bookmaker | `title` in API | Notes |
|:---|:---|:---|
| Pinnacle | `Pinnacle` | Industry gold standard |
| Betfair Exchange | `Betfair` | Peer-to-peer, multiple entries (different regions) |
| Coolbet | `Coolbet` | Low margin Nordic sharp |
| Smarkets | `Smarkets` | Exchange platform |
| LowVig.ag | `LowVig.ag` | Low juice US-facing |
| BetOnline.ag | `BetOnline.ag` | Semi-sharp US |
| Matchbook | `Matchbook` | Exchange |

## Implied Probability Conversion

```python
# Decimal odds to implied probability
def implied_prob(decimal_odds):
    return 1.0 / decimal_odds

# Remove vig (normalize to 100%)
def vig_free(home_odds, draw_odds, away_odds):
    home_p = 1/home_odds
    draw_p = 1/draw_odds
    away_p = 1/away_odds
    total = home_p + draw_p + away_p
    return home_p/total, draw_p/total, away_p/total
```

## Rate Limits

Generous — no documented per-second limit. But monthly cap is hard: 500 free requests. Request credits consumed per endpoint call, not per match returned. Each GET to the odds endpoint = 1 request regardless of how many matches/books it returns. Checking usage: the response header `x-requests-remaining` shows remaining count.
