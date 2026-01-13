"""
Sovereignty Alert System.

Generates alerts when sovereignty scores drop below thresholds or when
market conditions create optimization opportunities.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any

from .models import SovereigntyData
from .history import SovereigntySnapshot


class AlertType(str, Enum):
    """Types of sovereignty alerts."""
    SCORE_DROP = "score_drop"
    SCORE_MILESTONE = "score_milestone"
    REBALANCE_OPPORTUNITY = "rebalance_opportunity"
    PRICE_THRESHOLD = "price_threshold"
    CONCENTRATION_WARNING = "concentration_warning"


class AlertSeverity(str, Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class Alert:
    """A sovereignty alert."""
    type: AlertType
    severity: str
    title: str
    message: str
    suggested_action: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert alert to dictionary for JSON serialization."""
        return {
            "type": self.type.value,
            "severity": self.severity,
            "title": self.title,
            "message": self.message,
            "suggested_action": self.suggested_action,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata
        }


# Default thresholds for sovereignty score alerts
DEFAULT_THRESHOLDS = {
    "critical_drop": 0.5,        # Alert if score drops by 50%+ since last check
    "significant_drop": 0.2,     # Alert if score drops by 20%+
    "fragile_threshold": 1.0,    # Alert if score drops below 1.0 (Fragile)
    "vulnerable_threshold": 0.5, # Critical alert if below 0.5 (Vulnerable)
}


class AlertEngine:
    """
    Engine for generating sovereignty alerts.

    Checks various conditions and generates appropriate alerts when
    thresholds are crossed or opportunities arise.
    """

    def __init__(self):
        self.thresholds = DEFAULT_THRESHOLDS.copy()

    def check_score_thresholds(
        self,
        current_score: float,
        history: List[SovereigntySnapshot],
        thresholds: Optional[Dict[str, float]] = None
    ) -> List[Alert]:
        """
        Check if sovereignty score has crossed important thresholds.

        Args:
            current_score: Current sovereignty ratio
            history: Historical snapshots to compare against
            thresholds: Custom thresholds (uses defaults if not provided)

        Returns:
            List of alerts for threshold crossings
        """
        alerts = []
        thresholds = thresholds or self.thresholds

        # Check absolute threshold crossings
        if current_score < thresholds.get("vulnerable_threshold", 0.5):
            alerts.append(Alert(
                type=AlertType.SCORE_DROP,
                severity=AlertSeverity.CRITICAL.value,
                title="Critical: Vulnerable Status",
                message=f"Your sovereignty ratio ({current_score:.2f}) is critically low. "
                        "You have less than 6 months of fixed expenses covered.",
                suggested_action="Consider increasing hard money holdings (BTC, Gold, Silver) "
                                "or reducing monthly expenses to improve your runway.",
                metadata={"current_score": current_score, "threshold": "vulnerable"}
            ))
        elif current_score < thresholds.get("fragile_threshold", 1.0):
            alerts.append(Alert(
                type=AlertType.SCORE_DROP,
                severity=AlertSeverity.WARNING.value,
                title="Warning: Fragile Status",
                message=f"Your sovereignty ratio ({current_score:.2f}) is below 1.0. "
                        "You have less than 1 year of fixed expenses covered.",
                suggested_action="Focus on accumulating hard money assets to reach "
                                "the Robust threshold (3.0+ years).",
                metadata={"current_score": current_score, "threshold": "fragile"}
            ))

        # Check for drops compared to recent history
        if history:
            # Get the most recent previous snapshot
            sorted_history = sorted(history, key=lambda x: x.timestamp, reverse=True)
            if sorted_history:
                previous = sorted_history[0]
                prev_score = previous.sovereignty_ratio

                if prev_score > 0:
                    drop_pct = (prev_score - current_score) / prev_score

                    if drop_pct >= thresholds.get("critical_drop", 0.5):
                        alerts.append(Alert(
                            type=AlertType.SCORE_DROP,
                            severity=AlertSeverity.CRITICAL.value,
                            title="Critical Score Drop",
                            message=f"Your sovereignty ratio dropped {drop_pct*100:.1f}% "
                                    f"from {prev_score:.2f} to {current_score:.2f}.",
                            suggested_action="Review recent portfolio changes. Consider if "
                                            "this drop requires rebalancing.",
                            metadata={
                                "current_score": current_score,
                                "previous_score": prev_score,
                                "drop_percentage": drop_pct * 100
                            }
                        ))
                    elif drop_pct >= thresholds.get("significant_drop", 0.2):
                        alerts.append(Alert(
                            type=AlertType.SCORE_DROP,
                            severity=AlertSeverity.WARNING.value,
                            title="Significant Score Drop",
                            message=f"Your sovereignty ratio dropped {drop_pct*100:.1f}% "
                                    f"from {prev_score:.2f} to {current_score:.2f}.",
                            suggested_action="Monitor your portfolio and consider "
                                            "accumulating more hard money assets.",
                            metadata={
                                "current_score": current_score,
                                "previous_score": prev_score,
                                "drop_percentage": drop_pct * 100
                            }
                        ))

        # Check for positive milestones
        milestone_thresholds = [
            (20.0, "Generationally Sovereign", "You have 20+ years of runway!"),
            (6.0, "Antifragile", "You have 6+ years of runway!"),
            (3.0, "Robust", "You have 3+ years of runway!"),
            (1.0, "Fragile", "You have 1+ year of runway!"),
        ]

        if history:
            sorted_history = sorted(history, key=lambda x: x.timestamp, reverse=True)
            if sorted_history:
                prev_score = sorted_history[0].sovereignty_ratio

                for threshold, status_name, achievement_msg in milestone_thresholds:
                    if current_score >= threshold > prev_score:
                        alerts.append(Alert(
                            type=AlertType.SCORE_MILESTONE,
                            severity=AlertSeverity.INFO.value,
                            title=f"Milestone Reached: {status_name}",
                            message=f"Congratulations! You've reached {status_name} status. "
                                    f"{achievement_msg}",
                            suggested_action="Keep building your sovereignty. "
                                            "Consider saving this milestone to your history.",
                            metadata={
                                "current_score": current_score,
                                "milestone": status_name,
                                "threshold": threshold
                            }
                        ))
                        break  # Only show highest milestone reached

        return alerts

    def check_concentration_risk(
        self,
        holdings: Dict[str, List[Dict[str, Any]]],
        max_single_asset: float = 0.5
    ) -> List[Alert]:
        """
        Check for concentration risk in the portfolio.

        Args:
            holdings: Categories dict with asset holdings
            max_single_asset: Maximum allowed percentage for a single asset (0.5 = 50%)

        Returns:
            List of concentration warning alerts
        """
        alerts = []

        # Calculate total portfolio value
        total_value = 0.0
        all_assets = []

        for category, assets in holdings.items():
            for asset in assets:
                value = asset.get("usd_value", 0.0)
                if value > 0:
                    total_value += value
                    all_assets.append({
                        "ticker": asset.get("ticker", "Unknown"),
                        "name": asset.get("name", "Unknown"),
                        "value": value,
                        "category": category
                    })

        if total_value <= 0:
            return alerts

        # Check each asset for concentration
        for asset in all_assets:
            pct = asset["value"] / total_value
            if pct > max_single_asset:
                alerts.append(Alert(
                    type=AlertType.CONCENTRATION_WARNING,
                    severity=AlertSeverity.WARNING.value,
                    title=f"High Concentration: {asset['ticker']}",
                    message=f"{asset['ticker']} represents {pct*100:.1f}% of your portfolio. "
                            f"Consider diversifying to reduce single-asset risk.",
                    suggested_action=f"Consider rebalancing some {asset['ticker']} into other "
                                    "hard money assets (BTC, Gold, Silver) for better diversification.",
                    metadata={
                        "asset_ticker": asset["ticker"],
                        "asset_name": asset["name"],
                        "concentration_pct": pct * 100,
                        "threshold_pct": max_single_asset * 100,
                        "category": asset["category"]
                    }
                ))

        return alerts

    def check_price_opportunities(
        self,
        prices: Dict[str, float],
        targets: Dict[str, Dict[str, float]]
    ) -> List[Alert]:
        """
        Check if current prices present opportunities based on target prices.

        Args:
            prices: Current prices keyed by ticker (e.g., {"BTC": 95000, "GOLD$": 85.0})
            targets: Target prices keyed by ticker with "buy" and "sell" thresholds
                     e.g., {"BTC": {"buy": 80000, "sell": 120000}}

        Returns:
            List of price opportunity alerts
        """
        alerts = []

        for ticker, current_price in prices.items():
            if ticker not in targets:
                continue

            target = targets[ticker]
            buy_target = target.get("buy")
            sell_target = target.get("sell")

            if buy_target and current_price <= buy_target:
                discount_pct = ((buy_target - current_price) / buy_target) * 100
                alerts.append(Alert(
                    type=AlertType.PRICE_THRESHOLD,
                    severity=AlertSeverity.INFO.value,
                    title=f"Buy Opportunity: {ticker}",
                    message=f"{ticker} is at ${current_price:,.2f}, below your buy target of "
                            f"${buy_target:,.2f} ({discount_pct:.1f}% discount).",
                    suggested_action=f"Consider accumulating {ticker} while prices are below your target.",
                    metadata={
                        "ticker": ticker,
                        "current_price": current_price,
                        "buy_target": buy_target,
                        "discount_pct": discount_pct
                    }
                ))
            elif sell_target and current_price >= sell_target:
                premium_pct = ((current_price - sell_target) / sell_target) * 100
                alerts.append(Alert(
                    type=AlertType.PRICE_THRESHOLD,
                    severity=AlertSeverity.INFO.value,
                    title=f"Take Profit Opportunity: {ticker}",
                    message=f"{ticker} is at ${current_price:,.2f}, above your sell target of "
                            f"${sell_target:,.2f} ({premium_pct:.1f}% premium).",
                    suggested_action=f"Consider taking some profits on {ticker} and rebalancing "
                                    "into other hard money assets.",
                    metadata={
                        "ticker": ticker,
                        "current_price": current_price,
                        "sell_target": sell_target,
                        "premium_pct": premium_pct
                    }
                ))

        return alerts

    def generate_all_alerts(
        self,
        categories: Dict[str, List[Dict[str, Any]]],
        sovereignty_data: Optional[SovereigntyData],
        history: Optional[List[SovereigntySnapshot]] = None,
        user_prefs: Optional[Dict[str, Any]] = None
    ) -> List[Alert]:
        """
        Generate all relevant alerts for a wallet analysis.

        Args:
            categories: Asset categories from wallet analysis
            sovereignty_data: Current sovereignty metrics (may be None if no expenses)
            history: Historical snapshots for comparison
            user_prefs: User preferences for alerts (thresholds, enabled types, etc.)

        Returns:
            List of all applicable alerts, sorted by severity
        """
        alerts = []
        user_prefs = user_prefs or {}
        history = history or []

        # Get enabled alert types (default: all enabled)
        enabled_types = user_prefs.get("enabled_types", list(AlertType))

        # Check score thresholds if we have sovereignty data
        if sovereignty_data and AlertType.SCORE_DROP in enabled_types:
            custom_thresholds = user_prefs.get("thresholds")
            score_alerts = self.check_score_thresholds(
                current_score=sovereignty_data.sovereignty_ratio,
                history=history,
                thresholds=custom_thresholds
            )
            alerts.extend(score_alerts)

        # Check milestone alerts
        if sovereignty_data and AlertType.SCORE_MILESTONE in enabled_types:
            # Milestone alerts are included in check_score_thresholds
            pass

        # Check concentration risk
        if AlertType.CONCENTRATION_WARNING in enabled_types:
            max_concentration = user_prefs.get("max_concentration", 0.5)
            concentration_alerts = self.check_concentration_risk(
                holdings=categories,
                max_single_asset=max_concentration
            )
            alerts.extend(concentration_alerts)

        # Check price opportunities if targets are provided
        if AlertType.PRICE_THRESHOLD in enabled_types:
            price_targets = user_prefs.get("price_targets", {})
            current_prices = user_prefs.get("current_prices", {})
            if price_targets and current_prices:
                price_alerts = self.check_price_opportunities(
                    prices=current_prices,
                    targets=price_targets
                )
                alerts.extend(price_alerts)

        # Sort by severity (critical first, then warning, then info)
        severity_order = {
            AlertSeverity.CRITICAL.value: 0,
            AlertSeverity.WARNING.value: 1,
            AlertSeverity.INFO.value: 2
        }
        alerts.sort(key=lambda a: severity_order.get(a.severity, 3))

        return alerts
