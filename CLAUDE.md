# CLAUDE.md - Algorand Sovereignty Analyzer

## Project Overview

A full-stack web application that analyzes Algorand wallet holdings to calculate a "sovereignty score" based on hard money principles (Bitcoin, Gold, Silver). It measures financial freedom by determining how many years of fixed expenses can be covered by hard assets.

**Philosophy**: Hard Money Maximalism - only Bitcoin, Gold, and Silver are considered "sovereign" assets that preserve wealth across generations.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│         FRONTEND (Next.js 16 + React 19 + TypeScript)  │
│  web/                                                   │
└─────────────────────────────────────────────────────────┘
                    ↓ HTTP/JSON
┌─────────────────────────────────────────────────────────┐
│          API LAYER (FastAPI + Uvicorn)                 │
│  api/                                                   │
└─────────────────────────────────────────────────────────┘
                    ↓ Python SDK
┌─────────────────────────────────────────────────────────┐
│      CORE ENGINE (Pure Python Analysis)                │
│  core/                                                  │
└─────────────────────────────────────────────────────────┘
```

## Quick Start Commands

### Backend (FastAPI)
```bash
# Install dependencies
pip install -r requirements.txt

# Run API server (from project root)
uvicorn api.main:app --reload --port 8000
```

### Frontend (Next.js)
```bash
cd web
npm install
npm run dev    # Runs on port 3000
```

### CLI Tool
```bash
python -m scripts.cli <ALGORAND_ADDRESS>
```

### Testing
```bash
pytest tests/                    # Run all tests
pytest tests/test_analyzer.py    # Run specific test file
```

## Directory Structure

```
algo-sovereignty-analyzer/
├── api/                      # FastAPI Backend
│   ├── main.py              # App initialization, CORS setup
│   ├── routes.py            # API endpoints (289 lines)
│   ├── schemas.py           # Pydantic request/response models
│   └── agent.py             # Claude AI integration
│
├── core/                     # Core Analysis Engine
│   ├── analyzer.py          # Main wallet analysis (470 lines)
│   ├── classifier.py        # Asset auto-classification
│   ├── pricing.py           # Multi-source price fetching
│   ├── lp_parser.py         # LP token decomposition (421 lines)
│   ├── history.py           # Historical snapshot tracking
│   └── models.py            # Pydantic data models
│
├── web/                      # Next.js Frontend
│   ├── app/                 # App Router pages
│   │   ├── page.tsx         # Landing page
│   │   ├── analyze/         # Results dashboard
│   │   ├── training/        # Educational content
│   │   └── philosophy/      # Sovereignty Manifesto
│   ├── components/          # React components
│   └── lib/                 # Utilities and types
│
├── scripts/cli.py           # CLI tool
├── tests/                   # Pytest test files
├── data/
│   ├── asset_classification.csv  # Manual classification overrides
│   └── history/                  # Per-address JSON snapshots
│
├── requirements.txt         # Python dependencies
└── docker-compose.yml       # Docker configuration
```

## Key Concepts

### Asset Categories
1. **Hard Money**: BTC, WBTC, goBTC, Gold (XAUT, PAXG, GOLD$), Silver (SILVER$)
2. **Algorand**: ALGO and liquid staking (xALGO, fALGO, gALGO, mALGO, lALGO, tALGO)
3. **Dollars**: Stablecoins (USDC, USDT, DAI) and Folks Finance wrapped versions (fUSDC, fUSDT)
4. **Shitcoins**: Everything else (LP tokens, governance tokens, NFTs, etc.)

### Sovereignty Metrics
- **Sovereignty Ratio** = Total Portfolio USD / Annual Fixed Expenses
- **Status Levels**:
  - ≥20: "Generationally Sovereign"
  - ≥6: "Antifragile"
  - ≥3: "Robust"
  - ≥1: "Fragile"
  - <1: "Vulnerable"

### LP Token Handling
LP tokens from Tinyman, Pact, and other DEXs are automatically decomposed into their underlying assets for accurate classification.

## API Endpoints

**Base URL**: `http://localhost:8000/api/v1`

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/analyze` | Main wallet analysis |
| POST | `/agent/advice` | AI coaching (Claude) |
| GET | `/classifications` | Asset classification lookup |
| POST | `/history/save` | Save wallet snapshot |
| GET | `/history/{address}` | Get historical data |

### Example: Analyze Wallet
```bash
curl -X POST http://localhost:8000/api/v1/analyze \
  -H "Content-Type: application/json" \
  -d '{"address": "YOUR_ADDRESS", "monthly_fixed_expenses": 4000}'
```

## Technology Stack

### Backend
- Python 3.9+
- FastAPI 0.100+
- Pydantic 2.0+
- py-algorand-sdk 2.0+
- tinyman-py-sdk 2.0+
- anthropic (Claude AI)

### Frontend
- Next.js 16 (App Router)
- React 19
- TypeScript 5
- Tailwind CSS 4
- Recharts (charts)
- @txnlab/use-wallet (Algorand wallets)

## Environment Variables

Create a `.env` file in the project root:
```
ANTHROPIC_API_KEY=your_key_here
```

## Key Files to Know

| File | Purpose |
|------|---------|
| `core/analyzer.py` | Main analysis logic - `AlgorandSovereigntyAnalyzer` class |
| `core/classifier.py` | Asset classification with regex patterns |
| `core/pricing.py` | Multi-source price fetching (Vestige, CoinGecko) |
| `core/lp_parser.py` | LP token decomposition logic |
| `api/routes.py` | All API endpoints |
| `api/agent.py` | Claude AI integration for advice |
| `web/app/analyze/page.tsx` | Main results dashboard |
| `web/lib/api.ts` | Frontend API client |
| `web/lib/types.ts` | TypeScript interfaces |
| `data/asset_classification.csv` | Manual classification overrides |

## Common Development Tasks

### Adding a New Asset Classification
1. Add to `data/asset_classification.csv` for manual overrides, OR
2. Update regex patterns in `core/classifier.py`

### Adding a New API Endpoint
1. Define Pydantic schemas in `api/schemas.py`
2. Add route handler in `api/routes.py`
3. Update this documentation

### Adding a New Frontend Page
1. Create directory under `web/app/`
2. Add `page.tsx` file
3. Use existing components from `web/components/`

### Testing Changes
```bash
# Backend tests
pytest tests/ -v

# Frontend type checking
cd web && npm run build
```

## External APIs Used

| API | Purpose | Rate Limits |
|-----|---------|-------------|
| AlgoNode | Algorand blockchain data | Public (no key needed) |
| Vestige Labs | ASA pricing (primary) | Public |
| CoinGecko | Crypto pricing (fallback) | ~30 req/min free tier |
| Anthropic Claude | AI advice generation | Requires API key |

## Code Style

- **Python**: Follow PEP 8, use type hints
- **TypeScript**: Strict mode enabled, use interfaces
- **Commits**: Conventional commits preferred (feat:, fix:, docs:, etc.)

## Caching

- API responses cached 15 minutes in-memory (per address)
- History snapshots stored in `data/history/{address}.json`
- Retention: 365 days max per address

## Docker

```bash
docker-compose up --build
```

Runs FastAPI on port 8000.

## Troubleshooting

### "Anthropic API error"
- Ensure `ANTHROPIC_API_KEY` is set in `.env`
- Check API key is valid and has credits

### "Asset price not found"
- Vestige may not have pricing for obscure ASAs
- Fallback prices are used for major assets

### "CORS error in browser"
- Ensure backend is running on port 8000
- Check CORS config in `api/main.py`

### "Wallet connection fails"
- Ensure wallet extension is installed (Pera, Defly)
- Check WalletConnect project ID if using WalletConnect
