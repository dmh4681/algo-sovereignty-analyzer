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

Then edit `.env` with your values:

```bash
# =============================================================================
# REQUIRED: AI Coaching Feature
# =============================================================================
# Get your API key at: https://console.anthropic.com/
# Without this, the /agent/advice endpoint will return errors
ANTHROPIC_API_KEY=sk-ant-api03-xxxxxxxxxxxxx

# =============================================================================
# OPTIONAL: Algorand Node Configuration
# =============================================================================
# Default: Uses free public AlgoNode API (no auth needed)
# Set these only if running your own Algorand node for faster queries

# Your node's API endpoint (uncomment to use)
# ALGORAND_NODE_URL=http://127.0.0.1:8080

# Auth token for your node (required for private nodes)
# ALGORAND_NODE_TOKEN=aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa

# =============================================================================
# OPTIONAL: Security & CORS
# =============================================================================
# Comma-separated list of allowed frontend origins
# Default: "*" (all origins - OK for development)
# Production example:
# CORS_ORIGINS=https://algosovereignty.com,https://www.algosovereignty.com

# =============================================================================
# OPTIONAL: Data Seeding (for gold/silver miner features)
# =============================================================================
# Set to 'true' to reseed miner databases on startup
# RESEED_MINERS=false
# RESEED_SILVER=false
```

### Frontend Environment Variables

Create `web/.env.local` for the Next.js frontend:

```bash
# Development (local backend)
NEXT_PUBLIC_API_URL=http://localhost:8000

# Production (Railway backend example)
# NEXT_PUBLIC_API_URL=https://algo-sovereignty-api.up.railway.app
```

#### NEXT_PUBLIC_API_URL Configuration

This variable tells the frontend where to find the backend API:

| Environment | Value | Notes |
|-------------|-------|-------|
| Local Development | `http://localhost:8000` | Backend running locally |
| Vercel Preview | `https://your-railway-app.up.railway.app` | Railway staging URL |
| Production | `https://api.algosovereignty.com` | Custom domain on Railway |

**Important**: The `NEXT_PUBLIC_` prefix exposes the variable to the browser. Only use this for non-sensitive URLs.

### Verifying Configuration

Start the backend and check the startup logs:

```bash
uvicorn api.main:app --reload --port 8000
```

You should see:
```
INFO:     Environment Configuration:
INFO:     - ANTHROPIC_API_KEY: sk-a***03 (configured)
INFO:     - ALGORAND_NODE_URL: https://mainnet-api.algonode.cloud (default)
INFO:     - CORS_ORIGINS: * (default)
```

### Security Best Practices

1. **Never commit `.env` to Git** - Already in `.gitignore`
2. **Use environment-specific files**:
   - `.env` - Local development (gitignored)
   - `.env.example` - Template with placeholder values (committed)
3. **Rotate keys if exposed** - Generate new Anthropic key immediately
4. **Use secrets in production** - Railway/Vercel have built-in secrets management

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

### Production Architecture

```
┌─────────────────────┐     ┌─────────────────────┐
│   Vercel (Frontend) │────▶│  Railway (Backend)  │
│   algosovereignty   │     │  FastAPI + Python   │
│   .com              │     │                     │
└─────────────────────┘     └─────────────────────┘
                                      │
                    ┌─────────────────┼─────────────────┐
                    ▼                 ▼                 ▼
              AlgoNode API      Vestige Labs      Anthropic AI
              (Blockchain)      (Pricing)         (Coaching)
```

### Backend Deployment → Railway

**Step 1: Create Railway Project**

```bash
# Install Railway CLI (optional but recommended)
npm install -g @railway/cli
railway login
```

**Step 2: Connect Repository**

1. Go to [railway.app](https://railway.app)
2. Click "New Project" → "Deploy from GitHub repo"
3. Select your `algo-sovereignty-analyzer` repository
4. Railway auto-detects Python and creates the project

**Step 3: Configure Environment Variables**

In Railway dashboard → Variables tab, add:

| Variable | Value | Required |
|----------|-------|----------|
| `ANTHROPIC_API_KEY` | `sk-ant-api03-...` | Yes (for AI) |
| `CORS_ORIGINS` | `https://algosovereignty.com,https://www.algosovereignty.com` | Yes |
| `PORT` | (Railway sets automatically) | Auto |

**Step 4: Configure Build & Start**

In Railway dashboard → Settings tab:

- **Root Directory**: `/` (or path to project if monorepo)
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `uvicorn api.main:app --host 0.0.0.0 --port $PORT`

**Step 5: Deploy & Get URL**

1. Railway deploys automatically on push to main
2. Get your URL from Settings → Domains (e.g., `algo-sovereignty-api.up.railway.app`)
3. Optionally add custom domain

### Frontend Deployment → Vercel

**Step 1: Import Project**

1. Go to [vercel.com](https://vercel.com)
2. Click "Add New" → "Project"
3. Import from GitHub
4. Set **Root Directory** to `web`

**Step 2: Configure Environment Variables**

In Vercel dashboard → Settings → Environment Variables:

| Variable | Value | Environment |
|----------|-------|-------------|
| `NEXT_PUBLIC_API_URL` | `https://algo-sovereignty-api.up.railway.app` | Production |
| `NEXT_PUBLIC_API_URL` | `https://staging-api.up.railway.app` | Preview |

**Step 3: Configure Build Settings**

Vercel auto-detects Next.js, but verify:

- **Framework Preset**: Next.js
- **Build Command**: `npm run build`
- **Output Directory**: `.next`
- **Install Command**: `npm install`

**Step 4: Deploy & Configure Domain**

1. Vercel deploys automatically
2. Add custom domain in Settings → Domains
3. Configure DNS (Vercel provides instructions)

### Docker Deployment (Self-Hosted)

For running on your own infrastructure:

```bash
# Clone and navigate
git clone https://github.com/your-username/algo-sovereignty-analyzer.git
cd algo-sovereignty-analyzer

# Create .env file
cp .env.example .env
# Edit .env with your values

# Build and run
docker-compose up --build -d

# Services available at:
# - API: http://localhost:8000
# - Web: http://localhost:3000
```

**docker-compose.yml customization**:

```yaml
version: '3.8'
services:
  api:
    build: .
    ports:
      - "8000:8000"
    env_file:
      - .env
    restart: unless-stopped

  web:
    build: ./web
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://api:8000
    depends_on:
      - api
    restart: unless-stopped
```

### Health Checks & Monitoring

**Backend Health Check**:
```bash
curl https://your-api-url.up.railway.app/api/v1/health
# Expected: {"status": "healthy", "timestamp": "..."}
```

**Frontend Verification**:
1. Visit your domain
2. Enter any Algorand address
3. Verify analysis completes without errors

### Rollback Procedures

**Railway**:
1. Go to Deployments tab
2. Click on previous successful deployment
3. Click "Redeploy"

**Vercel**:
1. Go to Deployments tab
2. Find previous deployment
3. Click "..." → "Promote to Production"

---

## Troubleshooting

### Common Issues

#### "Anthropic API error" / "AI coaching unavailable"

**Symptoms**: The coaching panel shows an error or returns no advice.

**Solutions**:

1. **Check API key is set**:
   ```bash
   # Linux/Mac
   echo $ANTHROPIC_API_KEY

   # Windows PowerShell
   echo $env:ANTHROPIC_API_KEY

   # Should show: sk-ant-api03-...
   ```

2. **Verify key is valid**:
   ```bash
   curl https://api.anthropic.com/v1/messages \
     -H "x-api-key: $ANTHROPIC_API_KEY" \
     -H "anthropic-version: 2023-06-01" \
     -H "content-type: application/json" \
     -d '{"model":"claude-3-haiku-20240307","max_tokens":10,"messages":[{"role":"user","content":"Hi"}]}'
   ```

3. **Check credits**: Visit [console.anthropic.com](https://console.anthropic.com) → Usage

4. **Restart after .env changes**:
   ```bash
   # Stop server (Ctrl+C) and restart
   uvicorn api.main:app --reload --port 8000
   ```

#### "Asset price not found" / "$0.00 values"

**Symptoms**: Some assets show $0.00 USD value.

**Solutions**:

1. **Check if asset is too obscure**: Vestige only tracks actively traded ASAs
2. **Verify asset exists**: Search on [vestige.fi](https://vestige.fi)
3. **Add manual classification**: For known assets, add to `data/asset_classification.csv`:
   ```csv
   asset_id,category,name,ticker
   123456789,hard_money,My Gold Token,GOLD
   ```

#### "CORS error in browser"

**Symptoms**: Console shows "Access-Control-Allow-Origin" errors.

**Solutions**:

1. **Development** - Ensure frontend origin is allowed:
   ```bash
   # .env
   CORS_ORIGINS=http://localhost:3000
   ```

2. **Production** - Include all frontend domains:
   ```bash
   CORS_ORIGINS=https://algosovereignty.com,https://www.algosovereignty.com
   ```

3. **Verify in browser**: Check Network tab → Response Headers should include:
   ```
   Access-Control-Allow-Origin: https://algosovereignty.com
   ```

4. **Hard refresh**: Clear browser cache (Ctrl+Shift+R)

#### "Wallet connection fails"

**Symptoms**: "Connect Wallet" button doesn't respond or shows error.

**Solutions**:

1. **Install wallet extension**:
   - [Pera Wallet](https://perawallet.app/) (recommended)
   - [Defly Wallet](https://defly.app/)

2. **Check browser compatibility**: Use Chrome, Firefox, or Brave

3. **Mobile**: Ensure you're using the in-app browser of your wallet app

4. **WalletConnect issues**: The app uses WalletConnect v2 - check if your wallet supports it

#### "Analysis timeout" / Slow analysis

**Symptoms**: Analysis takes more than 30 seconds or times out.

**Solutions**:

1. **Large wallet**: Wallets with 100+ assets take longer
2. **LP tokens**: Each LP token requires additional Tinyman SDK calls
3. **Use local node**: Much faster than public AlgoNode:
   ```bash
   # .env
   ALGORAND_NODE_URL=http://127.0.0.1:8080
   ALGORAND_NODE_TOKEN=your-token
   ```

#### "Invalid address" error

**Symptoms**: Analysis fails immediately with address validation error.

**Solutions**:

1. **Check address format**: Must be 58 characters, alphanumeric
2. **Verify address exists**: Check on [allo.info](https://allo.info) or [algoexplorer.io](https://algoexplorer.io)
3. **No leading/trailing spaces**: Copy address carefully

### Performance Tips

1. **Use local Algorand node** for faster analysis:
   - Install [Algorand goal](https://developer.algorand.org/docs/run-a-node/setup/install/)
   - Or use [AlgoKit](https://github.com/algorandfoundation/algokit-cli)

2. **API caching**: Results are cached for 15 minutes per address
   - Second analysis of same address is instant
   - Cache clears on server restart

3. **LP token parsing**: Each LP adds ~2 seconds
   - Tinyman SDK queries pool state on-chain
   - Consider pre-calculating for known LP positions

4. **Production optimization**:
   - Enable gzip compression in Railway
   - Use CDN for frontend assets (Vercel handles this)
   - Monitor with Railway metrics dashboard

### Debug Mode

For detailed logging during development:

```bash
# Run with debug output
LOG_LEVEL=DEBUG uvicorn api.main:app --reload --port 8000
```

This shows:
- Every API request/response
- Asset classification decisions
- Price fetching attempts
- LP decomposition steps

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
