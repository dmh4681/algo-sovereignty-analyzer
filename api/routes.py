from fastapi import APIRouter, HTTPException, Query
from core.analyzer import AlgorandSovereigntyAnalyzer
from .schemas import AnalysisResponse

router = APIRouter()

@router.get("/analyze/{address}", response_model=AnalysisResponse)
async def analyze_wallet(address: str, use_local_node: bool = Query(False)):
    """
    Analyze an Algorand wallet for sovereignty metrics.
    """
    analyzer = AlgorandSovereigntyAnalyzer(use_local_node=use_local_node)
    
    # We need to modify analyzer to return the data structure we want directly
    # or just use what it returns. 
    # The current analyzer.analyze_wallet returns 'categories' dict.
    # It also stores state. Ideally we'd refactor analyzer to be stateless or return a full object.
    # For now, let's just use it as is and construct the response.
    
    try:
        categories = analyzer.analyze_wallet(address)
        if not categories:
            raise HTTPException(status_code=404, detail="Wallet not found or empty")
            
        # Construct response
        # Note: sovereignty_data is only calculated if we have expenses input, 
        # which we don't here. So it will be None.
        
        return AnalysisResponse(
            address=address,
            is_participating=analyzer.last_is_participating,
            hard_money_algo=analyzer.last_hard_money_algo,
            categories=categories,
            sovereignty_data=None 
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
