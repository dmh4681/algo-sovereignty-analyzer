"""
DeFi Yield Farming Sovereignty Cost Calculator

This module analyzes LP (Liquidity Provider) positions to calculate the "sovereignty cost"
of earning yield - how much sovereignty score is sacrificed for APY.

The core insight is: When you provide liquidity, you pair assets together. If one asset
is "hard money" (BTC, Gold, Silver) and the other is not (USDC, shitcoins), you're
diluting your sovereignty for yield.

Sovereignty Cost = What your position WOULD contribute to sovereignty score
                   if the non-sovereign half was converted to hard money.

Example:
    - You have $1,000 in an ALGO-USDC LP earning 10% APY
    - Half of that ($500) is ALGO, half is USDC
    - If you had $1,000 in pure ALGO, your sovereignty score would be higher
    - The "sovereignty cost" is the score difference
    - We can calculate: is 10% APY worth that sovereignty dilution?

Key Metrics:
    1. Current Sovereignty Contribution: What the LP adds to your score now
    2. Potential Sovereignty Contribution: If 100% was in the best asset
    3. Sovereignty Cost: The difference (potential - current)
    4. Sovereignty Cost Rate: Cost per APY point (is the yield worth it?)
    5. Break-even Period: How long until yield covers the sovereignty cost

Author: Dylan Heiney
Date: January 2026
"""

from dataclasses import dataclass
from typing import Dict, List, Any, Optional
from enum import Enum


class AssetSovereigntyTier(Enum):
    """Classification of assets by sovereignty value (hard money maximalist philosophy)"""
    HARD_MONEY = 4      # BTC, Gold, Silver - highest sovereignty
    ALGORAND = 3        # ALGO and liquid staking derivatives
    STABLECOIN = 1      # USDC, USDT - stable but not sovereign (fiat backed)
    SHITCOIN = 0        # Everything else - no sovereignty value


# Sovereignty tier mappings (same logic as classifier.py)
TICKER_SOVEREIGNTY_TIER = {
    # Hard Money (Tier 4)
    'GOBTC': AssetSovereigntyTier.HARD_MONEY,
    'WBTC': AssetSovereigntyTier.HARD_MONEY,
    'BTC': AssetSovereigntyTier.HARD_MONEY,
    'XAUT': AssetSovereigntyTier.HARD_MONEY,
    'PAXG': AssetSovereigntyTier.HARD_MONEY,
    'GOLD$': AssetSovereigntyTier.HARD_MONEY,
    'SILVER$': AssetSovereigntyTier.HARD_MONEY,

    # Algorand (Tier 3)
    'ALGO': AssetSovereigntyTier.ALGORAND,
    'XALGO': AssetSovereigntyTier.ALGORAND,
    'FALGO': AssetSovereigntyTier.ALGORAND,
    'GALGO': AssetSovereigntyTier.ALGORAND,
    'MALGO': AssetSovereigntyTier.ALGORAND,
    'TALGO': AssetSovereigntyTier.ALGORAND,
    'LALGO': AssetSovereigntyTier.ALGORAND,

    # Stablecoins (Tier 1)
    'USDC': AssetSovereigntyTier.STABLECOIN,
    'USDT': AssetSovereigntyTier.STABLECOIN,
    'DAI': AssetSovereigntyTier.STABLECOIN,
    'FUSDC': AssetSovereigntyTier.STABLECOIN,
    'FUSDT': AssetSovereigntyTier.STABLECOIN,
}


def get_sovereignty_tier(ticker: str) -> AssetSovereigntyTier:
    """Get the sovereignty tier for an asset ticker"""
    return TICKER_SOVEREIGNTY_TIER.get(ticker.upper(), AssetSovereigntyTier.SHITCOIN)


@dataclass
class LPSovereigntyCost:
    """
    Represents the sovereignty cost analysis for a single LP position.

    Attributes:
        lp_name: Name of the LP token
        lp_ticker: Ticker symbol
        total_usd_value: Total USD value of the LP position
        asset1_ticker: First underlying asset
        asset1_usd: USD value of first asset
        asset1_tier: Sovereignty tier of first asset
        asset2_ticker: Second underlying asset
        asset2_usd: USD value of second asset
        asset2_tier: Sovereignty tier of second asset
        current_sovereignty_score: Weighted sovereignty contribution now
        potential_sovereignty_score: If position was 100% best asset
        sovereignty_cost: The difference (what you're giving up)
        sovereignty_cost_percent: Cost as percentage of potential
        estimated_apy: Estimated annual yield (if provided)
        break_even_years: How long until yield covers the cost
        recommendation: Human-readable recommendation
    """
    lp_name: str
    lp_ticker: str
    total_usd_value: float

    asset1_ticker: str
    asset1_usd: float
    asset1_tier: AssetSovereigntyTier

    asset2_ticker: str
    asset2_usd: float
    asset2_tier: AssetSovereigntyTier

    current_sovereignty_score: float
    potential_sovereignty_score: float
    sovereignty_cost: float
    sovereignty_cost_percent: float

    estimated_apy: Optional[float] = None
    break_even_years: Optional[float] = None
    recommendation: str = ""


@dataclass
class PortfolioSovereigntyCostSummary:
    """
    Summary of sovereignty costs across all LP positions in a portfolio.

    Attributes:
        total_lp_value_usd: Total value locked in LPs
        total_current_score: Current weighted sovereignty contribution
        total_potential_score: If all LPs were converted to best asset
        total_sovereignty_cost: Sum of all costs
        total_sovereignty_cost_percent: Cost as percentage of potential
        total_estimated_apy_earnings: Estimated annual yield in USD
        overall_recommendation: Portfolio-level recommendation
        lp_details: Individual LP cost analyses
    """
    total_lp_value_usd: float
    total_current_score: float
    total_potential_score: float
    total_sovereignty_cost: float
    total_sovereignty_cost_percent: float
    total_estimated_apy_earnings: float
    overall_recommendation: str
    lp_details: List[LPSovereigntyCost]


class DeFiSovereigntyCostCalculator:
    """
    Calculator for analyzing the sovereignty cost of DeFi yield farming.

    This class examines LP positions and calculates how much sovereignty score
    is being "sacrificed" for yield. It helps users make informed decisions
    about whether yield farming is worth the sovereignty dilution.

    Philosophy:
        From a hard money maximalist perspective, yield farming often involves
        pairing hard money assets with non-sovereign assets. This calculator
        quantifies that trade-off.

    Usage:
        calculator = DeFiSovereigntyCostCalculator()
        cost = calculator.analyze_lp_position(breakdown, estimated_apy=10.0)
        summary = calculator.analyze_portfolio(all_lp_breakdowns, apy_estimates)
    """

    def __init__(self):
        """Initialize the calculator."""
        pass

    def _calculate_weighted_score(self, usd_value: float, tier: AssetSovereigntyTier) -> float:
        """
        Calculate the weighted sovereignty score contribution.

        Higher tiers contribute more to sovereignty.
        Score = USD Value × (Tier Value / Max Tier Value)
        """
        max_tier = AssetSovereigntyTier.HARD_MONEY.value  # 4
        return usd_value * (tier.value / max_tier)

    def analyze_lp_position(
        self,
        lp_ticker: str,
        lp_name: str,
        asset1_ticker: str,
        asset1_usd: float,
        asset2_ticker: str,
        asset2_usd: float,
        estimated_apy: Optional[float] = None
    ) -> LPSovereigntyCost:
        """
        Analyze the sovereignty cost of a single LP position.

        Args:
            lp_ticker: LP token ticker symbol
            lp_name: LP token name
            asset1_ticker: First underlying asset ticker
            asset1_usd: USD value of first asset
            asset2_ticker: Second underlying asset ticker
            asset2_usd: USD value of second asset
            estimated_apy: Estimated annual percentage yield (optional)

        Returns:
            LPSovereigntyCost with full analysis
        """
        total_usd = asset1_usd + asset2_usd

        # Get sovereignty tiers
        tier1 = get_sovereignty_tier(asset1_ticker)
        tier2 = get_sovereignty_tier(asset2_ticker)

        # Calculate current weighted sovereignty score
        score1 = self._calculate_weighted_score(asset1_usd, tier1)
        score2 = self._calculate_weighted_score(asset2_usd, tier2)
        current_score = score1 + score2

        # Calculate potential score (if entire position was best tier)
        best_tier = max(tier1, tier2, key=lambda t: t.value)
        potential_score = self._calculate_weighted_score(total_usd, best_tier)

        # Calculate sovereignty cost
        sovereignty_cost = potential_score - current_score
        cost_percent = (sovereignty_cost / potential_score * 100) if potential_score > 0 else 0

        # Calculate break-even period if APY is provided
        break_even_years = None
        if estimated_apy and estimated_apy > 0 and sovereignty_cost > 0:
            annual_yield_usd = total_usd * (estimated_apy / 100)
            # Break-even: when yield equals the sovereignty cost in USD terms
            # We approximate by assuming the cost could be "recovered" through yield
            break_even_years = sovereignty_cost / annual_yield_usd if annual_yield_usd > 0 else None

        # Generate recommendation
        recommendation = self._generate_recommendation(
            tier1, tier2, cost_percent, estimated_apy, break_even_years
        )

        return LPSovereigntyCost(
            lp_name=lp_name,
            lp_ticker=lp_ticker,
            total_usd_value=total_usd,
            asset1_ticker=asset1_ticker,
            asset1_usd=asset1_usd,
            asset1_tier=tier1,
            asset2_ticker=asset2_ticker,
            asset2_usd=asset2_usd,
            asset2_tier=tier2,
            current_sovereignty_score=round(current_score, 2),
            potential_sovereignty_score=round(potential_score, 2),
            sovereignty_cost=round(sovereignty_cost, 2),
            sovereignty_cost_percent=round(cost_percent, 1),
            estimated_apy=estimated_apy,
            break_even_years=round(break_even_years, 2) if break_even_years else None,
            recommendation=recommendation
        )

    def _generate_recommendation(
        self,
        tier1: AssetSovereigntyTier,
        tier2: AssetSovereigntyTier,
        cost_percent: float,
        apy: Optional[float],
        break_even: Optional[float]
    ) -> str:
        """Generate a human-readable recommendation based on analysis."""

        # Both assets are hard money - excellent for sovereignty
        if tier1 == AssetSovereigntyTier.HARD_MONEY and tier2 == AssetSovereigntyTier.HARD_MONEY:
            return "Excellent: Both assets are hard money. Sovereignty preserved."

        # One hard money, one not - depends on cost/yield trade-off
        if tier1 == AssetSovereigntyTier.HARD_MONEY or tier2 == AssetSovereigntyTier.HARD_MONEY:
            if cost_percent > 40:
                if apy and break_even:
                    if break_even > 5:
                        return f"High sovereignty cost ({cost_percent:.0f}%). Consider exiting - break-even is {break_even:.1f} years."
                    elif break_even > 2:
                        return f"Moderate trade-off. Yield may justify cost but break-even is {break_even:.1f} years."
                    else:
                        return f"Acceptable trade-off. Break-even in {break_even:.1f} years with {apy:.1f}% APY."
                return f"High sovereignty cost ({cost_percent:.0f}%). Consider consolidating to hard money."
            else:
                return f"Low sovereignty cost ({cost_percent:.0f}%). Reasonable LP position."

        # Both ALGO - good for sovereignty within Algorand
        if tier1 == AssetSovereigntyTier.ALGORAND and tier2 == AssetSovereigntyTier.ALGORAND:
            return "Good: Both assets are ALGO-based. Consider converting yield to hard money."

        # ALGO + Stablecoin - common but costly
        if (tier1 == AssetSovereigntyTier.ALGORAND and tier2 == AssetSovereigntyTier.STABLECOIN) or \
           (tier1 == AssetSovereigntyTier.STABLECOIN and tier2 == AssetSovereigntyTier.ALGORAND):
            if apy and apy > 15:
                return f"ALGO-Stablecoin LP: High yield ({apy:.1f}%) may justify the cost. Convert yield to hard money."
            return "ALGO-Stablecoin LP: Moderate sovereignty dilution. Consider ALGO-only staking."

        # Shitcoin involved
        if tier1 == AssetSovereigntyTier.SHITCOIN or tier2 == AssetSovereigntyTier.SHITCOIN:
            return "Warning: Shitcoin exposure. High risk, zero sovereignty value."

        return "Review this LP position relative to your sovereignty goals."

    def analyze_portfolio(
        self,
        lp_positions: List[Dict[str, Any]],
        apy_estimates: Optional[Dict[str, float]] = None
    ) -> PortfolioSovereigntyCostSummary:
        """
        Analyze sovereignty costs across all LP positions in a portfolio.

        Args:
            lp_positions: List of LP position dicts with keys:
                - lp_ticker, lp_name
                - asset1_ticker, asset1_usd
                - asset2_ticker, asset2_usd
            apy_estimates: Optional dict mapping lp_ticker to estimated APY

        Returns:
            PortfolioSovereigntyCostSummary with aggregate analysis
        """
        apy_estimates = apy_estimates or {}
        lp_details: List[LPSovereigntyCost] = []

        total_lp_value = 0.0
        total_current_score = 0.0
        total_potential_score = 0.0
        total_yield_estimate = 0.0

        for lp in lp_positions:
            apy = apy_estimates.get(lp.get('lp_ticker', ''))

            cost = self.analyze_lp_position(
                lp_ticker=lp.get('lp_ticker', 'UNKNOWN'),
                lp_name=lp.get('lp_name', 'Unknown LP'),
                asset1_ticker=lp.get('asset1_ticker', ''),
                asset1_usd=lp.get('asset1_usd', 0.0),
                asset2_ticker=lp.get('asset2_ticker', ''),
                asset2_usd=lp.get('asset2_usd', 0.0),
                estimated_apy=apy
            )

            lp_details.append(cost)
            total_lp_value += cost.total_usd_value
            total_current_score += cost.current_sovereignty_score
            total_potential_score += cost.potential_sovereignty_score

            if apy:
                total_yield_estimate += cost.total_usd_value * (apy / 100)

        # Calculate totals
        total_cost = total_potential_score - total_current_score
        total_cost_percent = (total_cost / total_potential_score * 100) if total_potential_score > 0 else 0

        # Generate overall recommendation
        overall_recommendation = self._generate_portfolio_recommendation(
            total_cost_percent, total_yield_estimate, total_lp_value
        )

        return PortfolioSovereigntyCostSummary(
            total_lp_value_usd=round(total_lp_value, 2),
            total_current_score=round(total_current_score, 2),
            total_potential_score=round(total_potential_score, 2),
            total_sovereignty_cost=round(total_cost, 2),
            total_sovereignty_cost_percent=round(total_cost_percent, 1),
            total_estimated_apy_earnings=round(total_yield_estimate, 2),
            overall_recommendation=overall_recommendation,
            lp_details=lp_details
        )

    def _generate_portfolio_recommendation(
        self,
        total_cost_percent: float,
        annual_yield: float,
        total_value: float
    ) -> str:
        """Generate portfolio-level recommendation."""

        if total_cost_percent < 10:
            return "Portfolio sovereignty well-preserved. Current LP strategy is aligned with hard money goals."

        elif total_cost_percent < 25:
            if annual_yield > 0:
                effective_yield = (annual_yield / total_value) * 100 if total_value > 0 else 0
                return f"Moderate sovereignty dilution ({total_cost_percent:.0f}%). " \
                       f"Earning ~{effective_yield:.1f}% effectively. Consider routing yield to hard money."
            return f"Moderate sovereignty dilution ({total_cost_percent:.0f}%). Review LP allocations."

        elif total_cost_percent < 50:
            return f"Significant sovereignty cost ({total_cost_percent:.0f}%). Consider consolidating to higher-tier assets."

        else:
            return f"High sovereignty cost ({total_cost_percent:.0f}%). Recommend reducing LP exposure and accumulating hard money."


def analyze_wallet_lp_costs(
    categories: Dict[str, List[Dict[str, Any]]],
    apy_estimates: Optional[Dict[str, float]] = None
) -> Optional[PortfolioSovereigntyCostSummary]:
    """
    Convenience function to analyze LP sovereignty costs from wallet analysis categories.

    Args:
        categories: Output from AlgorandSovereigntyAnalyzer.analyze_wallet()
        apy_estimates: Optional APY estimates by LP ticker

    Returns:
        PortfolioSovereigntyCostSummary or None if no LP positions found
    """
    # Extract LP positions from categories
    # LP components are marked with 'from_lp' key
    lp_positions: Dict[str, Dict[str, Any]] = {}

    for category_name, assets in categories.items():
        for asset in assets:
            if 'from_lp' in asset:
                lp_ticker = asset['from_lp']
                if lp_ticker not in lp_positions:
                    lp_positions[lp_ticker] = {
                        'lp_ticker': lp_ticker,
                        'lp_name': lp_ticker,
                        'asset1_ticker': None,
                        'asset1_usd': 0.0,
                        'asset2_ticker': None,
                        'asset2_usd': 0.0,
                    }

                # Add this component
                pos = lp_positions[lp_ticker]
                if pos['asset1_ticker'] is None:
                    pos['asset1_ticker'] = asset['ticker']
                    pos['asset1_usd'] = asset.get('usd_value', 0.0)
                else:
                    pos['asset2_ticker'] = asset['ticker']
                    pos['asset2_usd'] = asset.get('usd_value', 0.0)

    if not lp_positions:
        return None

    # Analyze with calculator
    calculator = DeFiSovereigntyCostCalculator()
    return calculator.analyze_portfolio(list(lp_positions.values()), apy_estimates)
