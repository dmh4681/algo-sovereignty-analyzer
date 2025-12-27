"""
Algorand Network Statistics Module

Fetches and calculates decentralization metrics from the Algorand mainnet.
Uses AlgoNode free API (no authentication required).
"""

import asyncio
import time
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
import httpx


# -----------------------------------------------------------------------------
# Data Classes
# -----------------------------------------------------------------------------

@dataclass
class NetworkStats:
    """Network-wide supply and participation statistics."""
    total_supply: int           # Total ALGO supply (microalgos)
    online_stake: int           # ALGO currently online/participating (microalgos)
    circulating_supply: int     # Circulating supply (microalgos)
    participation_rate: float   # online_stake / total_supply as percentage
    current_round: int          # Current blockchain round


@dataclass
class FoundationStats:
    """Statistics about Algorand Foundation's stake and participation."""
    total_balance: int              # Sum of all Foundation addresses (microalgos)
    online_balance: int             # Foundation stake that is online (microalgos)
    foundation_addresses: List[str] # List of known Foundation addresses
    address_details: List[Dict]     # Per-address breakdown
    foundation_pct_of_supply: float # % of total supply
    foundation_pct_of_online: float # % of online stake


@dataclass
class WalletParticipation:
    """Participation status for a specific wallet."""
    address: str
    is_online: bool
    balance: int                        # Balance in microalgos
    vote_first_valid: Optional[int]
    vote_last_valid: Optional[int]
    vote_key_dilution: Optional[int]
    is_key_expired: bool                # True if vote_last_valid < current_round
    stake_percentage: float             # This wallet's % of total online stake
    current_round: int


@dataclass
class DecentralizationScoreBreakdown:
    """Detailed breakdown of decentralization score factors."""
    # Positive factors (what we have)
    community_online_pct: float         # Community % of online stake
    community_online_score: int         # Points earned (max 30)
    participation_rate_score: int       # Points earned (max 10)

    # Risk factors (what we lose points for)
    foundation_supply_pct: float        # Foundation % of total supply
    foundation_supply_penalty: int      # Points deducted (max -25)
    foundation_potential_control: float # If Foundation went online, their % of stake
    potential_control_penalty: int      # Points deducted (max -20)
    relay_centralization_penalty: int   # Points deducted for relay node concentration (max -15)

    # Governance risk
    governance_penalty: int             # Foundation governance influence (-10)

    # Final
    raw_score: int                      # Before floor
    final_score: int                    # 0-100, floored


@dataclass
class DecentralizationSummary:
    """Combined summary for dashboard display."""
    network: NetworkStats
    foundation: FoundationStats
    community_stake: int                # online_stake - foundation_online
    community_pct_of_online: float      # % of online stake that is community
    decentralization_score: int         # 0-100 score
    score_breakdown: Optional[DecentralizationScoreBreakdown] = None  # Detailed breakdown
    fetched_at: float = 0.0             # Unix timestamp


# -----------------------------------------------------------------------------
# Cache Implementation
# -----------------------------------------------------------------------------

@dataclass
class CacheEntry:
    """Simple cache entry with expiration."""
    data: Any
    expires_at: float


class SimpleCache:
    """In-memory cache with TTL support."""

    def __init__(self):
        self._cache: Dict[str, CacheEntry] = {}

    def get(self, key: str) -> Optional[Any]:
        """Get cached value if not expired."""
        entry = self._cache.get(key)
        if entry is None:
            return None
        if time.time() > entry.expires_at:
            del self._cache[key]
            return None
        return entry.data

    def set(self, key: str, value: Any, ttl_seconds: int = 300):
        """Set cache value with TTL (default 5 minutes)."""
        self._cache[key] = CacheEntry(
            data=value,
            expires_at=time.time() + ttl_seconds
        )

    def clear(self):
        """Clear all cached entries."""
        self._cache.clear()


# -----------------------------------------------------------------------------
# Main Class
# -----------------------------------------------------------------------------

class AlgorandNetworkStats:
    """
    Fetches and calculates Algorand network decentralization metrics.

    Uses AlgoNode free API (no auth required).
    All balances are in microAlgos (1 ALGO = 1,000,000 microAlgos).
    """

    ALGOD_URL = "https://mainnet-api.algonode.cloud"

    # Known Foundation addresses (from algorand.foundation/updated-wallet-addresses)
    FOUNDATION_ADDRESSES = [
        "RW466IANOKLA36QARHMBX5VCY3PYDR3H2N5XHPDARG6UBOKCIK7WAMLSCA",
        "5NTF3MGWL5B2X426P27FE3AUPOUU3OYSRCLP3O4Y7JI2BFGJWPGUBOB2NI",
        "JEBTS2MKIIN2EWSXPWEWJ4GUMVOYB2JYZ4XCRD4KJPVNAO6YBJTPBBJBE4",
        "T5TGE4UXGMKZBQ3D3SOB34CQDMSRDXO5H6O55663SRD275ZMK6UG7PYNC4",
        "BMZT7U2KSXVGI7LWRJVDM7S7CEPT2VFOBMA45QC25WJ2TRB5P7USAD3TR4",
        "4SN2OPSTRXDAXAG5HY7GVSQUXYL5NXPENLMHRG2SH5Q2ZF5ACXJRGWDYNE",
        "IOSADRTSZUE6WBNXH7ANZANFDQ3GVCVUGZI3IP6T3AQI6RLGLI6TPNJQZA",
        "XNFDTOTUQME3NI2UWDJ5Y6LYOJKHNP4C7BKZYQ5GSDQ7JBXKEJ6HLM3LOE",
        "2TZAMEZZDWFY37QV66HXWQIYWYJIZKE2KP3QNPI2QHHKSMKUZEICNMMUFU",
        "TVUQW6NXMHZFZAV6D7PQMW4DIUL5UB42L2JLIYNGRHH6UW362HGNVI26DY",
        "B223SVF452UWAMMLNIHIUAPHYPX5J3HLVJF6MNOHUJE2NWJBG7C66JILGE",
        "4E7OINW7M6G6OT2SQZ7ZKFPWJ7CAAFTPOG2RZISJ3YZU5VCJQ64ZIROC44",
        "JB2EEILIBYWA3WACBIERYPG5TV6K6IHOWJKDFDHRGSCOEHTMEUUML7YXGE"
    ]

    # Cache TTL in seconds (5 minutes)
    CACHE_TTL = 300

    def __init__(self):
        self._cache = SimpleCache()
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create httpx async client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.ALGOD_URL,
                timeout=30.0,
                headers={"Accept": "application/json"}
            )
        return self._client

    async def close(self):
        """Close the HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    async def _fetch_json(self, path: str) -> Dict[str, Any]:
        """Fetch JSON from API with error handling."""
        client = await self._get_client()
        try:
            response = await client.get(path)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                # Rate limited - wait and retry once
                await asyncio.sleep(1)
                response = await client.get(path)
                response.raise_for_status()
                return response.json()
            raise
        except httpx.RequestError as e:
            raise ConnectionError(f"Failed to connect to Algorand API: {e}")

    async def get_current_round(self) -> int:
        """Get the current blockchain round."""
        cached = self._cache.get("current_round")
        if cached is not None:
            return cached

        data = await self._fetch_json("/v2/status")
        current_round = data.get("last-round", 0)
        self._cache.set("current_round", current_round, ttl_seconds=10)  # Short TTL
        return current_round

    async def get_network_stats(self) -> NetworkStats:
        """Fetch current network supply and participation stats."""
        cached = self._cache.get("network_stats")
        if cached is not None:
            return cached

        # Fetch supply data
        supply_data = await self._fetch_json("/v2/ledger/supply")
        current_round = await self.get_current_round()

        total_supply = supply_data.get("total-money", 0)
        online_stake = supply_data.get("online-money", 0)

        # Calculate participation rate
        participation_rate = 0.0
        if total_supply > 0:
            participation_rate = (online_stake / total_supply) * 100

        stats = NetworkStats(
            total_supply=total_supply,
            online_stake=online_stake,
            circulating_supply=total_supply,  # Algorand has no locked supply distinction in API
            participation_rate=round(participation_rate, 2),
            current_round=current_round
        )

        self._cache.set("network_stats", stats, self.CACHE_TTL)
        return stats

    async def _fetch_account(self, address: str) -> Optional[Dict[str, Any]]:
        """Fetch account details. Returns None if account not found."""
        try:
            data = await self._fetch_json(f"/v2/accounts/{address}")
            return data
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            raise

    async def get_foundation_stats(self) -> FoundationStats:
        """Calculate Foundation's stake and participation status."""
        cached = self._cache.get("foundation_stats")
        if cached is not None:
            return cached

        network_stats = await self.get_network_stats()
        current_round = network_stats.current_round

        total_balance = 0
        online_balance = 0
        address_details = []

        # Fetch all Foundation addresses concurrently
        tasks = [self._fetch_account(addr) for addr in self.FOUNDATION_ADDRESSES]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for addr, result in zip(self.FOUNDATION_ADDRESSES, results):
            if isinstance(result, Exception):
                # Log error but continue with other addresses
                address_details.append({
                    "address": addr,
                    "balance": 0,
                    "is_online": False,
                    "error": str(result)
                })
                continue

            if result is None:
                address_details.append({
                    "address": addr,
                    "balance": 0,
                    "is_online": False,
                    "error": "Account not found"
                })
                continue

            balance = result.get("amount", 0)
            status = result.get("status", "Offline")
            is_online = status == "Online"

            # Check if participation key is expired
            participation = result.get("participation", {})
            vote_last_valid = participation.get("vote-last-valid", 0)
            if is_online and vote_last_valid > 0 and vote_last_valid < current_round:
                is_online = False  # Key expired

            total_balance += balance
            if is_online:
                online_balance += balance

            address_details.append({
                "address": addr,
                "balance": balance,
                "is_online": is_online,
                "status": status,
                "vote_last_valid": vote_last_valid if vote_last_valid > 0 else None
            })

        # Calculate percentages
        foundation_pct_of_supply = 0.0
        foundation_pct_of_online = 0.0

        if network_stats.total_supply > 0:
            foundation_pct_of_supply = (total_balance / network_stats.total_supply) * 100

        if network_stats.online_stake > 0:
            foundation_pct_of_online = (online_balance / network_stats.online_stake) * 100

        stats = FoundationStats(
            total_balance=total_balance,
            online_balance=online_balance,
            foundation_addresses=self.FOUNDATION_ADDRESSES.copy(),
            address_details=address_details,
            foundation_pct_of_supply=round(foundation_pct_of_supply, 2),
            foundation_pct_of_online=round(foundation_pct_of_online, 2)
        )

        self._cache.set("foundation_stats", stats, self.CACHE_TTL)
        return stats

    async def check_wallet_participation(self, address: str) -> WalletParticipation:
        """Check if a specific wallet is participating in consensus."""
        cache_key = f"wallet_{address}"
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached

        network_stats = await self.get_network_stats()
        current_round = network_stats.current_round

        account = await self._fetch_account(address)

        if account is None:
            return WalletParticipation(
                address=address,
                is_online=False,
                balance=0,
                vote_first_valid=None,
                vote_last_valid=None,
                vote_key_dilution=None,
                is_key_expired=False,
                stake_percentage=0.0,
                current_round=current_round
            )

        balance = account.get("amount", 0)
        status = account.get("status", "Offline")
        participation = account.get("participation", {})

        vote_first_valid = participation.get("vote-first-valid")
        vote_last_valid = participation.get("vote-last-valid")
        vote_key_dilution = participation.get("vote-key-dilution")

        is_online = status == "Online"
        is_key_expired = False

        if vote_last_valid and vote_last_valid < current_round:
            is_key_expired = True
            is_online = False  # Treat as offline if key expired

        stake_percentage = 0.0
        if network_stats.online_stake > 0 and is_online:
            stake_percentage = (balance / network_stats.online_stake) * 100

        result = WalletParticipation(
            address=address,
            is_online=is_online,
            balance=balance,
            vote_first_valid=vote_first_valid,
            vote_last_valid=vote_last_valid,
            vote_key_dilution=vote_key_dilution,
            is_key_expired=is_key_expired,
            stake_percentage=round(stake_percentage, 6),
            current_round=current_round
        )

        self._cache.set(cache_key, result, ttl_seconds=60)  # 1 minute cache for wallets
        return result

    async def get_decentralization_summary(self) -> DecentralizationSummary:
        """
        Get combined summary for dashboard display.

        DECENTRALIZATION SCORING METHODOLOGY (Strict / Honest Assessment)
        =================================================================

        We start with a base of 100 points and apply both positive factors
        and risk penalties. This reflects our thesis that Algorand has
        POTENTIAL for decentralization but significant risks remain.

        POSITIVE FACTORS (max 40 points):
        - Community % of online stake: max 30 points
          (Scaled: 100% community = 30pts, 80% = 24pts, etc.)
        - Participation rate: max 10 points
          (Scaled: 30%+ participation = 10pts)

        RISK PENALTIES (can reduce score significantly):
        - Foundation % of total supply: up to -25 points
          (If Foundation controls 20%+ of supply, that's a centralization risk
           even if they're not currently online. They COULD go online.)
        - Foundation potential control: up to -20 points
          (If Foundation went fully online, what % would they control?
           This is the "nuclear option" risk.)
        - Relay node centralization: -15 points
          (Foundation runs/controls most relay nodes - known issue)
        - Governance influence: -10 points
          (Foundation controls protocol upgrades, grants, etc.)

        SCORE INTERPRETATION:
        - 70-100: Healthy decentralization (Bitcoin-like)
        - 50-69:  Moderate - improving but risks remain
        - 30-49:  Concerning - significant centralization
        - 0-29:   Critical - effectively centralized

        Current realistic expectation: ~45-55 for Algorand mainnet
        """
        cached = self._cache.get("decentralization_summary")
        if cached is not None:
            return cached

        # Fetch both stats concurrently
        network_stats, foundation_stats = await asyncio.gather(
            self.get_network_stats(),
            self.get_foundation_stats()
        )

        # Calculate community stake
        community_stake = network_stats.online_stake - foundation_stats.online_balance
        if community_stake < 0:
            community_stake = 0

        community_pct_of_online = 0.0
        if network_stats.online_stake > 0:
            community_pct_of_online = (community_stake / network_stats.online_stake) * 100

        # =====================================================================
        # STRICT DECENTRALIZATION SCORING (v3 - Realistic Assessment)
        # =====================================================================
        #
        # This scoring reflects our thesis: Algorand has POTENTIAL for
        # decentralization but currently has significant centralization risks.
        #
        # We use a 3-tier model:
        # 1. CONSENSUS CONTROL (40 points max) - Who controls block production?
        # 2. INFRASTRUCTURE (30 points max) - Who runs the network?
        # 3. GOVERNANCE (30 points max) - Who controls the protocol?
        #
        # Current realistic expectation for Algorand: ~45-55
        # Bitcoin comparison: would score ~85-90
        #
        # =====================================================================

        # --- TIER 1: CONSENSUS CONTROL (40 points max) ---
        # This is the most important: who actually produces blocks?

        # Points for community % of online stake (max 25 points)
        # 100% community = 25 points, scales linearly
        community_consensus_score = int(min(25, (community_pct_of_online / 100) * 25))

        # Penalty for Foundation potential control (max -15 points)
        # If Foundation went online, how much could they control?
        potential_foundation_online = foundation_stats.total_balance
        potential_total_online = network_stats.online_stake + (
            foundation_stats.total_balance - foundation_stats.online_balance
        )
        foundation_potential_control = 0.0
        if potential_total_online > 0:
            foundation_potential_control = (potential_foundation_online / potential_total_online) * 100

        # Tiered penalty based on threat level
        if foundation_potential_control >= 50:
            potential_control_penalty = 15  # Could halt network
        elif foundation_potential_control >= 33:
            potential_control_penalty = 12  # Blocking minority
        elif foundation_potential_control >= 20:
            potential_control_penalty = 8
        elif foundation_potential_control >= 10:
            potential_control_penalty = 5
        else:
            potential_control_penalty = int(foundation_potential_control / 2)

        # Foundation % of total supply is ALWAYS a risk (max -10 points)
        # Even 3% of 10B tokens = $300M potential attack vector
        foundation_supply_pct = foundation_stats.foundation_pct_of_supply
        foundation_supply_penalty = int(min(10, foundation_supply_pct * 2))

        tier1_score = max(0, community_consensus_score - potential_control_penalty - foundation_supply_penalty)

        # --- TIER 2: INFRASTRUCTURE (30 points max) ---
        # Who runs the actual network infrastructure?

        # Base infrastructure score from participation rate
        # 50%+ participation = 15 points (more nodes = more resilient)
        # 30% = 10 points, 20% = 7 points, 10% = 3 points
        participation_rate = network_stats.participation_rate
        if participation_rate >= 50:
            participation_score = 15
        elif participation_rate >= 30:
            participation_score = 10
        elif participation_rate >= 20:
            participation_score = 7
        elif participation_rate >= 10:
            participation_score = 3
        else:
            participation_score = 0

        # Relay node centralization is a MAJOR issue (fixed -10 points)
        # Foundation controls/coordinates most relay infrastructure
        # This is a significant centralization point, but community relays
        # are growing (Nodely, D13, etc.)
        relay_centralization_penalty = 10

        tier2_score = max(0, participation_score - relay_centralization_penalty + 15)
        # Add 15 to offset, so if participation is good we can get some points

        # --- TIER 3: GOVERNANCE (30 points max) ---
        # Who controls protocol direction?

        # Currently Foundation has significant governance control
        # - Protocol upgrades require Foundation coordination
        # - Grants program is Foundation-controlled
        # - Node software development is Foundation-led
        #
        # However, Algorand does have some governance mechanisms:
        # - Governance voting for rewards distribution
        # - Community input on protocol direction
        # - Open-source codebase
        #
        # We give partial credit for existing governance while
        # acknowledging Foundation still has ultimate control
        governance_score = 15  # Partial credit for existing governance

        # Penalty for Foundation's ongoing protocol control
        governance_penalty = 5  # Reduced - governance IS improving

        tier3_score = max(0, governance_score - governance_penalty + 10)

        # --- CALCULATE FINAL SCORE ---
        raw_score = tier1_score + tier2_score + tier3_score
        final_score = max(0, min(100, raw_score))

        # For the breakdown, map to expected fields
        community_online_score = community_consensus_score
        participation_rate_score = participation_score

        # Create breakdown
        breakdown = DecentralizationScoreBreakdown(
            community_online_pct=round(community_pct_of_online, 2),
            community_online_score=community_online_score,
            participation_rate_score=participation_rate_score,
            foundation_supply_pct=round(foundation_supply_pct, 2),
            foundation_supply_penalty=foundation_supply_penalty,
            foundation_potential_control=round(foundation_potential_control, 2),
            potential_control_penalty=potential_control_penalty,
            relay_centralization_penalty=relay_centralization_penalty,
            governance_penalty=governance_penalty,
            raw_score=raw_score,
            final_score=final_score
        )

        summary = DecentralizationSummary(
            network=network_stats,
            foundation=foundation_stats,
            community_stake=community_stake,
            community_pct_of_online=round(community_pct_of_online, 2),
            decentralization_score=final_score,
            score_breakdown=breakdown,
            fetched_at=time.time()
        )

        self._cache.set("decentralization_summary", summary, self.CACHE_TTL)
        return summary


# -----------------------------------------------------------------------------
# Helper Functions
# -----------------------------------------------------------------------------

def microalgos_to_algo(microalgos: int) -> float:
    """Convert microAlgos to ALGO."""
    return microalgos / 1_000_000


def format_algo(microalgos: int, decimals: int = 2) -> str:
    """Format microAlgos as human-readable ALGO string."""
    algo = microalgos_to_algo(microalgos)
    if algo >= 1_000_000_000:
        return f"{algo / 1_000_000_000:.{decimals}f}B ALGO"
    elif algo >= 1_000_000:
        return f"{algo / 1_000_000:.{decimals}f}M ALGO"
    elif algo >= 1_000:
        return f"{algo / 1_000:.{decimals}f}K ALGO"
    else:
        return f"{algo:.{decimals}f} ALGO"


# -----------------------------------------------------------------------------
# Test / Demo
# -----------------------------------------------------------------------------

async def main():
    """Test the network stats module with real mainnet data."""
    print("=" * 60)
    print("Algorand Network Statistics - Live Mainnet Data")
    print("=" * 60)

    stats = AlgorandNetworkStats()

    try:
        # Fetch decentralization summary
        print("\nFetching network data...")
        summary = await stats.get_decentralization_summary()

        print("\n--- NETWORK STATS ---")
        print(f"Current Round: {summary.network.current_round:,}")
        print(f"Total Supply: {format_algo(summary.network.total_supply)}")
        print(f"Online Stake: {format_algo(summary.network.online_stake)}")
        print(f"Participation Rate: {summary.network.participation_rate:.2f}%")

        print("\n--- FOUNDATION STATS ---")
        print(f"Foundation Total Balance: {format_algo(summary.foundation.total_balance)}")
        print(f"Foundation Online Stake: {format_algo(summary.foundation.online_balance)}")
        print(f"Foundation % of Total Supply: {summary.foundation.foundation_pct_of_supply:.2f}%")
        print(f"Foundation % of Online Stake: {summary.foundation.foundation_pct_of_online:.2f}%")

        print("\n--- Foundation Address Breakdown ---")
        for detail in summary.foundation.address_details:
            addr_short = detail["address"][:8] + "..." + detail["address"][-4:]
            balance = format_algo(detail["balance"])
            status = "ONLINE" if detail.get("is_online") else "offline"
            print(f"  {addr_short}: {balance:>15} [{status}]")

        print("\n--- COMMUNITY STATS ---")
        print(f"Community Stake: {format_algo(summary.community_stake)}")
        print(f"Community % of Online: {summary.community_pct_of_online:.2f}%")

        print("\n--- DECENTRALIZATION SCORE ---")
        print(f"Final Score: {summary.decentralization_score}/100")

        if summary.score_breakdown:
            b = summary.score_breakdown
            print("\n  POSITIVE FACTORS:")
            print(f"    Community online stake ({b.community_online_pct:.1f}%): +{b.community_online_score} pts")
            print(f"    Participation rate: +{b.participation_rate_score} pts")
            print(f"    Subtotal: +{b.community_online_score + b.participation_rate_score} pts")

            print("\n  RISK PENALTIES:")
            print(f"    Foundation supply ({b.foundation_supply_pct:.1f}%): -{b.foundation_supply_penalty} pts")
            print(f"    Potential control ({b.foundation_potential_control:.1f}%): -{b.potential_control_penalty} pts")
            print(f"    Relay centralization: -{b.relay_centralization_penalty} pts")
            print(f"    Governance influence: -{b.governance_penalty} pts")
            total_penalty = (b.foundation_supply_penalty + b.potential_control_penalty +
                           b.relay_centralization_penalty + b.governance_penalty)
            print(f"    Subtotal: -{total_penalty} pts")

            print(f"\n  Raw Score: {b.raw_score}")
            print(f"  Final Score (0-100): {b.final_score}")

        print("\n  INTERPRETATION:")
        if summary.decentralization_score >= 75:
            print("  Status: HEALTHY - Network is well decentralized")
        elif summary.decentralization_score >= 45:
            print("  Status: MODERATE - Improving but risks remain")
        elif summary.decentralization_score >= 25:
            print("  Status: CONCERNING - Significant centralization")
        else:
            print("  Status: CRITICAL - Effectively centralized")

        # Test wallet participation check
        print("\n--- WALLET PARTICIPATION CHECK ---")
        # Using a known online address (one of the Foundation addresses as a test)
        test_addr = "RW466IANOKLA36QARHMBX5VCY3PYDR3H2N5XHPDARG6UBOKCIK7WAMLSCA"
        wallet = await stats.check_wallet_participation(test_addr)
        print(f"Address: {test_addr[:12]}...")
        print(f"Balance: {format_algo(wallet.balance)}")
        print(f"Is Online: {wallet.is_online}")
        print(f"Key Expired: {wallet.is_key_expired}")
        if wallet.vote_last_valid:
            rounds_remaining = wallet.vote_last_valid - wallet.current_round
            print(f"Key Valid Until Round: {wallet.vote_last_valid:,} ({rounds_remaining:,} rounds remaining)")
        print(f"Stake %: {wallet.stake_percentage:.4f}%")

    finally:
        await stats.close()

    print("\n" + "=" * 60)
    print("Test complete!")


if __name__ == "__main__":
    asyncio.run(main())
