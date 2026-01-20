"""
Wallet Monitoring and Alerts System.

Provides automated monitoring of multiple wallets with sovereignty score tracking
and alerts for threshold crossings and arbitrage opportunities.

Features:
1. Multi-wallet tracking with configurable thresholds per wallet
2. Automated sovereignty score monitoring
3. Gold/Silver arbitrage alerts when premiums are favorable
4. Historical trend tracking and decline detection

Usage:
    monitor = WalletMonitor()
    monitor.add_wallet("ADDR1", min_score=3.0, monthly_expenses=4000)
    monitor.add_wallet("ADDR2", min_score=1.0)
    alerts = await monitor.check_all_wallets()
    arbitrage = monitor.check_arbitrage_opportunities()

Author: Dylan Heiney
Date: January 2026
"""

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from enum import Enum

from .alerts import Alert, AlertType, AlertSeverity, AlertEngine
from .models import SovereigntyData
from .history import get_history_manager, SovereigntySnapshot
from .pricing import (
    get_gold_price_per_oz,
    get_silver_price_per_oz,
    get_meld_gold_price,
    get_meld_silver_price,
    get_bitcoin_spot_price,
    get_gobtc_price,
    GRAMS_PER_TROY_OZ
)


class ArbitrageType(str, Enum):
    """Types of arbitrage opportunities."""
    GOLD_PREMIUM = "gold_premium"
    GOLD_DISCOUNT = "gold_discount"
    SILVER_PREMIUM = "silver_premium"
    SILVER_DISCOUNT = "silver_discount"
    BTC_PREMIUM = "btc_premium"
    BTC_DISCOUNT = "btc_discount"


@dataclass
class WalletConfig:
    """Configuration for a monitored wallet."""
    address: str
    label: str = ""                         # User-friendly name
    min_sovereignty_score: float = 1.0      # Alert if score drops below this
    monthly_fixed_expenses: float = 0.0     # For sovereignty calculation
    alert_on_drops: bool = True             # Alert on score decreases
    alert_on_milestones: bool = True        # Alert on positive milestones
    max_concentration: float = 0.5          # Maximum single-asset concentration
    last_checked: Optional[datetime] = None
    last_score: Optional[float] = None
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ArbitrageOpportunity:
    """Represents an arbitrage opportunity between spot and Algorand prices."""
    asset: str                              # GOLD, SILVER, BTC
    type: ArbitrageType
    spot_price: float                       # Current spot price
    algorand_price: float                   # Price on Algorand (MELD/goBTC)
    premium_percent: float                  # Positive = premium, negative = discount
    premium_usd: float                      # Absolute premium in USD
    recommendation: str                     # What action to take
    signal_strength: float                  # 0-100 strength of the signal
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "asset": self.asset,
            "type": self.type.value,
            "spot_price": self.spot_price,
            "algorand_price": self.algorand_price,
            "premium_percent": self.premium_percent,
            "premium_usd": self.premium_usd,
            "recommendation": self.recommendation,
            "signal_strength": self.signal_strength,
            "timestamp": self.timestamp.isoformat()
        }


class WalletMonitor:
    """
    Multi-wallet monitoring service with alert generation.

    Tracks multiple Algorand wallets, monitors sovereignty scores,
    and generates alerts for threshold crossings and opportunities.
    """

    # Arbitrage thresholds
    GOLD_PREMIUM_THRESHOLD = 5.0    # Alert if premium > 5%
    GOLD_DISCOUNT_THRESHOLD = -2.0  # Alert if discount > 2%
    SILVER_PREMIUM_THRESHOLD = 10.0 # Alert if premium > 10%
    SILVER_DISCOUNT_THRESHOLD = -5.0
    BTC_PREMIUM_THRESHOLD = 3.0
    BTC_DISCOUNT_THRESHOLD = -3.0

    def __init__(self, storage_path: Optional[str] = None):
        """
        Initialize the wallet monitor.

        Args:
            storage_path: Path to JSON file for persistent wallet configs
        """
        self.storage_path = Path(storage_path) if storage_path else Path("data/monitored_wallets.json")
        self.wallets: Dict[str, WalletConfig] = {}
        self.alert_engine = AlertEngine()
        self._load_wallets()

    def _load_wallets(self) -> None:
        """Load wallet configs from storage."""
        if self.storage_path.exists():
            try:
                with open(self.storage_path, 'r') as f:
                    data = json.load(f)
                    for addr, config in data.items():
                        # Convert datetime strings back to datetime objects
                        if config.get('last_checked'):
                            config['last_checked'] = datetime.fromisoformat(config['last_checked'])
                        if config.get('created_at'):
                            config['created_at'] = datetime.fromisoformat(config['created_at'])
                        self.wallets[addr] = WalletConfig(**config)
            except Exception as e:
                print(f"Warning: Could not load wallet configs: {e}")

    def _save_wallets(self) -> None:
        """Persist wallet configs to storage."""
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        data = {}
        for addr, config in self.wallets.items():
            config_dict = asdict(config)
            # Convert datetime to string for JSON
            if config_dict.get('last_checked'):
                config_dict['last_checked'] = config_dict['last_checked'].isoformat()
            if config_dict.get('created_at'):
                config_dict['created_at'] = config_dict['created_at'].isoformat()
            data[addr] = config_dict
        with open(self.storage_path, 'w') as f:
            json.dump(data, f, indent=2)

    def add_wallet(
        self,
        address: str,
        label: str = "",
        min_sovereignty_score: float = 1.0,
        monthly_fixed_expenses: float = 0.0,
        alert_on_drops: bool = True,
        alert_on_milestones: bool = True,
        max_concentration: float = 0.5
    ) -> WalletConfig:
        """
        Add a wallet to be monitored.

        Args:
            address: Algorand wallet address
            label: User-friendly name for the wallet
            min_sovereignty_score: Alert if score drops below this
            monthly_fixed_expenses: For sovereignty calculation
            alert_on_drops: Alert on score decreases
            alert_on_milestones: Alert on positive milestones
            max_concentration: Max single-asset concentration before alerting

        Returns:
            The created WalletConfig
        """
        config = WalletConfig(
            address=address,
            label=label or f"Wallet {address[:8]}",
            min_sovereignty_score=min_sovereignty_score,
            monthly_fixed_expenses=monthly_fixed_expenses,
            alert_on_drops=alert_on_drops,
            alert_on_milestones=alert_on_milestones,
            max_concentration=max_concentration
        )
        self.wallets[address] = config
        self._save_wallets()
        return config

    def remove_wallet(self, address: str) -> bool:
        """Remove a wallet from monitoring."""
        if address in self.wallets:
            del self.wallets[address]
            self._save_wallets()
            return True
        return False

    def update_wallet(self, address: str, **kwargs) -> Optional[WalletConfig]:
        """Update wallet configuration."""
        if address not in self.wallets:
            return None

        config = self.wallets[address]
        for key, value in kwargs.items():
            if hasattr(config, key):
                setattr(config, key, value)

        self._save_wallets()
        return config

    def get_wallet(self, address: str) -> Optional[WalletConfig]:
        """Get wallet configuration."""
        return self.wallets.get(address)

    def list_wallets(self) -> List[WalletConfig]:
        """List all monitored wallets."""
        return list(self.wallets.values())

    def check_wallet(
        self,
        address: str,
        analyzer_fn: Callable[[str], Optional[Dict[str, Any]]],
        sovereignty_fn: Callable[[Dict, float], Optional[SovereigntyData]]
    ) -> List[Alert]:
        """
        Check a single wallet and generate alerts.

        Args:
            address: Wallet address to check
            analyzer_fn: Function to analyze wallet (e.g., analyzer.analyze_wallet)
            sovereignty_fn: Function to calculate sovereignty metrics

        Returns:
            List of alerts for this wallet
        """
        if address not in self.wallets:
            return []

        config = self.wallets[address]
        alerts = []

        # Analyze wallet
        categories = analyzer_fn(address)
        if not categories:
            alerts.append(Alert(
                type=AlertType.SCORE_DROP,
                severity=AlertSeverity.WARNING.value,
                title=f"Cannot analyze wallet: {config.label}",
                message=f"Failed to fetch data for wallet {address[:8]}...{address[-6:]}",
                suggested_action="Check if the wallet address is correct and try again.",
                metadata={"address": address}
            ))
            return alerts

        # Calculate sovereignty if expenses are configured
        sovereignty_data = None
        if config.monthly_fixed_expenses > 0:
            sovereignty_data = sovereignty_fn(categories, config.monthly_fixed_expenses)

        # Get historical data
        history_manager = get_history_manager()
        history = history_manager.get_history(address)

        # Build user preferences for alert engine
        user_prefs = {
            "enabled_types": [],
            "thresholds": {
                "fragile_threshold": config.min_sovereignty_score
            },
            "max_concentration": config.max_concentration
        }

        if config.alert_on_drops:
            user_prefs["enabled_types"].append(AlertType.SCORE_DROP)
        if config.alert_on_milestones:
            user_prefs["enabled_types"].append(AlertType.SCORE_MILESTONE)
        user_prefs["enabled_types"].append(AlertType.CONCENTRATION_WARNING)

        # Generate alerts
        wallet_alerts = self.alert_engine.generate_all_alerts(
            categories=categories,
            sovereignty_data=sovereignty_data,
            history=history,
            user_prefs=user_prefs
        )

        # Add wallet context to alerts
        for alert in wallet_alerts:
            alert.metadata["wallet_address"] = address
            alert.metadata["wallet_label"] = config.label

        # Update last checked
        config.last_checked = datetime.utcnow()
        if sovereignty_data:
            config.last_score = sovereignty_data.sovereignty_ratio
        self._save_wallets()

        return wallet_alerts

    def check_arbitrage_opportunities(self) -> List[ArbitrageOpportunity]:
        """
        Check for gold/silver/BTC arbitrage opportunities.

        Compares spot prices to Algorand DEX prices (MELD Gold$/Silver$, goBTC)
        and identifies when premiums or discounts create trading opportunities.

        Returns:
            List of current arbitrage opportunities
        """
        opportunities = []

        # Check Gold
        try:
            gold_spot = get_gold_price_per_oz()
            gold_implied_per_gram = gold_spot / GRAMS_PER_TROY_OZ if gold_spot else None
            meld_gold = get_meld_gold_price()

            if gold_implied_per_gram and meld_gold:
                premium_pct = ((meld_gold - gold_implied_per_gram) / gold_implied_per_gram) * 100
                premium_usd = meld_gold - gold_implied_per_gram

                if premium_pct >= self.GOLD_PREMIUM_THRESHOLD:
                    signal_strength = min(100, (premium_pct - self.GOLD_PREMIUM_THRESHOLD) * 10)
                    opportunities.append(ArbitrageOpportunity(
                        asset="GOLD",
                        type=ArbitrageType.GOLD_PREMIUM,
                        spot_price=gold_implied_per_gram,
                        algorand_price=meld_gold,
                        premium_percent=round(premium_pct, 2),
                        premium_usd=round(premium_usd, 4),
                        recommendation="SELL GOLD$ on Algorand - premium above threshold. "
                                      "Consider selling GOLD$ and buying physical gold or XAUT.",
                        signal_strength=round(signal_strength, 1)
                    ))
                elif premium_pct <= self.GOLD_DISCOUNT_THRESHOLD:
                    signal_strength = min(100, abs(premium_pct - self.GOLD_DISCOUNT_THRESHOLD) * 20)
                    opportunities.append(ArbitrageOpportunity(
                        asset="GOLD",
                        type=ArbitrageType.GOLD_DISCOUNT,
                        spot_price=gold_implied_per_gram,
                        algorand_price=meld_gold,
                        premium_percent=round(premium_pct, 2),
                        premium_usd=round(premium_usd, 4),
                        recommendation="BUY GOLD$ on Algorand - trading at a discount to spot. "
                                      "Rare opportunity to accumulate gold below market price.",
                        signal_strength=round(signal_strength, 1)
                    ))
        except Exception as e:
            print(f"Error checking gold arbitrage: {e}")

        # Check Silver
        try:
            silver_spot = get_silver_price_per_oz()
            silver_implied_per_gram = silver_spot / GRAMS_PER_TROY_OZ if silver_spot else None
            meld_silver = get_meld_silver_price()

            if silver_implied_per_gram and meld_silver:
                premium_pct = ((meld_silver - silver_implied_per_gram) / silver_implied_per_gram) * 100
                premium_usd = meld_silver - silver_implied_per_gram

                if premium_pct >= self.SILVER_PREMIUM_THRESHOLD:
                    signal_strength = min(100, (premium_pct - self.SILVER_PREMIUM_THRESHOLD) * 5)
                    opportunities.append(ArbitrageOpportunity(
                        asset="SILVER",
                        type=ArbitrageType.SILVER_PREMIUM,
                        spot_price=silver_implied_per_gram,
                        algorand_price=meld_silver,
                        premium_percent=round(premium_pct, 2),
                        premium_usd=round(premium_usd, 4),
                        recommendation="SELL SILVER$ on Algorand - premium is high. "
                                      "Consider taking profits on SILVER$ position.",
                        signal_strength=round(signal_strength, 1)
                    ))
                elif premium_pct <= self.SILVER_DISCOUNT_THRESHOLD:
                    signal_strength = min(100, abs(premium_pct - self.SILVER_DISCOUNT_THRESHOLD) * 10)
                    opportunities.append(ArbitrageOpportunity(
                        asset="SILVER",
                        type=ArbitrageType.SILVER_DISCOUNT,
                        spot_price=silver_implied_per_gram,
                        algorand_price=meld_silver,
                        premium_percent=round(premium_pct, 2),
                        premium_usd=round(premium_usd, 4),
                        recommendation="BUY SILVER$ on Algorand - rare discount opportunity. "
                                      "Accumulate SILVER$ below spot price.",
                        signal_strength=round(signal_strength, 1)
                    ))
        except Exception as e:
            print(f"Error checking silver arbitrage: {e}")

        # Check Bitcoin (goBTC vs spot)
        try:
            btc_spot = get_bitcoin_spot_price()
            gobtc_price = get_gobtc_price()

            if btc_spot and gobtc_price:
                premium_pct = ((gobtc_price - btc_spot) / btc_spot) * 100
                premium_usd = gobtc_price - btc_spot

                if premium_pct >= self.BTC_PREMIUM_THRESHOLD:
                    signal_strength = min(100, (premium_pct - self.BTC_PREMIUM_THRESHOLD) * 20)
                    opportunities.append(ArbitrageOpportunity(
                        asset="BTC",
                        type=ArbitrageType.BTC_PREMIUM,
                        spot_price=btc_spot,
                        algorand_price=gobtc_price,
                        premium_percent=round(premium_pct, 2),
                        premium_usd=round(premium_usd, 2),
                        recommendation="SELL goBTC on Algorand - premium above threshold. "
                                      "Consider selling goBTC and buying spot BTC elsewhere.",
                        signal_strength=round(signal_strength, 1)
                    ))
                elif premium_pct <= self.BTC_DISCOUNT_THRESHOLD:
                    signal_strength = min(100, abs(premium_pct - self.BTC_DISCOUNT_THRESHOLD) * 20)
                    opportunities.append(ArbitrageOpportunity(
                        asset="BTC",
                        type=ArbitrageType.BTC_DISCOUNT,
                        spot_price=btc_spot,
                        algorand_price=gobtc_price,
                        premium_percent=round(premium_pct, 2),
                        premium_usd=round(premium_usd, 2),
                        recommendation="BUY goBTC on Algorand - trading below spot. "
                                      "Rare opportunity to accumulate BTC at a discount.",
                        signal_strength=round(signal_strength, 1)
                    ))
        except Exception as e:
            print(f"Error checking BTC arbitrage: {e}")

        # Sort by signal strength (strongest first)
        opportunities.sort(key=lambda x: x.signal_strength, reverse=True)
        return opportunities

    def get_monitoring_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the monitoring status.

        Returns:
            Dict with wallet count, alerts summary, and arbitrage status
        """
        wallets_needing_check = []
        check_threshold = datetime.utcnow() - timedelta(hours=24)

        for addr, config in self.wallets.items():
            if not config.last_checked or config.last_checked < check_threshold:
                wallets_needing_check.append({
                    "address": addr,
                    "label": config.label,
                    "last_checked": config.last_checked.isoformat() if config.last_checked else None
                })

        arbitrage = self.check_arbitrage_opportunities()

        return {
            "wallet_count": len(self.wallets),
            "wallets_needing_check": len(wallets_needing_check),
            "wallets_needing_check_details": wallets_needing_check,
            "active_arbitrage_opportunities": len(arbitrage),
            "arbitrage_opportunities": [opp.to_dict() for opp in arbitrage]
        }


# Singleton instance
_monitor_instance: Optional[WalletMonitor] = None


def get_wallet_monitor(storage_path: Optional[str] = None) -> WalletMonitor:
    """Get or create the wallet monitor singleton."""
    global _monitor_instance
    if _monitor_instance is None:
        _monitor_instance = WalletMonitor(storage_path)
    return _monitor_instance
