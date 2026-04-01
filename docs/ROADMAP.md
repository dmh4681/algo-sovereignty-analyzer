# Algo Sovereignty Roadmap

> Last updated: 2026-02-22

## Mission

Algo Sovereignty measures how financially sovereign an Algorand wallet really is. It decomposes LP tokens, classifies assets by sovereignty tier, and produces a single score that answers: "How much of your wealth is in assets you truly control?" The same hard money philosophy extends to precious metals tracking and miner analysis.

## Current Phase: Data Integrity

The core wallet analysis engine is production-quality and deployed at algosovereignty.com. LP parsing, asset classification, sovereignty scoring, and AI coaching all work. But the precious metals analytics features (gold/silver trackers, miner earnings, inflation charts, premium tracker) are running on fabricated data. The documented issues in `DATA-VALIDATION-NEEDED.md` are the single biggest liability. Everything else is secondary to fixing the data.

## Active Goals

### 1. Replace Fabricated Data with Real API Integrations
**Priority: Critical**
This is the most important work. Multiple pages display fabricated/estimated data:
- `core/earnings_calendar.py` — All miner EPS, revenue, production, AISC, and stock prices are fabricated. Replace with SEC EDGAR API or financial data provider (Alpha Vantage, Polygon.io)
- `core/premium_tracker.py` — Dealer prices are estimated, never scraped. Integrate real dealer API or scraping
- `core/inflation_data.py` — CPI and M2 data are manually entered estimates. Integrate FRED API (free, well-documented)
- `core/central_bank_gold.py` — Central bank holdings are manually estimated. Use World Gold Council data or IMF IFS API
- Fix stale spot prices for gold/silver with live API feeds

### 2. Complete Bitcoin 3-Way Arbitrage Feature
**Priority: High**
The plan is written (`BITCOIN_ARBITRAGE_PLAN.md`), loose files exist at root (`arbitrage_page.tsx`, `arbitrage_routes.py`), and the MeldArbitrageSpotter already works for gold/silver. Finish the integration:
- Move loose root files into proper module structure
- Add BTC price sources (exchanges, OTC desks, P2P platforms)
- Wire the arbitrage page into the frontend navigation
- Add alert thresholds for significant BTC price spreads

### 3. Wire Real Network Decentralization Metrics
**Priority: Medium**
The `/network` page exists but uses placeholder data for Algorand's decentralization:
- Fetch real Foundation vs. community stake percentages from Algorand indexer
- Add node count and geographic distribution
- Display governance participation rate
- Track relay node health via the infrastructure components that already exist

### 4. Clean Up Root-Level Loose Files
**Priority: Medium**
Multiple files at the repo root are half-integrated features or debug scripts:
- Move `arbitrage_page.tsx`, `arbitrage_routes.py`, `history_routes.py`, `meld_pricing.py` into proper directories
- Remove or archive `debug_crash.py`, `inspect_pool.py`, `test_tinyman_lp.py`
- Consolidate `PLAN-*.md` files into a single archive or docs subdirectory
- Address the 24 uncommitted changes flagged by dev-loop

### 5. Fix Failing API Tests
**Priority: Medium**
Two pre-existing test failures in `test_api.py` due to schema validation mismatch after a prior fix. These should be quick wins:
- Update test expectations to match current API response schema
- Ensure all 69 tests pass clean

## Deferred / Not Now

- **SQLite for historical snapshots** — The current in-memory + SQLite persistence layer works. Don't add a full ORM.
- **Background job system (Celery)** — Overkill for single-user analysis. The async job queue in `core/jobs.py` is sufficient.
- **Redis caching** — In-memory cache with 15-min TTL handles current load.
- **Auto-Mining NFT system** — Component exists but needs smart contract audit. Not priority until data integrity is solved.
- **Community page / ecosystem map** — Nice to have, not essential.
- **Frontend tests** — Backend test coverage is the priority. Frontend is stable.
- **Performance/load testing** — Single-user tool. Not a bottleneck concern.

## Completed Milestones

- [x] Core wallet analysis engine (470-line analyzer, full pipeline)
- [x] LP token decomposition (Tinyman + Pact DEXs, 421-line parser)
- [x] Asset classification system with CSV overrides and corrections workflow
- [x] Sovereignty scoring with tier-based classification
- [x] AI coaching via Claude (advisor endpoint)
- [x] Multi-source pricing (Vestige primary, CoinGecko fallback)
- [x] Wallet history tracking (365-day retention)
- [x] Rate limiting middleware (memory leak + race condition fixed)
- [x] CORS hardening
- [x] Async analysis job queue with SQLite persistence
- [x] Meld gold/silver arbitrage spotter
- [x] 66 passing backend tests
- [x] Comprehensive API and algorithm documentation
- [x] Frontend with 17 pages and 36 components
- [x] Production deployment (Railway + Vercel)
