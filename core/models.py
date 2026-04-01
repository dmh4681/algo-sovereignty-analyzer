from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum

class AssetCategory(str, Enum):
    HARD_MONEY = "hard_money"
    ALGO = "algo"
    DOLLARS = "dollars"
    SHITCOIN = "shitcoin"


# Sovereignty status thresholds and labels
SOVEREIGNTY_THRESHOLDS = [
    (20, "Generationally Sovereign"),
    (6, "Antifragile"),
    (3, "Robust"),
    (1, "Fragile"),
]


def get_sovereignty_status(ratio: float, include_emoji: bool = False) -> str:
    """
    Determine sovereignty status based on ratio.

    Centralizes the sovereignty status calculation logic to avoid duplication.

    Args:
        ratio: The sovereignty ratio (portfolio_usd / annual_expenses)
        include_emoji: If True, append status emoji to the string

    Returns:
        Status string like "Robust" or "Robust 🟡" if include_emoji=True

    Status Levels:
        >= 20: Generationally Sovereign (multi-generational wealth)
        >= 6:  Antifragile (benefits from volatility)
        >= 3:  Robust (can weather major storms)
        >= 1:  Fragile (building foundation)
        < 1:   Vulnerable (immediate action needed)
    """
    emojis = {
        "Generationally Sovereign": "🟩",
        "Antifragile": "🟢",
        "Robust": "🟡",
        "Fragile": "🔴",
        "Vulnerable": "⚫",
    }

    for threshold, status in SOVEREIGNTY_THRESHOLDS:
        if ratio >= threshold:
            return f"{status} {emojis[status]}" if include_emoji else status

    status = "Vulnerable"
    return f"{status} {emojis[status]}" if include_emoji else status

class Asset(BaseModel):
    ticker: str
    name: str
    amount: float
    usd_value: float = 0.0
    category: Optional[AssetCategory] = None
    asset_id: Optional[int] = None

class SovereigntyData(BaseModel):
    monthly_fixed_expenses: float
    annual_fixed_expenses: float
    algo_price: float
    portfolio_usd: float
    sovereignty_ratio: float
    sovereignty_status: str
    years_of_runway: float

class WalletAnalysis(BaseModel):
    address: str
    is_participating: bool
    hard_money_algo: float
    categories: Dict[str, List[Dict[str, Any]]]
    sovereignty_data: Optional[SovereigntyData] = None


class AssetPage(BaseModel):
    """A page of assets within a category for lazy loading."""
    items: List[Dict[str, Any]]
    total: int
    page: int
    page_size: int
    has_more: bool


class PaginatedAssets(BaseModel):
    """Paginated assets response for a single category."""
    category: str
    page: AssetPage
    category_total_usd: float


class QuickSovereigntyData(BaseModel):
    """Lightweight sovereignty data returned first for quick display."""
    sovereignty_ratio: float
    sovereignty_status: str
    portfolio_usd: float
    algo_price: float
    years_of_runway: float
    hard_money_total_usd: float
    algo_total_usd: float
    dollars_total_usd: float
    shitcoin_total_usd: float
    asset_counts: Dict[str, int]


class ProgressiveAnalysisResponse(BaseModel):
    """Response structure for progressive wallet analysis."""
    address: str
    is_participating: bool
    sovereignty_data: Optional[QuickSovereigntyData] = None
    initial_assets: Optional[Dict[str, List[Dict[str, Any]]]] = None
    total_assets_by_category: Dict[str, int]
    has_paginated_categories: bool
    participation_info: Optional[Dict[str, Any]] = None


class DataSourceStatus(BaseModel):
    """
    Tracks the provenance and reliability of data used in an analysis response.

    This model makes explicit which prices came from live APIs, the in-memory
    cache, or hardcoded fallbacks—and which data modules contain fabricated or
    manually-estimated values that have not been verified against real sources.

    Price source values:
        - "live_api"  : Fetched fresh from an external API during this request
        - "cache"     : Served from in-memory cache (previously fetched from API)
        - "hardcoded" : All live sources failed; a conservative constant was used
        - "unknown"   : Price fetch has not been attempted yet for this asset
    """
    algo_price_source: str = Field(
        "unknown",
        description="Source of ALGO price: live_api | cache | hardcoded | unknown"
    )
    btc_price_source: str = Field(
        "unknown",
        description="Source of BTC spot price: live_api | cache | hardcoded | unknown"
    )
    gold_price_source: str = Field(
        "unknown",
        description="Source of gold price (Yahoo Finance GC=F): live_api | cache | hardcoded | unknown"
    )
    silver_price_source: str = Field(
        "unknown",
        description="Source of silver price (Yahoo Finance SI=F): live_api | cache | hardcoded | unknown"
    )
    blockchain_source: str = Field(
        "algonode_live",
        description="Source of on-chain wallet data (always AlgoNode public API)"
    )
    fabricated_data_warnings: List[str] = Field(
        default_factory=list,
        description=(
            "Modules that contain fabricated, estimated, or unverified data. "
            "Values here are NOT sourced from real APIs and should not be used "
            "for financial decisions."
        )
    )
    fetched_at: str = Field(
        ...,
        description="ISO 8601 UTC timestamp when price data was fetched for this response"
    )
