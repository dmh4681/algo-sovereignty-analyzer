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


class NetworkStatsResponse(BaseModel):
    """Complete network statistics response."""
    network: NetworkInfo
    foundation: FoundationInfo
    community: CommunityInfo
    decentralization_score: int = Field(..., ge=0, le=100, description="0-100 decentralization score")
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
                "decentralization_score": 96,
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


class HistoryResponse(BaseModel):
    address: str
    snapshots: List[SovereigntySnapshot]
    count: int
