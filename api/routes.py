from fastapi import APIRouter, HTTPException, Query, Path
from core.analyzer import AlgorandSovereigntyAnalyzer
from core.history import SovereigntySnapshot, get_history_manager
from core.pricing import get_hardcoded_price, get_gold_price_per_oz, get_silver_price_per_oz
from core.network import AlgorandNetworkStats, microalgos_to_algo
from .schemas import (
    AnalysisResponse,
    AnalyzeRequest,
    HistorySaveRequest,
    HistorySaveResponse,
    HistoryResponse,
    NetworkStatsResponse,
    NetworkInfo,
    FoundationInfo,
    CommunityInfo,
    ScoreBreakdown,
    WalletParticipationResponse,
    ParticipationKeyInfo
)
from .agent import SovereigntyCoach, AdviceRequest
from typing import Dict, Any, Tuple, Optional, List
from datetime import datetime, timedelta
import asyncio

router = APIRouter()

# Global network stats instance (reused for caching)
_network_stats: Optional[AlgorandNetworkStats] = None

def get_network_stats_client() -> AlgorandNetworkStats:
    """Get or create the network stats client singleton."""
    global _network_stats
    if _network_stats is None:
        _network_stats = AlgorandNetworkStats()
    return _network_stats

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


@router.get("/history/{address}")
async def get_history(
    address: str = Path(..., description="Wallet address"),
    days: int = Query(90, description="Number of days (30, 90, or 365)")
):
    """
    Get historical sovereignty snapshots for an address with progress metrics.

    Returns snapshots within the specified time period along with progress
    tracking data for the HistoryChart component.
    """
    # Validate days parameter
    if days not in (30, 90, 365):
        days = 90

    history_manager = get_history_manager()
    snapshots = history_manager.get_history(address, days)

    # Calculate progress metrics
    progress = _calculate_progress(snapshots)

    # Calculate all-time stats
    all_time = _calculate_all_time(snapshots) if snapshots else None

    return {
        "address": address,
        "snapshots": snapshots,
        "count": len(snapshots),
        "progress": progress,
        "all_time": all_time
    }


def _calculate_progress(snapshots: list) -> dict:
    """Calculate progress metrics from snapshots."""
    if not snapshots:
        return {
            "current_ratio": 0,
            "previous_ratio": None,
            "change_absolute": None,
            "change_pct": None,
            "trend": "new",
            "days_tracked": 0,
            "snapshots_count": 0,
            "projected_next_status": None
        }

    # Snapshots are newest first
    current = snapshots[0]
    current_ratio = current.sovereignty_ratio if hasattr(current, 'sovereignty_ratio') else current.get('sovereignty_ratio', 0)

    # Find snapshot from ~30 days ago
    previous_ratio = None
    for snap in snapshots:
        ts = snap.timestamp if hasattr(snap, 'timestamp') else snap.get('timestamp', '')
        try:
            if isinstance(ts, str):
                snap_date = datetime.fromisoformat(ts.replace('Z', '+00:00'))
            else:
                snap_date = ts
            now = datetime.now(snap_date.tzinfo) if snap_date.tzinfo else datetime.utcnow()
            if (now - snap_date).days >= 25:
                previous_ratio = snap.sovereignty_ratio if hasattr(snap, 'sovereignty_ratio') else snap.get('sovereignty_ratio', 0)
                break
        except Exception:
            continue

    # Calculate change
    change_absolute = None
    change_pct = None
    trend = "new" if len(snapshots) == 1 else "stable"

    if previous_ratio is not None:
        change_absolute = round(current_ratio - previous_ratio, 2)
        change_pct = round((change_absolute / previous_ratio) * 100, 1) if previous_ratio > 0 else 0

        if change_pct > 5:
            trend = "improving"
        elif change_pct < -5:
            trend = "declining"
        else:
            trend = "stable"

    # Calculate days tracked
    days_tracked = 0
    if snapshots:
        oldest = snapshots[-1]
        ts = oldest.timestamp if hasattr(oldest, 'timestamp') else oldest.get('timestamp', '')
        try:
            if isinstance(ts, str):
                oldest_date = datetime.fromisoformat(ts.replace('Z', '+00:00'))
            else:
                oldest_date = ts
            now = datetime.now(oldest_date.tzinfo) if oldest_date.tzinfo else datetime.utcnow()
            days_tracked = (now - oldest_date).days
        except Exception:
            pass

    # Project next status
    projected_next_status = None
    STATUS_THRESHOLDS = [
        (1.0, "Fragile"),
        (3.0, "Robust"),
        (6.0, "Antifragile"),
        (20.0, "Generationally Sovereign")
    ]

    if trend == "improving" and change_absolute and change_absolute > 0:
        for threshold, status in STATUS_THRESHOLDS:
            if current_ratio < threshold:
                gap = threshold - current_ratio
                days_to_reach = int(gap / change_absolute * 30) if change_absolute > 0 else None
                if days_to_reach and days_to_reach < 365:
                    projected_date = datetime.now() + timedelta(days=days_to_reach)
                    projected_next_status = {
                        "status": status,
                        "ratio_needed": threshold,
                        "projected_date": projected_date.strftime("%Y-%m-%d")
                    }
                break

    return {
        "current_ratio": current_ratio,
        "previous_ratio": previous_ratio,
        "change_absolute": change_absolute,
        "change_pct": change_pct,
        "trend": trend,
        "days_tracked": days_tracked,
        "snapshots_count": len(snapshots),
        "projected_next_status": projected_next_status
    }


def _calculate_all_time(snapshots: list) -> Optional[dict]:
    """Calculate all-time statistics."""
    if not snapshots:
        return None

    ratios = []
    for snap in snapshots:
        ratio = snap.sovereignty_ratio if hasattr(snap, 'sovereignty_ratio') else snap.get('sovereignty_ratio', 0)
        ratios.append(ratio)

    oldest = snapshots[-1]
    ts = oldest.timestamp if hasattr(oldest, 'timestamp') else oldest.get('timestamp', '')

    return {
        "high": round(max(ratios), 2),
        "low": round(min(ratios), 2),
        "average": round(sum(ratios) / len(ratios), 2),
        "first_tracked": ts if isinstance(ts, str) else ts.isoformat() if hasattr(ts, 'isoformat') else str(ts)
    }


@router.get("/gold-silver-ratio")
async def get_gold_silver_ratio():
    """
    Get current Gold/Silver ratio using live Yahoo Finance spot prices.

    Fetches real-time COMEX futures prices for Gold (GC=F) and Silver (SI=F).
    Falls back to hardcoded prices on API failure.
    """
    # Fetch live prices per troy ounce from Yahoo Finance
    gold_price = get_gold_price_per_oz()
    silver_price = get_silver_price_per_oz()

    # Ensure we have valid prices
    if gold_price is None:
        gold_price = 4500.0  # Fallback
    if silver_price is None:
        silver_price = 70.0  # Fallback

    # Round for display
    gold_price = round(gold_price, 2)
    silver_price = round(silver_price, 2)

    # Calculate ratio
    ratio = round(gold_price / silver_price, 2)

    # Historical context
    historical_mean = 15.0
    historical_range = {"low": 12, "high": 90}

    # Status indicator
    if ratio > 80:
        status = "undervalued"
        color = "red"
        message = "Silver significantly undervalued relative to gold"
    elif ratio > 60:
        status = "below_average"
        color = "orange"
        message = "Silver moderately undervalued"
    elif ratio > 40:
        status = "normalized"
        color = "yellow"
        message = "Ratio approaching historical norms"
    else:
        status = "compressed"
        color = "green"
        message = "Ratio compressed - silver relatively expensive"

    return {
        "ratio": ratio,
        "gold_price": gold_price,
        "silver_price": silver_price,
        "historical_mean": historical_mean,
        "historical_range": historical_range,
        "status": status,
        "color": color,
        "message": message,
        "interpretation": {
            "what_it_means": "The Gold/Silver ratio measures how many ounces of silver it takes to buy one ounce of gold.",
            "current_signal": f"At {ratio}:1, silver is {('undervalued' if ratio > 60 else 'fairly valued')} compared to gold.",
            "historical_note": f"The ratio has ranged from {historical_range['low']}:1 to {historical_range['high']}:1 over the past century. The long-term mean is around {historical_mean}:1."
        }
    }


# -----------------------------------------------------------------------------
# Network Stats Endpoints
# -----------------------------------------------------------------------------

@router.get("/network/stats", response_model=NetworkStatsResponse)
async def get_network_statistics():
    """
    Get current Algorand network participation and decentralization statistics.

    Returns network-wide metrics including:
    - Total supply and online stake
    - Foundation stake breakdown
    - Community stake percentage
    - Decentralization score (0-100)

    Data is cached for 5 minutes.
    """
    client = get_network_stats_client()

    try:
        summary = await client.get_decentralization_summary()

        # Convert microalgos to ALGO for response
        network_info = NetworkInfo(
            total_supply_algo=round(microalgos_to_algo(summary.network.total_supply), 2),
            online_stake_algo=round(microalgos_to_algo(summary.network.online_stake), 2),
            participation_rate=summary.network.participation_rate,
            current_round=summary.network.current_round
        )

        foundation_info = FoundationInfo(
            total_balance_algo=round(microalgos_to_algo(summary.foundation.total_balance), 2),
            online_balance_algo=round(microalgos_to_algo(summary.foundation.online_balance), 2),
            pct_of_total_supply=summary.foundation.foundation_pct_of_supply,
            pct_of_online_stake=summary.foundation.foundation_pct_of_online,
            address_count=len(summary.foundation.foundation_addresses)
        )

        community_info = CommunityInfo(
            estimated_stake_algo=round(microalgos_to_algo(summary.community_stake), 2),
            pct_of_online_stake=summary.community_pct_of_online
        )

        # Build score breakdown if available
        score_breakdown = None
        if summary.score_breakdown:
            b = summary.score_breakdown
            score_breakdown = ScoreBreakdown(
                community_online_pct=b.community_online_pct,
                community_online_score=b.community_online_score,
                participation_rate_score=b.participation_rate_score,
                foundation_supply_pct=b.foundation_supply_pct,
                foundation_supply_penalty=b.foundation_supply_penalty,
                foundation_potential_control=b.foundation_potential_control,
                potential_control_penalty=b.potential_control_penalty,
                relay_centralization_penalty=b.relay_centralization_penalty,
                governance_penalty=b.governance_penalty,
                raw_score=b.raw_score,
                final_score=b.final_score
            )

        # Format timestamp
        fetched_at = datetime.utcfromtimestamp(summary.fetched_at).isoformat() + "Z"

        return NetworkStatsResponse(
            network=network_info,
            foundation=foundation_info,
            community=community_info,
            decentralization_score=summary.decentralization_score,
            score_breakdown=score_breakdown,
            estimated_node_count=3075,  # Estimate from Nodely.io
            fetched_at=fetched_at
        )

    except ConnectionError as e:
        raise HTTPException(
            status_code=503,
            detail=f"Unable to connect to Algorand network: {str(e)}"
        )
    except Exception as e:
        print(f"Error fetching network stats: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch network statistics: {str(e)}"
        )


def _get_contribution_tier(balance_algo: float, is_participating: bool) -> str:
    """
    Classify wallet contribution tier based on balance and participation status.
    """
    if not is_participating:
        if balance_algo >= 30000:
            return "Eligible but Offline"
        return "Observer"

    # Participating wallets
    if balance_algo >= 1_000_000:
        return "Whale Validator"
    elif balance_algo >= 100_000:
        return "Major Validator"
    elif balance_algo >= 30_000:
        return "Active Participant"
    elif balance_algo >= 1_000:
        return "Community Node"
    else:
        return "Micro Validator"


@router.get("/network/wallet/{address}", response_model=WalletParticipationResponse)
async def get_wallet_participation(
    address: str = Path(..., description="Algorand wallet address", min_length=58, max_length=58)
):
    """
    Check participation status for a specific Algorand wallet.

    Returns:
    - Whether the wallet is actively participating in consensus
    - Current balance and stake percentage
    - Participation key details (if registered)
    - Contribution tier classification

    Data is cached for 1 minute.
    """
    client = get_network_stats_client()

    try:
        wallet = await client.check_wallet_participation(address)

        # Convert balance to ALGO
        balance_algo = microalgos_to_algo(wallet.balance)

        # Build participation key info if available
        participation_key = None
        if wallet.vote_first_valid or wallet.vote_last_valid:
            rounds_remaining = None
            if wallet.vote_last_valid and not wallet.is_key_expired:
                rounds_remaining = wallet.vote_last_valid - wallet.current_round

            participation_key = ParticipationKeyInfo(
                first_valid=wallet.vote_first_valid,
                last_valid=wallet.vote_last_valid,
                is_expired=wallet.is_key_expired,
                rounds_remaining=rounds_remaining
            )

        # Determine contribution tier
        contribution_tier = _get_contribution_tier(balance_algo, wallet.is_online)

        return WalletParticipationResponse(
            address=address,
            is_participating=wallet.is_online,
            balance_algo=round(balance_algo, 6),
            stake_percentage=wallet.stake_percentage,
            participation_key=participation_key,
            contribution_tier=contribution_tier,
            current_round=wallet.current_round
        )

    except ConnectionError as e:
        raise HTTPException(
            status_code=503,
            detail=f"Unable to connect to Algorand network: {str(e)}"
        )
    except Exception as e:
        print(f"Error fetching wallet participation: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch wallet participation: {str(e)}"
        )
