import algosdk.encoding

from pydantic import BaseModel, Field, field_validator
from typing import List, Dict, Any, Optional
from datetime import datetime
from core.models import AssetCategory, SovereigntyData, AssetPage, PaginatedAssets
from core.history import SovereigntySnapshot


VALID_CATEGORIES = {"hard_money", "algo", "dollars", "shitcoin"}


def validate_algorand_address(address: str) -> str:
    """Validate an Algorand address: 58 chars, base32, valid checksum."""
    if len(address) != 58:
        raise ValueError("Algorand address must be exactly 58 characters")
    try:
        algosdk.encoding.decode_address(address)
    except Exception:
        raise ValueError("Algorand address is invalid (bad base32 encoding or checksum)")
    return address


# -----------------------------------------------------------------------------
# Error Response Schemas
# -----------------------------------------------------------------------------

class ErrorDetail(BaseModel):
    """Structured error detail information."""
    code: str = Field(..., description="Machine-readable error code")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error context")


class ErrorResponse(BaseModel):
    """Standardized error response format for all API errors."""
    success: bool = Field(default=False, description="Always false for error responses")
    error: ErrorDetail = Field(..., description="Error details")

    class Config:
        json_schema_extra = {
            "example": {
                "success": False,
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Invalid wallet address format",
                    "details": {
                        "field": "address",
                        "value": "invalid-address"
                    }
                }
            }
        }


# -----------------------------------------------------------------------------
# Network Stats Schemas
# -----------------------------------------------------------------------------

class NetworkInfo(BaseModel):
    """Network-wide supply and participation statistics."""
    total_supply_algo: float = Field(..., description="Total ALGO supply")
    online_stake_algo: float = Field(..., description="ALGO currently participating in consensus")
    participation_rate: float = Field(..., description="Percentage of supply participating")
    current_round: int = Field(..., description="Current blockchain round")


class FoundationInfo(BaseModel):
    """Algorand Foundation stake information."""
    total_balance_algo: float = Field(..., description="Total Foundation holdings")
    online_balance_algo: float = Field(..., description="Foundation stake that is online")
    pct_of_total_supply: float = Field(..., description="Foundation % of total supply")
    pct_of_online_stake: float = Field(..., description="Foundation % of online stake")
    address_count: int = Field(..., description="Number of known Foundation addresses")


class CommunityInfo(BaseModel):
    """Community (non-Foundation) stake information."""
    estimated_stake_algo: float = Field(..., description="Estimated community online stake")
    pct_of_online_stake: float = Field(..., description="Community % of online stake")


class ScoreBreakdown(BaseModel):
    """Detailed breakdown of decentralization score factors."""
    # Positive factors
    community_online_pct: float = Field(..., description="Community % of online stake")
    community_online_score: int = Field(..., description="Points earned for community stake (max 30)")
    participation_rate_score: int = Field(..., description="Points earned for participation rate (max 10)")

    # Risk penalties
    foundation_supply_pct: float = Field(..., description="Foundation % of total supply")
    foundation_supply_penalty: int = Field(..., description="Points deducted for Foundation holdings (max 25)")
    foundation_potential_control: float = Field(..., description="If Foundation went fully online, their % of stake")
    potential_control_penalty: int = Field(..., description="Points deducted for potential control risk (max 20)")
    relay_centralization_penalty: int = Field(..., description="Points deducted for relay node centralization (15)")
    governance_penalty: int = Field(..., description="Points deducted for governance influence (10)")

    # Totals
    raw_score: int = Field(..., description="Raw score before floor/ceiling")
    final_score: int = Field(..., description="Final score (0-100)")


class NetworkStatsResponse(BaseModel):
    """Complete network statistics response."""
    network: NetworkInfo
    foundation: FoundationInfo
    community: CommunityInfo
    decentralization_score: int = Field(..., ge=0, le=100, description="0-100 decentralization score")
    score_breakdown: Optional[ScoreBreakdown] = Field(None, description="Detailed score breakdown")
    estimated_node_count: int = Field(default=3075, description="Estimated number of participation nodes")
    fetched_at: str = Field(..., description="ISO timestamp of when data was fetched")

    class Config:
        json_schema_extra = {
            "example": {
                "network": {
                    "total_supply_algo": 9595000000,
                    "online_stake_algo": 1971000000,
                    "participation_rate": 20.55,
                    "current_round": 56857575
                },
                "foundation": {
                    "total_balance_algo": 275770000,
                    "online_balance_algo": 0,
                    "pct_of_total_supply": 2.87,
                    "pct_of_online_stake": 0.0,
                    "address_count": 13
                },
                "community": {
                    "estimated_stake_algo": 1971000000,
                    "pct_of_online_stake": 100.0
                },
                "decentralization_score": 48,
                "score_breakdown": {
                    "community_online_pct": 100.0,
                    "community_online_score": 30,
                    "participation_rate_score": 6,
                    "foundation_supply_pct": 2.87,
                    "foundation_supply_penalty": 3,
                    "foundation_potential_control": 12.3,
                    "potential_control_penalty": 5,
                    "relay_centralization_penalty": 15,
                    "governance_penalty": 10,
                    "raw_score": 3,
                    "final_score": 48
                },
                "estimated_node_count": 3075,
                "fetched_at": "2024-12-26T15:30:00Z"
            }
        }


class ParticipationKeyInfo(BaseModel):
    """Participation key details for a wallet."""
    first_valid: Optional[int] = Field(None, description="First valid round for participation key")
    last_valid: Optional[int] = Field(None, description="Last valid round for participation key")
    is_expired: bool = Field(..., description="Whether the participation key has expired")
    rounds_remaining: Optional[int] = Field(None, description="Rounds until key expires (if active)")


class WalletParticipationResponse(BaseModel):
    """Wallet participation status response."""
    address: str = Field(..., description="Wallet address")
    is_participating: bool = Field(..., description="Whether wallet is actively participating")
    balance_algo: float = Field(..., description="Wallet balance in ALGO")
    stake_percentage: float = Field(..., description="Wallet's percentage of total online stake")
    participation_key: Optional[ParticipationKeyInfo] = Field(None, description="Participation key details")
    contribution_tier: str = Field(..., description="Contribution tier classification")
    current_round: int = Field(..., description="Current blockchain round")

    class Config:
        json_schema_extra = {
            "example": {
                "address": "ABC123...",
                "is_participating": True,
                "balance_algo": 120000.5,
                "stake_percentage": 0.0048,
                "participation_key": {
                    "first_valid": 44000000,
                    "last_valid": 48000000,
                    "is_expired": False,
                    "rounds_remaining": 3000000
                },
                "contribution_tier": "Active Participant",
                "current_round": 45000000
            }
        }


# -----------------------------------------------------------------------------
# LP Token Decomposition Schemas
# -----------------------------------------------------------------------------

class LPDecomposeRequest(BaseModel):
    """Request to lazily decompose a single LP token into its underlying assets."""
    asset_id: int = Field(..., description="ASA ID of the LP token")
    ticker: str = Field(..., description="Ticker/unit-name of the LP token (e.g. 'TMPOOL2')")
    name: str = Field(..., description="Full name of the LP token (e.g. 'TinymanPool2.0 ALGO-USDC')")
    amount: float = Field(..., gt=0, description="User's LP token balance")


class LPDecomposeResponse(BaseModel):
    """Result of decomposing an LP token into its two underlying assets."""
    lp_ticker: str = Field(..., description="Ticker of the LP token")
    lp_amount: float = Field(..., description="User's LP token balance")
    asset1_ticker: str = Field(..., description="Ticker of the first underlying asset")
    asset1_amount: float = Field(..., description="User's share of the first asset")
    asset1_usd: float = Field(..., description="USD value of user's first asset share")
    asset2_ticker: str = Field(..., description="Ticker of the second underlying asset")
    asset2_amount: float = Field(..., description="User's share of the second asset")
    asset2_usd: float = Field(..., description="USD value of user's second asset share")
    total_usd: float = Field(..., description="Total USD value of the LP position")


# -----------------------------------------------------------------------------
# Wallet Analysis Schemas
# -----------------------------------------------------------------------------

class AlertSummary(BaseModel):
    """Summary of an alert for the analysis response."""
    type: str
    severity: str
    title: str
    message: str
    suggested_action: str


class AnalysisResponse(BaseModel):
    """
    Complete wallet analysis response with categorized assets and sovereignty metrics.

    This is the primary response model for the POST /analyze endpoint. It contains:
    - Categorized holdings (hard_money, algo, dollars, shitcoin)
    - Sovereignty metrics (if monthly_fixed_expenses was provided)
    - Participation status and key details
    - Any generated alerts

    The categories dict contains arrays of asset objects, each with:
    - name: Human-readable asset name
    - ticker: Asset ticker/unit-name
    - amount: Quantity held
    - usd_value: Current USD value
    - from_lp: (optional) LP token this came from if decomposed
    """
    address: str = Field(..., description="The analyzed wallet address")
    is_participating: bool = Field(..., description="Whether wallet participates in Algorand consensus")
    hard_money_algo: float = Field(..., description="Legacy field - ALGO in hard money (usually 0)")
    categories: Dict[str, List[Dict[str, Any]]] = Field(
        ...,
        description="Categorized assets: hard_money, algo, dollars, shitcoin"
    )
    sovereignty_data: Optional[SovereigntyData] = Field(
        None,
        description="Sovereignty metrics (only if monthly_fixed_expenses provided)"
    )
    participation_info: Optional[Dict[str, Any]] = Field(
        None,
        description="Participation key details if wallet is online"
    )
    alerts: Optional[List[AlertSummary]] = Field(
        None,
        description="Generated sovereignty alerts"
    )
    has_critical_alerts: Optional[bool] = Field(
        None,
        description="True if any critical alerts were generated"
    )

    class Config:
        json_schema_extra = {
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
                    "sovereignty_ratio": 0.4,
                    "sovereignty_status": "Vulnerable",
                    "years_of_runway": 0.4
                }
            }
        }


class AnalyzeRequest(BaseModel):
    """
    Request body for wallet sovereignty analysis.

    The address is required. If monthly_fixed_expenses is provided, sovereignty
    ratio and status will be calculated. Without expenses, only asset
    categorization is performed.

    Example:
        POST /api/v1/analyze
        {
            "address": "YOUR_58_CHAR_ALGORAND_ADDRESS",
            "monthly_fixed_expenses": 4000
        }
    """
    address: str = Field(
        ...,
        description="58-character Algorand wallet address",
        min_length=58,
        max_length=58
    )
    monthly_fixed_expenses: Optional[float] = Field(
        None,
        description="Monthly fixed expenses in USD for sovereignty ratio calculation",
        ge=0,
        le=1_000_000
    )

    @field_validator("address")
    @classmethod
    def check_algorand_address(cls, v: str) -> str:
        return validate_algorand_address(v)

    class Config:
        json_schema_extra = {
            "example": {
                "address": "I26BHULCOKKBNFF3KEXVH3KWMBK3VWJFKQXYOKFLW4UAET4U4MESL3BIP4",
                "monthly_fixed_expenses": 4000.0
            }
        }


class HistorySaveRequest(BaseModel):
    """
    Request body for saving a sovereignty snapshot to history.

    Both address and monthly_fixed_expenses are required because the
    sovereignty ratio cannot be calculated without knowing expenses.
    """
    address: str = Field(
        ...,
        description="58-character Algorand wallet address",
        min_length=58,
        max_length=58
    )
    monthly_fixed_expenses: float = Field(
        ...,
        description="Monthly fixed expenses in USD (required for ratio calculation)",
        gt=0,
        le=1_000_000
    )

    @field_validator("address")
    @classmethod
    def check_algorand_address(cls, v: str) -> str:
        return validate_algorand_address(v)

    class Config:
        json_schema_extra = {
            "example": {
                "address": "I26BHULCOKKBNFF3KEXVH3KWMBK3VWJFKQXYOKFLW4UAET4U4MESL3BIP4",
                "monthly_fixed_expenses": 4000.0
            }
        }


class HistorySaveResponse(BaseModel):
    """
    Response after saving a sovereignty snapshot.

    On success, includes the saved snapshot data. On failure, success=False
    with an error message.
    """
    success: bool = Field(..., description="Whether the save operation succeeded")
    message: str = Field(..., description="Status message (success or error details)")
    snapshot: Optional[SovereigntySnapshot] = Field(
        None,
        description="The saved snapshot data (null on failure)"
    )

    class Config:
        json_schema_extra = {
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


class ProgressData(BaseModel):
    """Progress metrics calculated from historical data."""
    current_ratio: float
    previous_ratio: Optional[float] = None
    change_absolute: Optional[float] = None
    change_pct: Optional[float] = None
    trend: str  # "improving", "declining", "stable", "new"
    days_tracked: int
    snapshots_count: int
    projected_next_status: Optional[dict] = None


class AllTimeData(BaseModel):
    """All-time statistics for an address."""
    high: float
    low: float
    average: float
    first_tracked: str


class HistoryResponse(BaseModel):
    address: str
    snapshots: List[SovereigntySnapshot]
    count: int


class HistoryResponseEnhanced(BaseModel):
    """Enhanced history response with progress metrics."""
    address: str
    snapshots: List[SovereigntySnapshot]
    count: int
    progress: ProgressData
    all_time: Optional[AllTimeData] = None


# -----------------------------------------------------------------------------
# Meld Arbitrage Schemas
# -----------------------------------------------------------------------------

class ArbitrageMetalData(BaseModel):
    """Arbitrage data for a single metal (gold or silver)."""
    spot_per_oz: float = Field(..., description="Spot price per troy ounce from Yahoo Finance")
    implied_per_gram: float = Field(..., description="Implied price per gram (spot_per_oz / 31.1035)")
    meld_price: float = Field(..., description="Meld token price per gram from Vestige")
    premium_pct: float = Field(..., description="Premium percentage ((meld - implied) / implied * 100)")
    premium_usd: float = Field(..., description="Premium in USD (meld - implied)")
    signal: str = Field(..., description="Trading signal: STRONG_BUY, BUY, HOLD, SELL, STRONG_SELL")
    signal_strength: float = Field(..., ge=0, le=100, description="Signal strength 0-100")


class ArbitrageMetalError(BaseModel):
    """Error response when price data is unavailable for a metal."""
    error: str = Field(..., description="Error message")
    spot_available: bool = Field(..., description="Whether spot price was available")
    meld_available: bool = Field(..., description="Whether Meld price was available")


class BitcoinTokenData(BaseModel):
    """Arbitrage data for a single wrapped Bitcoin token (goBTC or WBTC)."""
    price: float = Field(..., description="Token price from Vestige DEX in USD")
    premium_pct: float = Field(..., description="Premium percentage vs Coinbase spot ((token - spot) / spot * 100)")
    premium_usd: float = Field(..., description="Premium in USD (token_price - spot_price)")
    signal: str = Field(..., description="Trading signal: STRONG_BUY, BUY, HOLD, SELL, STRONG_SELL")
    signal_strength: float = Field(..., ge=0, le=100, description="Signal strength 0-100")
    asa_id: int = Field(..., description="Algorand Standard Asset ID")
    tinyman_url: str = Field(..., description="Tinyman swap URL for this token")
    liquidity_warning: Optional[str] = Field(None, description="Warning if liquidity is low")


class CrossDexSpread(BaseModel):
    """Cross-DEX spread between goBTC and WBTC."""
    gobtc_vs_wbtc_pct: float = Field(..., description="goBTC price relative to WBTC ((gobtc - wbtc) / wbtc * 100)")
    description: str = Field(..., description="Human-readable spread description")


class BestOpportunity(BaseModel):
    """Best arbitrage opportunity between goBTC and WBTC."""
    token: str = Field(..., description="Which token has the better opportunity: goBTC or WBTC")
    action: str = Field(..., description="Recommended action: BUY, PREFER, or EQUAL")
    reason: str = Field(..., description="Human-readable explanation")
    advantage_pct: float = Field(..., description="Percentage advantage vs the alternative token")
    liquidity_note: Optional[str] = Field(None, description="Liquidity caveat if applicable")


class ArbitrageBitcoinData(BaseModel):
    """3-way Bitcoin arbitrage data: Coinbase spot vs goBTC vs WBTC."""
    spot_price: float = Field(..., description="Coinbase BTC spot price in USD")
    gobtc: Dict[str, Any] = Field(..., description="goBTC token data (BitcoinTokenData) or error dict")
    wbtc: Dict[str, Any] = Field(..., description="WBTC token data (BitcoinTokenData) or error dict")
    cross_dex_spread: Optional[Dict[str, Any]] = Field(None, description="Cross-DEX spread between goBTC and WBTC")
    best_opportunity: Optional[Dict[str, Any]] = Field(None, description="Best trading opportunity recommendation")


class GSRContext(BaseModel):
    """Historical context for Gold/Silver Ratio."""
    zone: str = Field(..., description="Zone: extreme_high, high, normal, low, extreme_low")
    color: str = Field(..., description="Color indicator for UI")
    message: str = Field(..., description="Human-readable context message")
    bias: str = Field(..., description="Accumulation bias: silver, gold, or neutral")


class GSRData(BaseModel):
    """Gold/Silver Ratio data."""
    meld_gsr: float = Field(..., description="GSR calculated from Meld prices")
    spot_gsr: Optional[float] = Field(None, description="GSR calculated from spot prices")
    gsr_spread_pct: Optional[float] = Field(None, description="Spread between Meld and spot GSR")
    context: GSRContext = Field(..., description="Historical context for the GSR")


class RotationSignal(BaseModel):
    """Rotation signal between gold and silver."""
    signal: str = Field(..., description="Signal: HOLD, CONSIDER_*, SILVER_TO_GOLD, GOLD_TO_SILVER")
    strength: float = Field(..., ge=0, le=100, description="Signal strength 0-100")
    spread_pct: float = Field(..., description="Premium spread (silver - gold)")
    description: str = Field(..., description="Human-readable signal description")


class MeldArbitrageResponse(BaseModel):
    """Complete arbitrage analysis response."""
    gold: Optional[Dict[str, Any]] = Field(None, description="Gold arbitrage data or error")
    silver: Optional[Dict[str, Any]] = Field(None, description="Silver arbitrage data or error")
    bitcoin: Optional[Dict[str, Any]] = Field(None, description="Bitcoin/goBTC arbitrage data or error")
    gsr: Optional[Dict[str, Any]] = Field(None, description="Gold/Silver Ratio data")
    rotation: Optional[Dict[str, Any]] = Field(None, description="Rotation signal between gold and silver")
    timestamp: str = Field(..., description="ISO timestamp of analysis")
    data_complete: bool = Field(..., description="Whether all price data was available")


# -----------------------------------------------------------------------------
# Bitcoin Price History Schemas
# -----------------------------------------------------------------------------

class BTCHistoryDataPoint(BaseModel):
    """Single data point in the Bitcoin price history time series."""
    timestamp: str = Field(..., description="ISO 8601 timestamp (UTC)")
    spot_btc: float = Field(..., description="Coinbase BTC spot price in USD")
    gobtc_price: float = Field(..., description="goBTC price from Vestige in USD")
    wbtc_price: Optional[float] = Field(None, description="WBTC price from Vestige in USD (may be None)")
    gobtc_premium_pct: float = Field(..., description="goBTC premium/discount vs spot (%)")
    wbtc_premium_pct: Optional[float] = Field(None, description="WBTC premium/discount vs spot (%) (may be None)")


class BTCHistoryTokenStats(BaseModel):
    """Statistics for a single token over the requested time window."""
    avg_premium_pct: Optional[float] = Field(None, description="Average premium/discount (%)")
    min_premium_pct: Optional[float] = Field(None, description="Minimum (most negative = biggest discount) premium (%)")
    max_premium_pct: Optional[float] = Field(None, description="Maximum (highest premium) (%)")


class BTCHistoryStats(BaseModel):
    """Aggregate statistics for both tokens over the requested time window."""
    gobtc: BTCHistoryTokenStats = Field(..., description="goBTC statistics")
    wbtc: BTCHistoryTokenStats = Field(..., description="WBTC statistics")
    data_points: int = Field(..., description="Total number of data points in this window")
    hours: int = Field(..., description="Hours of history requested")


class BTCHistoryResponse(BaseModel):
    """Response for the /arbitrage/btc-history endpoint."""
    data_points: List[BTCHistoryDataPoint] = Field(..., description="Time-series data, oldest first")
    stats: BTCHistoryStats = Field(..., description="Aggregate statistics for the time window")
    hours_requested: int = Field(..., description="Hours of history that were requested")
    timestamp: str = Field(..., description="ISO 8601 timestamp when this response was generated")


# -----------------------------------------------------------------------------
# Classification Corrections Schemas
# -----------------------------------------------------------------------------

class CorrectionSubmitRequest(BaseModel):
    """Request to submit a classification correction."""
    asset_id: str = Field(..., description="The ASA ID", max_length=20)
    asset_name: str = Field(..., description="Human-readable asset name", max_length=100)
    ticker: str = Field(..., description="Asset ticker symbol", max_length=20)
    original_category: str = Field(..., description="The auto-classified category")
    corrected_category: str = Field(..., description="Your suggested category (hard_money, algo, dollars, shitcoin)")
    reason: Optional[str] = Field(None, description="Explanation for the correction", max_length=500)
    submitted_by: Optional[str] = Field(None, description="Your wallet address (optional)", max_length=58)

    @field_validator("original_category", "corrected_category")
    @classmethod
    def check_category(cls, v: str) -> str:
        if v not in VALID_CATEGORIES:
            raise ValueError(f"Category must be one of: {', '.join(sorted(VALID_CATEGORIES))}")
        return v

    @field_validator("submitted_by")
    @classmethod
    def check_submitted_by(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            return validate_algorand_address(v)
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "asset_id": "123456789",
                "asset_name": "Example Token",
                "ticker": "EXT",
                "original_category": "shitcoin",
                "corrected_category": "hard_money",
                "reason": "This is a wrapped Bitcoin token",
                "submitted_by": "ABC123..."
            }
        }


class CorrectionResponse(BaseModel):
    """Response after submitting a correction."""
    success: bool = Field(..., description="Whether the correction was submitted")
    message: str = Field(..., description="Status message")
    correction: Optional[Dict[str, Any]] = Field(None, description="The submitted correction")


class CorrectionsListResponse(BaseModel):
    """Response listing all corrections."""
    corrections: List[Dict[str, Any]] = Field(..., description="List of corrections")
    count: int = Field(..., description="Number of corrections")


class CorrectionStatsResponse(BaseModel):
    """Statistics about the corrections system."""
    total_corrections: int
    active_corrections: int
    pending_corrections: int
    approved_corrections: int
    rejected_corrections: int
    most_corrected_category: Optional[str] = None
    recent_corrections: List[Dict[str, Any]]

    class Config:
        json_schema_extra = {
            "example": {
                "gold": {
                    "spot_per_oz": 2650.00,
                    "implied_per_gram": 85.20,
                    "meld_price": 88.50,
                    "premium_pct": 3.87,
                    "premium_usd": 3.30,
                    "signal": "HOLD",
                    "signal_strength": 0
                },
                "silver": {
                    "spot_per_oz": 30.50,
                    "implied_per_gram": 0.981,
                    "meld_price": 1.15,
                    "premium_pct": 17.2,
                    "premium_usd": 0.169,
                    "signal": "STRONG_SELL",
                    "signal_strength": 86.0
                },
                "bitcoin": {
                    "spot_price": 94500.00,
                    "gobtc_price": 93800.00,
                    "premium_pct": -0.74,
                    "premium_usd": -700.00,
                    "signal": "HOLD",
                    "signal_strength": 0
                },
                "timestamp": "2024-12-27T15:30:00Z",
                "data_complete": True
            }
        }


# -----------------------------------------------------------------------------
# DeFi Sovereignty Cost Schemas
# -----------------------------------------------------------------------------

class LPSovereigntyCostResponse(BaseModel):
    """Sovereignty cost analysis for a single LP position."""
    lp_name: str = Field(..., description="Name of the LP token")
    lp_ticker: str = Field(..., description="Ticker of the LP token")
    total_usd_value: float = Field(..., description="Total USD value of the LP position")
    asset1_ticker: str = Field(..., description="First underlying asset")
    asset1_usd: float = Field(..., description="USD value of first asset")
    asset1_tier: str = Field(..., description="Sovereignty tier (HARD_MONEY, ALGORAND, STABLECOIN, SHITCOIN)")
    asset2_ticker: str = Field(..., description="Second underlying asset")
    asset2_usd: float = Field(..., description="USD value of second asset")
    asset2_tier: str = Field(..., description="Sovereignty tier of second asset")
    current_sovereignty_score: float = Field(..., description="Current weighted sovereignty contribution")
    potential_sovereignty_score: float = Field(..., description="Score if 100% was best asset")
    sovereignty_cost: float = Field(..., description="Difference (potential - current)")
    sovereignty_cost_percent: float = Field(..., description="Cost as percentage of potential")
    estimated_apy: Optional[float] = Field(None, description="Estimated annual yield if provided")
    break_even_years: Optional[float] = Field(None, description="Years until yield covers sovereignty cost")
    recommendation: str = Field(..., description="Human-readable recommendation")


class DeFiSovereigntyCostRequest(BaseModel):
    """Request for DeFi sovereignty cost analysis."""
    address: str = Field(..., description="Algorand wallet address", min_length=58, max_length=58)
    apy_estimates: Optional[Dict[str, float]] = Field(
        None,
        description="Optional APY estimates by LP ticker (e.g., {'TMPOOL2-ALGO-USDC': 10.5})"
    )

    @field_validator("address")
    @classmethod
    def check_algorand_address(cls, v: str) -> str:
        return validate_algorand_address(v)


class DeFiSovereigntyCostResponse(BaseModel):
    """Portfolio-level DeFi sovereignty cost summary."""
    total_lp_value_usd: float = Field(..., description="Total value in LP positions")
    total_current_score: float = Field(..., description="Current weighted sovereignty score")
    total_potential_score: float = Field(..., description="Score if optimally allocated")
    total_sovereignty_cost: float = Field(..., description="Sum of all costs")
    total_sovereignty_cost_percent: float = Field(..., description="Overall cost percentage")
    total_estimated_apy_earnings: float = Field(..., description="Estimated annual yield in USD")
    overall_recommendation: str = Field(..., description="Portfolio-level recommendation")
    lp_details: List[LPSovereigntyCostResponse] = Field(..., description="Per-LP breakdown")


# -----------------------------------------------------------------------------
# Pagination Schemas for Large Wallets
# -----------------------------------------------------------------------------

class AssetPageResponse(BaseModel):
    """A page of assets for a single category."""
    items: List[Dict[str, Any]] = Field(..., description="List of assets on this page")
    total: int = Field(..., description="Total number of assets in this category")
    page: int = Field(..., description="Current page number (1-indexed)")
    page_size: int = Field(..., description="Number of items per page")
    has_more: bool = Field(..., description="Whether more pages are available")


class PaginatedAssetsResponse(BaseModel):
    """Response for paginated asset requests."""
    address: str = Field(..., description="Wallet address")
    category: str = Field(..., description="Asset category (hard_money, algo, dollars, shitcoin)")
    page: AssetPageResponse = Field(..., description="Page of assets")
    category_total_usd: float = Field(..., description="Total USD value for this category")


class QuickSovereigntyResponse(BaseModel):
    """Lightweight sovereignty data for quick initial display."""
    address: str = Field(..., description="Wallet address")
    is_participating: bool = Field(..., description="Whether wallet participates in consensus")
    sovereignty_ratio: Optional[float] = Field(None, description="Sovereignty ratio (requires expenses)")
    sovereignty_status: Optional[str] = Field(None, description="Status text (requires expenses)")
    portfolio_usd: float = Field(..., description="Total portfolio value in USD")
    algo_price: float = Field(..., description="Current ALGO price")
    years_of_runway: Optional[float] = Field(None, description="Years of runway (requires expenses)")
    category_totals: Dict[str, float] = Field(..., description="USD totals by category")
    asset_counts: Dict[str, int] = Field(..., description="Asset counts by category")
    needs_pagination: Dict[str, bool] = Field(..., description="Whether each category needs pagination")
    participation_info: Optional[Dict[str, Any]] = Field(None, description="Participation key details")


class PaginatedAnalyzeRequest(BaseModel):
    """Request for paginated wallet analysis."""
    address: str = Field(..., description="Algorand wallet address", min_length=58, max_length=58)
    monthly_fixed_expenses: Optional[float] = Field(None, description="Monthly fixed expenses for ratio calculation", gt=0, le=1_000_000)
    initial_page_size: int = Field(default=10, description="Initial number of assets per category", ge=1, le=100)

    @field_validator("address")
    @classmethod
    def check_algorand_address(cls, v: str) -> str:
        return validate_algorand_address(v)


# -----------------------------------------------------------------------------
# Advisor Schemas
# -----------------------------------------------------------------------------

class AdvisorRequest(BaseModel):
    """Request for AI sovereignty advisor."""
    address: str = Field(..., description="Algorand wallet address", min_length=58, max_length=58)
    monthly_fixed_expenses: Optional[float] = Field(None, description="Monthly fixed expenses for ratio calculation", gt=0, le=1_000_000)

    @field_validator("address")
    @classmethod
    def check_algorand_address(cls, v: str) -> str:
        return validate_algorand_address(v)


class AdvisorAdvice(BaseModel):
    """Structured advice from the sovereignty advisor."""
    overall_assessment: str = Field(..., description="2-3 sentence sovereignty assessment")
    score_interpretation: str = Field(..., description="Interpretation of sovereignty ratio and status")
    recommendations: List[str] = Field(..., description="Actionable recommendations (max 5)")
    next_milestone: str = Field(..., description="Next sovereignty milestone to reach")


class AdvisorResponse(BaseModel):
    """Response combining analysis and advisor output."""
    analysis: AnalysisResponse = Field(..., description="Wallet analysis results")
    advice: AdvisorAdvice = Field(..., description="Structured sovereignty advice")


# -----------------------------------------------------------------------------
# Async Job Schemas
# -----------------------------------------------------------------------------

class AsyncAnalyzeRequest(BaseModel):
    """Request to start an async wallet analysis job."""
    address: str = Field(..., description="58-character Algorand wallet address", min_length=58, max_length=58)
    monthly_fixed_expenses: Optional[float] = Field(None, description="Monthly fixed expenses in USD", ge=0, le=1_000_000)

    @field_validator("address")
    @classmethod
    def check_algorand_address(cls, v: str) -> str:
        return validate_algorand_address(v)


class AsyncAnalyzeResponse(BaseModel):
    """Response after submitting an async analysis job."""
    job_id: str = Field(..., description="Unique job identifier for polling")
    status: str = Field(..., description="Current job status")
    poll_url: str = Field(..., description="URL to poll for job status")


class JobStatusResponse(BaseModel):
    """Response for job status polling."""
    job_id: str
    status: str
    address: str
    progress_message: str = ""
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
