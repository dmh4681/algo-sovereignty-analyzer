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

Create a `.env` file in the project root by copying the example:

```bash
cp .env.example .env
```

**SECURITY WARNING:** Never commit `.env` to version control. It should be in `.gitignore`.

#### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `ANTHROPIC_API_KEY` | API key for Claude AI coaching | `sk-ant-api03-...` |

#### Algorand Node Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `ALGORAND_NODE_URL` | `https://mainnet-api.algonode.cloud` | Algorand node API endpoint |
| `ALGORAND_NODE_TOKEN` | (empty) | Auth token for private nodes |

**Public API (default):** No configuration needed. Uses AlgoNode free tier.

**Local Node (faster):** If running your own Algorand node:
```bash
ALGORAND_NODE_URL=http://127.0.0.1:8080
ALGORAND_NODE_TOKEN=your-node-api-token
```

**AlgoExplorer Alternative:**
```bash
ALGORAND_NODE_URL=https://node.algoexplorerapi.io
```

#### Security & CORS

| Variable | Default | Description |
|----------|---------|-------------|
| `CORS_ORIGINS` | `*` | Comma-separated allowed origins |
| `API_KEY` | (none) | Optional API key for protected endpoints |

**Development:**
```bash
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

**Production:**
```bash
CORS_ORIGINS=https://algosovereignty.com,https://www.algosovereignty.com
```

#### Database Reseeding

| Variable | Default | Description |
|----------|---------|-------------|
| `RESEED_MINERS` | `false` | Reseed gold miner metrics on startup |
| `RESEED_SILVER` | `false` | Reseed silver miner metrics on startup |

Set to `true` to refresh market data databases on API restart.

#### Complete `.env` Example

```bash
# =============================================================================
# Algorand Sovereignty Analyzer - Environment Configuration
# =============================================================================

# -----------------------------------------------------------------------------
# AI Coaching (Required for /agent/advice endpoint)
# Get your key at: https://console.anthropic.com/
# -----------------------------------------------------------------------------
ANTHROPIC_API_KEY=sk-ant-api03-your-key-here

# -----------------------------------------------------------------------------
# Algorand Node Configuration
# Default: Uses AlgoNode public API (no configuration needed)
# For faster analysis, use a local node or paid API
# -----------------------------------------------------------------------------
# ALGORAND_NODE_URL=http://127.0.0.1:8080
# ALGORAND_NODE_TOKEN=your-local-node-token

# -----------------------------------------------------------------------------
# CORS Configuration
# Comma-separated list of allowed origins for browser requests
# Use * for development, specific origins for production
# -----------------------------------------------------------------------------
CORS_ORIGINS=http://localhost:3000,http://localhost:5173

# -----------------------------------------------------------------------------
# Optional: API Key Protection
# If set, protected endpoints require X-API-Key header
# -----------------------------------------------------------------------------
# API_KEY=your-secure-api-key-here

# -----------------------------------------------------------------------------
# Database Reseeding (set to true to refresh on startup)
# -----------------------------------------------------------------------------
# RESEED_MINERS=false
# RESEED_SILVER=false

# -----------------------------------------------------------------------------
# Logging
# -----------------------------------------------------------------------------
# LOG_LEVEL=INFO
```

### Frontend Environment

Create `web/.env.local` for the Next.js frontend:

```bash
# API endpoint (backend URL)
NEXT_PUBLIC_API_URL=http://localhost:8000

# WalletConnect Project ID (for wallet connections)
# Get one at: https://cloud.walletconnect.com/
NEXT_PUBLIC_WALLETCONNECT_PROJECT_ID=your-project-id
```

**Production frontend:**
```bash
NEXT_PUBLIC_API_URL=https://api.algosovereignty.com
NEXT_PUBLIC_WALLETCONNECT_PROJECT_ID=your-production-project-id
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

#### "Anthropic API error"

**Symptoms:**
- AI coaching returns error or empty response
- 401 Unauthorized or 403 Forbidden responses

**Solutions:**
```bash
# 1. Check if API key is set
echo $ANTHROPIC_API_KEY
# Should show: sk-ant-api03-...

# 2. Verify key in .env file
cat .env | grep ANTHROPIC

# 3. Test API key directly
curl https://api.anthropic.com/v1/messages \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -H "content-type: application/json" \
  -d '{"model":"claude-3-haiku-20240307","max_tokens":10,"messages":[{"role":"user","content":"Hi"}]}'

# 4. Check for API credits at console.anthropic.com
```

#### "Asset price not found"

**Symptoms:**
- Assets showing $0.00 value
- Warning messages about missing prices

**Causes & Solutions:**
- **Obscure ASA**: Vestige may not track this asset. Check if listed on any DEX.
- **New token**: Allow 24-48 hours for price feeds to populate.
- **Delisted token**: No longer traded, price feed removed.
- **Fallback used**: Major assets (BTC, ALGO, USDC) use hardcoded fallback prices if APIs fail.

```python
# Check if asset is priced on Vestige
# Visit: https://vestige.fi/asset/{ASSET_ID}

# Or use API directly:
curl "https://free-api.vestige.fi/asset/{ASSET_ID}/price"
```

#### "CORS error in browser"

**Symptoms:**
- Browser console shows: "Access-Control-Allow-Origin" error
- API calls work from Postman but fail from frontend

**Solutions:**
```bash
# 1. Check CORS_ORIGINS in .env
CORS_ORIGINS=http://localhost:3000,http://localhost:5173

# 2. For development, allow all origins (NOT for production!)
CORS_ORIGINS=*

# 3. Restart backend after .env changes
uvicorn api.main:app --reload

# 4. Clear browser cache (Ctrl+Shift+Delete)
```

#### "Wallet connection fails"

**Symptoms:**
- Pera/Defly wallet popup doesn't appear
- Connection timeout errors
- "No wallet found" message

**Solutions:**

1. **Install wallet extension:**
   - [Pera Wallet](https://perawallet.app/) (mobile + extension)
   - [Defly Wallet](https://defly.app/) (mobile + extension)

2. **Check browser compatibility:**
   - Chrome, Firefox, Brave, Edge supported
   - Safari may have issues with extensions

3. **WalletConnect issues:**
   ```bash
   # Ensure WalletConnect project ID is set (web/.env.local)
   NEXT_PUBLIC_WALLETCONNECT_PROJECT_ID=your_project_id
   ```

4. **Network mismatch:**
   - Ensure wallet is on Algorand Mainnet, not Testnet

#### "Algorand API timeout"

**Symptoms:**
- Analysis hangs or returns timeout error
- 504 Gateway Timeout responses

**Solutions:**
```bash
# 1. Switch to public AlgoNode (default, most reliable)
# In .env, either remove or set:
ALGORAND_NODE_URL=https://mainnet-api.algonode.cloud

# 2. If using local node, verify it's running
curl http://127.0.0.1:8080/health

# 3. Check network connectivity
ping mainnet-api.algonode.cloud

# 4. Large wallets (>500 assets) may need longer timeout
# The default is 15 seconds per API call
```

#### "LP token not decomposed"

**Symptoms:**
- LP tokens showing in "shitcoin" category
- No breakdown of underlying assets

**Causes & Solutions:**

1. **Unsupported DEX:** Only Tinyman and Pact are fully supported
2. **Name parsing failed:** LP token naming doesn't match expected patterns
3. **Missing Tinyman SDK:** Install with `pip install tinyman-py-sdk`

```bash
# Verify Tinyman SDK is installed
pip show tinyman-py-sdk

# If missing:
pip install tinyman-py-sdk
```

**Supported LP patterns:**
- Tinyman v1: `TM1POOL`, name like "TM1POOL ALGO-USDC"
- Tinyman v2: `TMPOOL2`, name like "TinymanPool2.0 ALGO-USDC"
- Pact: `PLP`, `PACT LP`

#### "Rate limit exceeded"

**Symptoms:**
- 429 Too Many Requests response
- "Rate limit exceeded" error message

**Solutions:**

| Endpoint | Limit | Cooldown |
|----------|-------|----------|
| `/analyze` | 30/min | Wait 60 seconds |
| `/agent/advice` | 10/min | Wait 60 seconds |
| All others | 100/min | Wait 60 seconds |

```bash
# The response includes Retry-After header
# Wait the specified number of seconds before retrying
```

### Performance Tips

1. **Use local Algorand node** for faster analysis:
   ```bash
   # If running a node, set in .env:
   ALGORAND_NODE_URL=http://127.0.0.1:8080
   ALGORAND_NODE_TOKEN=your-token-here
   ```

2. **API caching**: Results cached 15 minutes per address. Subsequent requests are instant.

3. **Progressive loading**: For large wallets, use:
   - `GET /analyze/quick/{address}` for fast initial render
   - `GET /assets/{address}/{category}` to load details progressively

4. **LP parsing overhead**: Tinyman SDK calls add ~2-3 seconds per LP token. Large LP portfolios will be slower.

5. **Batch analysis**: Analyze multiple wallets in parallel (up to rate limit).

### Debug Mode

Enable verbose logging for troubleshooting:

```bash
# Set log level to DEBUG
export LOG_LEVEL=DEBUG

# Run with reload for development
uvicorn api.main:app --reload --log-level debug
```

### Getting Help

- **Documentation**: `docs/` directory contains detailed guides
- **API Reference**: http://localhost:8000/docs (Swagger UI)
- **Website**: [algosovereignty.com](https://algosovereignty.com)
- **Email**: dylan@sovereignpath.com

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
