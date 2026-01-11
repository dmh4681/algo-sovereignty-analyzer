# Inflation-Adjusted Price Charts Implementation Plan

## Overview
Interactive charts showing gold and silver prices adjusted for inflation, M2 money supply expansion, and purchasing power changes. This feature helps precious metals enthusiasts understand the "real" value of their holdings vs nominal prices.

---

## Features

### 1. Inflation-Adjusted Price Charts
- **CPI-Adjusted Gold/Silver**: Prices in constant dollars (base year selectable)
- **Year selection**: View in 1970, 1980, 2000, or 2020 dollars
- **Real vs Nominal toggle**: Overlay or switch between views
- **Historical range**: 1970-present for full monetary history

### 2. M2 Money Supply Comparison
- **Gold/Silver vs M2**: Overlay chart showing correlation
- **Ratio analysis**: Gold price ÷ M2 supply (is gold cheap/expensive vs money printing?)
- **M2 growth rate** with gold price performance
- **Prediction zone**: If M2 continues growing at X%, where should gold be?

### 3. Purchasing Power Visualizer
- **What could you buy?**: Enter an oz of gold/silver, see purchasing power over time
  - "In 1970, 1 oz gold bought a good suit. Today it buys 2 suits."
  - "In 1980, 35 oz silver bought a new car. Today it takes 500 oz."
- **vs Assets comparison**: Gold vs housing, S&P 500, wages
- **Store of value score**: Has gold/silver kept up with real costs?

### 4. Debasement Dashboard
- **Dollar purchasing power chart**: $1 in 1970 → $0.14 today
- **Cumulative inflation calculator**
- **Annual debasement rate**: Rolling 1yr, 5yr, 10yr
- **Gold as inflation hedge**: Correlation analysis

### 5. Multi-Currency View
- Gold/Silver in: USD, EUR, GBP, JPY, CHF, AUD, CAD
- **Relative strength**: Which currency has debased most?
- **Gold in local terms**: Important for international users

---

## Data Sources

### Inflation Data (Free)
1. **FRED API (Federal Reserve Economic Data)** - Primary source
   - CPI-U (Consumer Price Index): `CPIAUCSL`
   - M2 Money Supply: `M2SL`
   - Dollar Index: `DTWEXBGS`
   - API: `https://api.stlouisfed.org/fred/series/observations`
   - Free API key required

2. **World Bank API** - Historical inflation by country
   - Endpoint: `https://api.worldbank.org/v2/country/us/indicator/FP.CPI.TOTL`

3. **BLS (Bureau of Labor Statistics)** - CPI historical data
   - Public data, no API key needed

### Historical Price Data (Free)
1. **LBMA Historical Gold Prices**
   - Daily London Fix back to 1968
   - CSV downloads available

2. **Kitco Historical** - Gold/Silver daily prices
   - Web scraping or CSV exports

3. **FRED Gold Price**: `GOLDAMGBD228NLBM`

### Currency Data
1. **FRED** - Exchange rates for major currencies
2. **ECB API** - Euro exchange rates

---

## Technical Architecture

### Backend (Python/FastAPI)

#### New Database Model: `InflationData`
```python
class InflationDataPoint(BaseModel):
    date: datetime
    cpi_value: float  # CPI-U index value
    m2_supply: float  # M2 in billions
    gold_price: float  # USD/oz
    silver_price: float  # USD/oz
    dollar_index: Optional[float]

class AdjustedPricePoint(BaseModel):
    date: datetime
    nominal_gold: float
    nominal_silver: float
    real_gold: float  # Adjusted to base year
    real_silver: float
    gold_m2_ratio: float  # Gold price / M2 supply
    silver_m2_ratio: float
```

#### New Module: `core/inflation_charts.py`
```python
# Key functions:
- get_inflation_db() -> InflationDatabase (singleton)
- fetch_cpi_data() -> List[CPIDataPoint]
- fetch_m2_data() -> List[M2DataPoint]
- calculate_real_price(nominal: float, date: datetime, base_year: int) -> float
- get_inflation_adjusted_series(metal: str, base_year: int) -> List[AdjustedPricePoint]
- get_m2_comparison() -> M2ComparisonData
- calculate_purchasing_power(year: int) -> PurchasingPowerData
- get_currency_adjusted_prices(currency: str) -> List[CurrencyPricePoint]
- seed_historical_data() -> int
- refresh_from_fred() -> None
```

#### Inflation Adjustment Formula
```python
def adjust_for_inflation(price: float, price_date: datetime, base_year: int) -> float:
    """
    Adjust a historical price to base_year dollars.

    Formula: real_price = nominal_price × (CPI_base / CPI_price_date)

    Example: $400 gold in Jan 1980, adjusted to 2020 dollars
    CPI Jan 1980 = 77.8
    CPI Jan 2020 = 258.8
    Real price = 400 × (258.8 / 77.8) = $1,330 in 2020 dollars
    """
    cpi_at_price_date = get_cpi(price_date)
    cpi_at_base_year = get_cpi(datetime(base_year, 1, 1))
    return price * (cpi_at_base_year / cpi_at_price_date)
```

#### API Endpoints
```
GET  /inflation/gold?base_year=2020
GET  /inflation/silver?base_year=2020
GET  /inflation/m2-comparison
GET  /inflation/purchasing-power?year=1980
GET  /inflation/currency/{currency}
GET  /inflation/cpi-history
GET  /inflation/m2-history
POST /inflation/refresh  (trigger FRED data refresh)
```

### Frontend (Next.js/React)

#### New Component: `components/InflationCharts.tsx`

**Sub-components:**
1. **RealVsNominalChart**: Dual-axis line chart
2. **M2OverlayChart**: Gold price vs M2 supply
3. **PurchasingPowerCalculator**: Interactive tool
4. **DebasementMeter**: Visual gauge of dollar decline
5. **CurrencySelector**: Dropdown for multi-currency view
6. **BaseYearSelector**: Radio buttons for 1970/1980/2000/2020

#### Chart.js Configuration
```typescript
// Example: Real vs Nominal Gold Price
const chartConfig = {
  type: 'line',
  data: {
    datasets: [
      {
        label: 'Nominal Price (USD)',
        data: nominalData,
        borderColor: 'rgb(251, 191, 36)', // amber
        yAxisID: 'y',
      },
      {
        label: `Real Price (${baseYear} USD)`,
        data: realData,
        borderColor: 'rgb(34, 197, 94)', // green
        borderDash: [5, 5],
        yAxisID: 'y',
      },
    ],
  },
  options: {
    scales: {
      y: {
        type: 'logarithmic', // Log scale for long-term price charts
        title: { text: 'Price ($/oz)' },
      },
    },
  },
};
```

#### New Page: `app/inflation-charts/page.tsx`
- Tab-based navigation between views
- Responsive design with stacked charts on mobile

---

## Implementation Phases

### Phase 1: Data Infrastructure
1. Create FRED API integration module
2. Build database schema for inflation/M2 data
3. Create data fetching and caching logic
4. Seed historical data (1970-present)

### Phase 2: Core Calculations
1. Implement CPI adjustment functions
2. Build M2 ratio calculations
3. Create purchasing power formulas
4. Add currency conversion logic

### Phase 3: API Layer
1. Add inflation endpoints to routes.py
2. Implement caching for expensive calculations
3. Add base year parameter handling
4. Test with historical edge cases

### Phase 4: Frontend Charts
1. Build Real vs Nominal chart component
2. Create M2 comparison overlay
3. Implement base year selector
4. Add interactive tooltips

### Phase 5: Purchasing Power Features
1. Build purchasing power calculator
2. Create "what could you buy" examples
3. Add asset comparison charts
4. Implement debasement meter

### Phase 6: Polish & Additional Views
1. Add multi-currency support
2. Mobile responsive adjustments
3. Add to navigation
4. Performance optimization

---

## Historical Data Points to Seed

### Key Milestones to Highlight
| Date | Event | Gold Price | CPI |
|------|-------|------------|-----|
| Aug 1971 | Nixon ends gold standard | $35 | 40.5 |
| Jan 1980 | Gold all-time high | $850 | 77.8 |
| Apr 2001 | Gold bear market low | $256 | 176.2 |
| Sep 2011 | Gold peak pre-2020 | $1,895 | 226.9 |
| Aug 2020 | COVID peak | $2,067 | 259.9 |
| Oct 2024 | Current range | $2,700+ | 315+ |

### M2 Money Supply Growth
| Year | M2 (Trillions) | Gold Price | Gold/M2 Ratio |
|------|----------------|------------|---------------|
| 1980 | $1.6T | $675 avg | 422 |
| 2000 | $4.9T | $279 avg | 57 |
| 2008 | $7.8T | $872 avg | 112 |
| 2020 | $18.4T | $1,770 avg | 96 |
| 2024 | $21.0T | $2,300 avg | 110 |

---

## UI/UX Mockup Concepts

### Real vs Nominal Chart
```
┌─────────────────────────────────────────────────────────────┐
│  Gold Price: Real vs Nominal          Base Year: [2020 ▼]  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  $3000 │                                        ╱──        │
│        │                               ╱───────╱  Nominal  │
│  $2000 │                    ╱─────────╱                    │
│        │           ╱───────╱                               │
│  $1000 │   ────────  ─ ─ ─ ─ ─ ─ ─ ─ ─ ─    Real (2020$)  │
│        │  ╱                                                │
│     $0 │──────────────────────────────────────────────────  │
│        1970    1980    1990    2000    2010    2020        │
│                                                             │
│  💡 1980 peak of $850 = $3,200 in 2020 dollars            │
│     Gold today at $2,700 has NOT beaten the 1980 high     │
│     in real terms!                                         │
└─────────────────────────────────────────────────────────────┘
```

### M2 Comparison
```
┌─────────────────────────────────────────────────────────────┐
│  Gold Price vs M2 Money Supply (Log Scale)                  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│        │                                   M2 ────          │
│        │                            ╱──────────            │
│        │                     ╱─────╱                       │
│        │              ╱─────╱                              │
│        │       ╱─────╱   Gold ════                         │
│        │  ────╱                 ════════════              │
│        │                                                    │
│        1980      1990      2000      2010      2020        │
│                                                             │
│  Gold/M2 Ratio: 110 (Current)                              │
│  Historical Avg: 95  |  Peak: 422 (1980)  |  Low: 57 (2000)│
│                                                             │
│  ⚠️  If gold returned to 1980 ratio, price = $8,862/oz     │
└─────────────────────────────────────────────────────────────┘
```

### Purchasing Power Calculator
```
┌─────────────────────────────────────────────────────────────┐
│  💰 Purchasing Power Time Machine                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Year: [1980 ▼]    Amount: [1 oz gold ▼]                   │
│                                                             │
│  In 1980, 1 oz of gold ($675) could buy:                   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ 🚗 10% of a new car (avg $7,200)                   │   │
│  │ 🏠 0.4% of median home ($63,700)                   │   │
│  │ 📺 3 color televisions ($225 each)                 │   │
│  │ ⛽ 561 gallons of gas ($1.20/gal)                  │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  Today, 1 oz of gold ($2,700) can buy:                     │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ 🚗 5% of a new car (avg $48,000)                   │   │
│  │ 🏠 0.6% of median home ($420,000)                  │   │
│  │ 📺 5 smart TVs ($500 each)                         │   │
│  │ ⛽ 750 gallons of gas ($3.60/gal)                  │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  📊 Gold's purchasing power increased 35% since 1980       │
└─────────────────────────────────────────────────────────────┘
```

### Debasement Meter
```
┌─────────────────────────────────────────────────────────────┐
│  💸 Dollar Debasement Meter                                 │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  $1 in 1970 = $0.13 today                                  │
│                                                             │
│  ████████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  87% lost    │
│                                                             │
│  Cumulative Inflation: 669%                                │
│  Average Annual: 3.7%                                       │
│                                                             │
│  Recent Rates:                                              │
│  ├─ Last Year:    3.2%                                     │
│  ├─ Last 5 Years: 4.1% avg                                 │
│  └─ Last 10 Years: 2.8% avg                                │
│                                                             │
│  Gold Performance vs Inflation:                             │
│  ├─ 1970 gold: $35 → Today: $2,700 (+7,614%)              │
│  ├─ CPI increase: +669%                                    │
│  └─ Gold outperformed inflation by 11× ✓                  │
└─────────────────────────────────────────────────────────────┘
```

---

## Estimated Effort

| Phase | Description | Complexity |
|-------|-------------|------------|
| 1 | Data Infrastructure | Medium (FRED API) |
| 2 | Core Calculations | Low |
| 3 | API Layer | Low |
| 4 | Frontend Charts | Medium |
| 5 | Purchasing Power Features | Medium |
| 6 | Polish & Currencies | Low |

---

## Open Questions for User

1. **Base year options**: 1970, 1980, 2000, 2020 - or allow any year?
2. **Currency priority**: Which currencies beyond USD are most important?
3. **Update frequency**: Daily refresh or weekly for inflation data?
4. **Purchasing power examples**: What items resonate most? (Cars, houses, gas, Big Macs?)
5. **Log vs Linear scale**: Default to log for long-term charts?

---

## Success Metrics

- Users understand gold's "real" all-time high vs nominal
- M2 comparison clearly shows monetary debasement
- Purchasing power calculator provides tangible comparisons
- Multi-currency view serves international users
- Page becomes go-to resource for inflation-adjusted PM analysis
