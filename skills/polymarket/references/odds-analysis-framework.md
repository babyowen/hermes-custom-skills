# Odds Analysis Framework

## Sharp (Pinnacle) De-Vig Methodology

### Why De-Vig?

Bookmaker odds include **vigorish (vig/fee)** — the house's cut.
Pinnacle's ~3% vig is the lowest in the industry but still needs removal
to get an accurate probability estimate.

### Step 1: Convert odds to implied probabilities

```
Implied Probability = 1 / Decimal Odds
```

### Step 2: Find the overround (total vig)

```
Overround = Sum of all implied probabilities
Pinnacle typical: ~2.5-3.5%
Retail typical: ~5-12%
```

### Step 3: Remove vig (Multiplicative method — recommended)

```
True Probability = Implied Probability / Overround
```

### Worked Example: Tottenham vs Everton (Pinnacle)

| Outcome | Odds | Implied | True (de-vig) |
|---------|:----:|:-------:|:-------------:|
| Home (TOT) | 1.97 | 50.76% | 49.3% |
| Draw | 3.57 | 28.01% | 27.2% |
| Away (EVE) | 4.14 | 24.15% | 23.5% |
| **Sum** | | **102.92%** | **100.0%** |

### Python De-Vig Helper

```python
def devig_multiplicative(odds: list[float]) -> list[float]:
    """Remove vig from a list of decimal odds using multiplicative method."""
    implied = [1/o for o in odds]
    overround = sum(implied)
    return [i / overround for i in implied]

# Pinnacle example
devig_multiplicative([1.97, 3.57, 4.14])
# Returns: [0.493, 0.272, 0.235]
```

## Three-Source Comparison

### Data Sources

| Source | Access Method | Vig | Best For |
|--------|--------------|:---:|----------|
| Pinnacle (Sharp) | The Odds API or direct scrape | ~3% | **Benchmark** — most accurate probability |
| Retail books | The Odds API (many bookmakers) | 5-12% | **Identifying public bias** — where casual money flows |
| Polymarket | Gamma API + CLOB API | ~3% fee | **Tradeable market** — you can actually bet here |

### Value Detection Example

```
Pinnacle True Probability:  Home 49.3% | Draw 27.2% | Away 23.5%
Polymarket Price:          Home 0.505  | Draw 0.265 | Away 0.235

Analysis:
  Home: +1.2% (slightly overpriced on Polymarket)  → ❌ avoid
  Draw: -0.7% (slightly underpriced)                → ⚠️ marginal value
  Away:  0.0% (exact match)                         → ↔️ neutral
```

### Signal Strength Matrix

| Scenario | Strength | Action |
|----------|:--------:|--------|
| Polymarket > Pinnacle +5% | ⭐⭐ | Overpriced — sell/short or avoid |
| Polymarket < Pinnacle -5% | ⭐⭐⭐ | Underpriced — buy if depth is adequate |
| Polymarket ≠ Retail + Pinnacle agrees with one | ⭐⭐ | Follow the two aligned sources |
| All three within 2% | ⭐ | Efficient market — no actionable edge |
| 1-week trend > 5% against fundamentals | ⭐⭐⭐ | Fade the move — trend likely overshot |

## Trend Analysis

Use the Gamma API market fields for quick trend detection:

```python
trends = {
    'home': {'1w_pct_change': m.get('oneWeekPriceChange')},  # e.g. +0.055
    'draw': {'1w_pct_change': m2.get('oneWeekPriceChange')}, # e.g. -0.015
    'away': {'1w_pct_change': m3.get('oneWeekPriceChange')}, # e.g. -0.075
}
```

**Interpretation**:
- Tottenham +5.5% in 1 week + Everton -7.5% = strong rotation INTO Tottenham
- Compare trend magnitude vs actual fundamentals (injuries, form)
- A 7.5% drop in Everton without corresponding negative news → potential overreaction → buy value

## Orderbook Depth Check

Before suggesting a trade, verify that the market can absorb the order:

```bash
curl -s "https://clob.polymarket.com/book?token_id={YES_TOKEN_ID}"
```

Key thresholds:
- **Bid-ask spread < 0.02** → healthy market
- **Top 5 levels total depth > $10K** → reasonable liquidity
- **Last trade price close to mid** → no manipulation

### Fee Consideration

Polymarket fee structure (Sports category):
- **Taker (market order)**: 3% of trade value — expensive for small edges
- **Maker (limit order)**: **0% fee** + 25% rebate on taker fees
- Always prefer Maker orders when the edge is < 5%

## Putting It Together: Full Workflow

```
1. Get odds: Pinnacle (The Odds API) + Polymarket (Gamma API)
2. De-vig Pinnacle to get Sharp benchmark probabilities
3. Compare Polymarket prices to benchmark
4. Check 1-week trends for money flow direction
5. Verify orderbook depth + spread
6. If edge > 3% after fees → actionable signal
7. If user wants a final prediction → ALSO check fundamentals:
   injuries, form, H2H, league stakes, lineup news
```
