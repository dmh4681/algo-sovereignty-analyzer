# Algo Sovereignty Analyzer - Setup Guide

## Overview

The Algo Sovereignty Analyzer calculates financial sovereignty scores for Algorand wallets based on hard money principles (Bitcoin, Gold, Silver).

## Prerequisites

- Python 3.9+
- Node.js 18+ (for frontend)
- Git

## Quick Start

### Backend (FastAPI)

```bash
# Clone repository
git clone https://github.com/dmh4681/algo-sovereignty-analyzer.git
cd algo-sovereignty-analyzer/algo-sovereignty-analyzer

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run API server
uvicorn api.main:app --reload --port 8000
```

API available at: http://localhost:8000

### Frontend (Next.js)

```bash
cd web
npm install
npm run dev
```

Frontend available at: http://localhost:3000

### CLI Tool

```bash
python -m scripts.cli <ALGORAND_ADDRESS>
```

## Environment Variables

Create a `.env` file in the project root:

```env
# Required for AI coaching
ANTHROPIC_API_KEY=your_key_here

# Optional: Use local Algorand node (faster)
USE_LOCAL_NODE=false
ALGOD_ADDRESS=http://127.0.0.1:8080
ALGOD_TOKEN=your_token_here

# Optional: CoinGecko Pro API for better rate limits
COINGECKO_API_KEY=your_key_here
```

## Project Structure

```
algo-sovereignty-analyzer/
├── api/                      # FastAPI Backend
│   ├── main.py              # App initialization, CORS
│   ├── routes.py            # API endpoints
│   ├── schemas.py           # Pydantic models
│   ├── agent.py             # Claude AI integration
│   └── errors.py            # Custom exceptions
│
├── core/                     # Analysis Engine
│   ├── analyzer.py          # Main wallet analysis (470 lines)
│   ├── classifier.py        # Asset classification
│   ├── corrections.py       # User correction system
│   ├── pricing.py           # Multi-source price fetching
│   ├── lp_parser.py         # LP token decomposition (421 lines)
│   ├── history.py           # Historical snapshots
│   ├── models.py            # Pydantic data models
│   └── network.py           # Algorand network stats
│
├── web/                      # Next.js Frontend
│   ├── app/                 # App Router pages
│   ├── components/          # React components
│   └── lib/                 # Utilities
│
├── data/
│   ├── asset_classification.csv  # Manual overrides
│   ├── user_corrections.json     # User-submitted corrections
│   └── history/                  # Per-address snapshots
│
├── scripts/
│   └── cli.py               # Command-line tool
│
├── tests/                   # Pytest test files
├── docs/                    # Documentation
└── requirements.txt         # Python dependencies
```

## Configuration

### Asset Classification

The system classifies assets using a hierarchy:

1. **CSV Overrides** (`data/asset_classification.csv`) - Highest priority
2. **User Corrections** (`data/user_corrections.json`) - Medium priority
3. **Auto-classification** (`core/classifier.py`) - Lowest priority

#### Adding Manual Classifications

Edit `data/asset_classification.csv`:

```csv
asset_id,name,ticker,category,notes
793124631,goBTC,goBTC,hard_money,Wrapped Bitcoin
312769,Tether,USDT,dollars,Stablecoin
386192725,goETH,goETH,shitcoin,Not hard money
```

### CORS Configuration

Edit `api/main.py` to add allowed origins:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://algosovereignty.com",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Running Tests

```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_analyzer.py

# Run with coverage
pytest tests/ --cov=core --cov-report=html
```

## Docker Deployment

```bash
# Build and run
docker-compose up --build

# Run in background
docker-compose up -d
```

The API will be available at http://localhost:8000

### docker-compose.yml

```yaml
version: '3.8'
services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
    volumes:
      - ./data:/app/data
```

## External API Dependencies

| API | Purpose | Rate Limits | Auth Required |
|-----|---------|-------------|---------------|
| AlgoNode | Algorand data | Unlimited | No |
| Vestige Labs | ASA pricing | Unlimited | No |
| CoinGecko | Crypto prices | 30/min (free) | Optional |
| Anthropic Claude | AI coaching | By plan | Yes |

## Troubleshooting

### "Asset price not found"
- Vestige may not have pricing for obscure ASAs
- Check if asset is delisted or has no liquidity
- Fallback prices used for major assets (BTC, ETH, stables)

### "CORS error in browser"
- Check allowed origins in `api/main.py`
- Ensure backend is running on port 8000
- Clear browser cache

### "Algorand API timeout"
- Switch to AlgoNode (public API)
- Set `USE_LOCAL_NODE=false` in `.env`
- Check network connectivity

### "Anthropic API error"
- Verify `ANTHROPIC_API_KEY` is set
- Check API key is valid
- Ensure you have available credits

### "LP token not decomposed"
- LP may be from unsupported DEX
- Check `core/lp_parser.py` for supported protocols
- Submit issue for new DEX support

## Performance Tips

1. **Use Local Node** - Much faster than public APIs
2. **Enable Caching** - API caches for 15 minutes
3. **Limit History Requests** - Use `days` parameter
4. **Batch Analysis** - Analyze multiple addresses together

## Development Workflow

1. Make changes in `core/` or `api/`
2. Run tests: `pytest tests/`
3. Start dev server: `uvicorn api.main:app --reload`
4. Test endpoints with Swagger: http://localhost:8000/docs
5. Submit PR when ready

## API Documentation

Interactive API docs available at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
