from fastapi import APIRouter, HTTPException, Query
from core.analyzer import AlgorandSovereigntyAnalyzer
from .schemas import AnalysisResponse, AnalyzeRequest
from typing import Dict, Any

router = APIRouter()

@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_wallet(request: AnalyzeRequest, use_local_node: bool = Query(False)):
    """
    Analyze an Algorand wallet for sovereignty metrics.
    """
    analyzer = AlgorandSovereigntyAnalyzer(use_local_node=use_local_node)
    
    try:
        categories = analyzer.analyze_wallet(request.address)
        if not categories:
            raise HTTPException(status_code=404, detail="Wallet not found or empty")
            
        # Calculate sovereignty metrics if expenses provided
        sovereignty_data = None
        if request.monthly_fixed_expenses:
            sovereignty_data = analyzer.calculate_sovereignty_metrics(
                analyzer.last_hard_money_algo, 
                request.monthly_fixed_expenses
            )
        
        return AnalysisResponse(
            address=request.address,
            is_participating=analyzer.last_is_participating,
            hard_money_algo=analyzer.last_hard_money_algo,
            categories=categories,
            sovereignty_data=sovereignty_data
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/classifications")
async def get_classifications() -> Dict[str, Dict[str, str]]:
    """
    Get manual asset classifications.
    """
    analyzer = AlgorandSovereigntyAnalyzer(use_local_node=False)
    return analyzer.classifier.classifications
