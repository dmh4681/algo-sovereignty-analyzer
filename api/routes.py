from fastapi import APIRouter, HTTPException, Query, Path
from core.analyzer import AlgorandSovereigntyAnalyzer
from core.history import SovereigntySnapshot, get_history_manager
from .schemas import (
    AnalysisResponse,
    AnalyzeRequest,
    HistorySaveRequest,
    HistorySaveResponse,
    HistoryResponse
)
from .agent import SovereigntyCoach, AdviceRequest
from typing import Dict, Any, Tuple, Optional, List
from datetime import datetime, timedelta

router = APIRouter()

@router.post("/agent/advice")
async def get_agent_advice(request: AdviceRequest):
    """
    Get personalized financial sovereignty advice from the AI agent.
    """
    print(f"DEBUG: Received advice request for address: {request.address}")
    try:
        coach = SovereigntyCoach()
        advice = coach.generate_advice(request.analysis)
        return {"advice": advice}
    except Exception as e:
        print(f"ERROR in /agent/advice: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

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
                # Auto-save history snapshot
                _create_and_save_snapshot(
                    address=request.address,
                    categories=categories,
                    sovereignty_data=sovereignty_data,
                    is_participating=cached['is_participating'],
                    algo_price=sovereignty_data.algo_price if sovereignty_data else 0.0
                )

            return AnalysisResponse(
                address=request.address,
                is_participating=cached['is_participating'],
                hard_money_algo=cached['hard_money_algo'],
                categories=categories,
                sovereignty_data=sovereignty_data,
                participation_info=cached.get('participation_info')
            )

    analyzer = AlgorandSovereigntyAnalyzer(use_local_node=use_local_node)
    
    try:
        print(f"📊 Starting analysis for {request.address[:8]}...")
        categories = analyzer.analyze_wallet(request.address)
        if not categories:
            raise HTTPException(status_code=404, detail="Wallet not found or empty")
        
        print(f"✅ Analysis complete. Categories: {list(categories.keys())}")
            
        # Calculate sovereignty metrics if expenses provided
        sovereignty_data = None
        if request.monthly_fixed_expenses:
            sovereignty_data = analyzer.calculate_sovereignty_metrics(
                categories,
                request.monthly_fixed_expenses
            )
            # Auto-save history snapshot
            _create_and_save_snapshot(
                address=request.address,
                categories=categories,
                sovereignty_data=sovereignty_data,
                is_participating=analyzer.last_is_participating,
                algo_price=sovereignty_data.algo_price if sovereignty_data else 0.0
            )

        # Prepare result
        result = {
            'address': request.address,
            'is_participating': analyzer.last_is_participating,
            'hard_money_algo': analyzer.last_hard_money_algo,
            'categories': categories,
            'participation_info': analyzer.last_participation_info
        }
        
        # Cache it
        if not use_local_node:
            cache_analysis(request.address, result)
        
        print(f"📤 Preparing response...")
        response = AnalysisResponse(
            address=request.address,
            is_participating=analyzer.last_is_participating,
            hard_money_algo=analyzer.last_hard_money_algo,
            categories=categories,
            sovereignty_data=sovereignty_data,
            participation_info=analyzer.last_participation_info
        )
        print(f"✅ Response ready, sending...")
        return response
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error in analyze_wallet endpoint: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@router.get("/classifications")
async def get_classifications() -> Dict[str, Dict[str, str]]:
    """
    Get manual asset classifications.
    """
    analyzer = AlgorandSovereigntyAnalyzer(use_local_node=False)
    return analyzer.classifier.classifications


def _create_and_save_snapshot(
    address: str,
    categories: Dict[str, List[Dict[str, Any]]],
    sovereignty_data: Any,
    is_participating: bool,
    algo_price: float
) -> Optional[SovereigntySnapshot]:
    """
    Helper function to create and save a history snapshot.

    Returns the saved snapshot or None if save failed.
    """
    try:
        # Calculate hard money USD from categories
        hard_money_usd = sum(
            asset.get('usd_value', 0)
            for asset in categories.get('hard_money', [])
        )

        # Calculate total portfolio USD
        total_portfolio_usd = sovereignty_data.portfolio_usd if sovereignty_data else sum(
            asset.get('usd_value', 0)
            for category in categories.values()
            for asset in category
        )

        snapshot = SovereigntySnapshot(
            address=address,
            timestamp=datetime.utcnow().isoformat(),
            sovereignty_ratio=sovereignty_data.sovereignty_ratio if sovereignty_data else 0.0,
            hard_money_usd=hard_money_usd,
            total_portfolio_usd=total_portfolio_usd,
            algo_price=algo_price,
            participation_status=is_participating
        )

        history_manager = get_history_manager()
        if history_manager.save_snapshot(snapshot):
            return snapshot
        return None
    except Exception as e:
        print(f"Error creating snapshot: {e}")
        return None


@router.post("/history/save", response_model=HistorySaveResponse)
async def save_history_snapshot(request: HistorySaveRequest):
    """
    Save a sovereignty snapshot for historical tracking.

    Calculates current sovereignty metrics and saves a snapshot to history.
    """
    analyzer = AlgorandSovereigntyAnalyzer(use_local_node=False)

    try:
        # First check cache for recent analysis
        cached = get_cached_analysis(request.address)

        if cached:
            categories = cached['categories']
            is_participating = cached['is_participating']
        else:
            # Perform fresh analysis
            categories = analyzer.analyze_wallet(request.address)
            if not categories:
                raise HTTPException(
                    status_code=404,
                    detail="Wallet not found or empty"
                )
            is_participating = analyzer.last_is_participating

            # Cache the result
            result = {
                'address': request.address,
                'is_participating': is_participating,
                'hard_money_algo': analyzer.last_hard_money_algo,
                'categories': categories
            }
            cache_analysis(request.address, result)

        # Calculate sovereignty metrics
        sovereignty_data = analyzer.calculate_sovereignty_metrics(
            categories,
            request.monthly_fixed_expenses
        )

        # Get algo price from sovereignty data
        algo_price = sovereignty_data.algo_price if sovereignty_data else 0.0

        # Save snapshot
        snapshot = _create_and_save_snapshot(
            address=request.address,
            categories=categories,
            sovereignty_data=sovereignty_data,
            is_participating=is_participating,
            algo_price=algo_price
        )

        if snapshot:
            return HistorySaveResponse(
                success=True,
                message="Snapshot saved successfully",
                snapshot=snapshot
            )
        else:
            return HistorySaveResponse(
                success=False,
                message="Failed to save snapshot",
                snapshot=None
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history/{address}", response_model=HistoryResponse)
async def get_history(
    address: str = Path(..., description="Wallet address"),
    days: int = Query(90, description="Number of days (30, 90, or 365)")
):
    """
    Get historical sovereignty snapshots for an address.

    Returns snapshots within the specified time period.
    """
    # Validate days parameter
    if days not in (30, 90, 365):
        days = 90

    history_manager = get_history_manager()
    snapshots = history_manager.get_history(address, days)

    return HistoryResponse(
        address=address,
        snapshots=snapshots,
        count=len(snapshots)
    )
