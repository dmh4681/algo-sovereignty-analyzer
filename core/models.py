from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum

class AssetCategory(str, Enum):
    HARD_MONEY = "hard_money"
    PRODUCTIVE = "productive"
    NFT = "nft"
    SHITCOIN = "shitcoin"

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
