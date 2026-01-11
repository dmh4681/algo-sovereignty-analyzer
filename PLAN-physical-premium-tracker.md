# Physical Premium Tracker Implementation Plan

## Overview
A real-time tracker showing premiums on popular physical gold and silver products across major dealers. This feature helps precious metals stackers find the best prices and understand market conditions through premium analysis.

---

## Features

### 1. Premium Dashboard
- **Live premiums** on popular products (Eagles, Maples, bars, rounds)
- **Premium over spot**: Both $ and % over current spot price
- **Best deal finder**: Lowest premium for each product type
- **Premium trend**: Are premiums rising or falling?

### 2. Product Comparison Grid
- **Side-by-side comparison**: Same product across multiple dealers
- **Sort by**: Price, premium %, shipping cost, total cost
- **Filter by**: Product type, metal, dealer, in-stock only
- **Quantity breaks**: Show pricing at 1, 10, 100+ units

### 3. Dealer Leaderboard
- **Cheapest by category**: Who has best prices on Eagles? Bars?
- **Overall value score**: Composite of premiums + shipping + reputation
- **In-stock tracking**: Which dealers actually have product?
- **Historical reliability**: Days to ship, customer ratings

### 4. Premium History Charts
- **30-day/90-day/1yr** premium trends per product
- **Premium vs spot**: When spot spikes, do premiums compress?
- **Crisis indicators**: Premium spikes = physical demand surge
- **Seasonal patterns**: Year-end buying, tax season selling

### 5. Alert System (Future)
- **Price alerts**: Notify when product drops below target premium
- **Restock alerts**: Notify when out-of-stock product returns
- **Deal alerts**: Unusual low premium opportunities

---

## Products to Track

### Gold Products
| Product | Weight | Typical Premium |
|---------|--------|-----------------|
| American Gold Eagle | 1 oz | 4-6% |
| Canadian Gold Maple | 1 oz | 3-5% |
| Austrian Philharmonic | 1 oz | 3-5% |
| South African Krugerrand | 1 oz | 3-5% |
| American Gold Buffalo | 1 oz | 4-6% |
| Gold Bar (PAMP/Valcambi) | 1 oz | 2-4% |
| Gold Bar | 10 oz | 2-3% |
| Gold Bar | 1 kilo | 1-2% |

### Silver Products
| Product | Weight | Typical Premium |
|---------|--------|-----------------|
| American Silver Eagle | 1 oz | 25-40% |
| Canadian Silver Maple | 1 oz | 15-25% |
| Austrian Philharmonic | 1 oz | 15-25% |
| Generic Silver Round | 1 oz | 8-15% |
| Silver Bar | 10 oz | 8-12% |
| Silver Bar | 100 oz | 5-8% |
| Junk Silver (90%) | $1 FV | 5-15% |
| Silver Bar | 1 kilo | 6-10% |

---

## Dealers to Track

### Tier 1 - Major Online Dealers
| Dealer | Website | Notes |
|--------|---------|-------|
| APMEX | apmex.com | Largest, wide selection |
| JM Bullion | jmbullion.com | Good prices, fast shipping |
| SD Bullion | sdbullion.com | Often lowest prices |
| Money Metals Exchange | moneymetals.com | Good for bars |
| Provident Metals | providentmetals.com | Part of JM Bullion |
| BGASC | bgasc.com | Competitive pricing |
| Golden Eagle Coins | goldeneaglecoin.com | Good for coins |
| Bullion Exchanges | bullionexchanges.com | NY-based |

### Tier 2 - Other Notable
| Dealer | Notes |
|--------|-------|
| Scottsdale Mint | Direct from mint, good bars |
| Silver Gold Bull | Canadian, ships to US |
| Hero Bullion | Newer, competitive |
| Bold Precious Metals | Good variety |
| Monument Metals | East coast |

---

## Data Sources & Scraping Strategy

### Option 1: Web Scraping (Primary)
Build scrapers for each dealer's product pages:

```python
# Example scraper structure
class APMEXScraper:
    base_url = "https://www.apmex.com"

    def get_product_price(self, product_url: str) -> ProductPrice:
        # Fetch page, parse price, calculate premium
        pass

    def get_category_prices(self, category: str) -> List[ProductPrice]:
        # Scrape entire category (Gold Eagles, Silver Maples, etc.)
        pass
```

**Challenges:**
- Sites may block scrapers (need rotating proxies, rate limiting)
- Prices change frequently (need caching strategy)
- HTML structure varies by dealer
- Terms of service considerations

### Option 2: Affiliate API Integration
Some dealers offer affiliate APIs:
- APMEX has affiliate program with product feeds
- JM Bullion offers data feeds to affiliates
- Requires affiliate signup and approval

### Option 3: Manual Entry + Community
- Admin dashboard for manual price entry
- Community-submitted prices (with verification)
- Weekly updates instead of real-time

### Recommended Approach: Hybrid
1. **Primary**: Scrape 3-4 major dealers (APMEX, JM Bullion, SD Bullion)
2. **Secondary**: Affiliate API where available
3. **Fallback**: Manual entry for others
4. **Caching**: 15-minute cache, refresh on demand

---

## Technical Architecture

### Backend (Python/FastAPI)

#### New Database Models
```python
class Dealer(BaseModel):
    id: str
    name: str
    website: str
    logo_url: Optional[str]
    is_active: bool
    scraper_enabled: bool
    affiliate_url_template: Optional[str]
    shipping_info: str  # "Free over $199", etc.
    created_at: datetime

class Product(BaseModel):
    id: str
    name: str  # "American Silver Eagle"
    metal: str  # 'gold' or 'silver'
    weight_oz: float
    product_type: str  # 'coin', 'bar', 'round', 'junk'
    mint: Optional[str]  # "US Mint", "Royal Canadian Mint"
    purity: float  # 0.999, 0.9999
    is_government: bool  # Government-minted vs private

class ProductPrice(BaseModel):
    id: str
    product_id: str
    dealer_id: str
    price: float
    quantity: int  # Price for this quantity (1, 10, 100)
    spot_price: float  # Spot at time of capture
    premium_dollars: float
    premium_percent: float
    in_stock: bool
    product_url: str
    captured_at: datetime

class PremiumHistory(BaseModel):
    id: str
    product_id: str
    dealer_id: str
    date: datetime  # Daily snapshot
    avg_premium_percent: float
    min_premium_percent: float
    spot_price: float
```

#### New Module: `core/premium_tracker.py`
```python
# Key functions:
- get_premium_db() -> PremiumDatabase (singleton)
- scrape_dealer(dealer_id: str) -> List[ProductPrice]
- get_current_prices(product_id: str) -> List[DealerPrice]
- get_best_price(product_id: str) -> DealerPrice
- get_premium_history(product_id: str, days: int) -> List[PremiumHistory]
- calculate_premium(price: float, spot: float, weight_oz: float) -> PremiumCalc
- get_dealer_leaderboard() -> List[DealerRanking]
- refresh_all_prices() -> RefreshResult
```

#### New Module: `core/scrapers/`
```
scrapers/
├── __init__.py
├── base.py          # BaseScraper class
├── apmex.py         # APMEXScraper
├── jmbullion.py     # JMBullionScraper
├── sdbullion.py     # SDBullionScraper
└── utils.py         # Shared utilities, proxy rotation
```

#### API Endpoints
```
GET  /premiums/products
GET  /premiums/products/{product_id}
GET  /premiums/dealers
GET  /premiums/dealers/{dealer_id}
GET  /premiums/compare?product_id=xxx
GET  /premiums/best-deals?metal=silver
GET  /premiums/history/{product_id}?days=30
GET  /premiums/leaderboard
POST /premiums/refresh  (trigger scrape)
POST /premiums/manual  (admin: manual entry)
```

### Frontend (Next.js/React)

#### New Component: `components/PremiumTracker.tsx`

**Sub-components:**
1. **PremiumDashboard**: Overview cards with key premiums
2. **ProductComparisonTable**: Multi-dealer comparison grid
3. **DealerLeaderboard**: Best dealers by category
4. **PremiumChart**: Historical premium trends
5. **BestDealFinder**: Filter and find lowest premiums
6. **ProductCard**: Individual product display

#### New Page: `app/premium-tracker/page.tsx`
- Tab-based: Overview, Gold Products, Silver Products, Dealers
- Filter sidebar for product selection
- Responsive grid layout

---

## Implementation Phases

### Phase 1: Data Model & Products
1. Create database models
2. Seed product catalog (20 gold, 20 silver products)
3. Create dealer registry
4. Build spot price integration (reuse existing)

### Phase 2: Scraping Infrastructure
1. Build base scraper class with retry/error handling
2. Implement APMEX scraper (largest selection)
3. Implement JM Bullion scraper
4. Add rate limiting and caching

### Phase 3: Premium Calculations
1. Premium calculation functions
2. Historical tracking (daily snapshots)
3. Best deal finder logic
4. Dealer ranking algorithm

### Phase 4: API Layer
1. Add premium endpoints to routes.py
2. Implement comparison endpoint
3. Add filtering/sorting
4. Create refresh/manual entry endpoints

### Phase 5: Frontend Dashboard
1. Build product comparison table
2. Create dealer leaderboard
3. Add premium trend charts
4. Implement filter controls

### Phase 6: Polish & Automation
1. Add to navigation
2. Scheduled refresh job (every 15 min)
3. Mobile responsive design
4. Error handling for failed scrapes

---

## Premium Calculation Logic

```python
def calculate_premium(
    price: float,
    spot_price: float,
    weight_oz: float,
    metal: str
) -> PremiumCalc:
    """
    Calculate premium over spot for a precious metals product.

    Args:
        price: Dealer's asking price
        spot_price: Current spot price per oz
        weight_oz: Weight in troy ounces
        metal: 'gold' or 'silver'

    Returns:
        PremiumCalc with dollar and percentage premium
    """
    melt_value = spot_price * weight_oz
    premium_dollars = price - melt_value
    premium_percent = (premium_dollars / melt_value) * 100

    return PremiumCalc(
        price=price,
        spot_price=spot_price,
        melt_value=melt_value,
        premium_dollars=round(premium_dollars, 2),
        premium_percent=round(premium_percent, 2),
        weight_oz=weight_oz
    )

# Example:
# Silver Eagle at $38.50, spot $30.00, weight 1oz
# Melt value: $30.00
# Premium: $8.50 (28.3%)
```

---

## UI/UX Mockup Concepts

### Premium Dashboard
```
┌─────────────────────────────────────────────────────────────────┐
│  🪙 Physical Premium Tracker         Spot: Au $2,680 | Ag $31  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌────────────────────────┐  ┌────────────────────────────┐    │
│  │ 🥇 Gold Eagle (1 oz)   │  │ 🥈 Silver Eagle (1 oz)     │    │
│  │ Best: $2,785           │  │ Best: $39.50               │    │
│  │ Premium: $105 (3.9%)   │  │ Premium: $8.50 (27.4%)     │    │
│  │ @ SD Bullion           │  │ @ JM Bullion               │    │
│  └────────────────────────┘  └────────────────────────────┘    │
│                                                                 │
│  ┌────────────────────────┐  ┌────────────────────────────┐    │
│  │ 🥇 Gold Bar (1 oz)     │  │ 🥈 Silver Maple (1 oz)     │    │
│  │ Best: $2,734           │  │ Best: $35.80               │    │
│  │ Premium: $54 (2.0%)    │  │ Premium: $4.80 (15.5%)     │    │
│  │ @ Money Metals         │  │ @ SD Bullion               │    │
│  └────────────────────────┘  └────────────────────────────┘    │
│                                                                 │
│  📊 Premium Trend: Silver Eagles ▲ 3% this week               │
│  💡 Tip: 10oz bars have lowest premiums right now              │
└─────────────────────────────────────────────────────────────────┘
```

### Product Comparison Table
```
┌─────────────────────────────────────────────────────────────────┐
│  American Silver Eagle (1 oz) - Compare Dealers                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Dealer          │ Price  │ Premium │  Stock  │  Ship  │ Total │
│  ─────────────────────────────────────────────────────────────  │
│  🏆 JM Bullion   │ $39.50 │  27.4%  │   ✓     │  Free  │ Best! │
│  SD Bullion      │ $39.85 │  28.5%  │   ✓     │  Free  │       │
│  APMEX           │ $41.20 │  33.0%  │   ✓     │  $9.95 │       │
│  Money Metals    │ $40.50 │  30.6%  │   ✓     │  Free  │       │
│  Provident       │ $39.95 │  28.8%  │   ✗     │  Free  │ OOS   │
│                                                                 │
│  Spot: $31.00 | Melt Value: $31.00 | Prices as of 5 min ago   │
│                                                   [Refresh 🔄]  │
└─────────────────────────────────────────────────────────────────┘
```

### Premium History Chart
```
┌─────────────────────────────────────────────────────────────────┐
│  Silver Eagle Premium History (90 days)                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  40% │          ╱╲                                             │
│      │         ╱  ╲    ╱╲                                      │
│  30% │    ────╱    ╲──╱  ╲────────────                         │
│      │   ╱                            ╲                        │
│  20% │──╱                              ╲───────                │
│      │                                                          │
│  10% │────────────────────────────────────────                 │
│      │                                                          │
│   0% └──────────────────────────────────────────────────────── │
│       Oct         Nov         Dec         Jan                   │
│                                                                 │
│  Current: 27.4% | 90d Avg: 29.1% | 90d Low: 24.2%             │
│                                                                 │
│  📊 Premium compressed 5% since December peak                  │
└─────────────────────────────────────────────────────────────────┘
```

### Dealer Leaderboard
```
┌─────────────────────────────────────────────────────────────────┐
│  Dealer Leaderboard                    Category: [Silver ▼]    │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  #  │ Dealer           │ Avg Premium │ Best For       │ Ship   │
│  ─────────────────────────────────────────────────────────────  │
│  1  │ SD Bullion       │   18.2%     │ Bars, Rounds   │ Free$  │
│  2  │ JM Bullion       │   19.5%     │ Eagles, Maples │ Free$  │
│  3  │ Money Metals     │   20.1%     │ Bars           │ Free$  │
│  4  │ Hero Bullion     │   21.3%     │ Generic        │ $8.00  │
│  5  │ APMEX            │   24.8%     │ Selection      │ $9.95  │
│                                                                 │
│  $ Free shipping over $199                                     │
│                                                                 │
│  💡 SD Bullion consistently lowest for silver bars & rounds   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Scraping Technical Details

### Rate Limiting Strategy
```python
class ScraperConfig:
    requests_per_minute = 10  # Conservative
    cache_ttl_minutes = 15  # Cache prices for 15 min
    retry_attempts = 3
    retry_delay_seconds = 5
    use_proxy_rotation = True  # For production
    user_agent_rotation = True
```

### Error Handling
```python
class ScrapeResult:
    success: bool
    products_scraped: int
    errors: List[ScrapeError]
    duration_seconds: float
    next_scrape_allowed: datetime
```

### Caching Layer
```python
# Redis or in-memory cache
cache_key = f"premium:{dealer_id}:{product_id}"
cached = cache.get(cache_key)
if cached and not force_refresh:
    return cached
# ... scrape and cache result
cache.set(cache_key, result, ttl=900)  # 15 min
```

---

## Estimated Effort

| Phase | Description | Complexity |
|-------|-------------|------------|
| 1 | Data Model & Products | Low |
| 2 | Scraping Infrastructure | High |
| 3 | Premium Calculations | Low |
| 4 | API Layer | Low |
| 5 | Frontend Dashboard | Medium |
| 6 | Polish & Automation | Medium |

**Note**: Scraping phase is highest complexity due to:
- Different HTML structures per dealer
- Anti-bot measures
- Maintenance as sites change

---

## Open Questions for User

1. **Scraping legality**: Are you comfortable with web scraping? Alternative is affiliate APIs or manual entry.
2. **Dealer priority**: Which 5 dealers are most important to launch with?
3. **Update frequency**: Real-time (more complexity) vs hourly vs daily?
4. **Affiliate links**: Want to monetize with affiliate links to dealers?
5. **Product scope**: Start with top 10 products each metal, or comprehensive catalog?
6. **Alerts feature**: Include price alerts in V1 or save for later?

---

## Legal/Ethical Considerations

### Web Scraping
- Check each dealer's `robots.txt` and Terms of Service
- Implement polite scraping (rate limits, identify as bot)
- Cache aggressively to minimize requests
- Consider reaching out for permission/API access

### Affiliate Disclosure
- If using affiliate links, disclose clearly
- "We may earn a commission from dealer links"
- Separate "Sponsored" dealers if paid placements

### Price Accuracy
- Clearly show "as of" timestamps
- Disclaimer: "Prices may vary, verify with dealer"
- Link directly to product pages

---

## Success Metrics

- Users find best prices on popular products
- Premium trends help users time purchases
- Dealer comparison saves users money
- Site becomes go-to for physical PM price comparison
- Potential affiliate revenue stream
