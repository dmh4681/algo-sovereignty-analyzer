"""
Portfolio Rebalancing Engine.

Suggests portfolio rebalancing moves to improve sovereignty scores by
shifting from low-sovereignty to high-sovereignty assets.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any

from .models import SovereigntyData


@dataclass
class RebalanceSuggestion:
    """A suggested portfolio rebalancing move."""
    from_asset: str
    to_asset: str
    amount: float
    reason: str
    impact_on_score: float

    def to_dict(self) -> Dict[str, Any]:
        """Convert suggestion to dictionary for JSON serialization."""
        return {
            "from_asset": self.from_asset,
            "to_asset": self.to_asset,
            "amount": self.amount,
            "reason": self.reason,
            "impact_on_score": self.impact_on_score
        }


# Hard money assets in order of sovereignty preference
HARD_MONEY_ASSETS = {
    "BTC": {"priority": 1, "type": "bitcoin"},
    "GOBTC": {"priority": 1, "type": "bitcoin"},
    "WBTC": {"priority": 1, "type": "bitcoin"},
    "FGOBTC": {"priority": 1, "type": "bitcoin"},
    "GOLD$": {"priority": 2, "type": "gold"},
    "XAUT": {"priority": 2, "type": "gold"},
    "PAXG": {"priority": 2, "type": "gold"},
    "SILVER$": {"priority": 3, "type": "silver"},
}

# Category weights for sovereignty calculation
# Higher weight = better for sovereignty
CATEGORY_WEIGHTS = {
    "hard_money": 1.0,   # Full sovereignty value
    "algo": 0.5,         # Moderate sovereignty (crypto, but not hard money)
    "dollars": 0.3,      # Low sovereignty (fiat-backed)
    "shitcoin": 0.1,     # Minimal sovereignty value
}


class RebalanceEngine:
    """
    Engine for calculating and suggesting portfolio rebalancing.

    Aims to improve sovereignty scores by shifting assets from
    low-sovereignty categories to hard money (BTC, Gold, Silver).
    """

    def __init__(self):
        self.category_weights = CATEGORY_WEIGHTS.copy()
        self.hard_money_assets = HARD_MONEY_ASSETS.copy()

    def calculate_optimal_allocation(
        self,
        current: Dict[str, List[Dict[str, Any]]],
        target_score: float
    ) -> Dict[str, float]:
        """
        Calculate optimal asset allocation to reach target sovereignty score.

        Args:
            current: Current holdings by category
            target_score: Target sovereignty ratio

        Returns:
            Dict with recommended percentage allocation per category
        """
        # Calculate current total value
        total_value = 0.0
        category_values = {}

        for category, assets in current.items():
            cat_value = sum(asset.get("usd_value", 0.0) for asset in assets)
            category_values[category] = cat_value
            total_value += cat_value

        if total_value <= 0:
            # Default allocation if no holdings
            return {
                "hard_money": 0.6,
                "algo": 0.3,
                "dollars": 0.1,
                "shitcoin": 0.0
            }

        # Current allocation percentages
        current_allocation = {
            cat: val / total_value for cat, val in category_values.items()
        }

        # For higher target scores, recommend more hard money
        # Score thresholds map to minimum hard money percentages
        if target_score >= 20:
            # Generationally Sovereign - maximize hard money
            optimal = {
                "hard_money": 0.80,
                "algo": 0.15,
                "dollars": 0.05,
                "shitcoin": 0.0
            }
        elif target_score >= 6:
            # Antifragile
            optimal = {
                "hard_money": 0.70,
                "algo": 0.20,
                "dollars": 0.10,
                "shitcoin": 0.0
            }
        elif target_score >= 3:
            # Robust
            optimal = {
                "hard_money": 0.60,
                "algo": 0.25,
                "dollars": 0.10,
                "shitcoin": 0.05
            }
        elif target_score >= 1:
            # Fragile -> Robust transition
            optimal = {
                "hard_money": 0.50,
                "algo": 0.30,
                "dollars": 0.15,
                "shitcoin": 0.05
            }
        else:
            # Vulnerable -> Fragile transition
            optimal = {
                "hard_money": 0.40,
                "algo": 0.30,
                "dollars": 0.20,
                "shitcoin": 0.10
            }

        return optimal

    def suggest_rebalancing(
        self,
        current_holdings: Dict[str, List[Dict[str, Any]]],
        target_allocation: Dict[str, float]
    ) -> List[RebalanceSuggestion]:
        """
        Generate specific rebalancing suggestions.

        Args:
            current_holdings: Current asset holdings by category
            target_allocation: Target percentage allocation per category

        Returns:
            List of rebalancing suggestions
        """
        suggestions = []

        # Calculate current values
        total_value = 0.0
        category_values = {}
        category_assets = {}

        for category, assets in current_holdings.items():
            cat_value = sum(asset.get("usd_value", 0.0) for asset in assets)
            category_values[category] = cat_value
            category_assets[category] = assets
            total_value += cat_value

        if total_value <= 0:
            return suggestions

        # Calculate current and target values per category
        current_pcts = {cat: val / total_value for cat, val in category_values.items()}

        # Identify over-allocated and under-allocated categories
        over_allocated = []
        under_allocated = []

        for category in ["hard_money", "algo", "dollars", "shitcoin"]:
            current_pct = current_pcts.get(category, 0.0)
            target_pct = target_allocation.get(category, 0.0)
            diff = current_pct - target_pct

            if diff > 0.05:  # More than 5% over target
                over_allocated.append((category, diff, current_pct))
            elif diff < -0.05:  # More than 5% under target
                under_allocated.append((category, abs(diff), target_pct))

        # Sort by difference (largest first)
        over_allocated.sort(key=lambda x: x[1], reverse=True)
        under_allocated.sort(key=lambda x: x[1], reverse=True)

        # Generate suggestions: move from over-allocated to under-allocated
        # Priority: move TO hard_money first
        for under_cat, under_diff, target_pct in under_allocated:
            if under_cat != "hard_money":
                continue

            for over_cat, over_diff, current_pct in over_allocated:
                if over_diff <= 0:
                    continue

                # Calculate amount to move
                move_pct = min(over_diff, under_diff)
                move_amount = move_pct * total_value

                if move_amount < 100:  # Skip tiny moves
                    continue

                # Find best source asset (largest value in over-allocated category)
                source_assets = category_assets.get(over_cat, [])
                if not source_assets:
                    continue

                source_asset = max(source_assets, key=lambda a: a.get("usd_value", 0))
                source_ticker = source_asset.get("ticker", "Unknown")

                # Suggest moving to BTC first (highest sovereignty)
                target_ticker = "BTC/goBTC"

                # Calculate rough impact on score
                # Moving from shitcoin to hard_money has biggest impact
                weight_improvement = (
                    self.category_weights.get("hard_money", 1.0) -
                    self.category_weights.get(over_cat, 0.1)
                )
                score_impact = move_pct * weight_improvement * 10  # Rough estimate

                suggestions.append(RebalanceSuggestion(
                    from_asset=source_ticker,
                    to_asset=target_ticker,
                    amount=round(move_amount, 2),
                    reason=f"Reduce {over_cat} exposure ({current_pct*100:.1f}% -> "
                           f"{(current_pct-move_pct)*100:.1f}%) and increase hard money",
                    impact_on_score=round(score_impact, 2)
                ))

                # Update remaining diff
                over_allocated = [(c, d-move_pct if c == over_cat else d, p)
                                  for c, d, p in over_allocated]

        # Additional suggestions for shitcoins -> algo (if hard_money is at target)
        shitcoin_assets = category_assets.get("shitcoin", [])
        if shitcoin_assets and current_pcts.get("shitcoin", 0) > 0.1:
            # Suggest converting top shitcoins to ALGO
            for asset in sorted(shitcoin_assets,
                               key=lambda a: a.get("usd_value", 0),
                               reverse=True)[:3]:
                value = asset.get("usd_value", 0)
                if value < 100:
                    continue

                suggestions.append(RebalanceSuggestion(
                    from_asset=asset.get("ticker", "Unknown"),
                    to_asset="ALGO",
                    amount=round(value, 2),
                    reason=f"Convert low-sovereignty shitcoin to ALGO for better diversification",
                    impact_on_score=round(value / total_value * 4, 2)  # Rough estimate
                ))

        # Sort by impact (highest first)
        suggestions.sort(key=lambda s: s.impact_on_score, reverse=True)

        # Limit to top 5 suggestions
        return suggestions[:5]

    def estimate_score_after_rebalance(
        self,
        current_holdings: Dict[str, List[Dict[str, Any]]],
        suggestions: List[RebalanceSuggestion],
        current_sovereignty: Optional[SovereigntyData]
    ) -> float:
        """
        Estimate what the sovereignty score would be after applying suggestions.

        Args:
            current_holdings: Current asset holdings by category
            suggestions: List of rebalancing suggestions to apply
            current_sovereignty: Current sovereignty data

        Returns:
            Estimated sovereignty ratio after rebalancing
        """
        if not current_sovereignty:
            return 0.0

        # Calculate current weighted portfolio value
        total_value = 0.0
        weighted_value = 0.0

        for category, assets in current_holdings.items():
            cat_value = sum(asset.get("usd_value", 0.0) for asset in assets)
            total_value += cat_value
            weighted_value += cat_value * self.category_weights.get(category, 0.1)

        if total_value <= 0:
            return current_sovereignty.sovereignty_ratio

        # Apply suggestions
        value_changes = {
            "hard_money": 0.0,
            "algo": 0.0,
            "dollars": 0.0,
            "shitcoin": 0.0
        }

        for suggestion in suggestions:
            amount = suggestion.amount

            # Determine source category based on asset name
            from_cat = self._get_asset_category(suggestion.from_asset, current_holdings)
            to_cat = self._get_asset_category(suggestion.to_asset, current_holdings)

            if from_cat:
                value_changes[from_cat] -= amount
            if to_cat:
                value_changes[to_cat] += amount

        # Calculate new weighted value
        new_weighted = weighted_value
        for category, change in value_changes.items():
            weight = self.category_weights.get(category, 0.1)
            new_weighted += change * weight

        # The sovereignty ratio is portfolio_usd / annual_expenses
        # Rebalancing doesn't change total value, but we're estimating
        # the "effective" value based on hard money concentration

        # Rough estimate: scale current ratio by improvement factor
        if weighted_value > 0:
            improvement_factor = new_weighted / weighted_value
            return round(current_sovereignty.sovereignty_ratio * improvement_factor, 2)

        return current_sovereignty.sovereignty_ratio

    def _get_asset_category(
        self,
        ticker: str,
        holdings: Dict[str, List[Dict[str, Any]]]
    ) -> Optional[str]:
        """Get the category for an asset ticker."""
        ticker_upper = ticker.upper()

        # Check hard money assets
        if ticker_upper in self.hard_money_assets:
            return "hard_money"

        # Check if it's a known hard money destination
        if any(hm in ticker_upper for hm in ["BTC", "GOLD", "SILVER"]):
            return "hard_money"

        # Check ALGO
        if ticker_upper in ["ALGO", "XALGO", "FALGO", "GALGO", "MALGO", "LALGO", "TALGO"]:
            return "algo"

        # Check stablecoins
        if ticker_upper in ["USDC", "USDT", "DAI", "FUSDC", "FUSDT", "STBL"]:
            return "dollars"

        # Check in current holdings
        for category, assets in holdings.items():
            for asset in assets:
                if asset.get("ticker", "").upper() == ticker_upper:
                    return category

        return "shitcoin"  # Default to shitcoin if unknown
