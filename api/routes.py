from fastapi import APIRouter, HTTPException, Query, Path
from core.analyzer import AlgorandSovereigntyAnalyzer
from core.history import SovereigntySnapshot, get_history_manager
from core.btc_history import get_btc_history_manager, save_current_prices
from core.pricing import (
    get_hardcoded_price,
    get_gold_price_per_oz,
    get_silver_price_per_oz,
    get_meld_gold_price,
    get_meld_silver_price,
    get_bitcoin_spot_price,
    get_gobtc_price,
    get_wbtc_price,
    GRAMS_PER_TROY_OZ,
    GOBTC_ASA,
    WBTC_ASA
)
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
    ParticipationKeyInfo,
    MeldArbitrageResponse
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

    # Snapshots are sorted oldest first, so newest is at the end
    current = snapshots[-1]
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

    # Calculate days tracked (snapshots sorted oldest first)
    days_tracked = 0
    if snapshots:
        oldest = snapshots[0]
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
    """Calculate all-time statistics (snapshots sorted oldest first)."""
    if not snapshots:
        return None

    ratios = []
    for snap in snapshots:
        ratio = snap.sovereignty_ratio if hasattr(snap, 'sovereignty_ratio') else snap.get('sovereignty_ratio', 0)
        ratios.append(ratio)

    # Oldest is first element
    oldest = snapshots[0]
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


# -----------------------------------------------------------------------------
# Meld Arbitrage Endpoint
# -----------------------------------------------------------------------------

def _calculate_arbitrage_signal(premium_pct: float) -> tuple:
    """
    Determine trading signal based on premium percentage.

    Thresholds:
    - STRONG_BUY/SELL: >6% discount/premium
    - BUY/SELL: 0.5% - 6%
    - HOLD: within ±0.5% (fair value)

    Args:
        premium_pct: The premium/discount percentage of Meld vs spot

    Returns:
        Tuple of (signal_name, signal_strength 0-100)
    """
    # Signal strength scales from 0-100 based on how far past threshold
    # For STRONG signals: 6% = ~50 strength, 12% = 100 strength
    # For regular signals: 0.5% = ~10 strength, 6% = ~50 strength

    if premium_pct > 6:
        # STRONG_SELL: asset trading >6% above spot
        strength = min(100, 50 + (premium_pct - 6) * 8.33)
        return ('STRONG_SELL', strength)
    elif premium_pct > 0.5:
        # SELL: asset trading 0.5-6% above spot
        strength = 10 + (premium_pct - 0.5) * 7.27  # scales 10-50
        return ('SELL', strength)
    elif premium_pct < -6:
        # STRONG_BUY: asset trading >6% below spot
        strength = min(100, 50 + (abs(premium_pct) - 6) * 8.33)
        return ('STRONG_BUY', strength)
    elif premium_pct < -0.5:
        # BUY: asset trading 0.5-6% below spot
        strength = 10 + (abs(premium_pct) - 0.5) * 7.27  # scales 10-50
        return ('BUY', strength)
    else:
        # HOLD: within ±0.5% of spot (fair value)
        return ('HOLD', 0)


def _calculate_rotation_signal(gold_premium_pct: float, silver_premium_pct: float) -> dict:
    """
    Calculate rotation signal between gold and silver based on premium spread.

    The spread = silver_premium - gold_premium
    - Positive spread (silver more expensive): Signal to rotate silver → gold
    - Negative spread (gold more expensive): Signal to rotate gold → silver

    Thresholds:
    - |spread| > 3%: Active rotation signal
    - |spread| 1-3%: Weak signal (consider)
    - |spread| < 1%: No signal (metals at parity)

    Returns signal with strength (0-100) scaled by how far past threshold.
    """
    spread_pct = silver_premium_pct - gold_premium_pct
    abs_spread = abs(spread_pct)

    if abs_spread < 1.0:
        return {
            'signal': 'HOLD',
            'strength': 0,
            'spread_pct': round(spread_pct, 2),
            'description': 'Gold and silver premiums at parity - no rotation advantage'
        }
    elif abs_spread < 3.0:
        # Weak signal zone (1-3%)
        strength = (abs_spread - 1.0) / 2.0 * 33  # Scale 0-33%
        if spread_pct > 0:
            return {
                'signal': 'CONSIDER_SILVER_TO_GOLD',
                'strength': round(strength, 1),
                'spread_pct': round(spread_pct, 2),
                'description': f'Silver slightly overpriced vs gold ({spread_pct:.2f}% spread) - weak rotation signal'
            }
        else:
            return {
                'signal': 'CONSIDER_GOLD_TO_SILVER',
                'strength': round(strength, 1),
                'spread_pct': round(spread_pct, 2),
                'description': f'Gold slightly overpriced vs silver ({abs_spread:.2f}% spread) - weak rotation signal'
            }
    else:
        # Strong signal zone (>3%)
        # Strength scales from 33% at 3% spread to 100% at 9%+ spread
        strength = min(100, 33 + (abs_spread - 3.0) / 6.0 * 67)
        if spread_pct > 0:
            return {
                'signal': 'SILVER_TO_GOLD',
                'strength': round(strength, 1),
                'spread_pct': round(spread_pct, 2),
                'description': f'Silver overpriced vs gold by {spread_pct:.2f}% - rotate silver to gold'
            }
        else:
            return {
                'signal': 'GOLD_TO_SILVER',
                'strength': round(strength, 1),
                'spread_pct': round(spread_pct, 2),
                'description': f'Gold overpriced vs silver by {abs_spread:.2f}% - rotate gold to silver'
            }


def _get_gsr_context(gsr: float) -> dict:
    """
    Provide historical context for the Gold/Silver Ratio (GSR).

    Historical ranges:
    - Modern era average: ~60:1
    - Historical (pre-1900): ~15:1
    - Extreme high: 120:1 (March 2020)
    - Extreme low: 30:1 (1980, 2011)
    """
    if gsr >= 80:
        return {
            'zone': 'extreme_high',
            'color': 'red',
            'message': f'GSR at {gsr:.1f} - silver historically cheap vs gold (buy silver)',
            'bias': 'silver'
        }
    elif gsr >= 70:
        return {
            'zone': 'high',
            'color': 'orange',
            'message': f'GSR at {gsr:.1f} - silver undervalued vs gold',
            'bias': 'silver'
        }
    elif gsr >= 50:
        return {
            'zone': 'normal',
            'color': 'yellow',
            'message': f'GSR at {gsr:.1f} - normal range, no strong bias',
            'bias': 'neutral'
        }
    elif gsr >= 40:
        return {
            'zone': 'low',
            'color': 'green',
            'message': f'GSR at {gsr:.1f} - gold undervalued vs silver',
            'bias': 'gold'
        }
    else:
        return {
            'zone': 'extreme_low',
            'color': 'green',
            'message': f'GSR at {gsr:.1f} - gold historically cheap vs silver (buy gold)',
            'bias': 'gold'
        }


@router.get("/arbitrage/meld", response_model=MeldArbitrageResponse)
async def get_meld_arbitrage():
    """
    Compare Algorand wrapped assets to their spot prices.

    Analyzes:
    - Meld GOLD$/SILVER$ vs Yahoo Finance spot prices
    - goBTC vs Coinbase BTC spot price
    - Gold/Silver Ratio (GSR) with rotation signals

    Returns premium/discount percentage and trading signals for arbitrage opportunities.

    **Signal Interpretation:**
    - STRONG_BUY: Asset >10% below spot (buy on Algorand, it's cheap)
    - BUY: Asset 5-10% below spot
    - HOLD: Within +/-5% of spot (fair value)
    - SELL: Asset 5-10% above spot
    - STRONG_SELL: Asset >10% above spot (sell on Algorand)

    **Data Sources:**
    - Gold/Silver spot: Yahoo Finance (COMEX futures GC=F, SI=F)
    - Bitcoin spot: Coinbase API
    - On-chain prices: Vestige API (Algorand DEX aggregator)
    """
    result = {
        'gold': None,
        'silver': None,
        'bitcoin': None,
        'gsr': None,
        'rotation': None,
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'data_complete': True
    }

    # =========== GOLD ===========
    try:
        spot_gold = get_gold_price_per_oz()
        meld_gold = get_meld_gold_price()

        if spot_gold and meld_gold and spot_gold > 0:
            implied_gold = spot_gold / GRAMS_PER_TROY_OZ
            premium_usd = meld_gold - implied_gold
            premium_pct = (premium_usd / implied_gold) * 100
            signal, strength = _calculate_arbitrage_signal(premium_pct)

            result['gold'] = {
                'spot_per_oz': round(spot_gold, 2),
                'implied_per_gram': round(implied_gold, 4),
                'meld_price': round(meld_gold, 4),
                'premium_pct': round(premium_pct, 2),
                'premium_usd': round(premium_usd, 4),
                'signal': signal,
                'signal_strength': round(strength, 1)
            }
        else:
            result['data_complete'] = False
            result['gold'] = {
                'error': 'Unable to fetch gold prices',
                'spot_available': spot_gold is not None,
                'meld_available': meld_gold is not None
            }
    except Exception as e:
        print(f"Error calculating gold arbitrage: {e}")
        result['data_complete'] = False
        result['gold'] = {
            'error': str(e),
            'spot_available': False,
            'meld_available': False
        }

    # =========== SILVER ===========
    try:
        spot_silver = get_silver_price_per_oz()
        meld_silver = get_meld_silver_price()

        if spot_silver and meld_silver and spot_silver > 0:
            implied_silver = spot_silver / GRAMS_PER_TROY_OZ
            premium_usd = meld_silver - implied_silver
            premium_pct = (premium_usd / implied_silver) * 100
            signal, strength = _calculate_arbitrage_signal(premium_pct)

            result['silver'] = {
                'spot_per_oz': round(spot_silver, 2),
                'implied_per_gram': round(implied_silver, 4),
                'meld_price': round(meld_silver, 4),
                'premium_pct': round(premium_pct, 2),
                'premium_usd': round(premium_usd, 4),
                'signal': signal,
                'signal_strength': round(strength, 1)
            }
        else:
            result['data_complete'] = False
            result['silver'] = {
                'error': 'Unable to fetch silver prices',
                'spot_available': spot_silver is not None,
                'meld_available': meld_silver is not None
            }
    except Exception as e:
        print(f"Error calculating silver arbitrage: {e}")
        result['data_complete'] = False
        result['silver'] = {
            'error': str(e),
            'spot_available': False,
            'meld_available': False
        }

    # =========== BITCOIN (3-way: Spot vs goBTC vs WBTC) ===========
    try:
        spot_btc = get_bitcoin_spot_price()
        gobtc_price = get_gobtc_price()
        wbtc_price = get_wbtc_price()

        bitcoin_result = {
            'spot_price': None,
            'gobtc': None,
            'wbtc': None,
            'cross_dex_spread': None,
            'best_opportunity': None
        }

        if spot_btc and spot_btc > 0:
            bitcoin_result['spot_price'] = round(spot_btc, 2)

            # goBTC analysis
            if gobtc_price and gobtc_price > 0:
                gobtc_premium_usd = gobtc_price - spot_btc
                gobtc_premium_pct = (gobtc_premium_usd / spot_btc) * 100
                gobtc_signal, gobtc_strength = _calculate_arbitrage_signal(gobtc_premium_pct)

                bitcoin_result['gobtc'] = {
                    'price': round(gobtc_price, 2),
                    'premium_pct': round(gobtc_premium_pct, 2),
                    'premium_usd': round(gobtc_premium_usd, 2),
                    'signal': gobtc_signal,
                    'signal_strength': round(gobtc_strength, 1),
                    'asa_id': GOBTC_ASA,
                    'tinyman_url': f'https://app.tinyman.org/#/swap?asset_in=0&asset_out={GOBTC_ASA}'
                }
            else:
                bitcoin_result['gobtc'] = {'error': 'Unable to fetch goBTC price'}

            # WBTC analysis
            if wbtc_price and wbtc_price > 0:
                wbtc_premium_usd = wbtc_price - spot_btc
                wbtc_premium_pct = (wbtc_premium_usd / spot_btc) * 100
                wbtc_signal, wbtc_strength = _calculate_arbitrage_signal(wbtc_premium_pct)

                bitcoin_result['wbtc'] = {
                    'price': round(wbtc_price, 2),
                    'premium_pct': round(wbtc_premium_pct, 2),
                    'premium_usd': round(wbtc_premium_usd, 2),
                    'signal': wbtc_signal,
                    'signal_strength': round(wbtc_strength, 1),
                    'asa_id': WBTC_ASA,
                    'tinyman_url': f'https://app.tinyman.org/#/swap?asset_in=0&asset_out={WBTC_ASA}',
                    'liquidity_warning': 'Lower liquidity than goBTC - higher slippage risk'
                }
            else:
                bitcoin_result['wbtc'] = {'error': 'Unable to fetch WBTC price'}

            # Cross-DEX spread (goBTC vs WBTC)
            if gobtc_price and wbtc_price and gobtc_price > 0 and wbtc_price > 0:
                cross_spread_pct = ((gobtc_price - wbtc_price) / wbtc_price) * 100
                bitcoin_result['cross_dex_spread'] = {
                    'gobtc_vs_wbtc_pct': round(cross_spread_pct, 2),
                    'description': f"goBTC is {abs(cross_spread_pct):.2f}% {'more expensive' if cross_spread_pct > 0 else 'cheaper'} than WBTC"
                }

                # Determine best opportunity
                gobtc_prem = bitcoin_result['gobtc'].get('premium_pct', 0)
                wbtc_prem = bitcoin_result['wbtc'].get('premium_pct', 0)

                if gobtc_prem < wbtc_prem:
                    # goBTC is cheaper relative to spot
                    bitcoin_result['best_opportunity'] = {
                        'token': 'goBTC',
                        'action': 'BUY' if gobtc_prem < -0.5 else 'PREFER',
                        'reason': f"goBTC has deeper discount ({gobtc_prem:.2f}% vs {wbtc_prem:.2f}%)",
                        'advantage_pct': round(wbtc_prem - gobtc_prem, 2)
                    }
                elif wbtc_prem < gobtc_prem:
                    # WBTC is cheaper relative to spot
                    bitcoin_result['best_opportunity'] = {
                        'token': 'WBTC',
                        'action': 'BUY' if wbtc_prem < -0.5 else 'PREFER',
                        'reason': f"WBTC has deeper discount ({wbtc_prem:.2f}% vs {gobtc_prem:.2f}%)",
                        'advantage_pct': round(gobtc_prem - wbtc_prem, 2),
                        'liquidity_note': 'Lower liquidity - use limit orders'
                    }
                else:
                    bitcoin_result['best_opportunity'] = {
                        'token': 'goBTC',
                        'action': 'EQUAL',
                        'reason': 'Both tokens at same premium - prefer goBTC for better liquidity',
                        'advantage_pct': 0
                    }

            result['bitcoin'] = bitcoin_result
        else:
            result['data_complete'] = False
            result['bitcoin'] = {
                'error': 'Unable to fetch Bitcoin spot price',
                'spot_available': False,
                'gobtc_available': gobtc_price is not None,
                'wbtc_available': wbtc_price is not None
            }
    except Exception as e:
        print(f"Error calculating Bitcoin arbitrage: {e}")
        result['data_complete'] = False
        result['bitcoin'] = {
            'error': str(e),
            'spot_available': False,
            'gobtc_available': False,
            'wbtc_available': False
        }

    # =========== GSR & ROTATION SIGNAL ===========
    try:
        # Calculate GSR if we have both gold and silver data
        gold_data = result.get('gold')
        silver_data = result.get('silver')

        if (gold_data and 'meld_price' in gold_data and
            silver_data and 'meld_price' in silver_data):

            meld_gold = gold_data['meld_price']
            meld_silver = silver_data['meld_price']

            # Calculate Meld GSR (gold price / silver price in same units - per gram)
            meld_gsr = meld_gold / meld_silver if meld_silver > 0 else None

            if meld_gsr:
                # Get spot GSR for comparison
                spot_gold_per_gram = gold_data['implied_per_gram']
                spot_silver_per_gram = silver_data['implied_per_gram']
                spot_gsr = spot_gold_per_gram / spot_silver_per_gram if spot_silver_per_gram > 0 else None

                gsr_context = _get_gsr_context(meld_gsr)

                result['gsr'] = {
                    'meld_gsr': round(meld_gsr, 2),
                    'spot_gsr': round(spot_gsr, 2) if spot_gsr else None,
                    'gsr_spread_pct': round(((meld_gsr - spot_gsr) / spot_gsr) * 100, 2) if spot_gsr else None,
                    'context': gsr_context
                }

                # Calculate rotation signal based on premium spreads
                gold_premium = gold_data.get('premium_pct', 0)
                silver_premium = silver_data.get('premium_pct', 0)

                rotation_signal = _calculate_rotation_signal(gold_premium, silver_premium)
                result['rotation'] = rotation_signal

    except Exception as e:
        print(f"Error calculating GSR/rotation: {e}")
        # GSR is optional, don't fail the whole response

    # Auto-capture price snapshot for history
    try:
        save_current_prices()
    except Exception as e:
        print(f"Warning: Failed to save BTC price snapshot: {e}")

    return result


@router.get("/arbitrage/btc-history")
async def get_btc_arbitrage_history(
    hours: int = Query(24, ge=1, le=720, description="Hours of history (1-720, default 24)")
):
    """
    Get historical Bitcoin price data for charting.

    Returns time-series data of:
    - Coinbase spot BTC price
    - goBTC price and premium vs spot
    - WBTC price and premium vs spot

    Useful for identifying arbitrage patterns over time.
    """
    try:
        history_manager = get_btc_history_manager()
        snapshots = history_manager.get_history(hours=hours)
        stats = history_manager.get_stats(hours=hours)

        # Convert to JSON-serializable format
        data_points = []
        for snap in snapshots:
            data_points.append({
                'timestamp': snap.timestamp.isoformat() + 'Z',
                'spot_btc': round(snap.spot_btc, 2),
                'gobtc_price': round(snap.gobtc_price, 2),
                'wbtc_price': round(snap.wbtc_price, 2) if snap.wbtc_price else None,
                'gobtc_premium_pct': round(snap.gobtc_premium_pct, 2),
                'wbtc_premium_pct': round(snap.wbtc_premium_pct, 2) if snap.wbtc_premium_pct else None
            })

        return {
            'data_points': data_points,
            'stats': stats,
            'hours_requested': hours,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
    except Exception as e:
        print(f"Error fetching BTC history: {e}")
        raise HTTPException(status_code=500, detail=str(e))
