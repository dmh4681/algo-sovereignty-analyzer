"""
History API Endpoints
Add these to your existing api/routes.py file
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

# Import the history module
from core.history import SovereigntyHistory, get_history_tracker

# If you have an existing router, add these routes to it
# Otherwise create a new one:
# router = APIRouter(prefix="/api/v1", tags=["history"])


# ============================================================================
# PYDANTIC SCHEMAS - Add to api/schemas.py
# ============================================================================

class HistorySaveRequest(BaseModel):
    address: str
    analysis_result: dict


class HistorySaveResponse(BaseModel):
    success: bool
    snapshot_id: Optional[int]
    message: str


class SnapshotData(BaseModel):
    id: int
    timestamp: str
    sovereignty_ratio: float
    sovereignty_status: str
    hard_money_usd: float
    total_portfolio_usd: float
    hard_money_pct: Optional[float]
    algo_balance: Optional[float]


class ProgressData(BaseModel):
    current_ratio: float
    previous_ratio: Optional[float]
    change_absolute: Optional[float]
    change_pct: Optional[float]
    trend: str
    days_tracked: int
    snapshots_count: int
    projected_next_status: Optional[dict]


class AllTimeData(BaseModel):
    high: float
    low: float
    average: float
    first_tracked: str
    last_tracked: str


class HistoryResponse(BaseModel):
    address: str
    snapshots: List[SnapshotData]
    progress: ProgressData
    all_time: Optional[AllTimeData]


class DeleteHistoryResponse(BaseModel):
    success: bool
    deleted_count: int


class HistorySummary(BaseModel):
    has_history: bool
    snapshots_count: int
    trend: Optional[str]
    change_30d_pct: Optional[float]


# ============================================================================
# API ENDPOINTS - Add these to your router
# ============================================================================

@router.post("/history/save", response_model=HistorySaveResponse)
async def save_history_snapshot(request: HistorySaveRequest):
    """
    Save a wallet analysis snapshot for historical tracking.
    Automatically deduplicates if a snapshot was saved within the last hour.
    """
    try:
        history = get_history_tracker()
        snapshot_id = history.save_snapshot(request.address, request.analysis_result)
        
        if snapshot_id:
            return HistorySaveResponse(
                success=True,
                snapshot_id=snapshot_id,
                message="Snapshot saved successfully"
            )
        else:
            return HistorySaveResponse(
                success=True,
                snapshot_id=None,
                message="Snapshot skipped - recent snapshot exists"
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save snapshot: {str(e)}")


@router.get("/history/{address}", response_model=HistoryResponse)
async def get_wallet_history(address: str, days: int = 90):
    """
    Get historical sovereignty data for a wallet.
    
    Args:
        address: Algorand wallet address
        days: Number of days of history (default 90, max 365)
    """
    try:
        history = get_history_tracker()
        
        snapshots = history.get_history(address, days=days)
        progress = history.get_progress(address)
        all_time = history.get_all_time_stats(address)
        
        return HistoryResponse(
            address=address,
            snapshots=[SnapshotData(**s) for s in snapshots],
            progress=ProgressData(
                current_ratio=progress.current_ratio,
                previous_ratio=progress.previous_ratio,
                change_absolute=progress.change_absolute,
                change_pct=progress.change_pct,
                trend=progress.trend,
                days_tracked=progress.days_tracked,
                snapshots_count=progress.snapshots_count,
                projected_next_status=progress.projected_next_status
            ),
            all_time=AllTimeData(
                high=all_time.high,
                low=all_time.low,
                average=all_time.average,
                first_tracked=str(all_time.first_tracked),
                last_tracked=str(all_time.last_tracked)
            ) if all_time else None
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get history: {str(e)}")


@router.delete("/history/{address}", response_model=DeleteHistoryResponse)
async def delete_wallet_history(address: str):
    """
    Delete all historical data for a wallet (privacy feature).
    """
    try:
        history = get_history_tracker()
        deleted_count = history.delete_history(address)
        
        return DeleteHistoryResponse(
            success=True,
            deleted_count=deleted_count
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete history: {str(e)}")


# ============================================================================
# HELPER FUNCTION - Add to your analyze endpoint
# ============================================================================

def get_history_summary(address: str) -> Optional[HistorySummary]:
    """
    Get a quick history summary to include in analyze response.
    Call this after successful analysis.
    """
    try:
        history = get_history_tracker()
        progress = history.get_progress(address)
        
        if progress.snapshots_count == 0:
            return HistorySummary(
                has_history=False,
                snapshots_count=0,
                trend=None,
                change_30d_pct=None
            )
        
        return HistorySummary(
            has_history=True,
            snapshots_count=progress.snapshots_count,
            trend=progress.trend,
            change_30d_pct=progress.change_pct
        )
    except:
        return None


# ============================================================================
# INTEGRATION EXAMPLE - Modify your existing /analyze endpoint
# ============================================================================
"""
In your existing POST /api/v1/analyze endpoint, add after successful analysis:

    # Auto-save snapshot for history tracking
    from core.history import get_history_tracker
    
    history = get_history_tracker()
    history.save_snapshot(request.address, response_data)
    
    # Add history summary to response
    history_summary = get_history_summary(request.address)
    if history_summary:
        response_data["history"] = history_summary.dict()

This will:
1. Automatically save a snapshot after each analysis
2. Include history summary in the response
"""
