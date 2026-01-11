# Central Bank Gold Tracker Implementation Plan

## Overview
A dashboard tracking global central bank gold purchases and sales, providing insights into the de-dollarization trend and sovereign accumulation patterns. This feature appeals to precious metals enthusiasts interested in institutional validation of gold as a reserve asset.

---

## Features

### 1. Net Purchases Dashboard
- **Monthly net purchases**: Bar chart showing global CB buying/selling
- **Rolling 12-month total**: Are central banks net buyers or sellers?
- **Year-over-year comparison**: 2024 vs 2023 vs 2022
- **Cumulative chart**: Total CB gold holdings over time

### 2. Country Leaderboard
- **Top 10 Buyers**: Which countries are accumulating most?
- **Top 10 Sellers**: Who's reducing gold reserves?
- **Holdings by country**: Sortable table with total tonnes
- **Gold as % of reserves**: How much of each country's reserves is gold?

### 3. Interactive World Map
- **Choropleth map**: Color-coded by gold holdings or recent activity
- **Clickable countries**: Show detail panel with country stats
- **Toggle views**: Holdings, % of reserves, recent purchases
- **Regional filters**: Americas, Europe, Asia, etc.

### 4. De-Dollarization Score
- **Composite index**: Measuring move away from USD reserves
- **Components**: Gold %, USD %, Euro %, CNY %, other
- **Trend analysis**: Is de-dollarization accelerating?
- **Key events timeline**: BRICS announcements, sanctions, etc.

### 5. Notable Country Deep Dives
- **China**: Monthly mystery purchases, reported vs actual
- **Russia**: Sanctions impact, gold as sanctions hedge
- **Turkey**: Volatile buyer, currency crisis correlation
- **India**: Steady accumulator, wedding season patterns
- **Poland/Hungary**: European gold repatriation trend

---

## Data Sources

### Primary Sources (Official)

1. **World Gold Council (WGC)** - Primary authoritative source
   - Monthly central bank statistics reports
   - Quarterly "Gold Demand Trends" publication
   - Data available via their website (PDF/Excel)
   - URL: `https://www.gold.org/goldhub/data/gold-reserves-by-country`

2. **IMF International Financial Statistics (IFS)**
   - Official reserve assets by country
   - Monthly updates with 2-month lag
   - API: `https://data.imf.org/api/`
   - Free access with registration

3. **Central Bank Websites** - For specific countries
   - PBOC (China): Often delayed/opaque reporting
   - Bank of Russia: Monthly bulletins
   - RBI (India): Weekly statistical supplements

### Secondary Sources

1. **LBMA** - London Bullion Market Association
   - Vault holdings data
   - Monthly clearing statistics

2. **Trading Economics** - Aggregated CB data
   - Good for historical trends
   - Some API access

### Data Update Frequency
- **WGC**: Monthly (released ~15th of following month)
- **IMF**: Monthly (2-month lag)
- Most recent data will always be 1-2 months behind

---

## Technical Architecture

### Backend (Python/FastAPI)

#### New Database Models
```python
class CentralBankHolding(BaseModel):
    id: str
    country_code: str  # ISO 3166-1 alpha-2 (US, CN, RU, etc.)
    country_name: str
    date: datetime  # Month/year of data
    gold_tonnes: float  # Holdings in metric tonnes
    gold_value_usd: float  # Value in billions USD
    total_reserves_usd: float  # Total FX reserves in billions
    gold_pct_of_reserves: float  # Gold as % of total reserves
    monthly_change_tonnes: Optional[float]  # Change from prior month
    source: str  # 'WGC', 'IMF', 'manual'
    created_at: datetime

class DeDollarizationMetric(BaseModel):
    id: str
    date: datetime
    gold_pct_global: float  # Gold as % of global reserves
    usd_pct_global: float  # USD as % of global reserves
    eur_pct_global: float
    cny_pct_global: float
    other_pct_global: float
    dedollarization_score: float  # Composite 0-100
    yoy_change: float  # Year-over-year change in USD %
```

#### New Module: `core/central_bank_gold.py`
```python
# Key functions:
- get_cb_gold_db() -> CentralBankDatabase (singleton)
- fetch_wgc_data() -> List[CentralBankHolding]
- fetch_imf_reserves() -> List[ReserveData]
- get_holdings_by_country(country_code: str) -> List[CentralBankHolding]
- get_global_net_purchases(period: str) -> NetPurchaseData
- get_top_buyers(n: int, months: int) -> List[CountryPurchase]
- get_top_sellers(n: int, months: int) -> List[CountrySale]
- calculate_dedollarization_score() -> DeDollarizationMetric
- get_country_leaderboard() -> List[CountryRanking]
- seed_historical_data() -> int
```

#### API Endpoints
```
GET  /central-banks/holdings
GET  /central-banks/holdings/{country_code}
GET  /central-banks/net-purchases?months=12
GET  /central-banks/leaderboard?sort_by=holdings
GET  /central-banks/top-buyers?n=10&months=12
GET  /central-banks/top-sellers?n=10&months=12
GET  /central-banks/dedollarization-score
GET  /central-banks/map-data
POST /central-banks/refresh  (trigger data update)
```

### Frontend (Next.js/React)

#### New Component: `components/CentralBankTracker.tsx`

**Sub-components:**
1. **NetPurchasesChart**: Bar chart of monthly buying/selling
2. **CountryLeaderboard**: Sortable table with rankings
3. **GoldMap**: Interactive choropleth map (react-simple-maps or Leaflet)
4. **DeDollarizationGauge**: Visual score indicator
5. **CountryDetailCard**: Expandable country information
6. **TimelineChart**: Historical holdings trend

#### Map Library Options
1. **react-simple-maps** - Lightweight, good for choropleths
2. **Leaflet + react-leaflet** - More interactive, heavier
3. **D3.js** - Most flexible, steepest learning curve

Recommendation: **react-simple-maps** for simplicity

#### New Page: `app/central-bank-gold/page.tsx`
- Dashboard layout with multiple widgets
- Responsive grid that stacks on mobile

---

## Implementation Phases

### Phase 1: Data Model & Seeding
1. Create database models for CB holdings
2. Manually seed top 30 countries' historical data (5 years)
3. Build data parsing from WGC CSV/Excel exports
4. Create country code mapping

### Phase 2: Core Calculations
1. Implement net purchase calculations
2. Build leaderboard ranking logic
3. Create de-dollarization score formula
4. Add gold % of reserves calculations

### Phase 3: API Endpoints
1. Add all CB endpoints to routes.py
2. Implement filtering (by date range, region)
3. Add sorting and pagination
4. Create map data endpoint with GeoJSON

### Phase 4: Frontend - Charts
1. Build net purchases bar chart
2. Create country leaderboard table
3. Add historical trend line chart
4. Implement de-dollarization gauge

### Phase 5: Interactive Map
1. Integrate react-simple-maps
2. Create choropleth coloring logic
3. Add country click handlers
4. Build detail panel/modal

### Phase 6: Polish & Integration
1. Add to navigation
2. Mobile responsive adjustments
3. Loading/error states
4. Data refresh automation

---

## Countries to Track (Top 30)

### Tier 1 - Major Holders
| Rank | Country | Holdings (tonnes) | % of Reserves |
|------|---------|-------------------|---------------|
| 1 | USA | 8,133 | 69% |
| 2 | Germany | 3,352 | 69% |
| 3 | Italy | 2,452 | 65% |
| 4 | France | 2,437 | 66% |
| 5 | Russia | 2,336 | 26% |
| 6 | China | 2,264 | 4% |
| 7 | Switzerland | 1,040 | 6% |
| 8 | Japan | 846 | 4% |
| 9 | India | 841 | 9% |
| 10 | Netherlands | 612 | 59% |

### Tier 2 - Active Accumulators
| Country | Recent Trend | Note |
|---------|--------------|------|
| Turkey | Volatile | Currency crisis buyer |
| Poland | Aggressive buyer | European leader |
| Hungary | Buyer | Tripled holdings 2018-2021 |
| Singapore | Steady buyer | Asian diversification |
| Czech Republic | Buyer | European trend |
| Iraq | Buyer | Oil wealth diversification |
| Uzbekistan | Buyer | Regional trend |
| Kazakhstan | Volatile | Producer country |

### Tier 3 - Other Notable
- UK, Portugal, Spain, Austria (historical holders)
- Saudi Arabia, UAE (oil wealth, opaque)
- Brazil, Mexico (Latin American reserves)
- South Korea, Taiwan (Asian holders)
- Australia, Canada (minimal gold, producer countries)

---

## De-Dollarization Score Formula

```python
def calculate_dedollarization_score() -> float:
    """
    Composite score 0-100 measuring global move away from USD reserves.

    Components:
    1. USD share of global reserves (inverse - lower USD = higher score)
    2. Gold share of global reserves (higher = higher score)
    3. Rate of change in USD share (declining faster = higher score)
    4. BRICS+ combined reserves shift
    5. Central bank net gold purchases (more buying = higher score)

    Weights:
    - USD share change: 30%
    - Gold accumulation: 25%
    - Alternative currency growth: 20%
    - Net CB gold purchases: 15%
    - Bilateral trade settlement trends: 10%
    """
    usd_component = (1 - (usd_pct / 100)) * 30  # e.g., 58% USD = 12.6
    gold_component = (gold_pct / 25) * 25  # e.g., 15% gold = 15
    trend_component = abs(yoy_usd_change) * 20 if yoy_usd_change < 0 else 0
    # ... additional components

    return min(100, sum(components))
```

Historical Score Examples:
- 2000: ~15 (USD dominant, gold out of favor)
- 2010: ~25 (Post-GFC, early CB buying)
- 2020: ~40 (Steady accumulation, COVID)
- 2024: ~55 (BRICS expansion, sanctions impact)

---

## UI/UX Mockup Concepts

### Main Dashboard Layout
```
┌─────────────────────────────────────────────────────────────────┐
│  🏦 Central Bank Gold Tracker          Last Updated: Dec 2024  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────────┐  ┌────────────────────────────────┐  │
│  │ Net Purchases (12mo) │  │  De-Dollarization Score        │  │
│  │                      │  │                                │  │
│  │ +1,037 tonnes        │  │         ◐ 55/100              │  │
│  │ 14th consecutive yr  │  │    ▲ +8 from last year        │  │
│  │ of net buying        │  │                                │  │
│  └──────────────────────┘  └────────────────────────────────┘  │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Monthly Net Purchases (2024)                            │  │
│  │  ████ ████ ████ ██ ████ ████ ███ ████ ██ ███ ████       │  │
│  │  Jan  Feb  Mar Apr May  Jun  Jul Aug Sep Oct Nov  Dec   │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Country Leaderboard
```
┌─────────────────────────────────────────────────────────────────┐
│  Country Leaderboard         Sort: [Holdings ▼] [Buyers ▼]     │
├─────────────────────────────────────────────────────────────────┤
│  #  │ Country      │ Holdings │ % Reserves │ 12mo Change      │
│─────┼──────────────┼──────────┼────────────┼──────────────────│
│  1  │ 🇺🇸 USA       │ 8,133 t  │    69%     │  —               │
│  2  │ 🇩🇪 Germany   │ 3,352 t  │    69%     │  —               │
│  3  │ 🇮🇹 Italy     │ 2,452 t  │    65%     │  —               │
│  4  │ 🇫🇷 France    │ 2,437 t  │    66%     │  —               │
│  5  │ 🇷🇺 Russia    │ 2,336 t  │    26%     │  +10 t  📈       │
│  6  │ 🇨🇳 China     │ 2,264 t  │     4%     │  +62 t  📈       │
│  7  │ 🇨🇭 Switzerland│ 1,040 t  │     6%     │  —               │
│  8  │ 🇯🇵 Japan     │   846 t  │     4%     │  —               │
│  9  │ 🇮🇳 India     │   841 t  │     9%     │  +37 t  📈       │
│ 10  │ 🇳🇱 Netherlands│   612 t  │    59%     │  —               │
└─────────────────────────────────────────────────────────────────┘
```

### Interactive Map
```
┌─────────────────────────────────────────────────────────────────┐
│  Global Gold Reserves Map      View: [Holdings ▼]              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│                    ┌─────────────────────┐                     │
│        ░░░░        │    Clicked: China   │     ░░░            │
│      ░░░░░░        │    Holdings: 2,264t │   ░░░░░            │
│    ▓▓▓▓░░░░░       │    % Reserves: 4%   │  ░░░░░░            │
│   ▓▓▓▓▓▓░░░░       │    12mo: +62t       │    ░░              │
│    ▓▓▓▓░░░░        │    [View Details]   │                    │
│      ░░░░          └─────────────────────┘                     │
│        ░                                                        │
│                          ████                                   │
│                         ██████                                  │
│                        ████████                                 │
│                         ░░░░░░                                 │
│                                                                 │
│  Legend: ░ <100t  ▒ 100-500t  ▓ 500-2000t  █ >2000t           │
└─────────────────────────────────────────────────────────────────┘
```

### China Deep Dive
```
┌─────────────────────────────────────────────────────────────────┐
│  🇨🇳 China: The Mystery Buyer                                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Official Holdings: 2,264 tonnes                                │
│  Estimated Actual:  4,000-5,000 tonnes (unofficial)            │
│                                                                 │
│  Timeline:                                                      │
│  ├─ 2009-2015: No reported purchases (accumulated secretly)    │
│  ├─ 2015: Surprised world with +604t announcement              │
│  ├─ 2016-2018: Steady monthly purchases                        │
│  ├─ 2019-2022: Resumed heavy buying                            │
│  └─ 2023-2024: 18 consecutive months of purchases              │
│                                                                 │
│  Why it matters:                                                │
│  • World's largest gold producer (≈380 tonnes/year)            │
│  • Minimal domestic gold leaves China                           │
│  • PBOC likely accumulates via state banks                     │
│  • De-dollarization strategy amid US-China tensions            │
│                                                                 │
│  ⚠️ China's true holdings likely 2x official numbers          │
└─────────────────────────────────────────────────────────────────┘
```

---

## Estimated Effort

| Phase | Description | Complexity |
|-------|-------------|------------|
| 1 | Data Model & Seeding | Medium |
| 2 | Core Calculations | Low |
| 3 | API Endpoints | Low |
| 4 | Frontend Charts | Medium |
| 5 | Interactive Map | High |
| 6 | Polish & Integration | Low |

---

## Open Questions for User

1. **Map library**: react-simple-maps (lighter) or Leaflet (more features)?
2. **Country flags**: Include emoji flags or country code only?
3. **Update frequency**: Monthly data refresh acceptable?
4. **Deep dive countries**: China, Russia, India, Turkey - any others?
5. **Historical depth**: How far back? (Suggested: 2010-present)
6. **BRICS focus**: Dedicated section for BRICS+ gold strategy?

---

## Data Challenges & Mitigations

| Challenge | Mitigation |
|-----------|------------|
| China underreports holdings | Note "estimated actual" alongside official |
| Data is 1-2 months delayed | Clear "as of" dates, don't imply real-time |
| Some countries don't report | Mark as "N/A" or "Not Reported" |
| Different reporting standards | Normalize to tonnes and USD, cite sources |
| WGC data in PDF/Excel | Build parser or manual quarterly entry |

---

## Success Metrics

- Users understand the global CB gold buying trend
- De-dollarization score provides unique insight
- Map visualization makes data engaging
- Country deep dives tell the "why" story
- Site becomes reference for CB gold data
