# Data Validation Required - Precious Metals Section

**IMPORTANT**: The data in this application was "vibe coded" - meaning values were estimated or fabricated without verification from authoritative sources. **ALL data points below require validation before production use.**

**Document Purpose**: Share this with AI tools or researchers to validate each data point against authoritative sources.

## UPDATES MADE (January 2026)

The following corrections have been applied based on external validation:

1. **1980 Gold Peak**: Fixed from $675 to **$850** (Jan 21, 1980 peak)
2. **1980 Silver Peak**: Fixed from $35 to **$49.45** (Jan 18, 1980 Hunt Brothers peak)
3. **Current Gold Price**: Updated to ~$4,523/oz (January 2026)
4. **Current Silver Price**: Updated to ~$80.65/oz (January 2026)
5. **CPI Data**: Extended through November 2025 (325.0)
6. **M2 Data**: Extended through November 2025 ($22,322B)
7. **Central Bank Holdings**: Added 2025 data with validated WGC figures
8. **Physical Premium Tracker**: Updated spot prices to January 2026 levels
9. **Data Disclaimers**: Added to all frontend components

---

## 1. INFLATION-ADJUSTED CHARTS (`core/inflation_data.py`)

### 1.1 Consumer Price Index (CPI-U) Data
**Claimed Source**: FRED API / BLS
**Actual Source**: Manually entered estimates
**Status**: NEEDS VERIFICATION

| Date | Current Value | Authoritative Source | Notes |
|------|---------------|---------------------|-------|
| 1970-01 | 37.8 | FRED CPIAUCSL | Verify |
| 1980-01 | 77.8 | FRED CPIAUCSL | Verify |
| 1980-06 | 82.7 | FRED CPIAUCSL | Verify |
| 2000-06 | 172.4 | FRED CPIAUCSL | Verify |
| 2020-01 | 258.7 | FRED CPIAUCSL | Verify |
| 2024-12 | 318.5 | FRED CPIAUCSL | **HIGH PRIORITY** - Current |
| 2025-01 | 319.8 | FRED CPIAUCSL | **HIGH PRIORITY** - Current |

**Validation Method**:
- Go to https://fred.stlouisfed.org/series/CPIAUCSL
- Download CSV, compare each value

### 1.2 M2 Money Supply Data (Billions USD)
**Claimed Source**: FRED API
**Actual Source**: Manually entered estimates
**Status**: NEEDS VERIFICATION

| Date | Current Value | Notes |
|------|---------------|-------|
| 1970-01 | 587 | Verify vs FRED M2SL |
| 1980-01 | 1,543 | Verify |
| 2000-01 | 4,662 | Verify |
| 2020-01 | 15,447 | Verify |
| 2020-06 | 18,306 | COVID spike - verify |
| 2024-12 | 21,437 | **HIGH PRIORITY** |
| 2025-01 | 21,560 | **HIGH PRIORITY** |

**Validation Method**:
- Go to https://fred.stlouisfed.org/series/M2SL
- Download CSV, compare each value

### 1.3 Historical Gold Prices (USD/oz)
**Claimed Source**: LBMA/Kitco
**Actual Source**: Manually entered estimates
**Status**: PARTIALLY CORRECTED

| Date | Current Value | Status |
|------|---------------|--------|
| 1970-01 | $35.00 | Correct - Bretton Woods fixed price |
| 1980-01 | $850.00 | **FIXED** - Peak was $850 on Jan 21, 1980 |
| 2011-09 | $1,895.00 | Correct |
| 2020-08 | $2,067.00 | Correct |
| 2025-12 | $4,400.00 | Estimated 2025 rally |
| 2026-01 | $4,523.00 | **UPDATED** - Verified Jan 2026 via Kitco |

**Fixed Issues**:
- January 1980 gold peak corrected from $675 to $850
- Current prices updated to January 2026 (~$4,523/oz)

**Validation Method**:
- Historical: https://www.macrotrends.net/1333/historical-gold-prices-100-year-chart
- Current: https://www.kitco.com/charts/livegold.html

### 1.4 Historical Silver Prices (USD/oz)
**Claimed Source**: LBMA/Kitco
**Actual Source**: Manually entered estimates
**Status**: PARTIALLY CORRECTED

| Date | Current Value | Status |
|------|---------------|--------|
| 1980-01 | $49.45 | **FIXED** - Hunt Brothers peak was $49.45 on Jan 18, 1980 |
| 2011-04 | $48.00 | Correct - Near $50 peak |
| 2025-12 | $75.00 | Estimated 2025 rally |
| 2026-01 | $80.65 | **UPDATED** - Verified Jan 2026 via Kitco |

**Fixed Issues**:
- January 1980 silver peak corrected from $35 to $49.45
- Current prices updated to January 2026 (~$80.65/oz)

**Validation Method**:
- Historical: https://www.macrotrends.net/1470/historical-silver-prices-100-year-chart
- Current: https://www.kitco.com/charts/livesilver.html

---

## 2. CENTRAL BANK GOLD TRACKER (`core/central_bank_gold.py`)

### 2.1 Central Bank Gold Holdings (tonnes)
**Claimed Source**: World Gold Council, IMF IFS
**Actual Source**: Manually estimated
**Status**: NEEDS VERIFICATION

#### Top 10 Holdings (2024-09 data point)
| Country | Current tonnes | % Reserves | Verify Against |
|---------|---------------|------------|----------------|
| USA | 8,133.5 | 71% | WGC official reserves |
| Germany | 3,351.5 | 70% | WGC |
| Italy | 2,451.8 | 67% | WGC |
| France | 2,437.0 | 66% | WGC |
| Russia | 2,335.9 | 27% | WGC - may be sanctioned/hidden |
| China | 2,264.3 | 4.9% | WGC - **often understated** |
| Switzerland | 1,040.0 | 5.5% | WGC |
| Japan | 846.0 | 4.5% | WGC |
| India | 854.7 | 9.2% | WGC |
| Netherlands | 612.5 | 62% | WGC |

**Critical Issues**:
- China's holdings are likely understated (commonly believed to be 3,000-5,000+ tonnes)
- Russia data may be unreliable post-sanctions
- % of reserves calculations depend on total reserve valuations

**Validation Method**:
- World Gold Council: https://www.gold.org/goldhub/data/gold-reserves-by-country
- IMF International Financial Statistics

### 2.2 Global Net Purchases by Year
**Status**: NEEDS VERIFICATION

| Year | Current Value (tonnes) | Notes |
|------|----------------------|-------|
| 2022 | 1,082 | Record year - verify |
| 2023 | 1,037 | Second highest - verify |
| 2024 | 800 | Estimate - update when final |

**Validation Method**:
- WGC Gold Demand Trends reports

---

## 3. MINER EARNINGS CALENDAR (`core/earnings_calendar.py`)

### 3.1 Company Fundamentals
**Status**: ENTIRELY FABRICATED - ALL VALUES NEED REAL DATA

#### Gold Miners Earnings Data
The following data was **completely made up**. Every single value needs to be replaced with actual historical data from SEC filings.

| Ticker | Company | Issues |
|--------|---------|--------|
| NEM | Newmont | All EPS, revenue, production, AISC, stock prices are fabricated |
| GOLD | Barrick Gold | All data fabricated |
| AEM | Agnico Eagle | All data fabricated |
| KGC | Kinross Gold | All data fabricated |
| BTG | B2Gold | All data fabricated |

#### Silver Miners Earnings Data
| Ticker | Company | Issues |
|--------|---------|--------|
| PAAS | Pan American Silver | All data fabricated |
| AG | First Majestic Silver | All data fabricated |
| HL | Hecla Mining | All data fabricated |
| CDE | Coeur Mining | All data fabricated |

**Critical Issues**:
- EPS figures are made up
- Revenue figures are made up
- Production figures are made up
- AISC figures are made up
- Stock prices are made up
- Beat/miss history is therefore meaningless

**Validation Method**:
- SEC EDGAR filings: https://www.sec.gov/cgi-bin/browse-edgar
- Company investor relations pages
- Earnings call transcripts
- Yahoo Finance / Seeking Alpha for historical data

### 3.2 Earnings Dates
**Status**: ESTIMATED - VERIFY

The earnings dates (Q4 2024, Q1 2025) are estimates. Verify against:
- https://www.earningswhispers.com
- Company investor relations calendars

---

## 4. PHYSICAL PREMIUM TRACKER (`core/premium_tracker.py`)

### 4.1 Current Spot Prices Used
**Status**: HARDCODED - LIKELY STALE

| Metal | Hardcoded Value | Issue |
|-------|-----------------|-------|
| Gold | $2,680/oz | May be outdated |
| Silver | $31/oz | May be outdated |

**Fix Required**: These should pull from a live API, not be hardcoded.

### 4.2 Product Prices at Dealers
**Status**: ENTIRELY ESTIMATED - NEVER SCRAPED

All dealer prices are fabricated estimates. None were scraped from actual dealer websites.

| Product | Prices Shown | Reality |
|---------|-------------|---------|
| Gold Eagle | $2,788-2,812 | Need to scrape APMEX, JM Bullion, etc. |
| Silver Eagle | $39.50-41.50 | Need to scrape actual prices |
| All products | Estimated | Need real data |

**Critical Issues**:
- Premium percentages are based on made-up prices
- "Best deals" are meaningless without real data
- Dealer rankings are arbitrary

**Validation Method**:
- Manually check each dealer website
- Or implement actual web scraping

### 4.3 Typical Premium Ranges
**Status**: ROUGH ESTIMATES - VERIFY

| Product | Claimed Range | Notes |
|---------|---------------|-------|
| Gold Eagle | 4-6% | Reasonable estimate |
| Silver Eagle | 25-40% | Wide range, verify current |
| Generic Silver Round | 8-15% | Verify |
| 100oz Silver Bar | 5-8% | Verify |

---

## 5. PRIORITY FIXES

### Immediate (Before Release)
1. **Update gold spot price** - Show actual current price (~$2,680-2,700 range as of Jan 2025)
2. **Update silver spot price** - Show actual current price
3. **Fix 1980 gold peak** - Change from $675 to ~$850
4. **Add disclaimers** - "Data for illustration only, verify before making decisions"

### Short Term
1. Integrate FRED API for CPI and M2 data
2. Integrate a gold/silver price API (Kitco, GoldAPI.io, etc.)
3. Replace earnings data with real SEC filings

### Medium Term
1. Implement dealer price scraping or affiliate API integration
2. Get WGC data feed for central bank holdings
3. Build earnings calendar from real data sources

---

## 6. RECOMMENDED DATA SOURCES

### Free APIs
| Data Type | Source | URL |
|-----------|--------|-----|
| CPI, M2 | FRED API | https://fred.stlouisfed.org/docs/api/fred/ |
| Gold/Silver Spot | GoldAPI.io | https://www.goldapi.io/ (free tier) |
| Stock Prices | Yahoo Finance | yfinance Python library |
| Earnings Dates | Earnings Whispers | Manual or scrape |

### Paid/Premium
| Data Type | Source | Notes |
|-----------|--------|-------|
| Central Bank Gold | World Gold Council | Subscription for detailed data |
| Dealer Prices | Affiliate APIs | APMEX, JM Bullion offer partner feeds |
| Mining Company Data | S&P Global | Comprehensive mining data |

---

## 7. DISCLAIMER TEXT TO ADD

Add this to any page displaying this data:

> **Data Disclaimer**: The data shown on this page is for illustrative purposes only. Many values are estimates that have not been verified against authoritative sources. Do not make financial decisions based on this data. Always verify current prices, holdings, and financial metrics with official sources before taking action.

---

## Document History
- Created: 2025-01-11
- Purpose: Enable external validation of all seeded data
- Status: Awaiting validation
