# Algo Sovereignty Analyzer - User Guide

## What is Sovereignty?

Financial sovereignty means having enough hard money assets to cover your essential expenses without relying on income. The Sovereignty Ratio tells you how many years you could maintain your lifestyle using only your hard money reserves.

```
Sovereignty Ratio = Total Hard Money Value / Annual Fixed Expenses
```

## Understanding Your Results

### The Four Asset Categories

When you analyze your wallet, assets are classified into four categories:

| Category | What It Includes | Counts Toward Sovereignty? |
|----------|------------------|---------------------------|
| **Hard Money** | Bitcoin (goBTC, wBTC), Gold (GOLD$, XAUT, PAXG), Silver (SILVER$) | **Yes** |
| **Algo** | ALGO, xALGO, fALGO, gALGO, mALGO, lALGO, tALGO | No |
| **Dollars** | USDC, USDT, DAI, fUSDC, fUSDT, BUSD, TUSD | No |
| **Shitcoins** | Everything else (governance tokens, LP tokens, NFTs) | No |

### Why Only Hard Money Counts

Hard money has properties that make it uniquely suitable for long-term wealth preservation:

1. **Scarcity** - Cannot be printed or inflated away
2. **History** - Gold and silver have 5,000+ years of monetary use
3. **Portability** - Bitcoin can cross borders instantly
4. **Divisibility** - Can be broken into any size needed
5. **Durability** - Doesn't degrade over time

ALGO, while useful for transactions and DeFi, has inflationary tokenomics and platform risk. Stablecoins are subject to issuer risk and fiat inflation.

## Sovereignty Status Levels

Your Sovereignty Ratio determines your status:

| Ratio | Status | What It Means |
|-------|--------|---------------|
| **20+** | Generationally Sovereign | Multi-generational wealth; 20+ years of reserves |
| **6-19** | Antifragile | You benefit from volatility; major economic freedom |
| **3-5** | Robust | Can weather major economic storms; building momentum |
| **1-2** | Fragile | Building reserves; keep stacking |
| **<1** | Vulnerable | Less than 1 year of coverage; priority is building reserves |

## How to Use the Analyzer

### Via Web Interface

1. Visit the analyzer at your deployed URL
2. Enter your Algorand wallet address (58 characters)
3. Enter your monthly fixed expenses (rent, utilities, insurance, minimum debt payments)
4. Click "Analyze"

### Via CLI

```bash
python -m scripts.cli YOUR_ALGORAND_ADDRESS
```

The CLI will prompt for your monthly fixed expenses after displaying your holdings.

### Via API

```bash
curl -X POST http://localhost:8000/api/v1/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "address": "YOUR_ADDRESS",
    "monthly_fixed_expenses": 4000
  }'
```

## Understanding LP Token Decomposition

If you have LP (Liquidity Provider) tokens from Tinyman, Pact, or other DEXes, the analyzer automatically breaks them down into their underlying assets.

**Example:**
```
You hold: 100 ALGO-USDC LP tokens
         ↓ Decomposed to:
50 ALGO → "algo" category
50 USDC → "dollars" category
```

This ensures your portfolio is accurately categorized.

## Fixing Misclassified Assets

If an asset is incorrectly classified, you can submit a correction:

```bash
curl -X POST http://localhost:8000/api/v1/corrections \
  -H "Content-Type: application/json" \
  -d '{
    "asset_id": "123456789",
    "asset_name": "New BTC Wrapper",
    "ticker": "nBTC",
    "original_category": "shitcoin",
    "corrected_category": "hard_money",
    "reason": "This is a legitimate wrapped Bitcoin token"
  }'
```

Your correction is applied immediately and reviewed by administrators.

## Building Your Sovereignty

### Strategy: Stack Hard Money

1. **Dollar-Cost Average (DCA)** - Buy Bitcoin regularly regardless of price
2. **Gold/Silver** - Consider Meld Gold (GOLD$) or Silver (SILVER$) on Algorand
3. **Reduce Expenses** - Lower fixed costs to improve your ratio faster

### Monitoring Progress

1. **Save Snapshots** - The analyzer stores historical data to track your progress
2. **Check Weekly** - Prices fluctuate; check your ratio periodically
3. **Set Goals** - Target the next sovereignty level as a milestone

### Example Path to Sovereignty

If your fixed expenses are $4,000/month ($48,000/year):

| Status | Ratio Needed | Hard Money Target |
|--------|-------------|-------------------|
| Fragile → Robust | 3.0 | $144,000 |
| Robust → Antifragile | 6.0 | $288,000 |
| Antifragile → Generationally Sovereign | 20.0 | $960,000 |

## FAQ

### Why doesn't ALGO count as hard money?

ALGO has no fixed supply cap and experiences ongoing token distribution. While it's a useful platform token, it doesn't meet the hard money criteria of absolute scarcity.

### What about ETH or other crypto?

Ethereum and most cryptocurrencies are classified as "shitcoins" for sovereignty purposes. They may have value, but they lack the monetary history and scarcity properties of hard money.

### What are "fixed expenses"?

Fixed expenses are costs you must pay regardless of lifestyle choices:
- Rent or mortgage
- Utilities
- Insurance (health, auto, home)
- Minimum debt payments
- Property taxes

Variable expenses (food, entertainment, travel) are excluded because they can be reduced in emergencies.

### How accurate are the prices?

Prices are fetched from Vestige (primary) and CoinGecko (fallback). They're cached for 5-15 minutes to reduce API calls. For precise valuation, verify against exchange prices.

### What if my LP token isn't decomposed?

If your LP token shows up in "shitcoins" instead of being decomposed:
1. Check if it's from a supported DEX (Tinyman, Pact, Humble)
2. Submit a GitHub issue with the LP token details
3. Use the corrections API to manually classify the underlying assets

## Getting Help

- **API Documentation**: `/docs` endpoint (Swagger UI)
- **Classification Issues**: Submit a correction via the API
- **Bug Reports**: Open an issue on GitHub
- **Philosophy Questions**: Read the Sovereignty Manifesto on the web interface

## Privacy Note

This analyzer reads **public blockchain data only**. Your wallet address and holdings are visible to anyone on the Algorand blockchain. The analyzer does not:
- Store your private keys
- Connect to your wallet
- Make any transactions
- Share data with third parties

Your monthly expenses are only used for ratio calculation and are not stored permanently unless you explicitly save a snapshot.
