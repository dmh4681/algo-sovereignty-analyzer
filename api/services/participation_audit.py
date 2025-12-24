"""
Participation Audit Service

Analyzes Algorand consensus participation statistics including:
- Online stake from ledger supply
- Participation account sampling from indexer
- Validator distribution analysis
"""

import requests
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
import threading


# Algorand API endpoints
ALGOD_MAINNET = "https://mainnet-api.algonode.cloud"
INDEXER_MAINNET = "https://mainnet-idx.algonode.cloud"

# Microalgos per ALGO
MICROALGOS = 1_000_000


@dataclass
class ParticipationAccount:
    """Represents a participating account"""
    address: str
    stake_algo: float
    incentive_eligible: bool
    vote_first_valid: int
    vote_last_valid: int
    last_proposed: Optional[int]
    last_heartbeat: Optional[int]


@dataclass
class ParticipationStats:
    """Aggregated participation statistics"""
    current_round: int
    online_stake_microalgos: int
    total_stake_microalgos: int
    online_stake_algo: float
    total_stake_algo: float
    online_percentage: float
    estimated_validators: int
    top_validators: List[ParticipationAccount]
    incentive_eligible_count: int
    incentive_eligible_stake: float
    timestamp: str
    cache_expires: str


class ParticipationCache:
    """Thread-safe cache for participation stats"""

    def __init__(self, ttl_minutes: int = 15):
        self._cache: Optional[ParticipationStats] = None
        self._lock = threading.Lock()
        self._ttl = timedelta(minutes=ttl_minutes)

    def get(self) -> Optional[ParticipationStats]:
        with self._lock:
            if self._cache is None:
                return None
            timestamp_str = self._cache.timestamp.replace("Z", "+00:00")
            cache_time = datetime.fromisoformat(timestamp_str).replace(tzinfo=None)
            if datetime.utcnow() - cache_time > self._ttl:
                self._cache = None
                return None
            return self._cache

    def set(self, stats: ParticipationStats):
        with self._lock:
            self._cache = stats

    def clear(self):
        with self._lock:
            self._cache = None


# Global cache instance (15 minute TTL since stake changes more frequently)
_participation_cache = ParticipationCache(ttl_minutes=15)


def get_ledger_supply() -> Dict[str, Any]:
    """
    Get current ledger supply from algod.

    Returns:
        Dict with current_round, online-money, total-money
    """
    try:
        response = requests.get(
            f"{ALGOD_MAINNET}/v2/ledger/supply",
            timeout=10
        )
        if response.status_code == 200:
            return response.json()
    except requests.RequestException as e:
        print(f"Error fetching ledger supply: {e}")

    return {}


def get_online_accounts_sample(
    min_stake_algo: int = 10000,
    limit: int = 100
) -> List[Dict[str, Any]]:
    """
    Get a sample of online accounts from the indexer.

    Args:
        min_stake_algo: Minimum stake in ALGO to filter
        limit: Maximum accounts to return

    Returns:
        List of account data dicts
    """
    online_accounts = []
    min_stake_microalgos = min_stake_algo * MICROALGOS

    try:
        # Query accounts with significant stake
        # Note: Indexer status filter may not work perfectly, so we filter client-side
        response = requests.get(
            f"{INDEXER_MAINNET}/v2/accounts",
            params={
                "currency-greater-than": min_stake_microalgos,
                "limit": limit * 3  # Get more to filter
            },
            timeout=30
        )

        if response.status_code == 200:
            data = response.json()
            all_accounts = data.get("accounts", [])

            # Filter to only actually online accounts with participation keys
            for acc in all_accounts:
                if (acc.get("status") == "Online" and
                    acc.get("participation") and
                    len(online_accounts) < limit):
                    online_accounts.append(acc)

    except requests.RequestException as e:
        print(f"Error fetching online accounts: {e}")

    return online_accounts


def count_online_accounts_estimate() -> int:
    """
    Estimate total number of online accounts by sampling.

    Uses multiple threshold queries to estimate total count.
    """
    thresholds = [
        100_000_000,   # 100M+ ALGO (whales)
        10_000_000,    # 10M+ ALGO
        1_000_000,     # 1M+ ALGO
        100_000,       # 100K+ ALGO
        10_000,        # 10K+ ALGO
        1_000,         # 1K+ ALGO
    ]

    counts = {}

    for threshold in thresholds:
        try:
            response = requests.get(
                f"{INDEXER_MAINNET}/v2/accounts",
                params={
                    "status": "Online",
                    "currency-greater-than": threshold * MICROALGOS,
                    "limit": 1  # Just need count estimate
                },
                timeout=10
            )

            if response.status_code == 200:
                # Count accounts by paginating (simplified - just get first page)
                data = response.json()
                # If we got results, there are at least some at this tier
                if data.get("accounts"):
                    counts[threshold] = len(data["accounts"])

        except requests.RequestException:
            pass

    return sum(counts.values()) if counts else 0


def get_incentive_eligible_sample(limit: int = 50) -> List[Dict[str, Any]]:
    """
    Get sample of incentive-eligible validators.

    These are accounts that meet the criteria for consensus rewards.
    """
    eligible = []

    try:
        # Get online accounts and filter for incentive-eligible
        response = requests.get(
            f"{INDEXER_MAINNET}/v2/accounts",
            params={
                "status": "Online",
                "currency-greater-than": 30000 * MICROALGOS,  # Min for incentives
                "limit": 200  # Get more to filter
            },
            timeout=30
        )

        if response.status_code == 200:
            data = response.json()
            for account in data.get("accounts", []):
                if account.get("incentive-eligible"):
                    eligible.append(account)
                    if len(eligible) >= limit:
                        break

    except requests.RequestException as e:
        print(f"Error fetching incentive-eligible accounts: {e}")

    return eligible


def audit_participation(force_refresh: bool = False) -> ParticipationStats:
    """
    Perform participation audit.

    Args:
        force_refresh: Bypass cache if True

    Returns:
        ParticipationStats with all participation data
    """
    # Check cache
    if not force_refresh:
        cached = _participation_cache.get()
        if cached:
            return cached

    # Get ledger supply (fast)
    supply = get_ledger_supply()
    current_round = supply.get("current_round", 0)
    online_micro = supply.get("online-money", 0)
    total_micro = supply.get("total-money", 0)

    online_algo = online_micro / MICROALGOS
    total_algo = total_micro / MICROALGOS
    online_pct = (online_micro / total_micro * 100) if total_micro > 0 else 0

    # Get sample of top validators (slower)
    top_accounts = get_online_accounts_sample(min_stake_algo=100000, limit=50)

    # Get incentive-eligible sample
    eligible_accounts = get_incentive_eligible_sample(limit=100)

    # Build top validators list
    top_validators = []
    for acc in sorted(top_accounts, key=lambda x: x.get("amount", 0), reverse=True)[:20]:
        participation = acc.get("participation", {})

        # Only include if actually online with valid participation
        if acc.get("status") == "Online" and participation:
            validator = ParticipationAccount(
                address=acc.get("address", ""),
                stake_algo=acc.get("amount", 0) / MICROALGOS,
                incentive_eligible=acc.get("incentive-eligible", False),
                vote_first_valid=participation.get("vote-first-valid", 0),
                vote_last_valid=participation.get("vote-last-valid", 0),
                last_proposed=acc.get("last-proposed"),
                last_heartbeat=acc.get("last-heartbeat")
            )
            top_validators.append(validator)

    # Calculate incentive-eligible stats
    incentive_count = len(eligible_accounts)
    incentive_stake = sum(
        acc.get("amount", 0) / MICROALGOS
        for acc in eligible_accounts
    )

    # Estimate total validator count
    # This is rough - actual count requires full pagination
    estimated_validators = len(top_validators) * 10  # Rough multiplier

    now = datetime.utcnow()
    stats = ParticipationStats(
        current_round=current_round,
        online_stake_microalgos=online_micro,
        total_stake_microalgos=total_micro,
        online_stake_algo=round(online_algo, 2),
        total_stake_algo=round(total_algo, 2),
        online_percentage=round(online_pct, 2),
        estimated_validators=estimated_validators,
        top_validators=top_validators,
        incentive_eligible_count=incentive_count,
        incentive_eligible_stake=round(incentive_stake, 2),
        timestamp=now.isoformat() + "Z",
        cache_expires=(now + timedelta(minutes=15)).isoformat() + "Z"
    )

    # Cache result
    _participation_cache.set(stats)

    return stats


def get_participation_summary(force_refresh: bool = False) -> Dict[str, Any]:
    """
    Get participation summary for API response.
    """
    stats = audit_participation(force_refresh=force_refresh)

    # Convert top validators to dicts
    top_validators_dict = [
        {
            "address": v.address,
            "address_short": f"{v.address[:8]}...{v.address[-4:]}",
            "stake_algo": v.stake_algo,
            "stake_formatted": format_algo(v.stake_algo),
            "incentive_eligible": v.incentive_eligible,
            "vote_first_valid": v.vote_first_valid,
            "vote_last_valid": v.vote_last_valid,
            "keys_valid": v.vote_last_valid > stats.current_round if v.vote_last_valid else False,
            "last_proposed": v.last_proposed,
            "last_heartbeat": v.last_heartbeat,
            "recently_active": is_recently_active(v.last_proposed, v.last_heartbeat, stats.current_round)
        }
        for v in stats.top_validators
    ]

    return {
        "current_round": stats.current_round,
        "online_stake": {
            "algo": stats.online_stake_algo,
            "formatted": format_algo(stats.online_stake_algo),
            "percentage": stats.online_percentage
        },
        "total_supply": {
            "algo": stats.total_stake_algo,
            "formatted": format_algo(stats.total_stake_algo)
        },
        "validators": {
            "estimated_count": stats.estimated_validators,
            "top_validators": top_validators_dict,
            "incentive_eligible_count": stats.incentive_eligible_count,
            "incentive_eligible_stake": format_algo(stats.incentive_eligible_stake)
        },
        "interpretation": get_participation_interpretation(stats),
        "timestamp": stats.timestamp,
        "cache_expires": stats.cache_expires
    }


def format_algo(amount: float) -> str:
    """Format ALGO amount with appropriate suffix"""
    if amount >= 1_000_000_000:
        return f"{amount / 1_000_000_000:.2f}B"
    elif amount >= 1_000_000:
        return f"{amount / 1_000_000:.2f}M"
    elif amount >= 1_000:
        return f"{amount / 1_000:.2f}K"
    else:
        return f"{amount:.2f}"


def is_recently_active(last_proposed: Optional[int], last_heartbeat: Optional[int], current_round: int) -> bool:
    """Check if validator has been recently active"""
    # Consider active if proposed or heartbeat within last ~24 hours (~180K rounds)
    threshold = current_round - 180_000

    if last_proposed and last_proposed > threshold:
        return True
    if last_heartbeat and last_heartbeat > threshold:
        return True

    return False


def get_participation_interpretation(stats: ParticipationStats) -> Dict[str, str]:
    """Generate human-readable interpretation"""

    pct = stats.online_percentage

    if pct >= 30:
        health = "strong"
        color = "green"
        message = "Network has strong consensus participation"
    elif pct >= 20:
        health = "healthy"
        color = "green"
        message = "Network participation is healthy"
    elif pct >= 15:
        health = "moderate"
        color = "yellow"
        message = "Network participation is moderate"
    elif pct >= 10:
        health = "low"
        color = "orange"
        message = "Network participation is below optimal"
    else:
        health = "critical"
        color = "red"
        message = "Network participation is critically low"

    return {
        "health": health,
        "color": color,
        "message": message,
        "stake_description": f"{format_algo(stats.online_stake_algo)} ALGO ({pct:.1f}%) is actively participating in consensus",
        "recommendation": (
            "Consider running a participation node to help secure the network"
            if pct < 25 else
            "Network has good participation coverage"
        )
    }
