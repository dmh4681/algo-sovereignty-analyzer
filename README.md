# Algorand Sovereignty Analyzer

> Analyze the "sovereignty" of any Algorand wallet based on hard money principles

**Live at:** [algosovereignty.com](https://algosovereignty.com)

## Vision

A tool that analyzes ANY Algorand wallet and outputs a "sovereignty score" based on hard money principles - then makes it accessible via web app for the entire Algorand community.

**Philosophy**: Hard Money Maximalism - only Bitcoin, Gold, and Silver are considered "sovereign" assets that preserve wealth across generations.

---

## Table of Contents

- [Quick Start](#quick-start)
- [Architecture](#architecture)
- [Installation](#installation)
- [Configuration](#configuration)
- [API Reference](#api-reference)
- [Core Concepts](#core-concepts)
- [Development](#development)
- [Deployment](#deployment)
- [Troubleshooting](#troubleshooting)

---

## Quick Start

```bash
# Clone repository
git clone https://github.com/your-username/algo-sovereignty-analyzer.git
cd algo-sovereignty-analyzer

# Backend setup
pip install -r requirements.txt
uvicorn api.main:app --reload --port 8000

# Frontend setup (separate terminal)
cd web
npm install
npm run dev
```

Visit http://localhost:3000 to analyze any Algorand wallet.

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│         FRONTEND (Next.js 16 + React 19 + TypeScript)  │
│  - Enter any Algorand address                           │
│  - View sovereignty breakdown                           │
│  - AI-powered coaching via Claude                       │
│  - Wallet connection (Pera, Defly)                      │
└─────────────────────────────────────────────────────────┘
                    ↓ HTTP/JSON
┌─────────────────────────────────────────────────────────┐
│          API LAYER (FastAPI + Uvicorn)                 │
│  - POST /analyze {address, expenses}                    │
│  - POST /agent/advice (AI coaching)                     │
│  - GET /classifications                                 │
│  - History snapshots                                    │
└─────────────────────────────────────────────────────────┘
                    ↓ Python SDK
┌─────────────────────────────────────────────────────────┐
│      CORE ENGINE (Pure Python Analysis)                │
│  - AlgorandSovereigntyAnalyzer                         │
│  - AssetClassifier (regex patterns)                     │
│  - LPParser (Tinyman/Pact decomposition)               │
│  - Multi-source pricing (Vestige, CoinGecko)           │
└─────────────────────────────────────────────────────────┘
                    ↓ API Calls
┌─────────────────────────────────────────────────────────┐
│              DATA SOURCES (External)                    │
│  - AlgoNode API (account data)                          │
│  - Vestige Labs (ASA pricing)                           │
│  - CoinGecko (fallback pricing)                         │
│  - Tinyman SDK (LP pool state)                          │
└─────────────────────────────────────────────────────────┘
```

---

## Installation

### Prerequisites

| Software | Version | Purpose |
|----------|---------|---------|
| Python | 3.9+ | Backend runtime |
| Node.js | 18+ | Frontend runtime |
| Git | Latest | Version control |

### Backend Setup

```bash
# Create virtual environment
python -m venv venv

# Activate (Windows)
.\venv\Scripts\activate

# Activate (macOS/Linux)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env
# Edit .env with your API keys
```

### Frontend Setup

```bash
cd web

# Install dependencies
npm install

# Copy environment template (if exists)
cp .env.example .env.local
```

### Start Development Servers

```bash
# Terminal 1: Backend
uvicorn api.main:app --reload --port 8000

# Terminal 2: Frontend
cd web && npm run dev
```

Visit http://localhost:3000

---

## Configuration

### Environment Variables

Create a `.env` file in the project root:

```bash
# ===================
# AI Coaching (Required for /agent/advice)
# ===================
ANTHROPIC_API_KEY=sk-ant-api03-...

# ===================
# Optional: Local Node
# ===================
ALGORAND_NODE_URL=http://127.0.0.1:8080
ALGORAND_NODE_TOKEN=your-token

# ===================
# Optional: API Security
# ===================
API_KEY=your-secure-api-key
CORS_ORIGINS=http://localhost:3000,https://algosovereignty.com
```

### Frontend Environment

Create `web/.env.local`:

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## API Reference

**Base URL**: `http://localhost:8000/api/v1`

### Core Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/analyze` | Main wallet analysis |
| POST | `/agent/advice` | AI coaching (Claude) |
| GET | `/classifications` | Asset classification lookup |
| POST | `/history/save` | Save wallet snapshot |
| GET | `/history/{address}` | Get historical data |

### Analyze Wallet

```bash
curl -X POST http://localhost:8000/api/v1/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "address": "AAAA...YOUR_ADDRESS...",
    "monthly_fixed_expenses": 4000
  }'
```

**Response:**

```json
{
  "total_usd": 25000.0,
  "categories": {
    "hard_money": [{"name": "goBTC", "ticker": "GOBTC", "amount": 0.015, "usd_value": 1500}],
    "algo": [{"name": "Algorand (PARTICIPATING)", "amount": 50000, "usd_value": 12500}],
    "dollars": [{"name": "USD Coin", "ticker": "USDC", "amount": 5000, "usd_value": 5000}],
    "shitcoin": [{"name": "SomeMeme", "amount": 1000000, "usd_value": 50}]
  },
  "sovereignty": {
    "ratio": 0.52,
    "years_of_freedom": 0.52,
    "status": "vulnerable",
    "hard_money_percentage": 15.0
  }
}
```

### Get AI Coaching

```bash
curl -X POST http://localhost:8000/api/v1/agent/advice \
  -H "Content-Type: application/json" \
  -d '{"analysis": {...analysis_result...}}'
```

---

## Core Concepts

### Asset Categories

| Category | Assets | Sovereignty Impact |
|----------|--------|-------------------|
| **hard_money** | BTC (goBTC, WBTC), Gold (XAUT, GOLD$), Silver (SILVER$) | Positive (generational wealth) |
| **algo** | ALGO, xALGO, fALGO, gALGO, mALGO, lALGO, tALGO | Positive (hard cap, staking) |
| **dollars** | USDC, USDT, DAI, fUSDC, fUSDT | Neutral (fiat proxy) |
| **shitcoin** | Everything else | Negative (speculative) |

### Sovereignty Status Levels

| Status | Ratio | Years | Meaning |
|--------|-------|-------|---------|
| Generationally Sovereign | ≥20 | 20+ years | Multigenerational wealth |
| Antifragile | ≥6 | 6-20 years | Benefits from volatility |
| Robust | ≥3 | 3-6 years | Solid position |
| Fragile | ≥1 | 1-3 years | Building foundation |
| Vulnerable | <1 | <1 year | Immediate action needed |

### LP Token Handling

LP tokens from Tinyman and Pact are automatically decomposed into underlying assets:

```
TMPOOL-ALGO-goBTC (100 tokens)
    ↓ LP Parser
├── ALGO: 5000 → "algo" category ($1,250)
└── goBTC: 0.0125 → "hard_money" category ($1,250)

Total: $2,500 correctly categorized
```

---

## Development

### Directory Structure

```
algo-sovereignty-analyzer/
├── api/                      # FastAPI Backend
│   ├── main.py              # App initialization, CORS
│   ├── routes.py            # API endpoints
│   ├── schemas.py           # Pydantic models
│   └── agent.py             # Claude AI integration
│
├── core/                     # Core Analysis Engine
│   ├── analyzer.py          # Main analysis logic
│   ├── classifier.py        # Asset classification
│   ├── pricing.py           # Price fetching
│   ├── lp_parser.py         # LP decomposition
│   ├── history.py           # Snapshot tracking
│   └── models.py            # Data models
│
├── web/                      # Next.js Frontend
│   ├── app/                 # App Router pages
│   ├── components/          # React components
│   └── lib/                 # Utilities
│
├── scripts/cli.py           # CLI tool
├── tests/                   # Pytest tests
├── data/
│   ├── asset_classification.csv
│   └── history/             # Per-address snapshots
│
├── docs/                    # Documentation
│   ├── api/                 # API docs
│   ├── analyzer.md          # Core analyzer docs
│   ├── lp-parser.md         # LP parsing docs
│   └── agent.md             # Claude integration docs
│
├── requirements.txt
└── docker-compose.yml
```

### CLI Tool

```bash
# Analyze a wallet from command line
python -m scripts.cli AAAA...YOUR_ADDRESS...

# With monthly expenses
python -m scripts.cli AAAA...YOUR_ADDRESS... --expenses 4000
```

### Running Tests

```bash
# All tests
pytest tests/

# Specific test file
pytest tests/test_analyzer.py -v

# With coverage
pytest tests/ --cov=core
```

### Adding Asset Classifications

**Option 1: CSV Override**

Add to `data/asset_classification.csv`:

```csv
asset_id,category,name
123456789,hard_money,My Gold Token
```

**Option 2: Regex Patterns**

Update `core/classifier.py`:

```python
HARD_MONEY_PATTERNS = [
    r"(?i)^(go)?btc",
    r"(?i)gold|xaut|paxg",
    r"(?i)silver",
    # Add your pattern here
]
```

---

## Deployment

### Backend → Railway

1. Create Railway project
2. Connect GitHub repo
3. Set environment variables:
   - `ANTHROPIC_API_KEY`
   - `CORS_ORIGINS=https://algosovereignty.com`
4. Set start command:
   ```bash
   uvicorn api.main:app --host 0.0.0.0 --port $PORT
   ```
5. Deploy

### Frontend → Vercel

1. Push to GitHub
2. Import in Vercel
3. Set environment variables:
   - `NEXT_PUBLIC_API_URL=https://your-railway-url.up.railway.app`
4. Deploy

### Docker (Alternative)

```bash
# Build and run
docker-compose up --build

# Services:
# - api: http://localhost:8000
# - web: http://localhost:3000
```

---

## Troubleshooting

### Common Issues

**"Anthropic API error"**
```bash
# Ensure API key is set
echo $ANTHROPIC_API_KEY

# Check key is valid and has credits
```

**"Asset price not found"**
- Vestige may not have pricing for obscure ASAs
- Fallback prices used for major assets (BTC, ALGO, USDC)

**"CORS error in browser"**
```bash
# Check CORS_ORIGINS in .env
CORS_ORIGINS=http://localhost:3000

# Restart backend
uvicorn api.main:app --reload
```

**"Wallet connection fails"**
- Install wallet extension (Pera, Defly)
- Check WalletConnect project ID if using WalletConnect

### Performance Tips

1. **Use local node** for faster analysis (if running a node)
2. **API caching**: Results cached 15 minutes per address
3. **LP parsing**: Additional Tinyman SDK calls when LP tokens detected

---

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
- Recharts
- @txnlab/use-wallet

### External APIs
| API | Purpose | Rate Limits |
|-----|---------|-------------|
| AlgoNode | Blockchain data | Public (no key) |
| Vestige Labs | ASA pricing | Public |
| CoinGecko | Fallback pricing | ~30 req/min |
| Anthropic Claude | AI coaching | Requires API key |

---

## Documentation

Detailed documentation available in `docs/`:

- **[API Documentation](docs/api/README.md)** - Complete endpoint reference
- **[Analyzer](docs/analyzer.md)** - Core analysis engine
- **[LP Parser](docs/lp-parser.md)** - LP token decomposition
- **[Claude Agent](docs/agent.md)** - AI coaching integration

---

## License

Proprietary - © 2025 Sovereign Path LLC

---

## Support

- **Website**: [algosovereignty.com](https://algosovereignty.com)
- **Email**: dylan@sovereignpath.com
- **Documentation**: `docs/` directory

---

*Last Updated: 2026-01-15*
