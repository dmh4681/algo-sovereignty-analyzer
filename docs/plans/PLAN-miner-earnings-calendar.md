# Miner Earnings Calendar Implementation Plan

## Overview
A comprehensive earnings calendar for gold and silver mining companies that tracks when each company reports quarterly results, historical beat/miss performance, and post-earnings price reactions.

---

## Features

### 1. Interactive Calendar View
- **Monthly calendar grid** showing earnings dates for all tracked miners
- **Color-coded by metal**: Gold miners (amber), Silver miners (slate/silver)
- **Clickable dates** to reveal detailed earnings info
- **Filter options**: Show all, Gold only, Silver only, By tier jurisdiction

### 2. Upcoming Earnings List
- **Next 30 days** of scheduled earnings
- Countdown timers for imminent reports
- Pre-market vs After-hours indicator
- Links to company investor relations pages

### 3. Historical Performance Dashboard
- **Beat/Miss Record**: Visual scorecard per company
  - EPS beats vs misses (last 8 quarters)
  - Revenue beats vs misses
  - Production beats vs misses (oz produced vs guidance)
  - AISC beats vs misses (actual vs guidance)

### 4. Post-Earnings Price Reaction Analysis
- **1-day, 5-day, 30-day** price changes after each earnings report
- **Average reaction by outcome**: What happens when a miner beats vs misses?
- **Volatility metrics**: Historical IV vs RV around earnings
- **Sector correlation**: Do all miners move together after one reports?

### 5. Guidance Tracker
- Track forward AISC guidance per company
- Production guidance for next quarter/year
- CapEx guidance and project updates
- Highlight guidance changes quarter-over-quarter

---

## Data Sources

### Primary Sources (Free/Open)
1. **SEC EDGAR API** - For US-listed companies (quarterly 10-Q, annual 10-K)
   - Endpoint: `https://data.sec.gov/submissions/CIK{cik}.json`
   - Filing dates give us historical earnings dates

2. **Yahoo Finance** - Earnings calendar data
   - Historical and upcoming earnings dates
   - EPS estimates and actuals
   - Unofficial API through web scraping

3. **Alpha Vantage** (Free tier: 25 calls/day)
   - Earnings calendar endpoint
   - Historical price data for reaction analysis

### Secondary Sources (Paid/Premium)
1. **Financial Modeling Prep** - Has free tier
   - Earnings calendar API
   - Historical earnings data

2. **Polygon.io** - If needed for real-time quotes

### Manual Data Entry
- Initial seeding with historical data from company press releases
- AISC/production guidance manually entered from earnings calls
- Quarterly update process after each earnings season

---

## Technical Architecture

### Backend (Python/FastAPI)

#### New Database Model: `EarningsEvent`
```python
class EarningsEvent(BaseModel):
    id: str
    ticker: str
    metal: str  # 'gold' or 'silver'
    company_name: str
    quarter: str  # 'Q1 2024', 'Q2 2024', etc.
    fiscal_year_end: str  # Month company's fiscal year ends

    # Timing
    earnings_date: datetime
    time_of_day: str  # 'pre-market', 'after-hours', 'during-market'
    is_confirmed: bool  # vs estimated

    # Results (null until reported)
    eps_actual: Optional[float]
    eps_estimate: Optional[float]
    revenue_actual: Optional[float]  # in millions
    revenue_estimate: Optional[float]

    # Mining-specific (manually entered)
    production_actual: Optional[int]  # oz
    production_guidance: Optional[int]
    aisc_actual: Optional[float]
    aisc_guidance: Optional[float]

    # Post-earnings price data
    price_before: Optional[float]
    price_1d_after: Optional[float]
    price_5d_after: Optional[float]
    price_30d_after: Optional[float]

    # Metadata
    transcript_url: Optional[str]
    press_release_url: Optional[str]
    created_at: datetime
    updated_at: datetime
```

#### New Module: `core/earnings_calendar.py`
```python
# Key functions:
- get_earnings_db() -> EarningsDatabase (singleton)
- fetch_upcoming_earnings() -> List[EarningsEvent]
- fetch_historical_earnings(ticker: str) -> List[EarningsEvent]
- calculate_beat_miss_stats(ticker: str) -> BeatMissStats
- calculate_price_reactions(ticker: str) -> PriceReactionStats
- update_earnings_from_sec(ticker: str) -> None
- seed_historical_data() -> int  # returns count seeded
```

#### API Endpoints: `api/routes.py`
```
GET  /earnings/calendar?month=2024-01
GET  /earnings/upcoming?days=30
GET  /earnings/ticker/{ticker}
GET  /earnings/stats/{ticker}
GET  /earnings/sector-stats?metal=gold
POST /earnings  (admin: manual entry)
POST /earnings/refresh  (trigger data refresh)
```

### Frontend (Next.js/React)

#### New Component: `components/EarningsCalendar.tsx`
- **CalendarView**: Monthly grid with earnings dots
- **UpcomingList**: Card list of next 30 days
- **CompanyDetail**: Modal/drawer with full earnings history
- **BeatMissChart**: Visual bar chart of historical performance
- **PriceReactionChart**: Line chart of post-earnings moves

#### New Page: `app/earnings-calendar/page.tsx`
- Full-page earnings calendar experience
- Responsive: calendar on desktop, list on mobile

#### Navigation Addition
Add to `preciousMetalsItems` in MainNav.tsx:
```typescript
{
  label: 'Earnings Calendar',
  href: '/earnings-calendar',
  description: 'Track miner quarterly reports and price reactions',
}
```

---

## Implementation Phases

### Phase 1: Database & Core Logic (Backend)
1. Create `EarningsEvent` model and database class
2. Implement SQLite storage with migrations
3. Build seed data for last 2 years of earnings (20 companies × 8 quarters = 160 records)
4. Create basic CRUD functions

### Phase 2: Data Fetching & Automation
1. Integrate SEC EDGAR API for US companies
2. Add Yahoo Finance scraping for estimates
3. Build price reaction calculator using existing price data
4. Create refresh/update job logic

### Phase 3: API Endpoints
1. Add all REST endpoints to routes.py
2. Implement filtering and pagination
3. Add stats aggregation endpoints
4. Test with Swagger/OpenAPI

### Phase 4: Frontend Calendar Component
1. Build calendar grid component (month view)
2. Create upcoming earnings list component
3. Add company detail modal with charts
4. Implement filtering controls

### Phase 5: Analysis Features
1. Beat/miss visualization component
2. Price reaction analysis charts
3. Sector correlation view
4. Guidance tracker display

### Phase 6: Polish & Integration
1. Add to navigation
2. Mobile responsive design
3. Loading states and error handling
4. Data refresh automation

---

## Companies to Track

### Gold Miners (from existing GoldTracker)
| Ticker | Company | Typical Earnings Month |
|--------|---------|----------------------|
| NEM | Newmont | Feb, May, Aug, Nov |
| GOLD | Barrick Gold | Feb, May, Aug, Nov |
| AEM | Agnico Eagle | Feb, May, Aug, Nov |
| FNV | Franco-Nevada | Mar, May, Aug, Nov |
| WPM | Wheaton PM | Mar, May, Aug, Nov |
| KGC | Kinross Gold | Feb, May, Aug, Nov |
| AU | AngloGold | Feb, May, Aug, Nov |
| AGI | Alamos Gold | Feb, May, Aug, Nov |
| BTG | B2Gold | Mar, May, Aug, Nov |
| EGO | Eldorado Gold | Feb, May, Aug, Nov |

### Silver Miners (from existing SilverTracker)
| Ticker | Company | Typical Earnings Month |
|--------|---------|----------------------|
| PAAS | Pan American | Feb, May, Aug, Nov |
| HL | Hecla Mining | Feb, May, Aug, Nov |
| AG | First Majestic | Feb, May, Aug, Nov |
| EXK | Endeavour Silver | Mar, May, Aug, Nov |
| CDE | Coeur Mining | Feb, May, Aug, Nov |
| MAG | MAG Silver | Mar, May, Aug, Nov |
| ASM | Avino Silver | Mar, Jun, Sep, Dec |
| SILV | SilverCrest | Mar, May, Aug, Nov |
| FSM | Fortuna Silver | Feb, May, Aug, Nov |
| SSRM | SSR Mining | Feb, May, Aug, Nov |

---

## UI/UX Mockup Concepts

### Calendar View
```
┌─────────────────────────────────────────────┐
│  ◀ January 2024 ▶    [All] [Gold] [Silver]  │
├─────────────────────────────────────────────┤
│ Sun  Mon  Tue  Wed  Thu  Fri  Sat           │
│      1    2    3    4    5    6             │
│                     🥇              Gold dot │
│  7   8    9   10   11   12   13             │
│           🥈                  Silver dot    │
│ ...                                         │
└─────────────────────────────────────────────┘
```

### Upcoming Earnings Card
```
┌─────────────────────────────────────────────┐
│ 🥇 Newmont (NEM)              Q4 2024       │
│ ─────────────────────────────────────────── │
│ 📅 Feb 20, 2025 · Before Market             │
│ EPS Est: $0.82 | Rev Est: $4.2B             │
│                                             │
│ Last Quarter: Beat ✓ (+$0.08)               │
│ Avg 1-Day Reaction: +2.4%                   │
│                          [View Details →]   │
└─────────────────────────────────────────────┘
```

### Beat/Miss Scorecard
```
┌─────────────────────────────────────────────┐
│ Newmont (NEM) - Last 8 Quarters             │
├─────────────────────────────────────────────┤
│ EPS:        ✓ ✓ ✗ ✓ ✓ ✓ ✗ ✓   (6/8 = 75%)  │
│ Revenue:    ✓ ✓ ✓ ✓ ✗ ✓ ✓ ✓   (7/8 = 88%)  │
│ Production: ✓ ✗ ✓ ✓ ✓ ✓ ✗ ✓   (6/8 = 75%)  │
│ AISC:       ✓ ✓ ✓ ✗ ✓ ✓ ✓ ✓   (7/8 = 88%)  │
└─────────────────────────────────────────────┘
```

---

## Estimated Effort

| Phase | Description | Complexity |
|-------|-------------|------------|
| 1 | Database & Core Logic | Medium |
| 2 | Data Fetching | High (API integration) |
| 3 | API Endpoints | Low |
| 4 | Frontend Calendar | Medium |
| 5 | Analysis Features | Medium |
| 6 | Polish & Integration | Low |

---

## Open Questions for User

1. **Historical depth**: How many years of historical earnings to seed? (Suggested: 2 years)
2. **Update frequency**: Manual updates vs automated daily refresh?
3. **Alerts/Notifications**: Add email/push alerts before earnings? (Future feature?)
4. **Conference call transcripts**: Link to transcripts or summarize key points?
5. **Estimates source**: Use consensus estimates from Yahoo/Alpha Vantage or manual entry?

---

## Success Metrics

- Users can see all upcoming miner earnings at a glance
- Historical beat/miss data helps users anticipate volatility
- Price reaction analysis informs trading decisions around earnings
- Guidance tracker keeps users informed of company projections
