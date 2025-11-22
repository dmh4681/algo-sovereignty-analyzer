from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from core.models import AssetCategory, SovereigntyData

class AnalysisResponse(BaseModel):
    address: str
    is_participating: bool
    hard_money_algo: float
    categories: Dict[str, List[Dict[str, Any]]]
    sovereignty_data: Optional[SovereigntyData] = None
