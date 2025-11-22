from fastapi import APIRouter, HTTPException, Query
from core.analyzer import AlgorandSovereigntyAnalyzer
from .schemas import AnalysisResponse, AnalyzeRequest
from typing import Dict, Any, Tuple, Optional
from datetime import datetime, timedelta

router = APIRouter()

# Simple cache: {address: (analysis_result, timestamp)}
_wallet_cache: Dict[str, Tuple[dict, datetime]] = {}
CACHE_TTL_MINUTES = 15

def get_cached_analysis(address: str) -> Optional[dict]:
    """Return cached analysis if exists and not expired"""
    if address in _wallet_cache:
        result, timestamp = _wallet_cache[address]
        if datetime.now() - timestamp < timedelta(minutes=CACHE_TTL_MINUTES):
            return result
    return None

def cache_analysis(address: str, result: dict):
    """Store analysis result in cache"""
    _wallet_cache[address] = (result, datetime.now())

@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_wallet(request: AnalyzeRequest, use_local_node: bool = Query(False)):
    """
    Analyze an Algorand wallet for sovereignty metrics.
    """
    # Check cache first (only if not using local node, as local node might be for dev/testing)
    if not use_local_node:
        cached = get_cached_analysis(request.address)
        if cached:
            # If we have expenses, we need to recalculate sovereignty data
            # But the base analysis (categories) is valid
            categories = cached['categories']
            analyzer = AlgorandSovereigntyAnalyzer(use_local_node=False) # Just for helper methods if needed
            
            sovereignty_data = None
            if request.monthly_fixed_expenses:
                sovereignty_data = analyzer.calculate_sovereignty_metrics(
                    categories, 
                    request.monthly_fixed_expenses
                )
                
            return AnalysisResponse(
                address=request.address,
                is_participating=cached['is_participating'],
                hard_money_algo=cached['hard_money_algo'],
                categories=categories,
                sovereignty_data=sovereignty_data
            )

    analyzer = AlgorandSovereigntyAnalyzer(use_local_node=use_local_node)
    
    try:
        categories = analyzer.analyze_wallet(request.address)
        if not categories:
            raise HTTPException(status_code=404, detail="Wallet not found or empty")
            
        # Calculate sovereignty metrics if expenses provided
        sovereignty_data = None
        if request.monthly_fixed_expenses:
            sovereignty_data = analyzer.calculate_sovereignty_metrics(
                categories, 
                request.monthly_fixed_expenses
            )
        
        # Prepare result
        result = {
            'address': request.address,
            'is_participating': analyzer.last_is_participating,
            'hard_money_algo': analyzer.last_hard_money_algo,
            'categories': categories
        }
        
        # Cache it
        if not use_local_node:
            cache_analysis(request.address, result)
        
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
