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
