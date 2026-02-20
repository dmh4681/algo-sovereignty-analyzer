# Sovereignty Scoring Methodology

## Overview

The Algorand Sovereignty Analyzer calculates a **Sovereignty Score** that measures one thing: how many years you could maintain your lifestyle using only your assets, with zero income. This document explains the philosophical framework, calculation methodology, asset classification logic, and how the scores connect to real-world financial independence.

---

## Philosophical Framework

### The Hard Money Maximalist Lens

The scoring system is built on **hard money maximalist** principles -- a worldview that distinguishes between assets that preserve purchasing power across generations and those that do not.

Throughout human history, only three asset classes have consistently held value across centuries, empires, and monetary regime changes:

| Asset | History | Scarcity Mechanism |
|-------|---------|-------------------|
| **Gold** | 5,000+ years of monetary use | Geological -- ~2% annual supply growth from mining |
| **Silver** | 4,000+ years of monetary use | Geological + industrial consumption reducing supply |
| **Bitcoin** | 15+ years (since 2009) | Cryptographic -- mathematically enforced 21M hard cap |

Everything else -- fiat currencies, stablecoins, altcoins, governance tokens -- is subject to supply manipulation, governance risk, or debasement. The system does not ignore these assets; it classifies and values them. But it draws a clear philosophical line about what constitutes *sovereign* wealth.

### What is Sovereignty?

Sovereignty, in this context, is the capacity to say "no" to income. It is the financial ability to refuse:

- A job that drains you because you need the paycheck
- Compromises on your values because of economic pressure
- Decisions made from scarcity rather than abundance

**Sovereignty is not about being rich.** It is about the ratio between your wealth and your needs. A person with $200,000 in hard assets and $2,000/month in expenses ($24,000/year) has a sovereignty ratio of 8.3 -- firmly in the "Antifragile" tier. A person with $2,000,000 and $20,000/month in expenses ($240,000/year) also has a ratio of 8.3. The dollar amount is irrelevant. The ratio is everything.

### The Formula

```
Sovereignty Ratio = Total Portfolio Value (USD) / Annual Fixed Expenses (USD)
```

The result is expressed in **years**: how many years you could sustain your essential expenses with zero income, funded entirely by your current holdings.

---

## Asset Classification

The system classifies all Algorand wallet holdings into four categories. Every asset in the wallet contributes to the total portfolio value used in the sovereignty calculation.

### Category 1: Hard Money

**Color**: Gold/Amber | **Mining Theme**: "Treasure Vault"

Assets that have preserved purchasing power across centuries. These are the foundation of financial sovereignty.

| Token | Type | Description |
|-------|------|-------------|
| goBTC | Bitcoin | Algorand-native wrapped Bitcoin via goMint |
| WBTC | Bitcoin | Wrapped Bitcoin bridged to Algorand |
| GOLD$ | Gold | Meld Gold -- physically backed gold token |
| XAUT | Gold | Tether Gold -- backed by London Good Delivery bars |
| PAXG | Gold | Paxos Gold -- backed by physical gold in London vaults |
| SILVER$ | Silver | Meld Silver -- physically backed silver token |

### Category 2: Algorand

**Color**: Amber | **Mining Theme**: Native token

The native token of the Algorand blockchain and its liquid staking derivatives. While not "hard money" by strict definition (no physical backing, relatively new blockchain), ALGO has a hard supply cap and proof-of-stake consensus. It is the platform these other assets exist on.

| Token | Description |
|-------|-------------|
| ALGO | Native Algorand token |
| xALGO | Folks Finance liquid staking (staked ALGO) |
| fALGO | Folks Finance wrapped ALGO |
| gALGO | Governance ALGO |
| mALGO | Messina ALGO |
| lALGO | Liquid ALGO variants |
| tALGO | Tinyman ALGO |

### Category 3: Dollars

**Color**: Green | **Mining Theme**: "Paper Money"

Stablecoins pegged to fiat currencies. Useful for short-term liquidity, but they inherit fiat's inflation problem. A dollar today buys less tomorrow. These are counted in the portfolio total because they have real purchasing power *today*, but they are philosophically distinct from hard money.

| Token | Description |
|-------|-------------|
| USDC | USD Coin by Circle |
| USDt / USDT | Tether USD |
| DAI | MakerDAO decentralized stablecoin |
| fUSDC | Folks Finance wrapped USDC |
| fUSDT | Folks Finance wrapped USDT |

### Category 4: Shitcoins

**Color**: Red | **Mining Theme**: "Raw Ore"

Everything else. Governance tokens, meme coins, NFTs, DEX tokens, LP tokens (after decomposition), and any asset that does not match the above patterns. These are speculative and carry high risk. They are still counted in the portfolio total because they have market value, but they are not considered dependable stores of wealth.

### Classification Hierarchy

The system uses a three-tier priority system for classifying assets:

```
Priority 1 (Highest): Manual CSV overrides (data/asset_classification.csv)
        |
        v
Priority 2 (Medium):  User-submitted corrections (data/user_corrections.json)
        |
        v
Priority 3 (Lowest):  Regex pattern matching (core/classifier.py)
        |
        v
    Default: shitcoin
```

### LP Token Decomposition

Liquidity Pool (LP) tokens from Tinyman, Pact, and other Algorand DEXs are automatically decomposed into their underlying assets before classification. This ensures that an LP token containing ALGO and goBTC is properly split -- the ALGO portion goes to the "algo" category, and the goBTC portion goes to "hard_money."

Example:
```
TinymanPool2.0 ALGO-goBTC (100 LP tokens)
    |
    +-- ALGO: 5,000 tokens  --> Category: algo     ($1,750 @ $0.35)
    +-- goBTC: 0.018 tokens --> Category: hard_money ($1,750 @ $97,000)

    Total: $3,500 correctly categorized across two categories
```

Without LP decomposition, the entire $3,500 would be classified as "shitcoin" (a generic LP token), dramatically understating the user's hard money position.

---

## Sovereignty Score Calculation

### The Numerator: Total Portfolio Value

The sovereignty ratio uses the **total portfolio value across all four categories** as the numerator. This is a deliberate design choice:

- **Why not just hard money?** Because sovereignty measures *practical runway*. If you lose your income tomorrow, you will sell whatever assets are necessary to cover expenses -- not just your Bitcoin. Your USDC, your ALGO, even your shitcoins all represent real purchasing power.
- **Why not weight categories differently?** Simplicity and honesty. A dollar of USDC buys groceries just as effectively as a dollar of gold. The *quality* of the wealth (its long-term preservation) is reflected in the category breakdown, not the ratio itself.

The portfolio value is calculated as:

```
portfolio_usd = sum(hard_money_assets_usd)
              + sum(algo_assets_usd)
              + sum(dollar_assets_usd)
              + sum(shitcoin_assets_usd)
```

### The Denominator: Annual Fixed Expenses

Fixed expenses are costs you cannot easily reduce or eliminate:

- Rent or mortgage payments
- Utilities (electricity, water, gas, internet)
- Insurance (health, auto, home/renters)
- Minimum debt payments
- Property taxes
- Basic food and transportation

The system takes **monthly fixed expenses** as input and multiplies by 12:

```
annual_fixed_expenses = monthly_fixed_expenses * 12
```

**Excluded from fixed expenses**: Entertainment, dining out, subscriptions, travel, and other discretionary spending. The point is to measure the irreducible baseline -- the minimum cost of maintaining your life.

### The Calculation

```python
sovereignty_ratio = portfolio_usd / annual_fixed_expenses
```

Example:
```
Portfolio: $180,000 (across all categories)
Monthly expenses: $5,000
Annual expenses: $60,000

Sovereignty Ratio = $180,000 / $60,000 = 3.0
Status: Robust
Meaning: 3 years of financial runway
```

---

## Sovereignty Tiers

The sovereignty ratio maps to five status tiers. These tiers are inspired by Nassim Nicholas Taleb's fragility framework (from *Antifragile*) and the practical realities of financial independence.

### Tier Definitions

| Tier | Ratio | Years | Status | Description |
|------|-------|-------|--------|-------------|
| 5 | >= 20 | 20+ | **Generationally Sovereign** | Multi-generational wealth. Your assets can sustain not just you, but your children. You are completely free from economic coercion. |
| 4 | >= 6 | 6-20 | **Antifragile** | You benefit from volatility. Market crashes are buying opportunities, not crises. You can weather any economic storm and emerge stronger. |
| 3 | >= 3 | 3-6 | **Robust** | Solid financial position. You can endure major disruptions -- job loss, health emergencies, economic downturns -- without existential threat. |
| 2 | >= 1 | 1-3 | **Fragile** | Building the foundation. You have breathing room but are not yet insulated from prolonged adversity. A single extended crisis could deplete your reserves. |
| 1 | < 1 | <1 | **Vulnerable** | Less than one year of coverage. Immediate action needed. You are one major event away from financial distress. |

### Mining Theme Names

In the frontend UI, the tiers are presented with a mining/treasure theme:

| Status | Mining Name | Emoji |
|--------|------------|-------|
| Generationally Sovereign | Dragon's Hoard | dragon |
| Antifragile | King's Treasury | crown |
| Robust | Merchant's Chest | coin |
| Fragile | Miner's Pouch | pickaxe |
| Vulnerable | Empty Mine | rock |

### Why These Thresholds?

- **1 year (Fragile)**: The widely-cited minimum emergency fund. Below this, any income disruption is immediately destabilizing.
- **3 years (Robust)**: The average length of a recession recovery cycle. At this level, you can weather most economic downturns without forced asset sales at depressed prices.
- **6 years (Antifragile)**: Named after Taleb's concept. At 6+ years of runway, you can take calculated risks -- quit a job to start a business, relocate to a lower-cost area, invest aggressively during downturns. Volatility becomes your friend.
- **20 years (Generationally Sovereign)**: At 20+ years, your assets will likely compound faster than your spending depletes them (assuming reasonable investment returns). This is the threshold where wealth becomes self-sustaining across generations.

---

## Price Sources and Accuracy

### Multi-Source Pricing

The system uses multiple price sources to ensure accuracy and resilience:

| Source | Priority | Assets Covered |
|--------|----------|----------------|
| Vestige Labs API | Primary | All Algorand ASAs (on-chain prices from DEX pools) |
| CoinGecko API | Fallback | Major cryptocurrencies (ALGO, BTC, ETH) |
| Coinbase API | Fallback | BTC spot price |
| Yahoo Finance | Fallback | Gold and silver futures (GC=F, SI=F) |

### Dust and NFT Filtering

To prevent noise from inflating asset counts, the system filters:

- **NFT-like tokens**: Small integer holdings (1-10 units) with no price data
- **Dust tokens**: Assets worth less than $1 USD
- **Reward/airdrop spam**: Tokens with keywords like "reward", "airdrop", "free" with negligible value

These filtered tokens do not appear in the analysis and do not contribute to the sovereignty ratio.

---

## Connecting to Real-World Financial Independence

### The FIRE Movement Parallel

The sovereignty ratio is conceptually similar to the Financial Independence / Retire Early (FIRE) movement's metrics, but with key differences:

| FIRE Approach | Sovereignty Approach |
|---------------|---------------------|
| Uses the 4% rule (25x annual expenses) | Uses 1x ratio (total portfolio / annual expenses) |
| Assumes traditional investments (stocks, bonds) | Focuses on hard money + crypto portfolio |
| Plans for perpetual withdrawal | Measures raw runway in years |
| Typically includes real estate | Focuses on liquid, portable assets |

### Why Portable, Liquid Assets Matter

Traditional financial independence calculations include illiquid assets like real estate. The sovereignty framework deliberately excludes these because:

1. **Portability**: You cannot move a house across borders. Gold, Bitcoin, and crypto travel with you.
2. **No counterparty risk**: Property can be seized, taxed, or regulated. Self-custodied assets cannot.
3. **True ownership**: Property taxes mean you never truly own real estate -- stop paying and you lose it.
4. **Liquidity**: In a crisis, you cannot sell half a house. You can sell half your Bitcoin in minutes.

### Practical Implications by Tier

**Vulnerable (< 1 year)**: Focus on reducing expenses and increasing savings rate. Every dollar saved extends your runway. Consider dollar-cost averaging into hard money assets.

**Fragile (1-3 years)**: You have a foundation. Begin optimizing your asset allocation toward hard money. Consider reducing stablecoin exposure in favor of Bitcoin, gold, or silver.

**Robust (3-6 years)**: You can begin taking calculated risks. This might mean leaving a high-stress job for lower-paying but more fulfilling work, or starting a business with a safety net.

**Antifragile (6-20 years)**: You benefit from chaos. Market crashes are buying opportunities. You have the luxury of long time horizons and can hold assets through any volatility.

**Generationally Sovereign (20+ years)**: Your wealth is self-sustaining. Focus shifts from accumulation to preservation and legacy planning.

---

## Implementation Reference

### Core Files

| File | Role |
|------|------|
| `core/models.py` | `SovereigntyData` model, `get_sovereignty_status()` function, threshold constants |
| `core/analyzer.py` | `calculate_sovereignty_metrics()` method -- the main calculation |
| `core/classifier.py` | `AssetClassifier` class -- three-tier classification hierarchy |
| `web/lib/api.ts` | `calculateSovereigntyMetrics()` -- client-side calculation for the runway calculator |
| `web/lib/types.ts` | TypeScript interfaces for `SovereigntyData`, `Categories`, `AnalysisResponse` |
| `web/components/SovereigntyScore.tsx` | Frontend display of the sovereignty score with tier-based gradient coloring |

### Threshold Constants (Python)

```python
# core/models.py
SOVEREIGNTY_THRESHOLDS = [
    (20, "Generationally Sovereign"),
    (6, "Antifragile"),
    (3, "Robust"),
    (1, "Fragile"),
]
# Default (< 1): "Vulnerable"
```

### API Response Structure

```json
{
  "sovereignty_data": {
    "monthly_fixed_expenses": 4000,
    "annual_fixed_expenses": 48000,
    "algo_price": 0.42,
    "portfolio_usd": 180000,
    "sovereignty_ratio": 3.75,
    "sovereignty_status": "Robust",
    "years_of_runway": 3.8
  }
}
```

---

*This document is part of the Algorand Sovereignty Analyzer project. For setup instructions, see the main [README.md](../README.md). For the full philosophy, visit the [Sovereignty Manifesto](/philosophy) on the live site.*
