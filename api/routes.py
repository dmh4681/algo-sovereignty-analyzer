"""
Algorand Sovereignty Analyzer - API Routes
==========================================

This module defines all REST API endpoints for the Algorand Sovereignty Analyzer.
The API provides functionality for:

1. **Wallet Analysis** - Analyze Algorand wallets for sovereignty metrics
2. **Asset Classification** - Query and manage asset categorizations
3. **Historical Tracking** - Save and retrieve sovereignty snapshots over time
4. **Network Statistics** - Algorand network participation and decentralization data
5. **Arbitrage Analysis** - Meld gold/silver/bitcoin premium comparisons
6. **AI Coaching** - Personalized financial advice via Claude AI

Authentication:
    Currently the API is open (no authentication required).
    For production, add API key authentication via the X-API-Key header.

Rate Limiting:
    - /analyze: 30 requests/minute per IP
    - /agent/advice: 10 requests/minute per IP
    - All others: 100 requests/minute per IP

Caching:
    - Wallet analysis: 15 minutes per address
    - Price data: 5 minutes
    - Network stats: 1 minute

OpenAPI/Swagger Documentation:
    - Swagger UI: http://localhost:8000/docs
    - ReDoc: http://localhost:8000/redoc
    - OpenAPI JSON: http://localhost:8000/openapi.json

Example Usage:
    ```python
    import requests

    # Analyze a wallet
    response = requests.post(
        "http://localhost:8000/api/v1/analyze",
        json={
            "address": "AAAA...YOUR_ADDRESS...",
            "monthly_fixed_expenses": 4000
        }
    )
    result = response.json()
    print(f"Sovereignty Ratio: {result['sovereignty_data']['sovereignty_ratio']}")
    ```

Error Handling:
    All endpoints return standardized error responses:
    ```json
    {
        "success": false,
        "error": {
            "code": "ERROR_CODE",
            "message": "Human-readable error message",
            "details": {"field": "value"},
            "request_id": "uuid-for-tracking"
        }
    }
    ```

See Also:
    - api/schemas.py: Pydantic request/response models
    - api/errors.py: Custom exception classes
    - docs/API-REFERENCE.md: Full API documentation
"""

import re
import logging
import requests
from fastapi import APIRouter, HTTPException, Query, Path
from core.analyzer import AlgorandSovereigntyAnalyzer
from core.models import get_sovereignty_status
from .errors import (
    ValidationException,
    NotFoundException,
    ExternalApiException,
    AlgorandApiException,
    PriceApiException,
    TimeoutException,
    ServiceUnavailableException,
    AnalysisException,
)
from core.history import SovereigntySnapshot, get_history_manager
from core.cache import get_cache, CacheCategory

# Configure module logger
logger = logging.getLogger("api.routes")
from core.btc_history import get_btc_history_manager, save_current_prices
from core.miner_metrics import get_miner_metrics_db, MinerMetric
from core.silver_metrics import get_silver_metrics_db, SilverMinerMetric
from core.inflation_data import get_inflation_db, fred_circuit_breaker
from core.circuit_breaker import CircuitOpenError
from core.central_bank_gold import get_cb_gold_db
from core.earnings_calendar import get_earnings_db, EarningsEvent
from core.premium_tracker import get_premium_db
from core.pricing import (
    get_hardcoded_price,
    get_gold_price_per_oz,
    get_silver_price_per_oz,
    get_meld_gold_price,
    get_meld_silver_price,
    get_bitcoin_spot_price,
    get_gobtc_price,
    get_wbtc_price,
    GRAMS_PER_TROY_OZ,
    GOBTC_ASA,
    WBTC_ASA
)
from core.network import AlgorandNetworkStats, microalgos_to_algo
from .schemas import (
    AnalysisResponse,
    AnalyzeRequest,
    HistorySaveRequest,
    HistorySaveResponse,
    HistoryResponse,
    NetworkStatsResponse,
    NetworkInfo,
    FoundationInfo,
    CommunityInfo,
    ScoreBreakdown,
    WalletParticipationResponse,
    ParticipationKeyInfo,
    MeldArbitrageResponse,
    BTCHistoryResponse,
    AdvisorRequest,
)
from .agent import SovereigntyCoach, AdviceRequest
from typing import Dict, Any, Tuple, Optional, List
from datetime import datetime, timedelta

router = APIRouter()

# Algorand address validation pattern (58 characters, base32 alphabet)
ALGORAND_ADDRESS_PATTERN = re.compile(r'^[A-Z2-7]{58}$')


def validate_algorand_address(address: str) -> None:
    """
    Validate Algorand wallet address format.

    Raises ValidationException if the address is invalid.
    """
    if not address:
        raise ValidationException(
            detail="Wallet address is required",
            error_code="MISSING_ADDRESS",
            details={"field": "address"}
        )

    if not ALGORAND_ADDRESS_PATTERN.match(address):
        raise ValidationException(
            detail="Invalid Algorand wallet address format",
            error_code="INVALID_ADDRESS_FORMAT",
            details={
                "field": "address",
                "value": address[:10] + "..." if len(address) > 10 else address,
                "expected": "58 character base32 string (A-Z, 2-7)"
            }
        )

# Global network stats instance (reused for caching)
_network_stats: Optional[AlgorandNetworkStats] = None

def get_network_stats_client() -> AlgorandNetworkStats:
    """Get or create the network stats client singleton."""
    global _network_stats
    if _network_stats is None:
        _network_stats = AlgorandNetworkStats()
    return _network_stats

@router.post(
    "/agent/advice",
    summary="Get AI sovereignty coaching",
    description="""
Get personalized financial sovereignty advice from Claude AI based on your wallet analysis.

## AI Coaching Philosophy

The Sovereignty Coach is a hard money maximalist AI that provides advice through the lens of:
- **Sound Money Principles**: Bitcoin, Gold, and Silver as true stores of value
- **Financial Independence**: Building runway measured in years, not months
- **Risk Management**: Reducing exposure to fiat and speculative assets
- **Long-term Thinking**: Generational wealth preservation

## Request Requirements

- Requires `ANTHROPIC_API_KEY` environment variable to be set
- Timeout: 60 seconds (AI responses can be lengthy)
- Rate limit: 10 requests per minute per IP

## Response Format

The advice is returned as Markdown-formatted text that can be rendered directly
in the frontend. It typically includes:

1. **Assessment**: Current sovereignty status analysis
2. **Priorities**: Top 3 recommended actions
3. **Specific Steps**: Actionable guidance based on holdings
4. **Timeline**: Projected path to next sovereignty level

## Example Advice Topics

- Increasing hard money allocation
- Reducing stablecoin exposure
- Participation in Algorand consensus
- LP position optimization
- Dollar-cost averaging strategies
    """,
    response_description="AI-generated sovereignty coaching advice in Markdown format",
    responses={
        200: {
            "description": "Successful advice generation",
            "content": {
                "application/json": {
                    "example": {
                        "advice": "## Sovereignty Assessment\\n\\nYour current ratio of 0.4 places you in the **Vulnerable** category...\\n\\n### Priority Actions\\n\\n1. **Increase Hard Money Holdings**..."
                    }
                }
            }
        },
        503: {
            "description": "AI service unavailable",
            "content": {
                "application/json": {
                    "example": {
                        "success": False,
                        "error": {
                            "code": "AI_SERVICE_UNAVAILABLE",
                            "message": "AI coaching service unavailable",
                            "details": {"service": "anthropic"}
                        }
                    }
                }
            }
        },
        504: {
            "description": "AI request timed out",
            "content": {
                "application/json": {
                    "example": {
                        "success": False,
                        "error": {
                            "code": "AI_TIMEOUT",
                            "message": "AI coaching request timed out"
                        }
                    }
                }
            }
        }
    },
    tags=["AI Coaching"]
)
async def get_agent_advice(request: AdviceRequest):
    """
    Get personalized financial sovereignty advice from the AI agent.

    Uses Claude AI to analyze the wallet data and provide hard money maximalist
    coaching advice tailored to the user's current situation.

    Args:
        request: AdviceRequest containing wallet analysis data

    Returns:
        Dict with 'advice' key containing Markdown-formatted coaching text

    Raises:
        TimeoutException: If AI request takes longer than 60 seconds
        ServiceUnavailableException: If Anthropic API is unreachable
        ExternalApiException: If AI processing fails for other reasons
    """
    try:
        coach = SovereigntyCoach()
        advice = coach.generate_advice(request.analysis)
        return {"advice": advice}
    except requests.exceptions.Timeout:
        logger.error("AI agent request timed out")
        raise TimeoutException(
            detail="AI coaching request timed out",
            error_code="AI_TIMEOUT",
            service="anthropic"
        )
    except requests.exceptions.ConnectionError as e:
        logger.error(f"AI agent connection error: {e}")
        raise ServiceUnavailableException(
            detail="AI coaching service unavailable",
            error_code="AI_SERVICE_UNAVAILABLE",
            details={"service": "anthropic"}
        )
    except Exception as e:
        logger.exception(f"Error in /agent/advice: {e}")
        raise ExternalApiException(
            detail="AI coaching failed",
            error_code="AI_ERROR",
            details={"error_type": type(e).__name__}
        )

# =============================================================================
# Wallet Analysis Cache (uses centralized cache from core/cache.py)
# =============================================================================

# Legacy constant for backwards compatibility
CACHE_TTL_MINUTES = 15


def get_cached_analysis(address: str) -> Optional[dict]:
    """
    Return cached analysis if exists and not expired.

    Uses the centralized cache system (core/cache.py) for consistent
    TTL management and statistics tracking.

    Args:
        address: Algorand wallet address

    Returns:
        Cached analysis result or None if not found/expired
    """
    cache = get_cache()
    return cache.get_analysis(address)


def cache_analysis(address: str, result: dict):
    """
    Store analysis result in the centralized cache.

    Args:
        address: Algorand wallet address
        result: Analysis result dictionary to cache
    """
    cache = get_cache()
    cache.set_analysis(address, result)

@router.post(
    "/analyze",
    response_model=AnalysisResponse,
    summary="Analyze wallet sovereignty",
    description="""
Analyze an Algorand wallet's holdings and calculate sovereignty metrics based on
hard money maximalist principles.

## Sovereignty Score Calculation

The sovereignty ratio measures financial independence:

```
Sovereignty Ratio = Total Portfolio USD / Annual Fixed Expenses
```

This ratio represents how many years of essential expenses can be covered by
the portfolio, providing a measure of true financial freedom.

## Asset Classification

Assets are automatically classified into four categories:

| Category | Assets | Impact |
|----------|--------|--------|
| **hard_money** | BTC (goBTC, WBTC), Gold (XAUT, GOLD$), Silver (SILVER$) | Generational wealth |
| **algo** | ALGO, xALGO, fALGO, gALGO, mALGO | Platform native |
| **dollars** | USDC, USDT, DAI, fUSDC, fUSDT | Fiat proxy |
| **shitcoin** | Everything else (LP tokens*, NFTs, etc.) | Speculative |

*LP tokens are automatically decomposed into underlying assets.

## Sovereignty Status Levels

| Status | Ratio | Meaning |
|--------|-------|---------|
| Generationally Sovereign | >= 20 | Multi-generational wealth |
| Antifragile | >= 6 | Benefits from volatility |
| Robust | >= 3 | Can weather major storms |
| Fragile | >= 1 | Building foundation |
| Vulnerable | < 1 | Immediate action needed |

## LP Token Handling

Liquidity Provider tokens from Tinyman and Pact are automatically decomposed:

```
TMPOOL-ALGO-goBTC (100 tokens)
    -> ALGO: 5000 -> "algo" category
    -> goBTC: 0.0125 -> "hard_money" category
```

## Caching

Results are cached for 15 minutes per address. Use `use_local_node=true`
to bypass cache for development/testing.
    """,
    response_description="Complete wallet analysis with sovereignty metrics",
    responses={
        200: {
            "description": "Successful analysis",
            "content": {
                "application/json": {
                    "example": {
                        "address": "I26BHULCOKKBNFF3KEXVH3KWMBK3VWJFKQXYOKFLW4UAET4U4MESL3BIP4",
                        "is_participating": True,
                        "hard_money_algo": 0.0,
                        "categories": {
                            "hard_money": [
                                {"name": "goBTC", "ticker": "goBTC", "amount": 0.015, "usd_value": 1500.0}
                            ],
                            "algo": [
                                {"name": "Algorand (PARTICIPATING)", "ticker": "ALGO", "amount": 50000, "usd_value": 12500.0}
                            ],
                            "dollars": [
                                {"name": "USD Coin", "ticker": "USDC", "amount": 5000, "usd_value": 5000.0}
                            ],
                            "shitcoin": []
                        },
                        "sovereignty_data": {
                            "monthly_fixed_expenses": 4000.0,
                            "annual_fixed_expenses": 48000.0,
                            "algo_price": 0.25,
                            "portfolio_usd": 19000.0,
                            "sovereignty_ratio": 0.40,
                            "sovereignty_status": "Vulnerable",
                            "years_of_runway": 0.4
                        },
                        "participation_info": {
                            "staked_amount": 50000,
                            "is_incentive_eligible": True,
                            "estimated_apy": 4.5
                        }
                    }
                }
            }
        },
        400: {
            "description": "Invalid request - address format validation failed",
            "content": {
                "application/json": {
                    "example": {
                        "success": False,
                        "error": {
                            "code": "INVALID_ADDRESS_FORMAT",
                            "message": "Invalid Algorand wallet address format",
                            "details": {
                                "field": "address",
                                "expected": "58 character base32 string (A-Z, 2-7)"
                            }
                        }
                    }
                }
            }
        },
        404: {
            "description": "Wallet not found or contains no assets",
            "content": {
                "application/json": {
                    "example": {
                        "success": False,
                        "error": {
                            "code": "WALLET_NOT_FOUND",
                            "message": "Wallet not found or contains no assets",
                            "details": {"address": "AAAA..."}
                        }
                    }
                }
            }
        },
        504: {
            "description": "Request timed out",
            "content": {
                "application/json": {
                    "example": {
                        "success": False,
                        "error": {
                            "code": "ALGORAND_API_TIMEOUT",
                            "message": "Algorand API request timed out. Please try again."
                        }
                    }
                }
            }
        }
    },
    tags=["Wallet Analysis"]
)
async def analyze_wallet(request: AnalyzeRequest, use_local_node: bool = Query(False, description="Use local Algorand node instead of AlgoNode public API")):
    """
    Analyze an Algorand wallet for sovereignty metrics.

    This endpoint fetches all assets from the Algorand blockchain, classifies them
    according to hard money maximalist principles, decomposes LP tokens, and
    calculates sovereignty metrics if monthly expenses are provided.

    Args:
        request: AnalyzeRequest containing address and optional monthly_fixed_expenses
        use_local_node: If True, uses configured local node; if False, uses AlgoNode public API

    Returns:
        AnalysisResponse with categorized assets and sovereignty calculations

    Raises:
        ValidationException: If address format is invalid
        NotFoundException: If wallet doesn't exist or has no assets
        AlgorandApiException: If Algorand API communication fails
        TimeoutException: If request times out (15 second limit)
    """
    # Validate address format
    validate_algorand_address(request.address)

    # Check cache first (only if not using local node, as local node might be for dev/testing)
    if not use_local_node:
        cached = get_cached_analysis(request.address)
        if cached:
            # If we have expenses, we need to recalculate sovereignty data
            # But the base analysis (categories) is valid
            categories = cached['categories']
            analyzer = AlgorandSovereigntyAnalyzer(use_local_node=False) # Just for helper methods if needed
            
            sovereignty_data = None
            if request.monthly_fixed_expenses:
                sovereignty_data = analyzer.calculate_sovereignty_metrics(
                    categories,
                    request.monthly_fixed_expenses
                )
                # Auto-save history snapshot
                _create_and_save_snapshot(
                    address=request.address,
                    categories=categories,
                    sovereignty_data=sovereignty_data,
                    is_participating=cached['is_participating'],
                    algo_price=sovereignty_data.algo_price if sovereignty_data else 0.0
                )

            return AnalysisResponse(
                address=request.address,
                is_participating=cached['is_participating'],
                hard_money_algo=cached['hard_money_algo'],
                categories=categories,
                sovereignty_data=sovereignty_data,
                participation_info=cached.get('participation_info')
            )

    analyzer = AlgorandSovereigntyAnalyzer(use_local_node=use_local_node)
    
    try:
        print(f"📊 Starting analysis for {request.address[:8]}...")
        categories = analyzer.analyze_wallet(request.address)
        if not categories:
            raise NotFoundException(
                detail="Wallet not found or contains no assets",
                error_code="WALLET_NOT_FOUND",
                details={"address": request.address}
            )
        
        print(f"✅ Analysis complete. Categories: {list(categories.keys())}")
            
        # Calculate sovereignty metrics if expenses provided
        sovereignty_data = None
        if request.monthly_fixed_expenses:
            sovereignty_data = analyzer.calculate_sovereignty_metrics(
                categories,
                request.monthly_fixed_expenses
            )
            # Auto-save history snapshot
            _create_and_save_snapshot(
                address=request.address,
                categories=categories,
                sovereignty_data=sovereignty_data,
                is_participating=analyzer.last_is_participating,
                algo_price=sovereignty_data.algo_price if sovereignty_data else 0.0
            )

        # Prepare result
        result = {
            'address': request.address,
            'is_participating': analyzer.last_is_participating,
            'hard_money_algo': analyzer.last_hard_money_algo,
            'categories': categories,
            'participation_info': analyzer.last_participation_info
        }
        
        # Cache it
        if not use_local_node:
            cache_analysis(request.address, result)
        
        print(f"📤 Preparing response...")
        response = AnalysisResponse(
            address=request.address,
            is_participating=analyzer.last_is_participating,
            hard_money_algo=analyzer.last_hard_money_algo,
            categories=categories,
            sovereignty_data=sovereignty_data,
            participation_info=analyzer.last_participation_info
        )
        print(f"✅ Response ready, sending...")
        return response
    except (ValidationException, NotFoundException):
        raise
    except requests.exceptions.Timeout:
        logger.warning(f"Algorand API timeout for address {request.address[:8]}...")
        raise AlgorandApiException(
            detail="Algorand API request timed out. Please try again.",
            is_timeout=True,
            details={"address": f"{request.address[:8]}...{request.address[-6:]}"}
        )
    except requests.exceptions.ConnectionError as e:
        logger.error(f"Algorand API connection error: {e}")
        raise AlgorandApiException(
            detail="Unable to connect to Algorand network",
            error_code="ALGORAND_CONNECTION_ERROR",
            details={
                "address": f"{request.address[:8]}...{request.address[-6:]}",
                "suggestion": "The Algorand node may be temporarily unavailable. Please try again."
            }
        )
    except requests.exceptions.RequestException as e:
        logger.error(f"Algorand API request error: {type(e).__name__}: {e}")
        raise AlgorandApiException(
            detail="Failed to communicate with Algorand API",
            error_code="ALGORAND_API_ERROR",
            details={
                "address": f"{request.address[:8]}...{request.address[-6:]}",
                "error_type": type(e).__name__
            }
        )
    except Exception as e:
        logger.exception(f"Unexpected error in analyze_wallet: {e}")
        raise AnalysisException(
            detail="Wallet analysis failed unexpectedly",
            error_code="ANALYSIS_FAILED",
            address=request.address
        )

@router.get(
    "/classifications",
    summary="Get asset classifications",
    description="""
Retrieve all manual asset classification overrides from the CSV database.

## Classification Hierarchy

The system uses a three-tier classification hierarchy:

1. **CSV Manual Overrides** (highest priority) - `data/asset_classification.csv`
2. **User-Submitted Corrections** (medium priority) - `data/user_corrections.json`
3. **Auto-Classification Regex** (lowest priority) - `core/classifier.py`

## Response Format

Returns a dictionary keyed by ASA ID with classification details:

```json
{
    "793124631": {
        "name": "goBTC",
        "ticker": "goBTC",
        "category": "hard_money"
    },
    "31566704": {
        "name": "USD Coin",
        "ticker": "USDC",
        "category": "dollars"
    }
}
```

## Categories

- `hard_money`: Bitcoin, Gold, Silver (wealth preservation)
- `algo`: ALGO and liquid staking derivatives
- `dollars`: Stablecoins and fiat proxies
- `shitcoin`: Everything else
    """,
    response_description="Dictionary of asset ID to classification mapping",
    responses={
        200: {
            "description": "Classification lookup successful",
            "content": {
                "application/json": {
                    "example": {
                        "793124631": {"name": "goBTC", "ticker": "goBTC", "category": "hard_money"},
                        "31566704": {"name": "USD Coin", "ticker": "USDC", "category": "dollars"},
                        "1241944285": {"name": "Meld Gold", "ticker": "GOLD$", "category": "hard_money"}
                    }
                }
            }
        }
    },
    tags=["Classification"]
)
async def get_classifications() -> Dict[str, Dict[str, str]]:
    """
    Get manual asset classifications from the CSV override file.

    Returns:
        Dictionary mapping ASA ID strings to classification objects containing
        name, ticker, and category fields.
    """
    analyzer = AlgorandSovereigntyAnalyzer(use_local_node=False)
    return analyzer.classifier.classifications


# -----------------------------------------------------------------------------
# Pagination Endpoints for Large Wallets
# -----------------------------------------------------------------------------

# Legacy constant for backwards compatibility
PAGINATION_CACHE_TTL_MINUTES = 15


def get_pagination_cached_analysis(address: str) -> Optional[dict]:
    """
    Get cached analysis for pagination requests.

    Uses the same centralized cache as regular analysis.

    Args:
        address: Algorand wallet address

    Returns:
        Cached analysis result or None if not found/expired
    """
    # Uses the same cache as regular analysis
    return get_cached_analysis(address)


def cache_for_pagination(address: str, result: dict):
    """
    Store analysis result in cache for pagination.

    Uses the same centralized cache as regular analysis.

    Args:
        address: Algorand wallet address
        result: Analysis result dictionary to cache
    """
    # Uses the same cache as regular analysis
    cache_analysis(address, result)


@router.get(
    "/assets/{address}/{category}",
    summary="Get paginated assets by category",
    description="""
Retrieve a paginated list of assets for a specific category from a wallet.

## Use Case

This endpoint is designed for **lazy loading** large asset lists in the UI.
Instead of loading all assets at once (which can be slow for wallets with
hundreds of shitcoins), you can:

1. First call `/analyze` or `/analyze/quick/{address}` for summary data
2. Then load each category's assets page-by-page as the user scrolls

## Pagination

- Pages are 1-indexed (first page = 1)
- Default page size is 20, max is 100
- Response includes `has_more` flag to indicate if more pages exist

## Caching

Uses the same 15-minute cache as `/analyze`. If the wallet hasn't been
analyzed recently, this endpoint will trigger a fresh analysis.
    """,
    response_description="Paginated list of assets with category totals",
    responses={
        200: {
            "description": "Assets retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "address": "I26BHULCO...",
                        "category": "shitcoin",
                        "page": {
                            "items": [
                                {"name": "Akita Inu", "ticker": "AKITA", "amount": 1000000, "usd_value": 50.0},
                                {"name": "Chips", "ticker": "CHIPS", "amount": 500000, "usd_value": 25.0}
                            ],
                            "total": 150,
                            "page": 1,
                            "page_size": 20,
                            "has_more": True
                        },
                        "category_total_usd": 1250.50
                    }
                }
            }
        },
        400: {
            "description": "Invalid category specified",
            "content": {
                "application/json": {
                    "example": {
                        "success": False,
                        "error": {
                            "code": "INVALID_CATEGORY",
                            "message": "Invalid category. Must be one of: hard_money, algo, dollars, shitcoin",
                            "details": {"category": "invalid", "valid_categories": ["hard_money", "algo", "dollars", "shitcoin"]}
                        }
                    }
                }
            }
        }
    },
    tags=["Wallet Analysis"]
)
async def get_paginated_assets(
    address: str = Path(..., description="58-character Algorand wallet address"),
    category: str = Path(..., description="Asset category: hard_money, algo, dollars, or shitcoin"),
    page: int = Query(1, ge=1, description="Page number (1-indexed, default: 1)"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page (1-100, default: 20)")
):
    """
    Get paginated assets for a specific category.

    This endpoint supports lazy loading of large asset lists. Useful for wallets
    with many shitcoins or LP positions.

    Args:
        address: Algorand wallet address (58 characters)
        category: One of hard_money, algo, dollars, shitcoin
        page: Page number starting from 1
        page_size: Number of items per page (max 100)

    Returns:
        PaginatedAssetsResponse with items, pagination metadata, and category totals

    Raises:
        ValidationException: If address or category is invalid
        NotFoundException: If wallet not found
    """
    from .schemas import PaginatedAssetsResponse, AssetPageResponse

    # Validate address
    validate_algorand_address(address)

    # Validate category
    valid_categories = ['hard_money', 'algo', 'dollars', 'shitcoin']
    if category not in valid_categories:
        raise ValidationException(
            detail=f"Invalid category. Must be one of: {', '.join(valid_categories)}",
            error_code="INVALID_CATEGORY",
            details={"category": category, "valid_categories": valid_categories}
        )

    # Try to get cached analysis
    cached = get_pagination_cached_analysis(address)

    if not cached:
        # Need to analyze the wallet first
        analyzer = AlgorandSovereigntyAnalyzer(use_local_node=False)
        categories = analyzer.analyze_wallet(address)

        if not categories:
            raise NotFoundException(
                detail="Wallet not found or contains no assets",
                error_code="WALLET_NOT_FOUND",
                details={"address": address}
            )

        # Cache for subsequent pagination requests
        cached = {
            'categories': categories,
            'is_participating': analyzer.last_is_participating,
            'hard_money_algo': analyzer.last_hard_money_algo,
            'participation_info': analyzer.last_participation_info
        }
        cache_for_pagination(address, cached)
        cache_analysis(address, cached)

    categories = cached['categories']
    assets = categories.get(category, [])
    total = len(assets)

    # Calculate pagination
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    page_items = assets[start_idx:end_idx]
    has_more = end_idx < total

    # Calculate category total USD
    category_total_usd = sum(a.get('usd_value', 0) for a in assets)

    return PaginatedAssetsResponse(
        address=address,
        category=category,
        page=AssetPageResponse(
            items=page_items,
            total=total,
            page=page,
            page_size=page_size,
            has_more=has_more
        ),
        category_total_usd=category_total_usd
    )


@router.get(
    "/analyze/quick/{address}",
    summary="Quick sovereignty summary",
    description="""
Get a lightweight sovereignty summary without full asset details.

## Progressive Loading Pattern

This endpoint is designed for **fast initial page render**:

```
1. GET /analyze/quick/{address}     <- Fast! Returns totals + sovereignty
2. Render sovereignty score UI
3. GET /assets/{address}/hard_money <- Load detailed lists
4. GET /assets/{address}/algo       <- As user scrolls/expands
5. GET /assets/{address}/dollars
6. GET /assets/{address}/shitcoin
```

## Response Contents

- **Sovereignty metrics**: ratio, status, years of runway
- **Category totals**: USD value per category
- **Asset counts**: Number of assets per category
- **Pagination hints**: Which categories need pagination (>50 assets)
- **Participation info**: Consensus participation details

## Performance

This endpoint performs the same full wallet analysis as `/analyze` but returns
a lighter response. The analysis is cached, so subsequent `/assets/` calls
use the same data.
    """,
    response_description="Quick sovereignty summary with category totals",
    responses={
        200: {
            "description": "Quick analysis successful",
            "content": {
                "application/json": {
                    "example": {
                        "address": "I26BHULCO...",
                        "is_participating": True,
                        "sovereignty_ratio": 3.25,
                        "sovereignty_status": "Robust",
                        "portfolio_usd": 156000.0,
                        "algo_price": 0.25,
                        "years_of_runway": 3.3,
                        "category_totals": {
                            "hard_money": 50000.0,
                            "algo": 75000.0,
                            "dollars": 25000.0,
                            "shitcoin": 6000.0
                        },
                        "asset_counts": {
                            "hard_money": 3,
                            "algo": 5,
                            "dollars": 2,
                            "shitcoin": 87
                        },
                        "needs_pagination": {
                            "hard_money": False,
                            "algo": False,
                            "dollars": False,
                            "shitcoin": True
                        },
                        "participation_info": {
                            "staked_amount": 50000,
                            "is_incentive_eligible": True
                        }
                    }
                }
            }
        }
    },
    tags=["Wallet Analysis"]
)
async def get_quick_sovereignty(
    address: str = Path(..., description="58-character Algorand wallet address"),
    monthly_fixed_expenses: Optional[float] = Query(None, description="Monthly fixed expenses in USD for ratio calculation"),
    use_local_node: bool = Query(False, description="Use local Algorand node instead of public API")
):
    """
    Get quick sovereignty metrics without full asset details.

    Optimized for fast initial page render. Returns sovereignty score and
    category totals immediately. Use /assets/{address}/{category} to load
    detailed asset lists progressively.

    Args:
        address: Algorand wallet address
        monthly_fixed_expenses: Optional monthly expenses for ratio calculation
        use_local_node: Whether to use local node (bypasses cache)

    Returns:
        QuickSovereigntyResponse with totals, counts, and pagination hints
    """
    from .schemas import QuickSovereigntyResponse

    # Validate address
    validate_algorand_address(address)

    # Try cache first
    cached = get_pagination_cached_analysis(address) if not use_local_node else None

    if cached:
        categories = cached['categories']
        is_participating = cached['is_participating']
        participation_info = cached.get('participation_info')
    else:
        # Analyze wallet
        analyzer = AlgorandSovereigntyAnalyzer(use_local_node=use_local_node)
        categories = analyzer.analyze_wallet(address)

        if not categories:
            raise NotFoundException(
                detail="Wallet not found or contains no assets",
                error_code="WALLET_NOT_FOUND",
                details={"address": address}
            )

        is_participating = analyzer.last_is_participating
        participation_info = analyzer.last_participation_info

        # Cache for subsequent requests
        if not use_local_node:
            cached_data = {
                'categories': categories,
                'is_participating': is_participating,
                'hard_money_algo': analyzer.last_hard_money_algo,
                'participation_info': participation_info
            }
            cache_for_pagination(address, cached_data)
            cache_analysis(address, cached_data)

    # Calculate totals
    from core.pricing import get_algo_price
    hard_money_total = sum(a.get('usd_value', 0) for a in categories.get('hard_money', []))
    algo_total = sum(a.get('usd_value', 0) for a in categories.get('algo', []))
    dollars_total = sum(a.get('usd_value', 0) for a in categories.get('dollars', []))
    shitcoin_total = sum(a.get('usd_value', 0) for a in categories.get('shitcoin', []))
    portfolio_total = hard_money_total + algo_total + dollars_total + shitcoin_total

    algo_price = get_algo_price() or 0.174

    # Asset counts
    asset_counts = {
        'hard_money': len(categories.get('hard_money', [])),
        'algo': len(categories.get('algo', [])),
        'dollars': len(categories.get('dollars', [])),
        'shitcoin': len(categories.get('shitcoin', []))
    }

    # Determine which categories need pagination (>50 assets)
    pagination_threshold = 50
    needs_pagination = {
        cat: count > pagination_threshold
        for cat, count in asset_counts.items()
    }

    # Calculate sovereignty ratio if expenses provided
    sovereignty_ratio = None
    sovereignty_status = None
    years_of_runway = None

    if monthly_fixed_expenses and monthly_fixed_expenses > 0:
        annual_fixed = monthly_fixed_expenses * 12
        sovereignty_ratio = portfolio_total / annual_fixed if annual_fixed > 0 else 0

        # Determine status using centralized helper (no emoji for API responses)
        sovereignty_status = get_sovereignty_status(sovereignty_ratio, include_emoji=False)

        sovereignty_ratio = round(sovereignty_ratio, 2)
        years_of_runway = round(sovereignty_ratio, 1)

    return QuickSovereigntyResponse(
        address=address,
        is_participating=is_participating,
        sovereignty_ratio=sovereignty_ratio,
        sovereignty_status=sovereignty_status,
        portfolio_usd=portfolio_total,
        algo_price=algo_price,
        years_of_runway=years_of_runway,
        category_totals={
            'hard_money': hard_money_total,
            'algo': algo_total,
            'dollars': dollars_total,
            'shitcoin': shitcoin_total
        },
        asset_counts=asset_counts,
        needs_pagination=needs_pagination,
        participation_info=participation_info
    )


@router.post("/defi/sovereignty-cost")
async def analyze_defi_sovereignty_cost(
    request: Dict[str, Any],
    use_local_node: bool = Query(False)
):
    """
    Analyze the sovereignty cost of DeFi yield farming positions.

    Calculates how much sovereignty score is "sacrificed" for yield by holding
    LP tokens instead of 100% hard money assets.

    Request body:
    - address: Algorand wallet address
    - apy_estimates: Optional dict mapping LP ticker to APY (e.g., {"TMPOOL2-ALGO-USDC": 10.5})

    Returns:
    - total_lp_value_usd: Total value in LP positions
    - total_sovereignty_cost: Score difference vs optimal allocation
    - total_sovereignty_cost_percent: Cost as percentage
    - overall_recommendation: What to do about it
    - lp_details: Per-LP breakdown with recommendations
    """
    from core.defi_sovereignty_cost import analyze_wallet_lp_costs

    address = request.get('address')
    apy_estimates = request.get('apy_estimates')

    # Validate address
    validate_algorand_address(address)

    # First, analyze the wallet to get categories
    cached = get_cached_analysis(address) if not use_local_node else None

    if cached:
        categories = cached['categories']
    else:
        analyzer = AlgorandSovereigntyAnalyzer(use_local_node=use_local_node)
        categories = analyzer.analyze_wallet(address)

        if not categories:
            raise NotFoundException(
                detail="Wallet not found or contains no assets",
                error_code="WALLET_NOT_FOUND",
                details={"address": address}
            )

        if not use_local_node:
            cache_analysis(address, {
                'categories': categories,
                'is_participating': analyzer.last_is_participating,
                'hard_money_algo': analyzer.last_hard_money_algo,
                'participation_info': analyzer.last_participation_info
            })

    # Analyze LP sovereignty costs
    result = analyze_wallet_lp_costs(categories, apy_estimates)

    if not result:
        return {
            "message": "No LP positions found in this wallet",
            "total_lp_value_usd": 0,
            "total_sovereignty_cost": 0,
            "total_sovereignty_cost_percent": 0,
            "lp_details": []
        }

    # Convert dataclasses to dict for JSON response
    return {
        "total_lp_value_usd": result.total_lp_value_usd,
        "total_current_score": result.total_current_score,
        "total_potential_score": result.total_potential_score,
        "total_sovereignty_cost": result.total_sovereignty_cost,
        "total_sovereignty_cost_percent": result.total_sovereignty_cost_percent,
        "total_estimated_apy_earnings": result.total_estimated_apy_earnings,
        "overall_recommendation": result.overall_recommendation,
        "lp_details": [
            {
                "lp_name": lp.lp_name,
                "lp_ticker": lp.lp_ticker,
                "total_usd_value": lp.total_usd_value,
                "asset1_ticker": lp.asset1_ticker,
                "asset1_usd": lp.asset1_usd,
                "asset1_tier": lp.asset1_tier.name,
                "asset2_ticker": lp.asset2_ticker,
                "asset2_usd": lp.asset2_usd,
                "asset2_tier": lp.asset2_tier.name,
                "current_sovereignty_score": lp.current_sovereignty_score,
                "potential_sovereignty_score": lp.potential_sovereignty_score,
                "sovereignty_cost": lp.sovereignty_cost,
                "sovereignty_cost_percent": lp.sovereignty_cost_percent,
                "estimated_apy": lp.estimated_apy,
                "break_even_years": lp.break_even_years,
                "recommendation": lp.recommendation
            }
            for lp in result.lp_details
        ]
    }


def _create_and_save_snapshot(
    address: str,
    categories: Dict[str, List[Dict[str, Any]]],
    sovereignty_data: Any,
    is_participating: bool,
    algo_price: float
) -> Optional[SovereigntySnapshot]:
    """
    Helper function to create and save a history snapshot.

    Returns the saved snapshot or None if save failed.
    """
    try:
        # Calculate hard money USD from categories
        hard_money_usd = sum(
            asset.get('usd_value', 0)
            for asset in categories.get('hard_money', [])
        )

        # Calculate total portfolio USD
        total_portfolio_usd = sovereignty_data.portfolio_usd if sovereignty_data else sum(
            asset.get('usd_value', 0)
            for category in categories.values()
            for asset in category
        )

        snapshot = SovereigntySnapshot(
            address=address,
            timestamp=datetime.utcnow().isoformat(),
            sovereignty_ratio=sovereignty_data.sovereignty_ratio if sovereignty_data else 0.0,
            hard_money_usd=hard_money_usd,
            total_portfolio_usd=total_portfolio_usd,
            algo_price=algo_price,
            participation_status=is_participating
        )

        history_manager = get_history_manager()
        if history_manager.save_snapshot(snapshot):
            return snapshot
        return None
    except Exception as e:
        print(f"Error creating snapshot: {e}")
        return None


@router.post(
    "/history/save",
    response_model=HistorySaveResponse,
    summary="Save sovereignty snapshot",
    description="""
Save a point-in-time sovereignty snapshot for historical tracking.

## Automatic vs Manual Saves

- **Automatic**: Snapshots are saved automatically on every `/analyze` call
  that includes `monthly_fixed_expenses`
- **Manual**: Use this endpoint to explicitly save a snapshot at a specific
  moment (e.g., after a major allocation change)

## Snapshot Data

Each snapshot captures:
- Timestamp (UTC ISO format)
- Sovereignty ratio at that moment
- Hard money USD value
- Total portfolio USD value
- ALGO price at snapshot time
- Participation status (online/offline)

## Storage

Snapshots are stored in `data/history/{address}.json` as JSON arrays.
Retention policy: 365 days maximum per address.

## Use Case: Progress Tracking

Track your journey to sovereignty over time:
1. Save snapshots regularly (daily/weekly)
2. Use GET /history/{address} to view trends
3. HistoryChart component visualizes progress
    """,
    response_description="Save confirmation with optional snapshot data",
    responses={
        200: {
            "description": "Snapshot saved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "message": "Snapshot saved successfully",
                        "snapshot": {
                            "address": "I26BHULCO...",
                            "timestamp": "2026-01-25T12:00:00Z",
                            "sovereignty_ratio": 3.25,
                            "hard_money_usd": 50000.0,
                            "total_portfolio_usd": 156000.0,
                            "algo_price": 0.25,
                            "participation_status": True
                        }
                    }
                }
            }
        }
    },
    tags=["History"]
)
async def save_history_snapshot(request: HistorySaveRequest):
    """
    Save a sovereignty snapshot for historical tracking.

    Performs fresh wallet analysis, calculates sovereignty metrics,
    and persists a snapshot to the history database.

    Args:
        request: HistorySaveRequest with address and monthly_fixed_expenses

    Returns:
        HistorySaveResponse with success status and saved snapshot

    Raises:
        ValidationException: If address format is invalid
        NotFoundException: If wallet not found
        AlgorandApiException: If network request fails
    """
    # Validate address format
    validate_algorand_address(request.address)

    analyzer = AlgorandSovereigntyAnalyzer(use_local_node=False)

    try:
        # First check cache for recent analysis
        cached = get_cached_analysis(request.address)

        if cached:
            categories = cached['categories']
            is_participating = cached['is_participating']
        else:
            # Perform fresh analysis
            categories = analyzer.analyze_wallet(request.address)
            if not categories:
                raise NotFoundException(
                    detail="Wallet not found or contains no assets",
                    error_code="WALLET_NOT_FOUND",
                    details={"address": f"{request.address[:8]}...{request.address[-6:]}"}
                )
            is_participating = analyzer.last_is_participating

            # Cache the result
            result = {
                'address': request.address,
                'is_participating': is_participating,
                'hard_money_algo': analyzer.last_hard_money_algo,
                'categories': categories
            }
            cache_analysis(request.address, result)

        # Calculate sovereignty metrics
        sovereignty_data = analyzer.calculate_sovereignty_metrics(
            categories,
            request.monthly_fixed_expenses
        )

        # Get algo price from sovereignty data
        algo_price = sovereignty_data.algo_price if sovereignty_data else 0.0

        # Save snapshot
        snapshot = _create_and_save_snapshot(
            address=request.address,
            categories=categories,
            sovereignty_data=sovereignty_data,
            is_participating=is_participating,
            algo_price=algo_price
        )

        if snapshot:
            return HistorySaveResponse(
                success=True,
                message="Snapshot saved successfully",
                snapshot=snapshot
            )
        else:
            logger.warning(f"Failed to save snapshot for {request.address[:8]}...")
            return HistorySaveResponse(
                success=False,
                message="Failed to save snapshot",
                snapshot=None
            )

    except (ValidationException, NotFoundException):
        raise
    except requests.exceptions.Timeout:
        raise AlgorandApiException(
            detail="Request timed out while fetching wallet data",
            is_timeout=True
        )
    except requests.exceptions.RequestException as e:
        logger.error(f"Network error in history save: {e}")
        raise AlgorandApiException(
            detail="Failed to fetch wallet data from Algorand network",
            error_code="ALGORAND_API_ERROR"
        )
    except Exception as e:
        logger.exception(f"Error saving history snapshot: {e}")
        raise AnalysisException(
            detail="Failed to save history snapshot",
            error_code="HISTORY_SAVE_FAILED",
            address=request.address
        )


@router.get(
    "/history/{address}",
    summary="Get sovereignty history",
    description="""
Retrieve historical sovereignty snapshots for an address with progress metrics.

## Time Periods

- `days=30`: Last month of snapshots
- `days=90`: Last quarter (default)
- `days=365`: Full year of history

## Response Structure

The response includes three main sections:

### 1. Snapshots Array
Raw snapshot data sorted oldest-first (for charting):
```json
{
  "snapshots": [
    {"timestamp": "2025-01-01T...", "sovereignty_ratio": 2.5, ...},
    {"timestamp": "2025-01-15T...", "sovereignty_ratio": 2.8, ...},
    {"timestamp": "2025-01-25T...", "sovereignty_ratio": 3.1, ...}
  ]
}
```

### 2. Progress Metrics
Calculated trend analysis:
- `current_ratio`: Most recent ratio
- `previous_ratio`: Ratio from ~30 days ago (for comparison)
- `change_absolute`: Ratio change (current - previous)
- `change_pct`: Percentage change
- `trend`: "improving", "declining", "stable", or "new"
- `projected_next_status`: When you'll reach next level (if improving)

### 3. All-Time Stats
Historical high/low/average for context:
- `high`: Best sovereignty ratio achieved
- `low`: Lowest ratio recorded
- `average`: Mean ratio over tracking period
- `first_tracked`: When tracking began
    """,
    response_description="Historical snapshots with progress metrics",
    responses={
        200: {
            "description": "History retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "address": "I26BHULCO...",
                        "snapshots": [
                            {
                                "timestamp": "2025-11-01T12:00:00Z",
                                "sovereignty_ratio": 2.5,
                                "hard_money_usd": 40000.0,
                                "total_portfolio_usd": 120000.0,
                                "algo_price": 0.22,
                                "participation_status": True
                            }
                        ],
                        "count": 45,
                        "progress": {
                            "current_ratio": 3.25,
                            "previous_ratio": 2.5,
                            "change_absolute": 0.75,
                            "change_pct": 30.0,
                            "trend": "improving",
                            "days_tracked": 90,
                            "snapshots_count": 45,
                            "projected_next_status": {
                                "status": "Antifragile",
                                "ratio_needed": 6.0,
                                "projected_date": "2026-05-15"
                            }
                        },
                        "all_time": {
                            "high": 3.25,
                            "low": 1.8,
                            "average": 2.65,
                            "first_tracked": "2025-10-01T12:00:00Z"
                        }
                    }
                }
            }
        }
    },
    tags=["History"]
)
async def get_history(
    address: str = Path(..., description="58-character Algorand wallet address"),
    days: int = Query(90, description="Time period: 30, 90, or 365 days")
):
    """
    Get historical sovereignty snapshots for an address with progress metrics.

    Returns snapshots within the specified time period along with calculated
    progress tracking data for the HistoryChart component.

    Args:
        address: Algorand wallet address
        days: Number of days of history (30, 90, or 365)

    Returns:
        Dict with snapshots array, count, progress metrics, and all-time stats
    """
    # Validate address format
    validate_algorand_address(address)

    # Validate days parameter
    if days not in (30, 90, 365):
        days = 90

    history_manager = get_history_manager()
    snapshots = history_manager.get_history(address, days)

    # Calculate progress metrics
    progress = _calculate_progress(snapshots)

    # Calculate all-time stats
    all_time = _calculate_all_time(snapshots) if snapshots else None

    return {
        "address": address,
        "snapshots": snapshots,
        "count": len(snapshots),
        "progress": progress,
        "all_time": all_time
    }


def _calculate_progress(snapshots: list) -> dict:
    """Calculate progress metrics from snapshots."""
    if not snapshots:
        return {
            "current_ratio": 0,
            "previous_ratio": None,
            "change_absolute": None,
            "change_pct": None,
            "trend": "new",
            "days_tracked": 0,
            "snapshots_count": 0,
            "projected_next_status": None
        }

    # Snapshots are sorted oldest first, so newest is at the end
    current = snapshots[-1]
    current_ratio = current.sovereignty_ratio if hasattr(current, 'sovereignty_ratio') else current.get('sovereignty_ratio', 0)

    # Find snapshot from ~30 days ago
    previous_ratio = None
    for snap in snapshots:
        ts = snap.timestamp if hasattr(snap, 'timestamp') else snap.get('timestamp', '')
        try:
            if isinstance(ts, str):
                snap_date = datetime.fromisoformat(ts.replace('Z', '+00:00'))
            else:
                snap_date = ts
            now = datetime.now(snap_date.tzinfo) if snap_date.tzinfo else datetime.utcnow()
            if (now - snap_date).days >= 25:
                previous_ratio = snap.sovereignty_ratio if hasattr(snap, 'sovereignty_ratio') else snap.get('sovereignty_ratio', 0)
                break
        except Exception:
            continue

    # Calculate change
    change_absolute = None
    change_pct = None
    trend = "new" if len(snapshots) == 1 else "stable"

    if previous_ratio is not None:
        change_absolute = round(current_ratio - previous_ratio, 2)
        change_pct = round((change_absolute / previous_ratio) * 100, 1) if previous_ratio > 0 else 0

        if change_pct > 5:
            trend = "improving"
        elif change_pct < -5:
            trend = "declining"
        else:
            trend = "stable"

    # Calculate days tracked (snapshots sorted oldest first)
    days_tracked = 0
    if snapshots:
        oldest = snapshots[0]
        ts = oldest.timestamp if hasattr(oldest, 'timestamp') else oldest.get('timestamp', '')
        try:
            if isinstance(ts, str):
                oldest_date = datetime.fromisoformat(ts.replace('Z', '+00:00'))
            else:
                oldest_date = ts
            now = datetime.now(oldest_date.tzinfo) if oldest_date.tzinfo else datetime.utcnow()
            days_tracked = (now - oldest_date).days
        except Exception:
            pass

    # Project next status
    projected_next_status = None
    STATUS_THRESHOLDS = [
        (1.0, "Fragile"),
        (3.0, "Robust"),
        (6.0, "Antifragile"),
        (20.0, "Generationally Sovereign")
    ]

    if trend == "improving" and change_absolute and change_absolute > 0:
        for threshold, status in STATUS_THRESHOLDS:
            if current_ratio < threshold:
                gap = threshold - current_ratio
                days_to_reach = int(gap / change_absolute * 30) if change_absolute > 0 else None
                if days_to_reach and days_to_reach < 365:
                    projected_date = datetime.now() + timedelta(days=days_to_reach)
                    projected_next_status = {
                        "status": status,
                        "ratio_needed": threshold,
                        "projected_date": projected_date.strftime("%Y-%m-%d")
                    }
                break

    return {
        "current_ratio": current_ratio,
        "previous_ratio": previous_ratio,
        "change_absolute": change_absolute,
        "change_pct": change_pct,
        "trend": trend,
        "days_tracked": days_tracked,
        "snapshots_count": len(snapshots),
        "projected_next_status": projected_next_status
    }


def _calculate_all_time(snapshots: list) -> Optional[dict]:
    """Calculate all-time statistics (snapshots sorted oldest first)."""
    if not snapshots:
        return None

    ratios = []
    for snap in snapshots:
        ratio = snap.sovereignty_ratio if hasattr(snap, 'sovereignty_ratio') else snap.get('sovereignty_ratio', 0)
        ratios.append(ratio)

    # Oldest is first element
    oldest = snapshots[0]
    ts = oldest.timestamp if hasattr(oldest, 'timestamp') else oldest.get('timestamp', '')

    return {
        "high": round(max(ratios), 2),
        "low": round(min(ratios), 2),
        "average": round(sum(ratios) / len(ratios), 2),
        "first_tracked": ts if isinstance(ts, str) else ts.isoformat() if hasattr(ts, 'isoformat') else str(ts)
    }


@router.get("/gold-silver-ratio")
async def get_gold_silver_ratio():
    """
    Get current Gold/Silver ratio using live Yahoo Finance spot prices.

    Fetches real-time COMEX futures prices for Gold (GC=F) and Silver (SI=F).
    Falls back to hardcoded prices on API failure.
    """
    # Fetch live prices per troy ounce from Yahoo Finance
    gold_price = get_gold_price_per_oz()
    silver_price = get_silver_price_per_oz()

    # Ensure we have valid prices
    if gold_price is None:
        gold_price = 4500.0  # Fallback
    if silver_price is None:
        silver_price = 70.0  # Fallback

    # Round for display
    gold_price = round(gold_price, 2)
    silver_price = round(silver_price, 2)

    # Calculate ratio
    ratio = round(gold_price / silver_price, 2)

    # Historical context
    historical_mean = 15.0
    historical_range = {"low": 12, "high": 90}

    # Status indicator
    if ratio > 80:
        status = "undervalued"
        color = "red"
        message = "Silver significantly undervalued relative to gold"
    elif ratio > 60:
        status = "below_average"
        color = "orange"
        message = "Silver moderately undervalued"
    elif ratio > 40:
        status = "normalized"
        color = "yellow"
        message = "Ratio approaching historical norms"
    else:
        status = "compressed"
        color = "green"
        message = "Ratio compressed - silver relatively expensive"

    return {
        "ratio": ratio,
        "gold_price": gold_price,
        "silver_price": silver_price,
        "historical_mean": historical_mean,
        "historical_range": historical_range,
        "status": status,
        "color": color,
        "message": message,
        "interpretation": {
            "what_it_means": "The Gold/Silver ratio measures how many ounces of silver it takes to buy one ounce of gold.",
            "current_signal": f"At {ratio}:1, silver is {('undervalued' if ratio > 60 else 'fairly valued')} compared to gold.",
            "historical_note": f"The ratio has ranged from {historical_range['low']}:1 to {historical_range['high']}:1 over the past century. The long-term mean is around {historical_mean}:1."
        }
    }


# -----------------------------------------------------------------------------
# Network Stats Endpoints
# -----------------------------------------------------------------------------

@router.get(
    "/network/stats",
    response_model=NetworkStatsResponse,
    summary="Get network statistics",
    description="""
Get current Algorand network participation and decentralization statistics.

## Decentralization Score

A 0-100 score measuring Algorand's decentralization, calculated from:

### Positive Factors
- **Community Online Stake** (max 30 points): % of online stake from non-Foundation addresses
- **Participation Rate** (max 10 points): % of total supply participating in consensus

### Risk Penalties
- **Foundation Supply** (max -25 points): Foundation's % of total supply
- **Potential Control** (max -20 points): If Foundation went fully online, their potential stake %
- **Relay Centralization** (-15 points): Foundation-operated relay node infrastructure
- **Governance Influence** (-10 points): Foundation's influence over protocol changes

## Network Info

- `total_supply_algo`: Total ALGO in circulation
- `online_stake_algo`: ALGO currently participating in consensus
- `participation_rate`: % of supply that is online
- `current_round`: Latest blockchain round number

## Foundation Info

Known Foundation addresses are tracked separately:
- `total_balance_algo`: Total Foundation holdings
- `online_balance_algo`: Foundation stake that is online
- `pct_of_total_supply`: Foundation % of total supply
- `pct_of_online_stake`: Foundation % of online stake

## Caching

Data is cached for 5 minutes to reduce API load.
    """,
    response_description="Complete network statistics with decentralization scoring",
    tags=["Network"]
)
async def get_network_statistics():
    """
    Get current Algorand network participation and decentralization statistics.

    Fetches real-time data from the Algorand network and calculates a
    comprehensive decentralization score based on multiple factors.

    Returns:
        NetworkStatsResponse with network, foundation, community info and score

    Raises:
        ServiceUnavailableException: If Algorand network unreachable
        TimeoutException: If request times out
        AlgorandApiException: If API communication fails
    """
    client = get_network_stats_client()

    try:
        summary = await client.get_decentralization_summary()

        # Convert microalgos to ALGO for response
        network_info = NetworkInfo(
            total_supply_algo=round(microalgos_to_algo(summary.network.total_supply), 2),
            online_stake_algo=round(microalgos_to_algo(summary.network.online_stake), 2),
            participation_rate=summary.network.participation_rate,
            current_round=summary.network.current_round
        )

        foundation_info = FoundationInfo(
            total_balance_algo=round(microalgos_to_algo(summary.foundation.total_balance), 2),
            online_balance_algo=round(microalgos_to_algo(summary.foundation.online_balance), 2),
            pct_of_total_supply=summary.foundation.foundation_pct_of_supply,
            pct_of_online_stake=summary.foundation.foundation_pct_of_online,
            address_count=len(summary.foundation.foundation_addresses)
        )

        community_info = CommunityInfo(
            estimated_stake_algo=round(microalgos_to_algo(summary.community_stake), 2),
            pct_of_online_stake=summary.community_pct_of_online
        )

        # Build score breakdown if available
        score_breakdown = None
        if summary.score_breakdown:
            b = summary.score_breakdown
            score_breakdown = ScoreBreakdown(
                community_online_pct=b.community_online_pct,
                community_online_score=b.community_online_score,
                participation_rate_score=b.participation_rate_score,
                foundation_supply_pct=b.foundation_supply_pct,
                foundation_supply_penalty=b.foundation_supply_penalty,
                foundation_potential_control=b.foundation_potential_control,
                potential_control_penalty=b.potential_control_penalty,
                relay_centralization_penalty=b.relay_centralization_penalty,
                governance_penalty=b.governance_penalty,
                raw_score=b.raw_score,
                final_score=b.final_score
            )

        # Format timestamp
        fetched_at = datetime.utcfromtimestamp(summary.fetched_at).isoformat() + "Z"

        return NetworkStatsResponse(
            network=network_info,
            foundation=foundation_info,
            community=community_info,
            decentralization_score=summary.decentralization_score,
            score_breakdown=score_breakdown,
            estimated_node_count=3075,  # Estimate from Nodely.io
            fetched_at=fetched_at
        )

    except ConnectionError as e:
        logger.error(f"Network stats connection error: {e}")
        raise ServiceUnavailableException(
            detail="Unable to connect to Algorand network",
            error_code="ALGORAND_CONNECTION_ERROR",
            details={"suggestion": "Please try again in a few moments"}
        )
    except requests.exceptions.Timeout:
        logger.warning("Network stats request timed out")
        raise TimeoutException(
            detail="Request timed out while fetching network statistics",
            error_code="NETWORK_STATS_TIMEOUT",
            service="algorand"
        )
    except Exception as e:
        logger.exception(f"Error fetching network stats: {e}")
        raise AlgorandApiException(
            detail="Failed to fetch network statistics",
            error_code="NETWORK_STATS_ERROR"
        )


def _get_contribution_tier(balance_algo: float, is_participating: bool) -> str:
    """
    Classify wallet contribution tier based on balance and participation status.
    """
    if not is_participating:
        if balance_algo >= 30000:
            return "Eligible but Offline"
        return "Observer"

    # Participating wallets
    if balance_algo >= 1_000_000:
        return "Whale Validator"
    elif balance_algo >= 100_000:
        return "Major Validator"
    elif balance_algo >= 30_000:
        return "Active Participant"
    elif balance_algo >= 1_000:
        return "Community Node"
    else:
        return "Micro Validator"


@router.get("/network/wallet/{address}", response_model=WalletParticipationResponse)
async def get_wallet_participation(
    address: str = Path(..., description="Algorand wallet address", min_length=58, max_length=58)
):
    """
    Check participation status for a specific Algorand wallet.

    Returns:
    - Whether the wallet is actively participating in consensus
    - Current balance and stake percentage
    - Participation key details (if registered)
    - Contribution tier classification

    Data is cached for 1 minute.
    """
    client = get_network_stats_client()

    try:
        wallet = await client.check_wallet_participation(address)

        # Convert balance to ALGO
        balance_algo = microalgos_to_algo(wallet.balance)

        # Build participation key info if available
        participation_key = None
        if wallet.vote_first_valid or wallet.vote_last_valid:
            rounds_remaining = None
            if wallet.vote_last_valid and not wallet.is_key_expired:
                rounds_remaining = wallet.vote_last_valid - wallet.current_round

            participation_key = ParticipationKeyInfo(
                first_valid=wallet.vote_first_valid,
                last_valid=wallet.vote_last_valid,
                is_expired=wallet.is_key_expired,
                rounds_remaining=rounds_remaining
            )

        # Determine contribution tier
        contribution_tier = _get_contribution_tier(balance_algo, wallet.is_online)

        return WalletParticipationResponse(
            address=address,
            is_participating=wallet.is_online,
            balance_algo=round(balance_algo, 6),
            stake_percentage=wallet.stake_percentage,
            participation_key=participation_key,
            contribution_tier=contribution_tier,
            current_round=wallet.current_round
        )

    except ConnectionError as e:
        logger.error(f"Wallet participation connection error: {e}")
        raise ServiceUnavailableException(
            detail="Unable to connect to Algorand network",
            error_code="ALGORAND_CONNECTION_ERROR"
        )
    except requests.exceptions.Timeout:
        logger.warning(f"Wallet participation request timed out for {address[:8]}...")
        raise TimeoutException(
            detail="Request timed out while fetching wallet participation",
            service="algorand"
        )
    except Exception as e:
        logger.exception(f"Error fetching wallet participation: {e}")
        raise AlgorandApiException(
            detail="Failed to fetch wallet participation data",
            error_code="WALLET_PARTICIPATION_ERROR",
            details={"address": f"{address[:8]}...{address[-6:]}"}
        )


# -----------------------------------------------------------------------------
# Meld Arbitrage Endpoint
# -----------------------------------------------------------------------------

def _calculate_arbitrage_signal(premium_pct: float) -> tuple:
    """
    Determine trading signal based on premium percentage.

    Thresholds:
    - STRONG_BUY/SELL: >6% discount/premium
    - BUY/SELL: 0.5% - 6%
    - HOLD: within ±0.5% (fair value)

    Args:
        premium_pct: The premium/discount percentage of Meld vs spot

    Returns:
        Tuple of (signal_name, signal_strength 0-100)
    """
    # Signal strength scales from 0-100 based on how far past threshold
    # For STRONG signals: 6% = ~50 strength, 12% = 100 strength
    # For regular signals: 0.5% = ~10 strength, 6% = ~50 strength

    if premium_pct > 6:
        # STRONG_SELL: asset trading >6% above spot
        strength = min(100, 50 + (premium_pct - 6) * 8.33)
        return ('STRONG_SELL', strength)
    elif premium_pct > 0.5:
        # SELL: asset trading 0.5-6% above spot
        strength = 10 + (premium_pct - 0.5) * 7.27  # scales 10-50
        return ('SELL', strength)
    elif premium_pct < -6:
        # STRONG_BUY: asset trading >6% below spot
        strength = min(100, 50 + (abs(premium_pct) - 6) * 8.33)
        return ('STRONG_BUY', strength)
    elif premium_pct < -0.5:
        # BUY: asset trading 0.5-6% below spot
        strength = 10 + (abs(premium_pct) - 0.5) * 7.27  # scales 10-50
        return ('BUY', strength)
    else:
        # HOLD: within ±0.5% of spot (fair value)
        return ('HOLD', 0)


def _calculate_rotation_signal(gold_premium_pct: float, silver_premium_pct: float) -> dict:
    """
    Calculate rotation signal between gold and silver based on premium spread.

    The spread = silver_premium - gold_premium
    - Positive spread (silver more expensive): Signal to rotate silver → gold
    - Negative spread (gold more expensive): Signal to rotate gold → silver

    Thresholds:
    - |spread| > 3%: Active rotation signal
    - |spread| 1-3%: Weak signal (consider)
    - |spread| < 1%: No signal (metals at parity)

    Returns signal with strength (0-100) scaled by how far past threshold.
    """
    spread_pct = silver_premium_pct - gold_premium_pct
    abs_spread = abs(spread_pct)

    if abs_spread < 1.0:
        return {
            'signal': 'HOLD',
            'strength': 0,
            'spread_pct': round(spread_pct, 2),
            'description': 'Gold and silver premiums at parity - no rotation advantage'
        }
    elif abs_spread < 3.0:
        # Weak signal zone (1-3%)
        strength = (abs_spread - 1.0) / 2.0 * 33  # Scale 0-33%
        if spread_pct > 0:
            return {
                'signal': 'CONSIDER_SILVER_TO_GOLD',
                'strength': round(strength, 1),
                'spread_pct': round(spread_pct, 2),
                'description': f'Silver slightly overpriced vs gold ({spread_pct:.2f}% spread) - weak rotation signal'
            }
        else:
            return {
                'signal': 'CONSIDER_GOLD_TO_SILVER',
                'strength': round(strength, 1),
                'spread_pct': round(spread_pct, 2),
                'description': f'Gold slightly overpriced vs silver ({abs_spread:.2f}% spread) - weak rotation signal'
            }
    else:
        # Strong signal zone (>3%)
        # Strength scales from 33% at 3% spread to 100% at 9%+ spread
        strength = min(100, 33 + (abs_spread - 3.0) / 6.0 * 67)
        if spread_pct > 0:
            return {
                'signal': 'SILVER_TO_GOLD',
                'strength': round(strength, 1),
                'spread_pct': round(spread_pct, 2),
                'description': f'Silver overpriced vs gold by {spread_pct:.2f}% - rotate silver to gold'
            }
        else:
            return {
                'signal': 'GOLD_TO_SILVER',
                'strength': round(strength, 1),
                'spread_pct': round(spread_pct, 2),
                'description': f'Gold overpriced vs silver by {abs_spread:.2f}% - rotate gold to silver'
            }


def _get_gsr_context(gsr: float) -> dict:
    """
    Provide historical context for the Gold/Silver Ratio (GSR).

    Historical ranges:
    - Modern era average: ~60:1
    - Historical (pre-1900): ~15:1
    - Extreme high: 120:1 (March 2020)
    - Extreme low: 30:1 (1980, 2011)
    """
    if gsr >= 80:
        return {
            'zone': 'extreme_high',
            'color': 'red',
            'message': f'GSR at {gsr:.1f} - silver historically cheap vs gold (buy silver)',
            'bias': 'silver'
        }
    elif gsr >= 70:
        return {
            'zone': 'high',
            'color': 'orange',
            'message': f'GSR at {gsr:.1f} - silver undervalued vs gold',
            'bias': 'silver'
        }
    elif gsr >= 50:
        return {
            'zone': 'normal',
            'color': 'yellow',
            'message': f'GSR at {gsr:.1f} - normal range, no strong bias',
            'bias': 'neutral'
        }
    elif gsr >= 40:
        return {
            'zone': 'low',
            'color': 'green',
            'message': f'GSR at {gsr:.1f} - gold undervalued vs silver',
            'bias': 'gold'
        }
    else:
        return {
            'zone': 'extreme_low',
            'color': 'green',
            'message': f'GSR at {gsr:.1f} - gold historically cheap vs silver (buy gold)',
            'bias': 'gold'
        }


@router.get("/arbitrage/meld", response_model=MeldArbitrageResponse)
async def get_meld_arbitrage():
    """
    Compare Algorand wrapped assets to their spot prices.

    Analyzes:
    - Meld GOLD$/SILVER$ vs Yahoo Finance spot prices
    - goBTC vs Coinbase BTC spot price
    - Gold/Silver Ratio (GSR) with rotation signals

    Returns premium/discount percentage and trading signals for arbitrage opportunities.

    **Signal Interpretation:**
    - STRONG_BUY: Asset >10% below spot (buy on Algorand, it's cheap)
    - BUY: Asset 5-10% below spot
    - HOLD: Within +/-5% of spot (fair value)
    - SELL: Asset 5-10% above spot
    - STRONG_SELL: Asset >10% above spot (sell on Algorand)

    **Data Sources:**
    - Gold/Silver spot: Yahoo Finance (COMEX futures GC=F, SI=F)
    - Bitcoin spot: Coinbase API
    - On-chain prices: Vestige API (Algorand DEX aggregator)
    """
    result = {
        'gold': None,
        'silver': None,
        'bitcoin': None,
        'gsr': None,
        'rotation': None,
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'data_complete': True
    }

    # =========== GOLD ===========
    try:
        spot_gold = get_gold_price_per_oz()
        meld_gold = get_meld_gold_price()

        if spot_gold and meld_gold and spot_gold > 0:
            implied_gold = spot_gold / GRAMS_PER_TROY_OZ
            premium_usd = meld_gold - implied_gold
            premium_pct = (premium_usd / implied_gold) * 100
            signal, strength = _calculate_arbitrage_signal(premium_pct)

            result['gold'] = {
                'spot_per_oz': round(spot_gold, 2),
                'implied_per_gram': round(implied_gold, 4),
                'meld_price': round(meld_gold, 4),
                'premium_pct': round(premium_pct, 2),
                'premium_usd': round(premium_usd, 4),
                'signal': signal,
                'signal_strength': round(strength, 1)
            }
        else:
            result['data_complete'] = False
            result['gold'] = {
                'error': 'Unable to fetch gold prices',
                'spot_available': spot_gold is not None,
                'meld_available': meld_gold is not None
            }
    except Exception as e:
        print(f"Error calculating gold arbitrage: {e}")
        result['data_complete'] = False
        result['gold'] = {
            'error': str(e),
            'spot_available': False,
            'meld_available': False
        }

    # =========== SILVER ===========
    try:
        spot_silver = get_silver_price_per_oz()
        meld_silver = get_meld_silver_price()

        if spot_silver and meld_silver and spot_silver > 0:
            implied_silver = spot_silver / GRAMS_PER_TROY_OZ
            premium_usd = meld_silver - implied_silver
            premium_pct = (premium_usd / implied_silver) * 100
            signal, strength = _calculate_arbitrage_signal(premium_pct)

            result['silver'] = {
                'spot_per_oz': round(spot_silver, 2),
                'implied_per_gram': round(implied_silver, 4),
                'meld_price': round(meld_silver, 4),
                'premium_pct': round(premium_pct, 2),
                'premium_usd': round(premium_usd, 4),
                'signal': signal,
                'signal_strength': round(strength, 1)
            }
        else:
            result['data_complete'] = False
            result['silver'] = {
                'error': 'Unable to fetch silver prices',
                'spot_available': spot_silver is not None,
                'meld_available': meld_silver is not None
            }
    except Exception as e:
        print(f"Error calculating silver arbitrage: {e}")
        result['data_complete'] = False
        result['silver'] = {
            'error': str(e),
            'spot_available': False,
            'meld_available': False
        }

    # =========== BITCOIN (3-way: Spot vs goBTC vs WBTC) ===========
    try:
        spot_btc = get_bitcoin_spot_price()
        gobtc_price = get_gobtc_price()
        wbtc_price = get_wbtc_price()

        bitcoin_result = {
            'spot_price': None,
            'gobtc': None,
            'wbtc': None,
            'cross_dex_spread': None,
            'best_opportunity': None
        }

        if spot_btc and spot_btc > 0:
            bitcoin_result['spot_price'] = round(spot_btc, 2)

            # goBTC analysis
            if gobtc_price and gobtc_price > 0:
                gobtc_premium_usd = gobtc_price - spot_btc
                gobtc_premium_pct = (gobtc_premium_usd / spot_btc) * 100
                gobtc_signal, gobtc_strength = _calculate_arbitrage_signal(gobtc_premium_pct)

                bitcoin_result['gobtc'] = {
                    'price': round(gobtc_price, 2),
                    'premium_pct': round(gobtc_premium_pct, 2),
                    'premium_usd': round(gobtc_premium_usd, 2),
                    'signal': gobtc_signal,
                    'signal_strength': round(gobtc_strength, 1),
                    'asa_id': GOBTC_ASA,
                    'tinyman_url': f'https://app.tinyman.org/#/swap?asset_in=0&asset_out={GOBTC_ASA}'
                }
            else:
                bitcoin_result['gobtc'] = {'error': 'Unable to fetch goBTC price'}

            # WBTC analysis
            if wbtc_price and wbtc_price > 0:
                wbtc_premium_usd = wbtc_price - spot_btc
                wbtc_premium_pct = (wbtc_premium_usd / spot_btc) * 100
                wbtc_signal, wbtc_strength = _calculate_arbitrage_signal(wbtc_premium_pct)

                bitcoin_result['wbtc'] = {
                    'price': round(wbtc_price, 2),
                    'premium_pct': round(wbtc_premium_pct, 2),
                    'premium_usd': round(wbtc_premium_usd, 2),
                    'signal': wbtc_signal,
                    'signal_strength': round(wbtc_strength, 1),
                    'asa_id': WBTC_ASA,
                    'tinyman_url': f'https://app.tinyman.org/#/swap?asset_in=0&asset_out={WBTC_ASA}',
                    'liquidity_warning': 'Lower liquidity than goBTC - higher slippage risk'
                }
            else:
                bitcoin_result['wbtc'] = {'error': 'Unable to fetch WBTC price'}

            # Cross-DEX spread (goBTC vs WBTC)
            if gobtc_price and wbtc_price and gobtc_price > 0 and wbtc_price > 0:
                cross_spread_pct = ((gobtc_price - wbtc_price) / wbtc_price) * 100
                bitcoin_result['cross_dex_spread'] = {
                    'gobtc_vs_wbtc_pct': round(cross_spread_pct, 2),
                    'description': f"goBTC is {abs(cross_spread_pct):.2f}% {'more expensive' if cross_spread_pct > 0 else 'cheaper'} than WBTC"
                }

                # Determine best opportunity
                gobtc_prem = bitcoin_result['gobtc'].get('premium_pct', 0)
                wbtc_prem = bitcoin_result['wbtc'].get('premium_pct', 0)

                if gobtc_prem < wbtc_prem:
                    # goBTC is cheaper relative to spot
                    bitcoin_result['best_opportunity'] = {
                        'token': 'goBTC',
                        'action': 'BUY' if gobtc_prem < -0.5 else 'PREFER',
                        'reason': f"goBTC has deeper discount ({gobtc_prem:.2f}% vs {wbtc_prem:.2f}%)",
                        'advantage_pct': round(wbtc_prem - gobtc_prem, 2)
                    }
                elif wbtc_prem < gobtc_prem:
                    # WBTC is cheaper relative to spot
                    bitcoin_result['best_opportunity'] = {
                        'token': 'WBTC',
                        'action': 'BUY' if wbtc_prem < -0.5 else 'PREFER',
                        'reason': f"WBTC has deeper discount ({wbtc_prem:.2f}% vs {gobtc_prem:.2f}%)",
                        'advantage_pct': round(gobtc_prem - wbtc_prem, 2),
                        'liquidity_note': 'Lower liquidity - use limit orders'
                    }
                else:
                    bitcoin_result['best_opportunity'] = {
                        'token': 'goBTC',
                        'action': 'EQUAL',
                        'reason': 'Both tokens at same premium - prefer goBTC for better liquidity',
                        'advantage_pct': 0
                    }

            result['bitcoin'] = bitcoin_result
        else:
            result['data_complete'] = False
            result['bitcoin'] = {
                'error': 'Unable to fetch Bitcoin spot price',
                'spot_available': False,
                'gobtc_available': gobtc_price is not None,
                'wbtc_available': wbtc_price is not None
            }
    except Exception as e:
        print(f"Error calculating Bitcoin arbitrage: {e}")
        result['data_complete'] = False
        result['bitcoin'] = {
            'error': str(e),
            'spot_available': False,
            'gobtc_available': False,
            'wbtc_available': False
        }

    # =========== GSR & ROTATION SIGNAL ===========
    try:
        # Calculate GSR if we have both gold and silver data
        gold_data = result.get('gold')
        silver_data = result.get('silver')

        if (gold_data and 'meld_price' in gold_data and
            silver_data and 'meld_price' in silver_data):

            meld_gold = gold_data['meld_price']
            meld_silver = silver_data['meld_price']

            # Calculate Meld GSR (gold price / silver price in same units - per gram)
            meld_gsr = meld_gold / meld_silver if meld_silver > 0 else None

            if meld_gsr:
                # Get spot GSR for comparison
                spot_gold_per_gram = gold_data['implied_per_gram']
                spot_silver_per_gram = silver_data['implied_per_gram']
                spot_gsr = spot_gold_per_gram / spot_silver_per_gram if spot_silver_per_gram > 0 else None

                gsr_context = _get_gsr_context(meld_gsr)

                result['gsr'] = {
                    'meld_gsr': round(meld_gsr, 2),
                    'spot_gsr': round(spot_gsr, 2) if spot_gsr else None,
                    'gsr_spread_pct': round(((meld_gsr - spot_gsr) / spot_gsr) * 100, 2) if spot_gsr else None,
                    'context': gsr_context
                }

                # Calculate rotation signal based on premium spreads
                gold_premium = gold_data.get('premium_pct', 0)
                silver_premium = silver_data.get('premium_pct', 0)

                rotation_signal = _calculate_rotation_signal(gold_premium, silver_premium)
                result['rotation'] = rotation_signal

    except Exception as e:
        print(f"Error calculating GSR/rotation: {e}")
        # GSR is optional, don't fail the whole response

    # Auto-capture price snapshot for history
    try:
        save_current_prices()
    except Exception as e:
        print(f"Warning: Failed to save BTC price snapshot: {e}")

    return result


@router.get("/arbitrage/btc-history", response_model=BTCHistoryResponse)
async def get_btc_arbitrage_history(
    hours: int = Query(24, ge=1, le=720, description="Hours of history (1-720, default 24)")
):
    """
    Get historical Bitcoin price data for charting.

    Returns time-series data of:
    - Coinbase spot BTC price
    - goBTC price and premium vs spot
    - WBTC price and premium vs spot

    Useful for identifying arbitrage patterns over time.
    """
    try:
        history_manager = get_btc_history_manager()
        snapshots = history_manager.get_history(hours=hours)
        stats = history_manager.get_stats(hours=hours)

        # Convert to JSON-serializable format
        data_points = []
        for snap in snapshots:
            data_points.append({
                'timestamp': snap.timestamp.isoformat() + 'Z',
                'spot_btc': round(snap.spot_btc, 2),
                'gobtc_price': round(snap.gobtc_price, 2),
                'wbtc_price': round(snap.wbtc_price, 2) if snap.wbtc_price else None,
                'gobtc_premium_pct': round(snap.gobtc_premium_pct, 2),
                'wbtc_premium_pct': round(snap.wbtc_premium_pct, 2) if snap.wbtc_premium_pct else None
            })

        return {
            'data_points': data_points,
            'stats': stats,
            'hours_requested': hours,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
    except Exception as e:
        logger.exception(f"Error fetching BTC history: {e}")
        raise PriceApiException(
            detail="Failed to fetch Bitcoin price history",
            error_code="BTC_HISTORY_ERROR",
            asset="BTC"
        )


# -----------------------------------------------------------------------------
# Gold Miner Metrics Endpoints
# -----------------------------------------------------------------------------

@router.get("/gold/miners")
async def get_miner_metrics(
    limit: int = Query(100, ge=1, le=500, description="Maximum records to return")
):
    """
    Get all gold miner quarterly metrics.

    Returns metrics ordered by period (newest first), then by ticker.
    Used for historical trend analysis and data tables.
    """
    try:
        db = get_miner_metrics_db()
        metrics = db.get_all_metrics(limit=limit)

        return {
            'metrics': [m.to_dict() for m in metrics],
            'count': len(metrics),
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
    except Exception as e:
        logger.exception(f"Error fetching miner metrics: {e}")
        raise ExternalApiException(
            detail="Failed to fetch gold miner metrics",
            error_code="MINER_METRICS_ERROR"
        )


@router.get("/gold/miners/latest")
async def get_latest_miner_metrics():
    """
    Get the most recent metrics for each gold mining company.

    Returns one record per company (their latest quarterly report).
    Used for dashboard KPIs and efficiency frontier chart.
    """
    try:
        db = get_miner_metrics_db()
        metrics = db.get_latest_by_company()

        return {
            'metrics': [m.to_dict() for m in metrics],
            'count': len(metrics),
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
    except Exception as e:
        logger.exception(f"Error fetching latest miner metrics: {e}")
        raise ExternalApiException(
            detail="Failed to fetch latest miner metrics",
            error_code="MINER_METRICS_ERROR"
        )


@router.get("/gold/miners/stats")
async def get_sector_stats():
    """
    Get sector-wide statistics from the latest data.

    Returns aggregated metrics:
    - Average AISC across sector
    - Total quarterly production
    - Average dividend yield
    - Weighted Tier 1 jurisdiction exposure
    """
    try:
        db = get_miner_metrics_db()
        stats = db.get_sector_stats()

        return {
            'stats': stats,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
    except Exception as e:
        logger.exception(f"Error fetching sector stats: {e}")
        raise ExternalApiException(
            detail="Failed to fetch gold sector statistics",
            error_code="SECTOR_STATS_ERROR"
        )


@router.get("/gold/miners/{ticker}")
async def get_miner_by_ticker(
    ticker: str = Path(..., description="Company ticker symbol (e.g., NEM, GOLD, AEM)")
):
    """
    Get all quarterly metrics for a specific company.

    Returns historical data for trend analysis of a single miner.
    """
    try:
        db = get_miner_metrics_db()
        metrics = db.get_metrics_by_ticker(ticker.upper())

        if not metrics:
            raise NotFoundException(
                detail=f"No data found for gold miner ticker: {ticker}",
                error_code="MINER_NOT_FOUND",
                details={"ticker": ticker.upper()}
            )

        return {
            'ticker': ticker.upper(),
            'company': metrics[0].company if metrics else None,
            'metrics': [m.to_dict() for m in metrics],
            'count': len(metrics),
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
    except NotFoundException:
        raise
    except Exception as e:
        logger.exception(f"Error fetching metrics for {ticker}: {e}")
        raise ExternalApiException(
            detail="Failed to fetch miner metrics",
            error_code="MINER_METRICS_ERROR",
            details={"ticker": ticker.upper()}
        )


@router.post("/gold/miners")
async def create_miner_metric(data: Dict[str, Any]):
    """
    Submit a new quarterly report for a gold miner.

    Required fields:
    - company: Company name (e.g., "Newmont")
    - ticker: Stock ticker (e.g., "NEM")
    - period: Reporting period (e.g., "2024-Q1")
    - aisc: All-In Sustaining Cost ($/oz)
    - production: Quarterly production (Moz)
    - revenue: Revenue (Billions USD)
    - fcf: Free Cash Flow (Billions USD)
    - dividend_yield: Dividend yield (%)
    - market_cap: Market capitalization (Billions USD)

    Optional fields:
    - tier1, tier2, tier3: Jurisdiction exposure percentages
    """
    try:
        # Validate required fields
        required = ['company', 'ticker', 'period', 'aisc', 'production',
                    'revenue', 'fcf', 'dividend_yield', 'market_cap']
        missing = [f for f in required if f not in data or data[f] is None]
        if missing:
            raise ValidationException(
                detail=f"Missing required fields: {', '.join(missing)}",
                error_code="MISSING_FIELDS",
                details={"missing_fields": missing}
            )

        # Create metric object
        metric = MinerMetric(
            id=None,
            company=data['company'],
            ticker=data['ticker'].upper(),
            period=data['period'],
            aisc=float(data['aisc']),
            production=float(data['production']),
            revenue=float(data['revenue']),
            fcf=float(data['fcf']),
            dividend_yield=float(data['dividend_yield']),
            market_cap=float(data['market_cap']),
            tier1=int(data.get('tier1', 0)),
            tier2=int(data.get('tier2', 0)),
            tier3=int(data.get('tier3', 0))
        )

        db = get_miner_metrics_db()
        new_id = db.create_metric(metric)

        if new_id is None:
            raise ValidationException(
                detail=f"Duplicate entry: {metric.ticker} for {metric.period} already exists",
                error_code="DUPLICATE_ENTRY",
                details={"ticker": metric.ticker, "period": metric.period}
            )

        return {
            'success': True,
            'id': new_id,
            'message': f"Created metric for {metric.ticker} ({metric.period})",
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
    except ValidationException:
        raise
    except Exception as e:
        logger.exception(f"Error creating miner metric: {e}")
        raise ExternalApiException(
            detail="Failed to create miner metric",
            error_code="MINER_CREATE_ERROR"
        )


@router.post("/gold/miners/reseed")
async def reseed_miner_metrics():
    """
    Clear all miner metrics and reseed with built-in seed data.
    Use this to reset the database to the latest seed data (2023-2025).

    WARNING: This deletes all existing data!
    """
    try:
        db = get_miner_metrics_db()
        count = db.reseed()
        return {
            'success': True,
            'message': f"Database reseeded with {count} records",
            'count': count,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
    except Exception as e:
        logger.exception(f"Error reseeding miner metrics: {e}")
        raise ExternalApiException(
            detail="Failed to reseed gold miner metrics",
            error_code="RESEED_ERROR"
        )


# -----------------------------------------------------------------------------
# Silver Miner Metrics Endpoints
# -----------------------------------------------------------------------------

@router.get("/silver/miners")
async def get_silver_miner_metrics(
    limit: int = Query(100, ge=1, le=500, description="Maximum records to return")
):
    """
    Get all silver miner quarterly metrics.

    Returns metrics ordered by period (newest first), then by ticker.
    Used for historical trend analysis and data tables.
    """
    try:
        db = get_silver_metrics_db()
        metrics = db.get_all_metrics(limit=limit)

        return {
            'metrics': [m.to_dict() for m in metrics],
            'count': len(metrics),
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
    except Exception as e:
        logger.exception(f"Error fetching silver miner metrics: {e}")
        raise ExternalApiException(
            detail="Failed to fetch silver miner metrics",
            error_code="SILVER_MINER_METRICS_ERROR"
        )


@router.get("/silver/miners/latest")
async def get_latest_silver_miner_metrics():
    """
    Get the most recent metrics for each silver mining company.

    Returns one record per company (their latest quarterly report).
    Used for dashboard KPIs and efficiency frontier chart.
    """
    try:
        db = get_silver_metrics_db()
        metrics = db.get_latest_by_company()

        return {
            'metrics': [m.to_dict() for m in metrics],
            'count': len(metrics),
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
    except Exception as e:
        logger.exception(f"Error fetching latest silver miner metrics: {e}")
        raise ExternalApiException(
            detail="Failed to fetch latest silver miner metrics",
            error_code="SILVER_MINER_METRICS_ERROR"
        )


@router.get("/silver/miners/stats")
async def get_silver_sector_stats():
    """
    Get sector-wide statistics from the latest silver miner data.

    Returns aggregated metrics:
    - Average AISC across sector
    - Total quarterly production
    - Average dividend yield
    - Weighted Tier 1 jurisdiction exposure
    """
    try:
        db = get_silver_metrics_db()
        stats = db.get_sector_stats()

        return {
            'stats': stats,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
    except Exception as e:
        logger.exception(f"Error fetching silver sector stats: {e}")
        raise ExternalApiException(
            detail="Failed to fetch silver sector statistics",
            error_code="SECTOR_STATS_ERROR"
        )


@router.get("/silver/miners/{ticker}")
async def get_silver_miner_by_ticker(
    ticker: str = Path(..., description="Company ticker symbol (e.g., PAAS, AG, HL)")
):
    """
    Get all quarterly metrics for a specific silver mining company.

    Returns historical data for trend analysis of a single miner.
    """
    try:
        db = get_silver_metrics_db()
        metrics = db.get_metrics_by_ticker(ticker.upper())

        if not metrics:
            raise NotFoundException(
                detail=f"No data found for silver miner ticker: {ticker}",
                error_code="MINER_NOT_FOUND",
                details={"ticker": ticker.upper()}
            )

        return {
            'ticker': ticker.upper(),
            'company': metrics[0].company if metrics else None,
            'metrics': [m.to_dict() for m in metrics],
            'count': len(metrics),
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
    except NotFoundException:
        raise
    except Exception as e:
        logger.exception(f"Error fetching silver metrics for {ticker}: {e}")
        raise ExternalApiException(
            detail="Failed to fetch silver miner metrics",
            error_code="SILVER_MINER_METRICS_ERROR",
            details={"ticker": ticker.upper()}
        )


@router.post("/silver/miners")
async def create_silver_miner_metric(data: Dict[str, Any]):
    """
    Submit a new quarterly report for a silver miner.

    Required fields:
    - company: Company name (e.g., "Pan American Silver")
    - ticker: Stock ticker (e.g., "PAAS")
    - period: Reporting period (e.g., "2024-Q1")
    - aisc: All-In Sustaining Cost ($/oz)
    - production: Quarterly production (Moz)
    - revenue: Revenue (Billions USD)
    - fcf: Free Cash Flow (Billions USD)
    - dividend_yield: Dividend yield (%)
    - market_cap: Market capitalization (Billions USD)

    Optional fields:
    - tier1, tier2, tier3: Jurisdiction exposure percentages
    """
    try:
        # Validate required fields
        required = ['company', 'ticker', 'period', 'aisc', 'production',
                    'revenue', 'fcf', 'dividend_yield', 'market_cap']
        missing = [f for f in required if f not in data or data[f] is None]
        if missing:
            raise ValidationException(
                detail=f"Missing required fields: {', '.join(missing)}",
                error_code="MISSING_FIELDS",
                details={"missing_fields": missing}
            )

        # Create metric object
        metric = SilverMinerMetric(
            id=None,
            company=data['company'],
            ticker=data['ticker'].upper(),
            period=data['period'],
            aisc=float(data['aisc']),
            production=float(data['production']),
            revenue=float(data['revenue']),
            fcf=float(data['fcf']),
            dividend_yield=float(data['dividend_yield']),
            market_cap=float(data['market_cap']),
            tier1=int(data.get('tier1', 0)),
            tier2=int(data.get('tier2', 0)),
            tier3=int(data.get('tier3', 0))
        )

        db = get_silver_metrics_db()
        new_id = db.create_metric(metric)

        if new_id is None:
            raise ValidationException(
                detail=f"Duplicate entry: {metric.ticker} for {metric.period} already exists",
                error_code="DUPLICATE_ENTRY",
                details={"ticker": metric.ticker, "period": metric.period}
            )

        return {
            'success': True,
            'id': new_id,
            'message': f"Created metric for {metric.ticker} ({metric.period})",
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
    except ValidationException:
        raise
    except Exception as e:
        logger.exception(f"Error creating silver miner metric: {e}")
        raise ExternalApiException(
            detail="Failed to create silver miner metric",
            error_code="MINER_CREATE_ERROR"
        )


@router.post("/silver/miners/reseed")
async def reseed_silver_miner_metrics():
    """
    Clear all silver miner metrics and reseed with built-in seed data.
    Use this to reset the database to the latest seed data (2023-2025).

    WARNING: This deletes all existing data!
    """
    try:
        db = get_silver_metrics_db()
        count = db.reseed()
        return {
            'success': True,
            'message': f"Database reseeded with {count} records",
            'count': count,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
    except Exception as e:
        logger.exception(f"Error reseeding silver miner metrics: {e}")
        raise ExternalApiException(
            detail="Failed to reseed silver miner metrics",
            error_code="RESEED_ERROR"
        )


# -----------------------------------------------------------------------------
# Inflation-Adjusted Charts Endpoints
# -----------------------------------------------------------------------------

@router.get("/inflation/summary")
async def get_inflation_summary():
    """
    Get summary statistics for the inflation dashboard.

    Returns current CPI, M2, gold/silver prices, and key insights like:
    - What the 1980 gold peak would be in today's dollars
    - Dollar purchasing power decline since 1970
    """
    try:
        db = get_inflation_db()
        stats = db.get_summary_stats()

        return {
            'stats': stats,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
    except Exception as e:
        logger.exception(f"Error fetching inflation summary: {e}")
        raise ExternalApiException(
            detail="Failed to fetch inflation summary",
            error_code="INFLATION_DATA_ERROR"
        )


@router.get("/inflation/data")
async def get_inflation_data(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM format)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM format)")
):
    """
    Get historical inflation data (CPI, M2, gold, silver prices).

    Returns raw data points for charting. Can filter by date range.
    """
    try:
        db = get_inflation_db()
        data = db.get_all_data(start_date=start_date, end_date=end_date)

        return {
            'data': [d.to_dict() for d in data],
            'count': len(data),
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
    except Exception as e:
        logger.exception(f"Error fetching inflation data: {e}")
        raise ExternalApiException(
            detail="Failed to fetch inflation data",
            error_code="INFLATION_DATA_ERROR"
        )


@router.get("/inflation/adjusted/{metal}")
async def get_inflation_adjusted_prices(
    metal: str = Path(..., description="Metal type: 'gold' or 'silver'"),
    base_year: int = Query(2024, ge=1970, le=2025, description="Base year for adjustment")
):
    """
    Get inflation-adjusted prices for gold or silver.

    Adjusts historical prices to constant dollars for the specified base year.
    This shows the "real" price after accounting for CPI inflation.

    Example: Gold at $675 in Jan 1980 equals ~$2,800 in 2024 dollars.
    """
    if metal not in ('gold', 'silver'):
        raise ValidationException(
            detail="metal must be 'gold' or 'silver'",
            error_code="INVALID_METAL",
            details={"provided": metal, "valid_options": ["gold", "silver"]}
        )

    try:
        db = get_inflation_db()
        data = db.calculate_inflation_adjusted_prices(metal=metal, base_year=base_year)

        return {
            'metal': metal,
            'base_year': base_year,
            'data': [d.to_dict() for d in data],
            'count': len(data),
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
    except ValueError as e:
        raise ValidationException(
            detail=str(e),
            error_code="INVALID_PARAMETER"
        )
    except Exception as e:
        logger.exception(f"Error calculating adjusted prices: {e}")
        raise ExternalApiException(
            detail="Failed to calculate inflation-adjusted prices",
            error_code="INFLATION_CALCULATION_ERROR"
        )


@router.get("/inflation/m2-comparison")
async def get_m2_comparison():
    """
    Get gold/silver prices compared to M2 money supply.

    The gold/M2 ratio helps visualize if gold is cheap or expensive
    relative to money printing. A high ratio means gold is expensive
    vs the money supply; a low ratio suggests gold is undervalued.

    Includes comparison to 1980 peak ratio as benchmark.
    """
    try:
        db = get_inflation_db()
        data = db.get_m2_comparison()

        return {
            'data': [d.to_dict() for d in data],
            'count': len(data),
            'interpretation': {
                'peak_year': 1980,
                'peak_context': 'In 1980, gold was extremely expensive relative to M2 money supply',
                'current_pct_of_peak': data[-1].gold_m2_ratio_pct_of_peak if data else None,
                'implication': 'If ratio returns to 1980 peak levels, gold would need to rise significantly'
            },
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
    except Exception as e:
        print(f"Error calculating M2 comparison: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/inflation/purchasing-power")
async def get_purchasing_power(
    from_year: int = Query(1970, ge=1970, le=2020, description="Starting year for calculation")
):
    """
    Calculate dollar purchasing power decline from a given year.

    Shows how much value the US dollar has lost since the specified year.
    Useful for visualizing currency debasement over time.
    """
    try:
        db = get_inflation_db()
        result = db.calculate_purchasing_power(from_year=from_year)

        return {
            'purchasing_power': result,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
    except Exception as e:
        print(f"Error calculating purchasing power: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/inflation/reseed")
async def reseed_inflation_data():
    """
    Clear all inflation data and reseed with built-in historical data.

    WARNING: This deletes all existing data!
    """
    try:
        db = get_inflation_db()
        count = db.reseed()
        return {
            'success': True,
            'message': f"Database reseeded with {count} data points",
            'count': count,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
    except Exception as e:
        print(f"Error reseeding inflation data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/inflation/update-fred")
async def update_inflation_from_fred():
    """
    Fetch latest CPI and M2 data from FRED API and merge into the database.

    Requires FRED_API_KEY environment variable to be set.
    Gold/silver prices are not affected (FRED doesn't provide commodity spot prices).
    """
    try:
        db = get_inflation_db()
        results = db.update_from_fred()
        total = results['cpi'] + results['m2']
        if total == 0:
            return {
                'success': False,
                'message': 'No data fetched. Is FRED_API_KEY set?',
                'results': results,
            }
        return {
            'success': True,
            'message': f"Updated {results['cpi']} CPI and {results['m2']} M2 records from FRED",
            'results': results,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
    except CircuitOpenError as e:
        raise HTTPException(
            status_code=503,
            detail={
                "error": "FRED circuit breaker is OPEN",
                "retry_after_seconds": e.retry_after,
                "message": str(e),
            },
        )
    except Exception as e:
        logger.exception(f"Error updating from FRED: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/inflation/fred-circuit-breaker")
async def get_fred_circuit_breaker_status():
    """
    Return the current status of the FRED API circuit breaker.

    Useful for monitoring whether the FRED API is reachable and how many
    consecutive failures have been recorded.
    """
    return fred_circuit_breaker.status()


@router.post("/inflation/fred-circuit-breaker/reset")
async def reset_fred_circuit_breaker():
    """
    Manually reset the FRED API circuit breaker to CLOSED state.

    Use this after confirming the FRED API is reachable again, or to force
    a retry before the automatic recovery timeout elapses.
    """
    fred_circuit_breaker.reset()
    return {
        "success": True,
        "message": "FRED circuit breaker reset to CLOSED",
        "status": fred_circuit_breaker.status(),
    }


# -----------------------------------------------------------------------------
# Central Bank Gold Tracker Endpoints
# -----------------------------------------------------------------------------

@router.get("/central-banks/summary")
async def get_cb_gold_summary():
    """
    Get summary statistics for the central bank gold dashboard.

    Returns total global holdings, recent purchase activity,
    de-dollarization score, and top holder info.
    """
    try:
        db = get_cb_gold_db()
        stats = db.get_summary_stats()

        return {
            'stats': stats,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
    except Exception as e:
        print(f"Error fetching CB gold summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/central-banks/leaderboard")
async def get_cb_gold_leaderboard(
    limit: int = Query(20, ge=1, le=50, description="Number of countries to return")
):
    """
    Get country leaderboard ranked by gold holdings.

    Includes 12-month change in holdings for trend analysis.
    """
    try:
        db = get_cb_gold_db()
        rankings = db.get_leaderboard(limit=limit)

        return {
            'rankings': [r.to_dict() for r in rankings],
            'count': len(rankings),
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
    except Exception as e:
        print(f"Error fetching CB leaderboard: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/central-banks/country/{country_code}")
async def get_cb_country_history(
    country_code: str = Path(..., description="ISO 3166-1 alpha-2 country code (e.g., US, CN, RU)")
):
    """
    Get historical gold holdings for a specific country.

    Returns time series data for charting a country's accumulation.
    """
    try:
        db = get_cb_gold_db()
        history = db.get_country_history(country_code)

        if not history:
            raise HTTPException(status_code=404, detail=f"No data for country: {country_code}")

        return {
            'country_code': country_code.upper(),
            'country_name': history[0].country_name if history else country_code,
            'history': [h.to_dict() for h in history],
            'count': len(history),
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching CB history for {country_code}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/central-banks/net-purchases")
async def get_cb_net_purchases():
    """
    Get global net gold purchases by year.

    Shows whether central banks as a group are buying or selling.
    2022 was a record year at 1,082 tonnes.
    """
    try:
        db = get_cb_gold_db()
        purchases = db.get_net_purchases()

        # Calculate summary stats
        total = sum(p.tonnes for p in purchases)
        avg = total / len(purchases) if purchases else 0
        recent_avg = sum(p.tonnes for p in purchases[-5:]) / 5 if len(purchases) >= 5 else avg

        return {
            'purchases': [p.to_dict() for p in purchases],
            'count': len(purchases),
            'summary': {
                'total_tonnes': round(total, 0),
                'average_per_year': round(avg, 0),
                'recent_5yr_avg': round(recent_avg, 0),
                'peak_year': max(purchases, key=lambda x: x.tonnes).year if purchases else None,
                'peak_tonnes': max(p.tonnes for p in purchases) if purchases else 0,
            },
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
    except Exception as e:
        print(f"Error fetching CB net purchases: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/central-banks/top-buyers")
async def get_cb_top_buyers(
    n: int = Query(10, ge=1, le=30, description="Number of top buyers to return")
):
    """
    Get countries with the largest gold accumulation in the past 12 months.
    """
    try:
        db = get_cb_gold_db()
        buyers = db.get_top_buyers(n=n)

        return {
            'buyers': [b.to_dict() for b in buyers],
            'count': len(buyers),
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
    except Exception as e:
        print(f"Error fetching top buyers: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/central-banks/top-sellers")
async def get_cb_top_sellers(
    n: int = Query(10, ge=1, le=30, description="Number of top sellers to return")
):
    """
    Get countries that have reduced gold holdings in the past 12 months.
    """
    try:
        db = get_cb_gold_db()
        sellers = db.get_top_sellers(n=n)

        return {
            'sellers': [s.to_dict() for s in sellers],
            'count': len(sellers),
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
    except Exception as e:
        print(f"Error fetching top sellers: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/central-banks/dedollarization")
async def get_dedollarization_score():
    """
    Get the composite de-dollarization score (0-100).

    Higher scores indicate stronger trend of central banks
    diversifying away from USD reserves into gold.
    """
    try:
        db = get_cb_gold_db()
        score = db.calculate_dedollarization_score()

        return {
            'score': score.to_dict(),
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
    except Exception as e:
        print(f"Error calculating de-dollarization score: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/central-banks/reseed")
async def reseed_cb_gold_data():
    """
    Clear all central bank gold data and reseed with built-in data.

    WARNING: This deletes all existing data!
    """
    try:
        db = get_cb_gold_db()
        count = db.reseed()
        return {
            'success': True,
            'message': f"Database reseeded with {count} holdings records",
            'count': count,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
    except Exception as e:
        print(f"Error reseeding CB gold data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# -----------------------------------------------------------------------------
# Miner Earnings Calendar Endpoints
# -----------------------------------------------------------------------------

@router.get("/earnings/calendar")
async def get_earnings_calendar(
    month: Optional[str] = Query(None, description="Month in YYYY-MM format (default: current month)")
):
    """
    Get earnings events for a specific month.

    Returns all gold and silver miner earnings scheduled for the month.
    Use for displaying a calendar view of upcoming earnings.
    """
    try:
        db = get_earnings_db()
        events = db.get_calendar(month=month)

        return {
            'events': [e.to_dict() for e in events],
            'count': len(events),
            'month': month or datetime.now().strftime('%Y-%m'),
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
    except Exception as e:
        print(f"Error fetching earnings calendar: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/earnings/upcoming")
async def get_upcoming_earnings(
    days: int = Query(30, ge=1, le=90, description="Number of days to look ahead")
):
    """
    Get earnings events in the next N days.

    Returns upcoming earnings sorted by date.
    Includes countdown information and estimates.
    """
    try:
        db = get_earnings_db()
        events = db.get_upcoming(days=days)

        # Add countdown days
        today = datetime.now().date()
        events_with_countdown = []
        for event in events:
            event_dict = event.to_dict()
            try:
                event_date = datetime.strptime(event.earnings_date, '%Y-%m-%d').date()
                event_dict['days_until'] = (event_date - today).days
            except ValueError:
                event_dict['days_until'] = None
            events_with_countdown.append(event_dict)

        return {
            'events': events_with_countdown,
            'count': len(events),
            'days_ahead': days,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
    except Exception as e:
        print(f"Error fetching upcoming earnings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/earnings/ticker/{ticker}")
async def get_earnings_by_ticker(
    ticker: str = Path(..., description="Company ticker symbol (e.g., NEM, PAAS)")
):
    """
    Get all earnings events for a specific company.

    Returns historical and upcoming earnings for trend analysis.
    """
    try:
        db = get_earnings_db()
        events = db.get_by_ticker(ticker)

        if not events:
            raise HTTPException(status_code=404, detail=f"No earnings data for ticker: {ticker}")

        return {
            'ticker': ticker.upper(),
            'company_name': events[0].company_name if events else None,
            'metal': events[0].metal if events else None,
            'events': [e.to_dict() for e in events],
            'count': len(events),
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching earnings for {ticker}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/earnings/stats/{ticker}")
async def get_earnings_stats(
    ticker: str = Path(..., description="Company ticker symbol")
):
    """
    Get beat/miss statistics for a specific company.

    Returns historical EPS, revenue, production, and AISC beat rates,
    plus average price reactions on earnings.
    """
    try:
        db = get_earnings_db()
        stats = db.get_stats(ticker)

        if not stats:
            raise HTTPException(status_code=404, detail=f"No earnings stats for ticker: {ticker}")

        return {
            'stats': stats.to_dict(),
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching earnings stats for {ticker}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/earnings/sector-stats")
async def get_sector_earnings_stats(
    metal: Optional[str] = Query(None, description="Filter by metal: 'gold' or 'silver'")
):
    """
    Get sector-wide earnings statistics.

    Returns aggregate beat rates, next upcoming earnings,
    and average price reactions across all tracked miners.
    """
    if metal and metal not in ('gold', 'silver'):
        raise HTTPException(status_code=400, detail="metal must be 'gold' or 'silver'")

    try:
        db = get_earnings_db()
        stats = db.get_sector_stats(metal=metal)

        return {
            'stats': stats.to_dict(),
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
    except Exception as e:
        print(f"Error fetching sector earnings stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/earnings")
async def create_earnings_event(data: Dict[str, Any]):
    """
    Create a new earnings event (manual entry).

    Required fields:
    - ticker: Stock ticker (e.g., "NEM")
    - metal: 'gold' or 'silver'
    - company_name: Full company name
    - quarter: Period (e.g., "Q1 2025")
    - earnings_date: Date in YYYY-MM-DD format
    - time_of_day: 'pre-market', 'after-hours', or 'during-market'
    - is_confirmed: Whether date is confirmed vs estimated
    """
    try:
        required = ['ticker', 'metal', 'company_name', 'quarter', 'earnings_date', 'time_of_day', 'is_confirmed']
        missing = [f for f in required if f not in data]
        if missing:
            raise HTTPException(
                status_code=400,
                detail=f"Missing required fields: {', '.join(missing)}"
            )

        if data['metal'] not in ('gold', 'silver'):
            raise HTTPException(status_code=400, detail="metal must be 'gold' or 'silver'")

        event = EarningsEvent(
            id=None,
            ticker=data['ticker'].upper(),
            metal=data['metal'],
            company_name=data['company_name'],
            quarter=data['quarter'],
            earnings_date=data['earnings_date'],
            time_of_day=data['time_of_day'],
            is_confirmed=bool(data['is_confirmed']),
            eps_actual=data.get('eps_actual'),
            eps_estimate=data.get('eps_estimate'),
            revenue_actual=data.get('revenue_actual'),
            revenue_estimate=data.get('revenue_estimate'),
            production_actual=data.get('production_actual'),
            production_guidance=data.get('production_guidance'),
            aisc_actual=data.get('aisc_actual'),
            aisc_guidance=data.get('aisc_guidance'),
            price_before=data.get('price_before'),
            price_1d_after=data.get('price_1d_after'),
            price_5d_after=data.get('price_5d_after'),
            price_30d_after=data.get('price_30d_after'),
            transcript_url=data.get('transcript_url'),
            press_release_url=data.get('press_release_url'),
        )

        db = get_earnings_db()
        new_id = db.create_event(event)

        if new_id is None:
            raise HTTPException(
                status_code=409,
                detail=f"Duplicate: {event.ticker} {event.quarter} already exists"
            )

        return {
            'success': True,
            'id': new_id,
            'message': f"Created earnings event for {event.ticker} ({event.quarter})",
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error creating earnings event: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/earnings/{event_id}")
async def update_earnings_event(
    event_id: int = Path(..., description="Earnings event ID"),
    data: Dict[str, Any] = None
):
    """
    Update an existing earnings event.

    Use this to add actual results after earnings are reported.
    """
    try:
        if not data:
            raise HTTPException(status_code=400, detail="No update data provided")

        db = get_earnings_db()
        success = db.update_event(event_id, data)

        if not success:
            raise HTTPException(status_code=404, detail=f"Event {event_id} not found or no valid updates")

        return {
            'success': True,
            'message': f"Updated earnings event {event_id}",
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error updating earnings event: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/earnings/refresh")
async def refresh_earnings_from_edgar():
    """
    Refresh earnings data from SEC EDGAR without clearing existing records.

    Fetches the latest quarterly EPS and revenue from real SEC filings.
    Adds new quarters and updates SEC-sourced fields on existing records.
    Records marked as data_source='manual' are not overwritten.
    """
    try:
        db = get_earnings_db()
        result = db.refresh_from_edgar()
        return {
            'success': True,
            'message': (
                f"SEC EDGAR refresh complete: "
                f"{result['inserted']} new records, {result['updated']} updated"
            ),
            'inserted': result['inserted'],
            'updated': result['updated'],
            'data_source': 'sec_edgar',
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
    except Exception as e:
        print(f"Error refreshing earnings from SEC EDGAR: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/earnings/reseed")
async def reseed_earnings_data():
    """
    Clear all earnings data and re-populate from SEC EDGAR.

    WARNING: This deletes all existing records including manual corrections!
    Use /earnings/refresh to update without destroying manual data.
    """
    try:
        db = get_earnings_db()
        count = db.reseed()
        return {
            'success': True,
            'message': f"Database reseeded with {count} earnings events from SEC EDGAR",
            'count': count,
            'data_source': 'sec_edgar',
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
    except Exception as e:
        print(f"Error reseeding earnings data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# -----------------------------------------------------------------------------
# Physical Premium Tracker Endpoints
# -----------------------------------------------------------------------------

@router.get("/premiums/summary")
async def get_premiums_summary():
    """
    Get summary statistics for the premium tracker dashboard.

    Returns spot prices, average premiums by metal, and data freshness.
    """
    try:
        db = get_premium_db()
        stats = db.get_summary_stats()

        return {
            'stats': stats,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
    except Exception as e:
        print(f"Error fetching premiums summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/premiums/products")
async def get_premium_products(
    metal: Optional[str] = Query(None, description="Filter by metal: 'gold' or 'silver'")
):
    """
    Get all tracked products.

    Returns product catalog with typical premium ranges.
    """
    if metal and metal not in ('gold', 'silver'):
        raise HTTPException(status_code=400, detail="metal must be 'gold' or 'silver'")

    try:
        db = get_premium_db()
        products = db.get_products(metal=metal)

        return {
            'products': [p.to_dict() for p in products],
            'count': len(products),
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
    except Exception as e:
        print(f"Error fetching products: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/premiums/products/{product_id}")
async def get_premium_product(
    product_id: str = Path(..., description="Product ID (e.g., 'silver-eagle-1oz')")
):
    """
    Get details for a specific product.
    """
    try:
        db = get_premium_db()
        product = db.get_product(product_id)

        if not product:
            raise HTTPException(status_code=404, detail=f"Product not found: {product_id}")

        return {
            'product': product.to_dict(),
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching product {product_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/premiums/dealers")
async def get_premium_dealers():
    """
    Get all active dealers.
    """
    try:
        db = get_premium_db()
        dealers = db.get_dealers()

        return {
            'dealers': [d.to_dict() for d in dealers],
            'count': len(dealers),
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
    except Exception as e:
        print(f"Error fetching dealers: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/premiums/compare/{product_id}")
async def compare_product_prices(
    product_id: str = Path(..., description="Product ID to compare")
):
    """
    Compare prices for a product across all dealers.

    Returns prices sorted by total cost with best deal highlighted.
    """
    try:
        db = get_premium_db()
        comparison = db.get_comparison(product_id)

        if not comparison:
            raise HTTPException(status_code=404, detail=f"No prices found for: {product_id}")

        return {
            'comparison': comparison.to_dict(),
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error comparing prices for {product_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/premiums/best-deals")
async def get_best_deals(
    metal: Optional[str] = Query(None, description="Filter by metal: 'gold' or 'silver'"),
    limit: int = Query(10, ge=1, le=50, description="Number of deals to return")
):
    """
    Get products with the lowest current premiums.

    Returns the best value products available right now.
    """
    if metal and metal not in ('gold', 'silver'):
        raise HTTPException(status_code=400, detail="metal must be 'gold' or 'silver'")

    try:
        db = get_premium_db()
        deals = db.get_best_deals(metal=metal, limit=limit)

        return {
            'deals': deals,
            'count': len(deals),
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
    except Exception as e:
        print(f"Error fetching best deals: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/premiums/leaderboard")
async def get_dealer_leaderboard(
    metal: Optional[str] = Query(None, description="Filter by metal: 'gold' or 'silver'")
):
    """
    Get dealers ranked by average premium.

    Lower average premium = better value for customers.
    """
    if metal and metal not in ('gold', 'silver'):
        raise HTTPException(status_code=400, detail="metal must be 'gold' or 'silver'")

    try:
        db = get_premium_db()
        rankings = db.get_dealer_leaderboard(metal=metal)

        return {
            'rankings': [r.to_dict() for r in rankings],
            'count': len(rankings),
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
    except Exception as e:
        print(f"Error fetching dealer leaderboard: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/premiums/price")
async def add_price(data: Dict[str, Any]):
    """
    Add a new price entry (manual update).

    Required fields:
    - product_id: Product ID
    - dealer_id: Dealer ID
    - price: Current price
    - spot_price: Current spot price for the metal

    Optional fields:
    - in_stock: Whether product is in stock (default: true)
    - product_url: URL to product page
    """
    try:
        required = ['product_id', 'dealer_id', 'price', 'spot_price']
        missing = [f for f in required if f not in data]
        if missing:
            raise HTTPException(
                status_code=400,
                detail=f"Missing required fields: {', '.join(missing)}"
            )

        db = get_premium_db()
        new_id = db.add_price(
            product_id=data['product_id'],
            dealer_id=data['dealer_id'],
            price=float(data['price']),
            spot_price=float(data['spot_price']),
            in_stock=data.get('in_stock', True),
            product_url=data.get('product_url'),
        )

        if new_id is None:
            raise HTTPException(status_code=400, detail="Invalid product_id")

        return {
            'success': True,
            'id': new_id,
            'message': f"Price added for {data['product_id']} at {data['dealer_id']}",
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error adding price: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/premiums/reseed")
async def reseed_premium_data():
    """
    Clear all premium data and reseed with sample data.

    WARNING: This deletes all existing data!
    """
    try:
        db = get_premium_db()
        count = db.reseed()
        return {
            'success': True,
            'message': f"Database reseeded with {count} price entries",
            'count': count,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
    except Exception as e:
        print(f"Error reseeding premium data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# CLASSIFICATION CORRECTIONS ENDPOINTS
# =============================================================================

from core.corrections import get_corrections_manager, CorrectionStatus
from .schemas import (
    CorrectionSubmitRequest,
    CorrectionResponse,
    CorrectionsListResponse,
    CorrectionStatsResponse
)


@router.post("/corrections", response_model=CorrectionResponse)
async def submit_correction(request: CorrectionSubmitRequest):
    """
    Submit a classification correction.

    Users can suggest corrections when they disagree with an asset's
    auto-classification. Corrections are stored and used to improve
    the classification system.

    Valid categories: hard_money, algo, dollars, shitcoin
    """
    try:
        manager = get_corrections_manager()

        # Validate category
        valid_categories = ['hard_money', 'algo', 'dollars', 'shitcoin']
        if request.corrected_category not in valid_categories:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid category. Must be one of: {valid_categories}"
            )

        correction = manager.submit_correction(
            asset_id=request.asset_id,
            asset_name=request.asset_name,
            ticker=request.ticker,
            original_category=request.original_category,
            corrected_category=request.corrected_category,
            reason=request.reason,
            submitted_by=request.submitted_by
        )

        return CorrectionResponse(
            success=True,
            message=f"Correction submitted for {request.ticker} ({request.asset_id})",
            correction=correction.model_dump()
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"Error submitting correction: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/corrections", response_model=CorrectionsListResponse)
async def list_corrections(
    status: Optional[str] = Query(None, description="Filter by status: active, pending, approved, rejected")
):
    """
    List all submitted corrections.

    Optionally filter by status.
    """
    try:
        manager = get_corrections_manager()

        status_filter = None
        if status:
            try:
                status_filter = CorrectionStatus(status)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid status. Must be one of: active, pending, approved, rejected"
                )

        corrections = manager.get_all_corrections(status=status_filter)

        return CorrectionsListResponse(
            corrections=[c.model_dump() for c in corrections],
            count=len(corrections)
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error listing corrections: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/corrections/stats", response_model=CorrectionStatsResponse)
async def get_correction_stats():
    """
    Get statistics about the corrections system.

    Returns counts by status, most corrected category, and recent corrections.
    """
    try:
        manager = get_corrections_manager()
        stats = manager.get_stats()
        return CorrectionStatsResponse(**stats.model_dump())
    except Exception as e:
        print(f"Error getting correction stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/corrections/{asset_id}")
async def get_correction(asset_id: str = Path(..., description="The ASA ID", max_length=20)):
    """
    Get the correction for a specific asset.
    """
    try:
        manager = get_corrections_manager()
        corrections = manager.get_all_corrections()
        correction = next((c for c in corrections if c.asset_id == asset_id), None)

        if not correction:
            raise HTTPException(
                status_code=404,
                detail=f"No correction found for asset {asset_id}"
            )

        return correction.model_dump()
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error getting correction: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/corrections/{asset_id}")
async def delete_correction(asset_id: str = Path(..., description="The ASA ID", max_length=20)):
    """
    Delete a correction.
    """
    try:
        manager = get_corrections_manager()
        deleted = manager.delete_correction(asset_id)

        if not deleted:
            raise HTTPException(
                status_code=404,
                detail=f"No correction found for asset {asset_id}"
            )

        return {
            'success': True,
            'message': f"Correction deleted for asset {asset_id}"
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error deleting correction: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/corrections/export/csv")
async def export_corrections_csv():
    """
    Export approved corrections in CSV format.

    Useful for reviewing corrections before adding them to the main
    asset_classification.csv file.
    """
    try:
        manager = get_corrections_manager()
        csv_content = manager.export_to_csv_format()

        return {
            'csv': csv_content,
            'instructions': "Add approved lines to data/asset_classification.csv"
        }
    except Exception as e:
        print(f"Error exporting corrections: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Wallet Monitoring Endpoints
# =============================================================================

@router.get("/monitor/wallets")
async def list_monitored_wallets():
    """
    List all monitored wallets with their configurations.
    """
    from core.wallet_monitor import get_wallet_monitor

    monitor = get_wallet_monitor()
    wallets = monitor.list_wallets()

    return {
        "wallets": [
            {
                "address": w.address,
                "label": w.label,
                "min_sovereignty_score": w.min_sovereignty_score,
                "monthly_fixed_expenses": w.monthly_fixed_expenses,
                "alert_on_drops": w.alert_on_drops,
                "alert_on_milestones": w.alert_on_milestones,
                "max_concentration": w.max_concentration,
                "last_checked": w.last_checked.isoformat() if w.last_checked else None,
                "last_score": w.last_score,
                "created_at": w.created_at.isoformat()
            }
            for w in wallets
        ],
        "count": len(wallets)
    }


@router.post("/monitor/wallets")
async def add_monitored_wallet(request: Dict[str, Any]):
    """
    Add a wallet to be monitored.

    Request body:
    - address: Algorand wallet address (required)
    - label: User-friendly name
    - min_sovereignty_score: Alert threshold (default 1.0)
    - monthly_fixed_expenses: For sovereignty calculation
    - alert_on_drops: Alert on score decreases (default true)
    - alert_on_milestones: Alert on milestones (default true)
    - max_concentration: Max single-asset concentration (default 0.5)
    """
    from core.wallet_monitor import get_wallet_monitor

    address = request.get('address')
    if not address:
        raise ValidationException(
            detail="Address is required",
            error_code="MISSING_ADDRESS",
            details={"field": "address"}
        )

    validate_algorand_address(address)

    monitor = get_wallet_monitor()
    config = monitor.add_wallet(
        address=address,
        label=request.get('label', ''),
        min_sovereignty_score=request.get('min_sovereignty_score', 1.0),
        monthly_fixed_expenses=request.get('monthly_fixed_expenses', 0.0),
        alert_on_drops=request.get('alert_on_drops', True),
        alert_on_milestones=request.get('alert_on_milestones', True),
        max_concentration=request.get('max_concentration', 0.5)
    )

    return {
        "success": True,
        "message": f"Wallet {config.label} added to monitoring",
        "wallet": {
            "address": config.address,
            "label": config.label,
            "min_sovereignty_score": config.min_sovereignty_score
        }
    }


@router.delete("/monitor/wallets/{address}")
async def remove_monitored_wallet(address: str):
    """
    Remove a wallet from monitoring.
    """
    from core.wallet_monitor import get_wallet_monitor

    monitor = get_wallet_monitor()
    removed = monitor.remove_wallet(address)

    if not removed:
        raise NotFoundException(
            detail="Wallet not found in monitoring list",
            error_code="WALLET_NOT_MONITORED",
            details={"address": address}
        )

    return {
        "success": True,
        "message": f"Wallet {address[:8]}... removed from monitoring"
    }


@router.post("/monitor/wallets/{address}/check")
async def check_monitored_wallet(address: str, use_local_node: bool = Query(False)):
    """
    Check a monitored wallet and generate alerts.

    Returns list of alerts for this wallet based on configured thresholds.
    """
    from core.wallet_monitor import get_wallet_monitor

    validate_algorand_address(address)

    monitor = get_wallet_monitor()
    if not monitor.get_wallet(address):
        raise NotFoundException(
            detail="Wallet not found in monitoring list",
            error_code="WALLET_NOT_MONITORED",
            details={"address": address}
        )

    # Create analyzer functions
    def analyzer_fn(addr):
        analyzer = AlgorandSovereigntyAnalyzer(use_local_node=use_local_node)
        return analyzer.analyze_wallet(addr)

    def sovereignty_fn(categories, expenses):
        analyzer = AlgorandSovereigntyAnalyzer(use_local_node=use_local_node)
        return analyzer.calculate_sovereignty_metrics(categories, expenses)

    alerts = monitor.check_wallet(address, analyzer_fn, sovereignty_fn)

    return {
        "address": address,
        "alerts": [alert.to_dict() for alert in alerts],
        "alert_count": len(alerts)
    }


@router.get("/monitor/arbitrage")
async def get_arbitrage_opportunities():
    """
    Get current gold/silver/BTC arbitrage opportunities.

    Compares Algorand DEX prices (MELD Gold$/Silver$, goBTC) to spot prices
    and identifies when premiums or discounts create trading opportunities.
    """
    from core.wallet_monitor import get_wallet_monitor

    monitor = get_wallet_monitor()
    opportunities = monitor.check_arbitrage_opportunities()

    return {
        "opportunities": [opp.to_dict() for opp in opportunities],
        "count": len(opportunities),
        "thresholds": {
            "gold_premium": monitor.GOLD_PREMIUM_THRESHOLD,
            "gold_discount": monitor.GOLD_DISCOUNT_THRESHOLD,
            "silver_premium": monitor.SILVER_PREMIUM_THRESHOLD,
            "silver_discount": monitor.SILVER_DISCOUNT_THRESHOLD,
            "btc_premium": monitor.BTC_PREMIUM_THRESHOLD,
            "btc_discount": monitor.BTC_DISCOUNT_THRESHOLD
        }
    }


@router.get("/monitor/summary")
async def get_monitoring_summary():
    """
    Get a summary of the monitoring system status.

    Returns wallet count, wallets needing check, and active arbitrage opportunities.
    """
    from core.wallet_monitor import get_wallet_monitor

    monitor = get_wallet_monitor()
    return monitor.get_monitoring_summary()


# -----------------------------------------------------------------------------
# Cache & Rate Limit Management Endpoints
# -----------------------------------------------------------------------------

@router.get(
    "/admin/cache/stats",
    summary="Get cache statistics",
    description="""
Get comprehensive statistics about the caching system.

## Response Fields

### Overall Statistics
- `hits`: Total cache hits
- `misses`: Total cache misses
- `sets`: Total cache set operations
- `evictions`: Entries removed due to size limits
- `expirations`: Entries removed due to TTL expiry
- `invalidations`: Entries manually invalidated
- `hit_rate`: Hit rate as decimal (0-1)

### By Category
Statistics broken down by cache category:
- `price_live`: Live price data (60s TTL)
- `price_hist`: Historical prices (1h TTL)
- `analysis`: Wallet analysis results (15min TTL)
- `network`: Network statistics (60s TTL)
- `classification`: Asset classifications (1h TTL)
- `arbitrage`: Premium/arbitrage data (2min TTL)

### Utilization
- `size`: Current number of cached entries
- `max_size`: Maximum cache capacity
- `utilization`: Current usage as percentage

## Use Cases

- Monitor cache efficiency
- Identify if cache size needs adjustment
- Debug cache-related issues
- Performance tuning
    """,
    response_description="Cache statistics with hit rates and category breakdowns",
    tags=["Admin"]
)
async def get_cache_stats():
    """
    Get comprehensive statistics about the caching system.

    Returns hit/miss rates, eviction counts, and per-category breakdowns.
    Useful for monitoring cache efficiency and tuning configuration.
    """
    cache = get_cache()
    stats = cache.get_stats()

    return {
        "cache_stats": stats,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }


@router.get(
    "/admin/rate-limit/stats",
    summary="Get rate limiting statistics",
    description="""
Get statistics about the rate limiting system.

## Response Fields

### Overall Statistics
- `total_requests`: Total requests processed
- `allowed_requests`: Requests that passed rate limiting
- `blocked_requests`: Requests blocked by rate limits
- `blocked_by_ip`: Blocks due to per-IP limits
- `blocked_by_wallet`: Blocks due to per-wallet limits
- `blocked_by_burst`: Blocks due to burst limits
- `block_rate`: Percentage of blocked requests

### By Tier
Statistics for each rate limit tier:
- `analyze`: Wallet analysis endpoints (30/min)
- `ai_advice`: AI coaching endpoints (10/min)
- `history`: Historical data endpoints (60/min)
- `network`: Network stats endpoints (60/min)
- `default`: All other endpoints (100/min)

### Active Tracking
- `active_clients`: Number of IPs being tracked
- `tracked_wallets`: Number of wallets being tracked

## Use Cases

- Monitor for abuse patterns
- Identify if rate limits need adjustment
- Debug rate limiting issues
- Security monitoring
    """,
    response_description="Rate limiting statistics with tier breakdowns",
    tags=["Admin"]
)
async def get_rate_limit_stats():
    """
    Get statistics about the rate limiting system.

    Returns request counts, block rates, and per-tier breakdowns.
    Useful for monitoring abuse patterns and tuning rate limits.
    """
    from .security import get_rate_limiter

    limiter = get_rate_limiter()
    stats = limiter.get_stats()

    return {
        "rate_limit_stats": stats,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }


@router.post(
    "/admin/cache/invalidate",
    summary="Invalidate cache entries",
    description="""
Manually invalidate cache entries for cache management.

## Invalidation Modes

### By Address
Invalidate analysis cache for a specific wallet:
```json
{"address": "ABC...XYZ"}
```

### By Category
Invalidate all entries in a category:
```json
{"category": "price_live"}
```

Valid categories: `price_live`, `price_hist`, `analysis`, `network`, `classification`, `arbitrage`, `general`

### All Analyses
Clear all wallet analysis caches:
```json
{"all_analyses": true}
```

### All Prices
Clear all price caches:
```json
{"all_prices": true}
```

### Clear All
Clear the entire cache (use with caution):
```json
{"clear_all": true}
```

## Use Cases

- Force refresh after data updates
- Clear stale data during maintenance
- Debug cache issues
- Post-deployment cache clearing
    """,
    response_description="Number of cache entries invalidated",
    tags=["Admin"]
)
async def invalidate_cache(request: Dict[str, Any]):
    """
    Manually invalidate cache entries.

    Supports invalidation by address, category, or clearing all entries.
    Returns the number of entries invalidated.
    """
    cache = get_cache()
    invalidated = 0

    if request.get("address"):
        # Invalidate specific wallet analysis
        address = request["address"]
        if cache.invalidate_analysis(address):
            invalidated = 1

    elif request.get("category"):
        # Invalidate by category
        category_name = request["category"]
        try:
            category = CacheCategory(category_name)
            invalidated = cache._backend.invalidate_category(category)
        except ValueError:
            raise ValidationException(
                detail=f"Invalid cache category: {category_name}",
                error_code="INVALID_CATEGORY",
                details={
                    "provided": category_name,
                    "valid_categories": [c.value for c in CacheCategory]
                }
            )

    elif request.get("all_analyses"):
        # Invalidate all wallet analyses
        invalidated = cache.invalidate_all_analyses()

    elif request.get("all_prices"):
        # Invalidate all price cache
        invalidated = cache.invalidate_prices()

    elif request.get("clear_all"):
        # Clear entire cache
        invalidated = cache.clear_all()

    else:
        raise ValidationException(
            detail="No invalidation target specified",
            error_code="MISSING_TARGET",
            details={
                "valid_options": [
                    "address",
                    "category",
                    "all_analyses",
                    "all_prices",
                    "clear_all"
                ]
            }
        )

    return {
        "success": True,
        "invalidated_count": invalidated,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }


@router.get(
    "/admin/cache/entry/{key}",
    summary="Get cache entry details",
    description="""
Get detailed information about a specific cache entry (for debugging).

Returns:
- Key and category
- Creation and expiration timestamps
- Remaining TTL
- Hit count
- Whether entry is expired
    """,
    response_description="Cache entry details or null if not found",
    tags=["Admin"]
)
async def get_cache_entry(
    key: str,
    category: str = Query("general", description="Cache category")
):
    """
    Get detailed information about a specific cache entry.

    Useful for debugging cache behavior and TTL issues.
    """
    cache = get_cache()

    try:
        cat = CacheCategory(category)
    except ValueError:
        raise ValidationException(
            detail=f"Invalid cache category: {category}",
            error_code="INVALID_CATEGORY",
            details={"valid_categories": [c.value for c in CacheCategory]}
        )

    entry_info = cache._backend.get_entry_info(key, cat)

    if entry_info is None:
        return {
            "found": False,
            "key": key,
            "category": category,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }

    return {
        "found": True,
        "entry": entry_info,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }

# -------------------------------------------------------------------------
# AI Sovereignty Advisor
# -------------------------------------------------------------------------

@router.post("/advisor")
async def get_advisor_analysis(request: AdvisorRequest):
    """
    Analyze a wallet and return structured sovereignty improvement advice.

    Runs full wallet analysis then generates AI-powered recommendations.
    """
    from core.advisor import generate_sovereignty_advice

    validate_algorand_address(request.address)

    # Run analysis
    try:
        analyzer = AlgorandSovereigntyAnalyzer(use_local_node=False)
        categories = analyzer.analyze_wallet(request.address)
    except requests.exceptions.Timeout:
        raise TimeoutException(
            detail="Algorand API timed out during wallet analysis",
            error_code="ALGORAND_TIMEOUT",
            service="algorand"
        )
    except requests.exceptions.ConnectionError as e:
        logger.error(f"Algorand API connection error: {e}")
        raise AlgorandApiException(
            detail="Cannot connect to Algorand network",
            error_code="ALGORAND_CONNECTION_ERROR"
        )

    if categories is None:
        raise NotFoundException(
            detail="Wallet not found or has no assets",
            error_code="WALLET_NOT_FOUND",
            details={"address": request.address[:10] + "..."}
        )

    # Calculate sovereignty data if expenses provided
    sovereignty_data = None
    if request.monthly_fixed_expenses and request.monthly_fixed_expenses > 0:
        sovereignty_data = analyzer.calculate_sovereignty_metrics(
            categories, request.monthly_fixed_expenses
        )

    analysis_dict = {
        "address": request.address,
        "is_participating": analyzer.last_is_participating,
        "hard_money_algo": analyzer.last_hard_money_algo,
        "categories": categories,
        "sovereignty_data": sovereignty_data.dict() if sovereignty_data else None,
    }

    # Generate advice
    try:
        advice = generate_sovereignty_advice(analysis_dict)
    except ValueError as e:
        logger.error(f"Advisor config error: {e}")
        raise ServiceUnavailableException(
            detail="AI advisor not configured",
            error_code="ADVISOR_NOT_CONFIGURED",
            details={"error": str(e)}
        )
    except Exception as e:
        logger.exception(f"Advisor generation failed: {e}")
        raise ExternalApiException(
            detail="AI advisor failed to generate advice",
            error_code="ADVISOR_ERROR",
            details={"error_type": type(e).__name__}
        )

    return {
        "analysis": {
            "address": request.address,
            "is_participating": analyzer.last_is_participating,
            "hard_money_algo": analyzer.last_hard_money_algo,
            "categories": categories,
            "sovereignty_data": sovereignty_data,
        },
        "advice": advice,
    }


@router.get("/advisor/{wallet_address}")
async def get_advisor_for_address(
    wallet_address: str = Path(..., description="Algorand wallet address"),
    monthly_fixed_expenses: Optional[float] = Query(None, description="Monthly fixed expenses"),
):
    """
    Get sovereignty advice for a wallet address via GET.

    Convenience endpoint that accepts address as a path parameter.
    """
    from .schemas import AdvisorRequest

    request = AdvisorRequest(
        address=wallet_address,
        monthly_fixed_expenses=monthly_fixed_expenses,
    )
    return await get_advisor_analysis(request)


# =============================================================================
# Async Analysis Jobs
# =============================================================================

from fastapi import BackgroundTasks
from core.jobs import get_job_store, JobStatus
from .schemas import AsyncAnalyzeRequest, AsyncAnalyzeResponse, JobStatusResponse


def _run_analysis_job(job_id: str, address: str, monthly_expenses: Optional[float]) -> None:
    """Background task that runs wallet analysis and updates the job store."""
    store = get_job_store()
    store.update_job(job_id, status=JobStatus.PROCESSING, progress_message="Fetching wallet data...")

    try:
        analyzer = AlgorandSovereigntyAnalyzer(use_local_node=False)

        # Check cache first
        cached = get_cached_analysis(address)
        if cached:
            categories = cached['categories']
            is_participating = cached['is_participating']
            hard_money_algo = cached['hard_money_algo']
            participation_info = cached.get('participation_info')
        else:
            store.update_job(job_id, progress_message="Analyzing wallet assets...")
            categories = analyzer.analyze_wallet(address)
            if not categories:
                store.update_job(job_id, status=JobStatus.FAILED, error="Wallet not found or contains no assets")
                return

            is_participating = analyzer.last_is_participating
            hard_money_algo = analyzer.last_hard_money_algo
            participation_info = analyzer.last_participation_info

            # Cache the result
            cache_analysis(address, {
                'address': address,
                'is_participating': is_participating,
                'hard_money_algo': hard_money_algo,
                'categories': categories,
                'participation_info': participation_info,
            })

        store.update_job(job_id, progress_message="Calculating sovereignty metrics...")

        sovereignty_data = None
        if monthly_expenses:
            sovereignty_data = analyzer.calculate_sovereignty_metrics(categories, monthly_expenses)

        result = {
            "address": address,
            "is_participating": is_participating,
            "hard_money_algo": hard_money_algo,
            "categories": categories,
            "sovereignty_data": sovereignty_data.model_dump() if sovereignty_data else None,
            "participation_info": participation_info,
        }

        store.update_job(job_id, status=JobStatus.COMPLETED, result=result, progress_message="Analysis complete")

    except Exception as e:
        logger.exception(f"Async analysis job {job_id} failed: {e}")
        store.update_job(job_id, status=JobStatus.FAILED, error=str(e))


@router.post(
    "/analyze/async",
    response_model=AsyncAnalyzeResponse,
    summary="Start async wallet analysis",
    description="Submit a wallet for background analysis. Returns a job ID for polling.",
    tags=["Wallet Analysis"],
)
async def analyze_wallet_async(request: AsyncAnalyzeRequest, background_tasks: BackgroundTasks):
    """Start an async wallet analysis job."""
    validate_algorand_address(request.address)

    store = get_job_store()
    job = store.create_job(request.address)

    background_tasks.add_task(
        _run_analysis_job,
        job.id,
        request.address,
        request.monthly_fixed_expenses,
    )

    return AsyncAnalyzeResponse(
        job_id=job.id,
        status=job.status.value,
        poll_url=f"/api/v1/jobs/{job.id}",
    )


@router.get(
    "/jobs/{job_id}",
    response_model=JobStatusResponse,
    summary="Get job status",
    description="Poll for the status of a background analysis job.",
    tags=["Jobs"],
)
async def get_job_status(job_id: str = Path(..., description="Job ID from async analyze")):
    """Get the status of a background job."""
    store = get_job_store()
    job = store.get_job(job_id)

    if not job:
        raise NotFoundException(
            detail="Job not found",
            error_code="JOB_NOT_FOUND",
            details={"job_id": job_id},
        )

    return JobStatusResponse(**job.to_dict())
