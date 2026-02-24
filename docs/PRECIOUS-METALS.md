# Precious Metals Analytics Modules

## Data Integrity Warning

**Multiple modules in this section use fabricated/estimated data.** This is the single biggest liability in the codebase. See ROADMAP.md Goal #1 for the plan to replace all fabricated data with real API integrations.

## Module Overview

| Module | Purpose | Data Status |
|--------|---------|-------------|
| `core/pricing.py` | Live spot prices for gold/silver | **Real** — Yahoo Finance (GC=F, SI=F) + Vestige for Meld tokens |
| `core/earnings_calendar.py` | Gold/silver miner quarterly earnings | **Fabricated** — All EPS, revenue, production, AISC, and stock prices are manually estimated |
| `core/premium_tracker.py` | Physical gold/silver dealer premiums | **Fabricated** — Dealer prices are estimated, never scraped from real dealers |
| `core/inflation_data.py` | CPI and M2 money supply history | **Partially fabricated** — Seed data is manually entered. FRED API integration exists but requires `FRED_API_KEY` |
| `core/central_bank_gold.py` | Global central bank gold holdings | **Fabricated** — Holdings are manually estimated from public reports |

## Module Details

### `core/pricing.py` (Real Data)

Multi-source price fetching with caching and fallback chain:

- **Gold/Silver spot**: Yahoo Finance COMEX futures (GC=F, SI=F)
- **Meld GOLD$/SILVER$**: Vestige API (Algorand DEX aggregator), falls back to implied spot price
- **BTC**: Coinbase API (primary), CoinGecko (fallback)
- **All ASAs**: Vestige Labs API denominated in USDC

Cache: 60s TTL for live prices, 5min for Meld. Hardcoded fallbacks for API outages.

### `core/earnings_calendar.py` (Fabricated)

Tracks quarterly earnings for gold/silver mining companies (NEM, GOLD, AEM, KGC, etc.).

**What's fabricated:**
- EPS actual/estimate values
- Revenue actual/estimate values
- Production (oz) and AISC ($/oz) figures
- Pre/post earnings stock prices and price reactions

**Planned fix:** Integrate SEC EDGAR API or financial data provider (Alpha Vantage, Polygon.io, or Financial Modeling Prep) for real earnings data.

**Database:** SQLite at `data/earnings_calendar.db`

### `core/premium_tracker.py` (Fabricated)

Tracks premiums on physical gold/silver products across dealers (JM Bullion, APMEX, SD Bullion, etc.).

**What's fabricated:**
- Dealer product prices are estimated, not scraped
- Premium percentages are approximations
- No real-time inventory or pricing data

**Planned fix:** Integrate real dealer APIs or implement web scraping for actual product prices and premiums.

**Database:** SQLite at `data/premium_tracker.db`

### `core/inflation_data.py` (Partially Fabricated)

Provides historical CPI, M2 money supply, and gold/silver prices for inflation-adjusted charting.

**What's real:**
- FRED API integration code exists for CPI (`CPIAUCSL`) and M2 (`M2SL`)
- The API calls are implemented and will work with a valid `FRED_API_KEY`

**What's fabricated:**
- Seed data (CPI values from 1970-2025) is manually entered
- Without `FRED_API_KEY`, the module falls back to stale seed data

**Planned fix:** Set `FRED_API_KEY` environment variable (free from FRED) to enable live data. The code is already written.

### `core/central_bank_gold.py` (Fabricated)

Tracks central bank gold reserves and de-dollarization metrics.

**What's fabricated:**
- Country-level gold holdings (tonnes)
- Purchase/sale activity
- Reserve-to-GDP ratios

**Planned fix:** Integrate World Gold Council data or IMF International Financial Statistics API.

**Database:** SQLite at `data/central_bank_gold.db`

## Arbitrage Module (Real Data)

The Meld arbitrage spotter (`meld_pricing.py`, `arbitrage_routes.py`) uses **real data** — it compares live Vestige on-chain prices to Yahoo Finance spot prices. See `docs/` or ROADMAP.md Goal #2 for the planned Bitcoin 3-way arbitrage extension.

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `FRED_API_KEY` | For inflation data | Free API key from [FRED](https://fred.stlouisfed.org/docs/api/api_key.html) |
| `RESEED_MINERS` | No | Set `true` to re-seed earnings calendar DB on startup |
| `RESEED_SILVER` | No | Set `true` to re-seed silver miner DB on startup |
