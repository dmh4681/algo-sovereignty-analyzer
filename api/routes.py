import re
import requests
from fastapi import APIRouter, HTTPException, Query, Path
from core.analyzer import AlgorandSovereigntyAnalyzer
from .errors import ValidationException, NotFoundException, ExternalApiException
from core.history import SovereigntySnapshot, get_history_manager
from core.btc_history import get_btc_history_manager, save_current_prices
from core.miner_metrics import get_miner_metrics_db, MinerMetric
from core.silver_metrics import get_silver_metrics_db, SilverMinerMetric
from core.inflation_data import get_inflation_db
from core.central_bank_gold import get_cb_gold_db
from core.earnings_calendar import get_earnings_db, EarningsEvent
from core.premium_tracker import get_premium_db
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

# Algorand address validation pattern (58 characters, base32 alphabet)
ALGORAND_ADDRESS_PATTERN = re.compile(r'^[A-Z2-7]{58}$')


def validate_algorand_address(address: str) -> None:
    """
    Validate Algorand wallet address format.

    Raises ValidationException if the address is invalid.
    """
    if not address:
        raise ValidationException(
            detail="Wallet address is required",
            error_code="MISSING_ADDRESS",
            details={"field": "address"}
        )

    if not ALGORAND_ADDRESS_PATTERN.match(address):
        raise ValidationException(
            detail="Invalid Algorand wallet address format",
            error_code="INVALID_ADDRESS_FORMAT",
            details={
                "field": "address",
                "value": address[:10] + "..." if len(address) > 10 else address,
                "expected": "58 character base32 string (A-Z, 2-7)"
            }
        )

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
    # Validate address format
    validate_algorand_address(request.address)

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
            raise NotFoundException(
                detail="Wallet not found or contains no assets",
                error_code="WALLET_NOT_FOUND",
                details={"address": request.address}
            )
        
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
    except (ValidationException, NotFoundException):
        raise
    except requests.exceptions.Timeout:
        raise ExternalApiException(
            detail="Algorand API request timed out",
            error_code="ALGORAND_API_TIMEOUT",
            details={"address": request.address}
        )
    except requests.exceptions.RequestException as e:
        raise ExternalApiException(
            detail="Failed to communicate with Algorand API",
            error_code="ALGORAND_API_ERROR",
            details={"address": request.address, "error_type": type(e).__name__}
        )
    except Exception as e:
        print(f"❌ Error in analyze_wallet endpoint: {e}")
        import traceback
        traceback.print_exc()
        raise ExternalApiException(
            detail="Analysis failed due to an external service error",
            error_code="ANALYSIS_FAILED",
            details={"address": request.address}
        )

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


# -----------------------------------------------------------------------------
# Gold Miner Metrics Endpoints
# -----------------------------------------------------------------------------

@router.get("/gold/miners")
async def get_miner_metrics(
    limit: int = Query(100, ge=1, le=500, description="Maximum records to return")
):
    """
    Get all gold miner quarterly metrics.

    Returns metrics ordered by period (newest first), then by ticker.
    Used for historical trend analysis and data tables.
    """
    try:
        db = get_miner_metrics_db()
        metrics = db.get_all_metrics(limit=limit)

        return {
            'metrics': [m.to_dict() for m in metrics],
            'count': len(metrics),
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
    except Exception as e:
        print(f"Error fetching miner metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/gold/miners/latest")
async def get_latest_miner_metrics():
    """
    Get the most recent metrics for each gold mining company.

    Returns one record per company (their latest quarterly report).
    Used for dashboard KPIs and efficiency frontier chart.
    """
    try:
        db = get_miner_metrics_db()
        metrics = db.get_latest_by_company()

        return {
            'metrics': [m.to_dict() for m in metrics],
            'count': len(metrics),
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
    except Exception as e:
        print(f"Error fetching latest miner metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/gold/miners/stats")
async def get_sector_stats():
    """
    Get sector-wide statistics from the latest data.

    Returns aggregated metrics:
    - Average AISC across sector
    - Total quarterly production
    - Average dividend yield
    - Weighted Tier 1 jurisdiction exposure
    """
    try:
        db = get_miner_metrics_db()
        stats = db.get_sector_stats()

        return {
            'stats': stats,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
    except Exception as e:
        print(f"Error fetching sector stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/gold/miners/{ticker}")
async def get_miner_by_ticker(
    ticker: str = Path(..., description="Company ticker symbol (e.g., NEM, GOLD, AEM)")
):
    """
    Get all quarterly metrics for a specific company.

    Returns historical data for trend analysis of a single miner.
    """
    try:
        db = get_miner_metrics_db()
        metrics = db.get_metrics_by_ticker(ticker.upper())

        if not metrics:
            raise HTTPException(status_code=404, detail=f"No data found for ticker: {ticker}")

        return {
            'ticker': ticker.upper(),
            'company': metrics[0].company if metrics else None,
            'metrics': [m.to_dict() for m in metrics],
            'count': len(metrics),
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching metrics for {ticker}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/gold/miners")
async def create_miner_metric(data: Dict[str, Any]):
    """
    Submit a new quarterly report for a gold miner.

    Required fields:
    - company: Company name (e.g., "Newmont")
    - ticker: Stock ticker (e.g., "NEM")
    - period: Reporting period (e.g., "2024-Q1")
    - aisc: All-In Sustaining Cost ($/oz)
    - production: Quarterly production (Moz)
    - revenue: Revenue (Billions USD)
    - fcf: Free Cash Flow (Billions USD)
    - dividend_yield: Dividend yield (%)
    - market_cap: Market capitalization (Billions USD)

    Optional fields:
    - tier1, tier2, tier3: Jurisdiction exposure percentages
    """
    try:
        # Validate required fields
        required = ['company', 'ticker', 'period', 'aisc', 'production',
                    'revenue', 'fcf', 'dividend_yield', 'market_cap']
        missing = [f for f in required if f not in data or data[f] is None]
        if missing:
            raise HTTPException(
                status_code=400,
                detail=f"Missing required fields: {', '.join(missing)}"
            )

        # Create metric object
        metric = MinerMetric(
            id=None,
            company=data['company'],
            ticker=data['ticker'].upper(),
            period=data['period'],
            aisc=float(data['aisc']),
            production=float(data['production']),
            revenue=float(data['revenue']),
            fcf=float(data['fcf']),
            dividend_yield=float(data['dividend_yield']),
            market_cap=float(data['market_cap']),
            tier1=int(data.get('tier1', 0)),
            tier2=int(data.get('tier2', 0)),
            tier3=int(data.get('tier3', 0))
        )

        db = get_miner_metrics_db()
        new_id = db.create_metric(metric)

        if new_id is None:
            raise HTTPException(
                status_code=409,
                detail=f"Duplicate entry: {metric.ticker} for {metric.period} already exists"
            )

        return {
            'success': True,
            'id': new_id,
            'message': f"Created metric for {metric.ticker} ({metric.period})",
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error creating miner metric: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/gold/miners/reseed")
async def reseed_miner_metrics():
    """
    Clear all miner metrics and reseed with built-in seed data.
    Use this to reset the database to the latest seed data (2023-2025).

    WARNING: This deletes all existing data!
    """
    try:
        db = get_miner_metrics_db()
        count = db.reseed()
        return {
            'success': True,
            'message': f"Database reseeded with {count} records",
            'count': count,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
    except Exception as e:
        print(f"Error reseeding miner metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# -----------------------------------------------------------------------------
# Silver Miner Metrics Endpoints
# -----------------------------------------------------------------------------

@router.get("/silver/miners")
async def get_silver_miner_metrics(
    limit: int = Query(100, ge=1, le=500, description="Maximum records to return")
):
    """
    Get all silver miner quarterly metrics.

    Returns metrics ordered by period (newest first), then by ticker.
    Used for historical trend analysis and data tables.
    """
    try:
        db = get_silver_metrics_db()
        metrics = db.get_all_metrics(limit=limit)

        return {
            'metrics': [m.to_dict() for m in metrics],
            'count': len(metrics),
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
    except Exception as e:
        print(f"Error fetching silver miner metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/silver/miners/latest")
async def get_latest_silver_miner_metrics():
    """
    Get the most recent metrics for each silver mining company.

    Returns one record per company (their latest quarterly report).
    Used for dashboard KPIs and efficiency frontier chart.
    """
    try:
        db = get_silver_metrics_db()
        metrics = db.get_latest_by_company()

        return {
            'metrics': [m.to_dict() for m in metrics],
            'count': len(metrics),
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
    except Exception as e:
        print(f"Error fetching latest silver miner metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/silver/miners/stats")
async def get_silver_sector_stats():
    """
    Get sector-wide statistics from the latest silver miner data.

    Returns aggregated metrics:
    - Average AISC across sector
    - Total quarterly production
    - Average dividend yield
    - Weighted Tier 1 jurisdiction exposure
    """
    try:
        db = get_silver_metrics_db()
        stats = db.get_sector_stats()

        return {
            'stats': stats,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
    except Exception as e:
        print(f"Error fetching silver sector stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/silver/miners/{ticker}")
async def get_silver_miner_by_ticker(
    ticker: str = Path(..., description="Company ticker symbol (e.g., PAAS, AG, HL)")
):
    """
    Get all quarterly metrics for a specific silver mining company.

    Returns historical data for trend analysis of a single miner.
    """
    try:
        db = get_silver_metrics_db()
        metrics = db.get_metrics_by_ticker(ticker.upper())

        if not metrics:
            raise HTTPException(status_code=404, detail=f"No data found for ticker: {ticker}")

        return {
            'ticker': ticker.upper(),
            'company': metrics[0].company if metrics else None,
            'metrics': [m.to_dict() for m in metrics],
            'count': len(metrics),
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching silver metrics for {ticker}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/silver/miners")
async def create_silver_miner_metric(data: Dict[str, Any]):
    """
    Submit a new quarterly report for a silver miner.

    Required fields:
    - company: Company name (e.g., "Pan American Silver")
    - ticker: Stock ticker (e.g., "PAAS")
    - period: Reporting period (e.g., "2024-Q1")
    - aisc: All-In Sustaining Cost ($/oz)
    - production: Quarterly production (Moz)
    - revenue: Revenue (Billions USD)
    - fcf: Free Cash Flow (Billions USD)
    - dividend_yield: Dividend yield (%)
    - market_cap: Market capitalization (Billions USD)

    Optional fields:
    - tier1, tier2, tier3: Jurisdiction exposure percentages
    """
    try:
        # Validate required fields
        required = ['company', 'ticker', 'period', 'aisc', 'production',
                    'revenue', 'fcf', 'dividend_yield', 'market_cap']
        missing = [f for f in required if f not in data or data[f] is None]
        if missing:
            raise HTTPException(
                status_code=400,
                detail=f"Missing required fields: {', '.join(missing)}"
            )

        # Create metric object
        metric = SilverMinerMetric(
            id=None,
            company=data['company'],
            ticker=data['ticker'].upper(),
            period=data['period'],
            aisc=float(data['aisc']),
            production=float(data['production']),
            revenue=float(data['revenue']),
            fcf=float(data['fcf']),
            dividend_yield=float(data['dividend_yield']),
            market_cap=float(data['market_cap']),
            tier1=int(data.get('tier1', 0)),
            tier2=int(data.get('tier2', 0)),
            tier3=int(data.get('tier3', 0))
        )

        db = get_silver_metrics_db()
        new_id = db.create_metric(metric)

        if new_id is None:
            raise HTTPException(
                status_code=409,
                detail=f"Duplicate entry: {metric.ticker} for {metric.period} already exists"
            )

        return {
            'success': True,
            'id': new_id,
            'message': f"Created metric for {metric.ticker} ({metric.period})",
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error creating silver miner metric: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/silver/miners/reseed")
async def reseed_silver_miner_metrics():
    """
    Clear all silver miner metrics and reseed with built-in seed data.
    Use this to reset the database to the latest seed data (2023-2025).

    WARNING: This deletes all existing data!
    """
    try:
        db = get_silver_metrics_db()
        count = db.reseed()
        return {
            'success': True,
            'message': f"Database reseeded with {count} records",
            'count': count,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
    except Exception as e:
        print(f"Error reseeding silver miner metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# -----------------------------------------------------------------------------
# Inflation-Adjusted Charts Endpoints
# -----------------------------------------------------------------------------

@router.get("/inflation/summary")
async def get_inflation_summary():
    """
    Get summary statistics for the inflation dashboard.

    Returns current CPI, M2, gold/silver prices, and key insights like:
    - What the 1980 gold peak would be in today's dollars
    - Dollar purchasing power decline since 1970
    """
    try:
        db = get_inflation_db()
        stats = db.get_summary_stats()

        return {
            'stats': stats,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
    except Exception as e:
        print(f"Error fetching inflation summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/inflation/data")
async def get_inflation_data(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM format)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM format)")
):
    """
    Get historical inflation data (CPI, M2, gold, silver prices).

    Returns raw data points for charting. Can filter by date range.
    """
    try:
        db = get_inflation_db()
        data = db.get_all_data(start_date=start_date, end_date=end_date)

        return {
            'data': [d.to_dict() for d in data],
            'count': len(data),
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
    except Exception as e:
        print(f"Error fetching inflation data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/inflation/adjusted/{metal}")
async def get_inflation_adjusted_prices(
    metal: str = Path(..., description="Metal type: 'gold' or 'silver'"),
    base_year: int = Query(2024, ge=1970, le=2025, description="Base year for adjustment")
):
    """
    Get inflation-adjusted prices for gold or silver.

    Adjusts historical prices to constant dollars for the specified base year.
    This shows the "real" price after accounting for CPI inflation.

    Example: Gold at $675 in Jan 1980 equals ~$2,800 in 2024 dollars.
    """
    if metal not in ('gold', 'silver'):
        raise HTTPException(status_code=400, detail="metal must be 'gold' or 'silver'")

    try:
        db = get_inflation_db()
        data = db.calculate_inflation_adjusted_prices(metal=metal, base_year=base_year)

        return {
            'metal': metal,
            'base_year': base_year,
            'data': [d.to_dict() for d in data],
            'count': len(data),
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"Error calculating adjusted prices: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/inflation/m2-comparison")
async def get_m2_comparison():
    """
    Get gold/silver prices compared to M2 money supply.

    The gold/M2 ratio helps visualize if gold is cheap or expensive
    relative to money printing. A high ratio means gold is expensive
    vs the money supply; a low ratio suggests gold is undervalued.

    Includes comparison to 1980 peak ratio as benchmark.
    """
    try:
        db = get_inflation_db()
        data = db.get_m2_comparison()

        return {
            'data': [d.to_dict() for d in data],
            'count': len(data),
            'interpretation': {
                'peak_year': 1980,
                'peak_context': 'In 1980, gold was extremely expensive relative to M2 money supply',
                'current_pct_of_peak': data[-1].gold_m2_ratio_pct_of_peak if data else None,
                'implication': 'If ratio returns to 1980 peak levels, gold would need to rise significantly'
            },
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
    except Exception as e:
        print(f"Error calculating M2 comparison: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/inflation/purchasing-power")
async def get_purchasing_power(
    from_year: int = Query(1970, ge=1970, le=2020, description="Starting year for calculation")
):
    """
    Calculate dollar purchasing power decline from a given year.

    Shows how much value the US dollar has lost since the specified year.
    Useful for visualizing currency debasement over time.
    """
    try:
        db = get_inflation_db()
        result = db.calculate_purchasing_power(from_year=from_year)

        return {
            'purchasing_power': result,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
    except Exception as e:
        print(f"Error calculating purchasing power: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/inflation/reseed")
async def reseed_inflation_data():
    """
    Clear all inflation data and reseed with built-in historical data.

    WARNING: This deletes all existing data!
    """
    try:
        db = get_inflation_db()
        count = db.reseed()
        return {
            'success': True,
            'message': f"Database reseeded with {count} data points",
            'count': count,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
    except Exception as e:
        print(f"Error reseeding inflation data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# -----------------------------------------------------------------------------
# Central Bank Gold Tracker Endpoints
# -----------------------------------------------------------------------------

@router.get("/central-banks/summary")
async def get_cb_gold_summary():
    """
    Get summary statistics for the central bank gold dashboard.

    Returns total global holdings, recent purchase activity,
    de-dollarization score, and top holder info.
    """
    try:
        db = get_cb_gold_db()
        stats = db.get_summary_stats()

        return {
            'stats': stats,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
    except Exception as e:
        print(f"Error fetching CB gold summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/central-banks/leaderboard")
async def get_cb_gold_leaderboard(
    limit: int = Query(20, ge=1, le=50, description="Number of countries to return")
):
    """
    Get country leaderboard ranked by gold holdings.

    Includes 12-month change in holdings for trend analysis.
    """
    try:
        db = get_cb_gold_db()
        rankings = db.get_leaderboard(limit=limit)

        return {
            'rankings': [r.to_dict() for r in rankings],
            'count': len(rankings),
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
    except Exception as e:
        print(f"Error fetching CB leaderboard: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/central-banks/country/{country_code}")
async def get_cb_country_history(
    country_code: str = Path(..., description="ISO 3166-1 alpha-2 country code (e.g., US, CN, RU)")
):
    """
    Get historical gold holdings for a specific country.

    Returns time series data for charting a country's accumulation.
    """
    try:
        db = get_cb_gold_db()
        history = db.get_country_history(country_code)

        if not history:
            raise HTTPException(status_code=404, detail=f"No data for country: {country_code}")

        return {
            'country_code': country_code.upper(),
            'country_name': history[0].country_name if history else country_code,
            'history': [h.to_dict() for h in history],
            'count': len(history),
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching CB history for {country_code}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/central-banks/net-purchases")
async def get_cb_net_purchases():
    """
    Get global net gold purchases by year.

    Shows whether central banks as a group are buying or selling.
    2022 was a record year at 1,082 tonnes.
    """
    try:
        db = get_cb_gold_db()
        purchases = db.get_net_purchases()

        # Calculate summary stats
        total = sum(p.tonnes for p in purchases)
        avg = total / len(purchases) if purchases else 0
        recent_avg = sum(p.tonnes for p in purchases[-5:]) / 5 if len(purchases) >= 5 else avg

        return {
            'purchases': [p.to_dict() for p in purchases],
            'count': len(purchases),
            'summary': {
                'total_tonnes': round(total, 0),
                'average_per_year': round(avg, 0),
                'recent_5yr_avg': round(recent_avg, 0),
                'peak_year': max(purchases, key=lambda x: x.tonnes).year if purchases else None,
                'peak_tonnes': max(p.tonnes for p in purchases) if purchases else 0,
            },
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
    except Exception as e:
        print(f"Error fetching CB net purchases: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/central-banks/top-buyers")
async def get_cb_top_buyers(
    n: int = Query(10, ge=1, le=30, description="Number of top buyers to return")
):
    """
    Get countries with the largest gold accumulation in the past 12 months.
    """
    try:
        db = get_cb_gold_db()
        buyers = db.get_top_buyers(n=n)

        return {
            'buyers': [b.to_dict() for b in buyers],
            'count': len(buyers),
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
    except Exception as e:
        print(f"Error fetching top buyers: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/central-banks/top-sellers")
async def get_cb_top_sellers(
    n: int = Query(10, ge=1, le=30, description="Number of top sellers to return")
):
    """
    Get countries that have reduced gold holdings in the past 12 months.
    """
    try:
        db = get_cb_gold_db()
        sellers = db.get_top_sellers(n=n)

        return {
            'sellers': [s.to_dict() for s in sellers],
            'count': len(sellers),
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
    except Exception as e:
        print(f"Error fetching top sellers: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/central-banks/dedollarization")
async def get_dedollarization_score():
    """
    Get the composite de-dollarization score (0-100).

    Higher scores indicate stronger trend of central banks
    diversifying away from USD reserves into gold.
    """
    try:
        db = get_cb_gold_db()
        score = db.calculate_dedollarization_score()

        return {
            'score': score.to_dict(),
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
    except Exception as e:
        print(f"Error calculating de-dollarization score: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/central-banks/reseed")
async def reseed_cb_gold_data():
    """
    Clear all central bank gold data and reseed with built-in data.

    WARNING: This deletes all existing data!
    """
    try:
        db = get_cb_gold_db()
        count = db.reseed()
        return {
            'success': True,
            'message': f"Database reseeded with {count} holdings records",
            'count': count,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
    except Exception as e:
        print(f"Error reseeding CB gold data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# -----------------------------------------------------------------------------
# Miner Earnings Calendar Endpoints
# -----------------------------------------------------------------------------

@router.get("/earnings/calendar")
async def get_earnings_calendar(
    month: Optional[str] = Query(None, description="Month in YYYY-MM format (default: current month)")
):
    """
    Get earnings events for a specific month.

    Returns all gold and silver miner earnings scheduled for the month.
    Use for displaying a calendar view of upcoming earnings.
    """
    try:
        db = get_earnings_db()
        events = db.get_calendar(month=month)

        return {
            'events': [e.to_dict() for e in events],
            'count': len(events),
            'month': month or datetime.now().strftime('%Y-%m'),
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
    except Exception as e:
        print(f"Error fetching earnings calendar: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/earnings/upcoming")
async def get_upcoming_earnings(
    days: int = Query(30, ge=1, le=90, description="Number of days to look ahead")
):
    """
    Get earnings events in the next N days.

    Returns upcoming earnings sorted by date.
    Includes countdown information and estimates.
    """
    try:
        db = get_earnings_db()
        events = db.get_upcoming(days=days)

        # Add countdown days
        today = datetime.now().date()
        events_with_countdown = []
        for event in events:
            event_dict = event.to_dict()
            try:
                event_date = datetime.strptime(event.earnings_date, '%Y-%m-%d').date()
                event_dict['days_until'] = (event_date - today).days
            except ValueError:
                event_dict['days_until'] = None
            events_with_countdown.append(event_dict)

        return {
            'events': events_with_countdown,
            'count': len(events),
            'days_ahead': days,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
    except Exception as e:
        print(f"Error fetching upcoming earnings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/earnings/ticker/{ticker}")
async def get_earnings_by_ticker(
    ticker: str = Path(..., description="Company ticker symbol (e.g., NEM, PAAS)")
):
    """
    Get all earnings events for a specific company.

    Returns historical and upcoming earnings for trend analysis.
    """
    try:
        db = get_earnings_db()
        events = db.get_by_ticker(ticker)

        if not events:
            raise HTTPException(status_code=404, detail=f"No earnings data for ticker: {ticker}")

        return {
            'ticker': ticker.upper(),
            'company_name': events[0].company_name if events else None,
            'metal': events[0].metal if events else None,
            'events': [e.to_dict() for e in events],
            'count': len(events),
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching earnings for {ticker}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/earnings/stats/{ticker}")
async def get_earnings_stats(
    ticker: str = Path(..., description="Company ticker symbol")
):
    """
    Get beat/miss statistics for a specific company.

    Returns historical EPS, revenue, production, and AISC beat rates,
    plus average price reactions on earnings.
    """
    try:
        db = get_earnings_db()
        stats = db.get_stats(ticker)

        if not stats:
            raise HTTPException(status_code=404, detail=f"No earnings stats for ticker: {ticker}")

        return {
            'stats': stats.to_dict(),
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching earnings stats for {ticker}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/earnings/sector-stats")
async def get_sector_earnings_stats(
    metal: Optional[str] = Query(None, description="Filter by metal: 'gold' or 'silver'")
):
    """
    Get sector-wide earnings statistics.

    Returns aggregate beat rates, next upcoming earnings,
    and average price reactions across all tracked miners.
    """
    if metal and metal not in ('gold', 'silver'):
        raise HTTPException(status_code=400, detail="metal must be 'gold' or 'silver'")

    try:
        db = get_earnings_db()
        stats = db.get_sector_stats(metal=metal)

        return {
            'stats': stats.to_dict(),
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
    except Exception as e:
        print(f"Error fetching sector earnings stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/earnings")
async def create_earnings_event(data: Dict[str, Any]):
    """
    Create a new earnings event (manual entry).

    Required fields:
    - ticker: Stock ticker (e.g., "NEM")
    - metal: 'gold' or 'silver'
    - company_name: Full company name
    - quarter: Period (e.g., "Q1 2025")
    - earnings_date: Date in YYYY-MM-DD format
    - time_of_day: 'pre-market', 'after-hours', or 'during-market'
    - is_confirmed: Whether date is confirmed vs estimated
    """
    try:
        required = ['ticker', 'metal', 'company_name', 'quarter', 'earnings_date', 'time_of_day', 'is_confirmed']
        missing = [f for f in required if f not in data]
        if missing:
            raise HTTPException(
                status_code=400,
                detail=f"Missing required fields: {', '.join(missing)}"
            )

        if data['metal'] not in ('gold', 'silver'):
            raise HTTPException(status_code=400, detail="metal must be 'gold' or 'silver'")

        event = EarningsEvent(
            id=None,
            ticker=data['ticker'].upper(),
            metal=data['metal'],
            company_name=data['company_name'],
            quarter=data['quarter'],
            earnings_date=data['earnings_date'],
            time_of_day=data['time_of_day'],
            is_confirmed=bool(data['is_confirmed']),
            eps_actual=data.get('eps_actual'),
            eps_estimate=data.get('eps_estimate'),
            revenue_actual=data.get('revenue_actual'),
            revenue_estimate=data.get('revenue_estimate'),
            production_actual=data.get('production_actual'),
            production_guidance=data.get('production_guidance'),
            aisc_actual=data.get('aisc_actual'),
            aisc_guidance=data.get('aisc_guidance'),
            price_before=data.get('price_before'),
            price_1d_after=data.get('price_1d_after'),
            price_5d_after=data.get('price_5d_after'),
            price_30d_after=data.get('price_30d_after'),
            transcript_url=data.get('transcript_url'),
            press_release_url=data.get('press_release_url'),
        )

        db = get_earnings_db()
        new_id = db.create_event(event)

        if new_id is None:
            raise HTTPException(
                status_code=409,
                detail=f"Duplicate: {event.ticker} {event.quarter} already exists"
            )

        return {
            'success': True,
            'id': new_id,
            'message': f"Created earnings event for {event.ticker} ({event.quarter})",
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error creating earnings event: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/earnings/{event_id}")
async def update_earnings_event(
    event_id: int = Path(..., description="Earnings event ID"),
    data: Dict[str, Any] = None
):
    """
    Update an existing earnings event.

    Use this to add actual results after earnings are reported.
    """
    try:
        if not data:
            raise HTTPException(status_code=400, detail="No update data provided")

        db = get_earnings_db()
        success = db.update_event(event_id, data)

        if not success:
            raise HTTPException(status_code=404, detail=f"Event {event_id} not found or no valid updates")

        return {
            'success': True,
            'message': f"Updated earnings event {event_id}",
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error updating earnings event: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/earnings/reseed")
async def reseed_earnings_data():
    """
    Clear all earnings data and reseed with built-in historical data.

    WARNING: This deletes all existing data!
    """
    try:
        db = get_earnings_db()
        count = db.reseed()
        return {
            'success': True,
            'message': f"Database reseeded with {count} earnings events",
            'count': count,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
    except Exception as e:
        print(f"Error reseeding earnings data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# -----------------------------------------------------------------------------
# Physical Premium Tracker Endpoints
# -----------------------------------------------------------------------------

@router.get("/premiums/summary")
async def get_premiums_summary():
    """
    Get summary statistics for the premium tracker dashboard.

    Returns spot prices, average premiums by metal, and data freshness.
    """
    try:
        db = get_premium_db()
        stats = db.get_summary_stats()

        return {
            'stats': stats,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
    except Exception as e:
        print(f"Error fetching premiums summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/premiums/products")
async def get_premium_products(
    metal: Optional[str] = Query(None, description="Filter by metal: 'gold' or 'silver'")
):
    """
    Get all tracked products.

    Returns product catalog with typical premium ranges.
    """
    if metal and metal not in ('gold', 'silver'):
        raise HTTPException(status_code=400, detail="metal must be 'gold' or 'silver'")

    try:
        db = get_premium_db()
        products = db.get_products(metal=metal)

        return {
            'products': [p.to_dict() for p in products],
            'count': len(products),
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
    except Exception as e:
        print(f"Error fetching products: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/premiums/products/{product_id}")
async def get_premium_product(
    product_id: str = Path(..., description="Product ID (e.g., 'silver-eagle-1oz')")
):
    """
    Get details for a specific product.
    """
    try:
        db = get_premium_db()
        product = db.get_product(product_id)

        if not product:
            raise HTTPException(status_code=404, detail=f"Product not found: {product_id}")

        return {
            'product': product.to_dict(),
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching product {product_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/premiums/dealers")
async def get_premium_dealers():
    """
    Get all active dealers.
    """
    try:
        db = get_premium_db()
        dealers = db.get_dealers()

        return {
            'dealers': [d.to_dict() for d in dealers],
            'count': len(dealers),
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
    except Exception as e:
        print(f"Error fetching dealers: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/premiums/compare/{product_id}")
async def compare_product_prices(
    product_id: str = Path(..., description="Product ID to compare")
):
    """
    Compare prices for a product across all dealers.

    Returns prices sorted by total cost with best deal highlighted.
    """
    try:
        db = get_premium_db()
        comparison = db.get_comparison(product_id)

        if not comparison:
            raise HTTPException(status_code=404, detail=f"No prices found for: {product_id}")

        return {
            'comparison': comparison.to_dict(),
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error comparing prices for {product_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/premiums/best-deals")
async def get_best_deals(
    metal: Optional[str] = Query(None, description="Filter by metal: 'gold' or 'silver'"),
    limit: int = Query(10, ge=1, le=50, description="Number of deals to return")
):
    """
    Get products with the lowest current premiums.

    Returns the best value products available right now.
    """
    if metal and metal not in ('gold', 'silver'):
        raise HTTPException(status_code=400, detail="metal must be 'gold' or 'silver'")

    try:
        db = get_premium_db()
        deals = db.get_best_deals(metal=metal, limit=limit)

        return {
            'deals': deals,
            'count': len(deals),
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
    except Exception as e:
        print(f"Error fetching best deals: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/premiums/leaderboard")
async def get_dealer_leaderboard(
    metal: Optional[str] = Query(None, description="Filter by metal: 'gold' or 'silver'")
):
    """
    Get dealers ranked by average premium.

    Lower average premium = better value for customers.
    """
    if metal and metal not in ('gold', 'silver'):
        raise HTTPException(status_code=400, detail="metal must be 'gold' or 'silver'")

    try:
        db = get_premium_db()
        rankings = db.get_dealer_leaderboard(metal=metal)

        return {
            'rankings': [r.to_dict() for r in rankings],
            'count': len(rankings),
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
    except Exception as e:
        print(f"Error fetching dealer leaderboard: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/premiums/price")
async def add_price(data: Dict[str, Any]):
    """
    Add a new price entry (manual update).

    Required fields:
    - product_id: Product ID
    - dealer_id: Dealer ID
    - price: Current price
    - spot_price: Current spot price for the metal

    Optional fields:
    - in_stock: Whether product is in stock (default: true)
    - product_url: URL to product page
    """
    try:
        required = ['product_id', 'dealer_id', 'price', 'spot_price']
        missing = [f for f in required if f not in data]
        if missing:
            raise HTTPException(
                status_code=400,
                detail=f"Missing required fields: {', '.join(missing)}"
            )

        db = get_premium_db()
        new_id = db.add_price(
            product_id=data['product_id'],
            dealer_id=data['dealer_id'],
            price=float(data['price']),
            spot_price=float(data['spot_price']),
            in_stock=data.get('in_stock', True),
            product_url=data.get('product_url'),
        )

        if new_id is None:
            raise HTTPException(status_code=400, detail="Invalid product_id")

        return {
            'success': True,
            'id': new_id,
            'message': f"Price added for {data['product_id']} at {data['dealer_id']}",
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error adding price: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/premiums/reseed")
async def reseed_premium_data():
    """
    Clear all premium data and reseed with sample data.

    WARNING: This deletes all existing data!
    """
    try:
        db = get_premium_db()
        count = db.reseed()
        return {
            'success': True,
            'message': f"Database reseeded with {count} price entries",
            'count': count,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
    except Exception as e:
        print(f"Error reseeding premium data: {e}")
        raise HTTPException(status_code=500, detail=str(e))
