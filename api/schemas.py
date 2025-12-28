from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
from core.models import AssetCategory, SovereigntyData
from core.history import SovereigntySnapshot


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
# Wallet Analysis Schemas
# -----------------------------------------------------------------------------

class AnalysisResponse(BaseModel):
    address: str
    is_participating: bool
    hard_money_algo: float
    categories: Dict[str, List[Dict[str, Any]]]
    sovereignty_data: Optional[SovereigntyData] = None
    participation_info: Optional[Dict[str, Any]] = None

class AnalyzeRequest(BaseModel):
    address: str
    monthly_fixed_expenses: Optional[float] = None


class HistorySaveRequest(BaseModel):
    address: str
    monthly_fixed_expenses: float


class HistorySaveResponse(BaseModel):
    success: bool
    message: str
    snapshot: Optional[SovereigntySnapshot] = None


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


class ArbitrageBitcoinData(BaseModel):
    """Arbitrage data for Bitcoin/goBTC comparison."""
    spot_price: float = Field(..., description="Coinbase BTC spot price in USD")
    gobtc_price: float = Field(..., description="goBTC price from Vestige in USD")
    premium_pct: float = Field(..., description="Premium percentage ((gobtc - spot) / spot * 100)")
    premium_usd: float = Field(..., description="Premium in USD (gobtc - spot)")
    signal: str = Field(..., description="Trading signal: STRONG_BUY, BUY, HOLD, SELL, STRONG_SELL")
    signal_strength: float = Field(..., ge=0, le=100, description="Signal strength 0-100")


class MeldArbitrageResponse(BaseModel):
    """Complete arbitrage analysis response."""
    gold: Optional[Dict[str, Any]] = Field(None, description="Gold arbitrage data or error")
    silver: Optional[Dict[str, Any]] = Field(None, description="Silver arbitrage data or error")
    bitcoin: Optional[Dict[str, Any]] = Field(None, description="Bitcoin/goBTC arbitrage data or error")
    timestamp: str = Field(..., description="ISO timestamp of analysis")
    data_complete: bool = Field(..., description="Whether all price data was available")

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
