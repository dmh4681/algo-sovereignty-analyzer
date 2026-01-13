"""
API routes for sovereignty alerts and rebalancing suggestions.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime

from core.alerts import AlertEngine, Alert, AlertType
from core.rebalancer import RebalanceEngine, RebalanceSuggestion
from core.analyzer import AlgorandSovereigntyAnalyzer
from core.history import get_history_manager

router = APIRouter(prefix="/alerts", tags=["alerts"])
rebalance_router = APIRouter(prefix="/rebalance", tags=["rebalance"])


# -----------------------------------------------------------------------------
# Request/Response Schemas
# -----------------------------------------------------------------------------

class AlertCheckRequest(BaseModel):
    """Request to check alerts for a wallet."""
    address: str = Field(..., description="Algorand wallet address")
    monthly_fixed_expenses: Optional[float] = Field(None, description="Monthly fixed expenses in USD")
    user_prefs: Optional[Dict[str, Any]] = Field(None, description="User alert preferences")


class AlertConfigureRequest(BaseModel):
    """Request to configure alert preferences."""
    enabled_types: Optional[List[str]] = Field(None, description="List of enabled alert types")
    thresholds: Optional[Dict[str, float]] = Field(None, description="Custom thresholds")
    max_concentration: Optional[float] = Field(0.5, description="Max single asset concentration (0-1)")
    price_targets: Optional[Dict[str, Dict[str, float]]] = Field(None, description="Price targets per asset")


class AlertResponse(BaseModel):
    """A single alert in the response."""
    type: str
    severity: str
    title: str
    message: str
    suggested_action: str
    timestamp: str
    metadata: Dict[str, Any]


class AlertCheckResponse(BaseModel):
    """Response containing all alerts for a wallet."""
    address: str
    alerts: List[AlertResponse]
    alert_count: int
    has_critical_alerts: bool
    checked_at: str


class RebalanceSuggestionResponse(BaseModel):
    """A single rebalancing suggestion."""
    from_asset: str
    to_asset: str
    amount: float
    reason: str
    impact_on_score: float


class RebalanceSuggestionsResponse(BaseModel):
    """Response containing rebalancing suggestions."""
    address: str
    suggestions: List[RebalanceSuggestionResponse]
    current_score: Optional[float]
    estimated_score_after: Optional[float]
    generated_at: str


class SimulateRebalanceRequest(BaseModel):
    """Request to simulate a rebalance."""
    address: str = Field(..., description="Algorand wallet address")
    monthly_fixed_expenses: Optional[float] = Field(None, description="Monthly fixed expenses in USD")
    target_score: Optional[float] = Field(None, description="Target sovereignty score")


class SimulateRebalanceResponse(BaseModel):
    """Response from simulating a rebalance."""
    address: str
    current_score: Optional[float]
    target_score: float
    optimal_allocation: Dict[str, float]
    suggestions: List[RebalanceSuggestionResponse]
    estimated_score_after: Optional[float]
    simulated_at: str


# -----------------------------------------------------------------------------
# Alert Endpoints
# -----------------------------------------------------------------------------

@router.post("/check", response_model=AlertCheckResponse)
async def check_alerts(request: AlertCheckRequest):
    """
    Check all alerts for a wallet address.

    Analyzes the wallet and generates alerts based on:
    - Sovereignty score thresholds
    - Score drops compared to history
    - Concentration risk
    - Milestone achievements
    """
    try:
        # Analyze the wallet
        analyzer = AlgorandSovereigntyAnalyzer(use_local_node=False)
        categories = analyzer.analyze_wallet(request.address)

        if not categories:
            raise HTTPException(status_code=404, detail="Wallet not found or empty")

        # Calculate sovereignty metrics if expenses provided
        sovereignty_data = None
        if request.monthly_fixed_expenses and request.monthly_fixed_expenses > 0:
            sovereignty_data = analyzer.calculate_sovereignty_metrics(
                categories, request.monthly_fixed_expenses
            )

        # Get history for comparison
        history_manager = get_history_manager()
        history = history_manager.get_history(request.address, days=90)

        # Generate alerts
        alert_engine = AlertEngine()
        user_prefs = request.user_prefs or {}

        alerts = alert_engine.generate_all_alerts(
            categories=categories,
            sovereignty_data=sovereignty_data,
            history=history,
            user_prefs=user_prefs
        )

        # Convert alerts to response format
        alert_responses = [
            AlertResponse(
                type=alert.type.value,
                severity=alert.severity,
                title=alert.title,
                message=alert.message,
                suggested_action=alert.suggested_action,
                timestamp=alert.timestamp.isoformat(),
                metadata=alert.metadata
            )
            for alert in alerts
        ]

        has_critical = any(a.severity == "critical" for a in alerts)

        return AlertCheckResponse(
            address=request.address,
            alerts=alert_responses,
            alert_count=len(alerts),
            has_critical_alerts=has_critical,
            checked_at=datetime.utcnow().isoformat()
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error checking alerts: {str(e)}")


@router.post("/configure")
async def configure_alerts(request: AlertConfigureRequest):
    """
    Configure alert preferences.

    Note: This is a placeholder that returns the configuration.
    In a full implementation, this would persist to user settings.
    """
    # Validate enabled types
    valid_types = [t.value for t in AlertType]
    if request.enabled_types:
        for t in request.enabled_types:
            if t not in valid_types:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid alert type: {t}. Valid types: {valid_types}"
                )

    return {
        "message": "Alert preferences configured",
        "config": {
            "enabled_types": request.enabled_types or valid_types,
            "thresholds": request.thresholds or {},
            "max_concentration": request.max_concentration,
            "price_targets": request.price_targets or {}
        }
    }


# -----------------------------------------------------------------------------
# Rebalance Endpoints
# -----------------------------------------------------------------------------

@rebalance_router.get("/suggestions/{address}", response_model=RebalanceSuggestionsResponse)
async def get_rebalance_suggestions(
    address: str,
    monthly_fixed_expenses: Optional[float] = None,
    target_score: Optional[float] = None
):
    """
    Get rebalancing suggestions for a wallet.

    Analyzes current holdings and suggests moves to improve sovereignty score.
    """
    try:
        # Analyze the wallet
        analyzer = AlgorandSovereigntyAnalyzer(use_local_node=False)
        categories = analyzer.analyze_wallet(address)

        if not categories:
            raise HTTPException(status_code=404, detail="Wallet not found or empty")

        # Calculate current sovereignty
        sovereignty_data = None
        current_score = None
        if monthly_fixed_expenses and monthly_fixed_expenses > 0:
            sovereignty_data = analyzer.calculate_sovereignty_metrics(
                categories, monthly_fixed_expenses
            )
            if sovereignty_data:
                current_score = sovereignty_data.sovereignty_ratio

        # Determine target score
        if target_score is None:
            # Default: aim for next milestone
            if current_score is None:
                target_score = 3.0  # Robust
            elif current_score < 1.0:
                target_score = 1.0  # Fragile
            elif current_score < 3.0:
                target_score = 3.0  # Robust
            elif current_score < 6.0:
                target_score = 6.0  # Antifragile
            else:
                target_score = 20.0  # Generationally Sovereign

        # Generate suggestions
        rebalance_engine = RebalanceEngine()

        # Calculate optimal allocation
        optimal_allocation = rebalance_engine.calculate_optimal_allocation(
            current=categories,
            target_score=target_score
        )

        # Get specific suggestions
        suggestions = rebalance_engine.suggest_rebalancing(
            current_holdings=categories,
            target_allocation=optimal_allocation
        )

        # Estimate score after rebalance
        estimated_after = None
        if sovereignty_data:
            estimated_after = rebalance_engine.estimate_score_after_rebalance(
                current_holdings=categories,
                suggestions=suggestions,
                current_sovereignty=sovereignty_data
            )

        # Convert to response format
        suggestion_responses = [
            RebalanceSuggestionResponse(
                from_asset=s.from_asset,
                to_asset=s.to_asset,
                amount=s.amount,
                reason=s.reason,
                impact_on_score=s.impact_on_score
            )
            for s in suggestions
        ]

        return RebalanceSuggestionsResponse(
            address=address,
            suggestions=suggestion_responses,
            current_score=current_score,
            estimated_score_after=estimated_after,
            generated_at=datetime.utcnow().isoformat()
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating suggestions: {str(e)}")


@rebalance_router.post("/simulate", response_model=SimulateRebalanceResponse)
async def simulate_rebalance(request: SimulateRebalanceRequest):
    """
    Simulate a portfolio rebalance and show expected impact.

    Returns optimal allocation and specific suggestions with
    estimated impact on sovereignty score.
    """
    try:
        # Analyze the wallet
        analyzer = AlgorandSovereigntyAnalyzer(use_local_node=False)
        categories = analyzer.analyze_wallet(request.address)

        if not categories:
            raise HTTPException(status_code=404, detail="Wallet not found or empty")

        # Calculate current sovereignty
        sovereignty_data = None
        current_score = None
        if request.monthly_fixed_expenses and request.monthly_fixed_expenses > 0:
            sovereignty_data = analyzer.calculate_sovereignty_metrics(
                categories, request.monthly_fixed_expenses
            )
            if sovereignty_data:
                current_score = sovereignty_data.sovereignty_ratio

        # Determine target score
        target_score = request.target_score
        if target_score is None:
            target_score = 6.0  # Default to Antifragile

        # Generate rebalancing plan
        rebalance_engine = RebalanceEngine()

        optimal_allocation = rebalance_engine.calculate_optimal_allocation(
            current=categories,
            target_score=target_score
        )

        suggestions = rebalance_engine.suggest_rebalancing(
            current_holdings=categories,
            target_allocation=optimal_allocation
        )

        estimated_after = None
        if sovereignty_data:
            estimated_after = rebalance_engine.estimate_score_after_rebalance(
                current_holdings=categories,
                suggestions=suggestions,
                current_sovereignty=sovereignty_data
            )

        suggestion_responses = [
            RebalanceSuggestionResponse(
                from_asset=s.from_asset,
                to_asset=s.to_asset,
                amount=s.amount,
                reason=s.reason,
                impact_on_score=s.impact_on_score
            )
            for s in suggestions
        ]

        return SimulateRebalanceResponse(
            address=request.address,
            current_score=current_score,
            target_score=target_score,
            optimal_allocation=optimal_allocation,
            suggestions=suggestion_responses,
            estimated_score_after=estimated_after,
            simulated_at=datetime.utcnow().isoformat()
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error simulating rebalance: {str(e)}")
