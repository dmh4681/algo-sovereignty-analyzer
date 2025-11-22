# Algorand Sovereignty Analyzer

Analyze the "sovereignty" of an Algorand wallet based on asset allocation.

## Vision: Algorand DeFi Sovereignty Scoring System

**Goal:** A tool that analyzes ANY Algorand wallet and outputs a "sovereignty score" based on hard money principles - then makes it accessible via web app for the entire Algorand community.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    FRONTEND (Next.js)                   │
│  - Enter any Algorand address                           │
│  - View sovereignty breakdown                           │
│  - Compare wallets                                      │
│  - Historical tracking (future)                         │
└─────────────────────────────────────────────────────────┘
                            ↓ HTTP/JSON
┌─────────────────────────────────────────────────────────┐
│                   API LAYER (FastAPI)                   │
│  - POST /analyze {address, expenses?}                   │
│  - GET /wallet/{address}                                │
│  - GET /classifications (ASA lookup table)              │
│  - WebSocket for real-time updates (future)             │
└─────────────────────────────────────────────────────────┘
                            ↓ Python SDK
┌─────────────────────────────────────────────────────────┐
│              CORE ENGINE (Python Module)                │
│  - algo_sovereignty.py (what we built)                  │
│  - Auto-classification logic                            │
│  - Sovereignty ratio calculations                       │
│  - JSON export                                          │
└─────────────────────────────────────────────────────────┘
                            ↓ API Calls
┌─────────────────────────────────────────────────────────┐
│              DATA SOURCES (External)                    │
│  - AlgoNode API (account data)                          │
│  - CoinGecko (pricing)                                  │
│  - Local node (optional, for privacy)                   │
└─────────────────────────────────────────────────────────┘
```

## Structure

- `core/`: Core analysis logic
- `api/`: FastAPI backend
- `scripts/`: CLI tools
- `data/`: Data files
- `tests/`: Unit tests

## Usage

### CLI
```bash
python -m scripts.cli <ADDRESS>
```

### API
```bash
uvicorn api.main:app --reload
```
