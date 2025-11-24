from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from core.models import AssetCategory, SovereigntyData
from core.history import SovereigntySnapshot

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
