"""
Test fixtures for sovereignty score calculation testing.

This module provides:
- Pre-built wallet compositions for each sovereignty tier
- Expected calculation results for deterministic assertions
- Helper functions for building custom wallet scenarios
- Mock data generators for stress testing

Sovereignty Tiers:
    >= 20: Generationally Sovereign
    >= 6:  Antifragile
    >= 3:  Robust
    >= 1:  Fragile
    <  1:  Vulnerable

Usage:
    from tests.fixtures.sovereignty_fixtures import (
        TIER_WALLETS,
        EXPECTED_RESULTS,
        make_wallet_with_portfolio,
    )
"""

from typing import Dict, List, Any, Optional


# ============================================================================
# Standard Monthly Expense Scenarios
# ============================================================================

EXPENSE_SCENARIOS = {
    "low": 1000,       # $1,000/mo = $12,000/yr (minimal lifestyle)
    "modest": 2500,    # $2,500/mo = $30,000/yr (frugal individual)
    "average": 4000,   # $4,000/mo = $48,000/yr (US median)
    "comfort": 6000,   # $6,000/mo = $72,000/yr (comfortable urban)
    "high": 10000,     # $10,000/mo = $120,000/yr (HCOL area family)
    "luxury": 20000,   # $20,000/mo = $240,000/yr (high-end lifestyle)
}


# ============================================================================
# Standard Price Assumptions
# ============================================================================

STANDARD_PRICES = {
    "ALGO": 0.35,
    "goBTC": 95000.0,
    "WBTC": 95000.0,
    "GOLD$": 85.0,      # per gram
    "SILVER$": 1.0,      # per gram
    "XAUT": 85.0,        # per gram
    "PAXG": 85.0,        # per gram
    "USDC": 1.0,
    "USDT": 1.0,
    "DAI": 1.0,
    "xALGO": 0.38,
    "fALGO": 0.35,
    "fUSDC": 1.0,
    "fUSDT": 1.0,
}


# ============================================================================
# Pre-built Wallet Categories for Each Sovereignty Tier
# ============================================================================

def _make_categories(
    hard_money: Optional[List[Dict]] = None,
    algo: Optional[List[Dict]] = None,
    dollars: Optional[List[Dict]] = None,
    shitcoin: Optional[List[Dict]] = None,
) -> Dict[str, List[Dict[str, Any]]]:
    """Build a categories dict with sensible defaults."""
    return {
        "hard_money": hard_money or [],
        "algo": algo or [],
        "dollars": dollars or [],
        "shitcoin": shitcoin or [],
    }


# --- Vulnerable (< 1 year) ---
WALLET_VULNERABLE = _make_categories(
    algo=[
        {"ticker": "ALGO", "name": "Algorand (NOT PARTICIPATING)", "amount": 5000, "usd_value": 1750},
    ],
    dollars=[
        {"ticker": "USDC", "name": "USDC", "amount": 500, "usd_value": 500},
    ],
)
# Portfolio: $2,250 | At $4,000/mo ($48,000/yr) -> ratio = 0.047 -> Vulnerable

# --- Fragile (1-3 years) ---
WALLET_FRAGILE = _make_categories(
    hard_money=[
        {"ticker": "goBTC", "name": "goBTC", "amount": 0.1, "usd_value": 9500},
    ],
    algo=[
        {"ticker": "ALGO", "name": "Algorand (PARTICIPATING)", "amount": 50000, "usd_value": 17500},
    ],
    dollars=[
        {"ticker": "USDC", "name": "USDC", "amount": 30000, "usd_value": 30000},
    ],
)
# Portfolio: $57,000 | At $4,000/mo ($48,000/yr) -> ratio = 1.19 -> Fragile

# --- Robust (3-6 years) ---
WALLET_ROBUST = _make_categories(
    hard_money=[
        {"ticker": "goBTC", "name": "goBTC", "amount": 0.5, "usd_value": 47500},
        {"ticker": "GOLD$", "name": "Meld Gold", "amount": 500, "usd_value": 42500},
    ],
    algo=[
        {"ticker": "ALGO", "name": "Algorand (PARTICIPATING)", "amount": 100000, "usd_value": 35000},
    ],
    dollars=[
        {"ticker": "USDC", "name": "USDC", "amount": 50000, "usd_value": 50000},
    ],
)
# Portfolio: $175,000 | At $4,000/mo ($48,000/yr) -> ratio = 3.65 -> Robust

# --- Antifragile (6-20 years) ---
WALLET_ANTIFRAGILE = _make_categories(
    hard_money=[
        {"ticker": "goBTC", "name": "goBTC", "amount": 2.0, "usd_value": 190000},
        {"ticker": "GOLD$", "name": "Meld Gold", "amount": 1000, "usd_value": 85000},
        {"ticker": "SILVER$", "name": "Meld Silver", "amount": 5000, "usd_value": 5000},
    ],
    algo=[
        {"ticker": "ALGO", "name": "Algorand (PARTICIPATING)", "amount": 200000, "usd_value": 70000},
        {"ticker": "xALGO", "name": "xAlgo", "amount": 50000, "usd_value": 19000},
    ],
    dollars=[
        {"ticker": "USDC", "name": "USDC", "amount": 100000, "usd_value": 100000},
    ],
)
# Portfolio: $469,000 | At $4,000/mo ($48,000/yr) -> ratio = 9.77 -> Antifragile

# --- Generationally Sovereign (20+ years) ---
WALLET_GENERATIONALLY_SOVEREIGN = _make_categories(
    hard_money=[
        {"ticker": "goBTC", "name": "goBTC", "amount": 5.0, "usd_value": 475000},
        {"ticker": "WBTC", "name": "Wrapped BTC", "amount": 3.0, "usd_value": 285000},
        {"ticker": "GOLD$", "name": "Meld Gold", "amount": 3000, "usd_value": 255000},
        {"ticker": "SILVER$", "name": "Meld Silver", "amount": 10000, "usd_value": 10000},
    ],
    algo=[
        {"ticker": "ALGO", "name": "Algorand (PARTICIPATING)", "amount": 500000, "usd_value": 175000},
    ],
    dollars=[
        {"ticker": "USDC", "name": "USDC", "amount": 200000, "usd_value": 200000},
    ],
    shitcoin=[
        {"ticker": "RNDM", "name": "Random Token", "amount": 100000, "usd_value": 500},
    ],
)
# Portfolio: $1,400,500 | At $4,000/mo ($48,000/yr) -> ratio = 29.18 -> Generationally Sovereign


# Convenience mapping: tier name -> wallet fixture
TIER_WALLETS = {
    "vulnerable": WALLET_VULNERABLE,
    "fragile": WALLET_FRAGILE,
    "robust": WALLET_ROBUST,
    "antifragile": WALLET_ANTIFRAGILE,
    "generationally_sovereign": WALLET_GENERATIONALLY_SOVEREIGN,
}


# ============================================================================
# Expected Calculation Results
# ============================================================================

def _portfolio_total(categories: Dict) -> float:
    """Sum USD values across all categories."""
    total = 0.0
    for cat_assets in categories.values():
        for asset in cat_assets:
            total += asset.get("usd_value", 0)
    return total


def _expected_result(categories: Dict, monthly: float) -> Dict[str, Any]:
    """Compute expected sovereignty metrics for a given wallet + expenses."""
    portfolio = _portfolio_total(categories)
    annual = monthly * 12
    ratio = round(portfolio / annual, 2) if annual > 0 else 0.0

    if ratio >= 20:
        status = "Generationally Sovereign"
    elif ratio >= 6:
        status = "Antifragile"
    elif ratio >= 3:
        status = "Robust"
    elif ratio >= 1:
        status = "Fragile"
    else:
        status = "Vulnerable"

    return {
        "portfolio_usd": portfolio,
        "monthly_fixed_expenses": monthly,
        "annual_fixed_expenses": annual,
        "sovereignty_ratio": ratio,
        "sovereignty_status": status,
        "years_of_runway": ratio,
    }


# Expected results at $4,000/mo expenses
EXPECTED_RESULTS = {
    tier_name: _expected_result(wallet, 4000)
    for tier_name, wallet in TIER_WALLETS.items()
}


# ============================================================================
# Parametrized Test Data: Boundary Cases
# ============================================================================

# Exact boundary values at $4,000/mo ($48,000/yr annual expenses)
# Note: The analyzer rounds the ratio to 2 decimal places, but the status check
# uses the rounded value. 47999/48000 = 1.00 rounded, but the actual value is
# 0.99979... so depending on implementation the status may use pre-round or
# post-round value. These cases match the actual analyzer behavior.
BOUNDARY_CASES = [
    # (portfolio_usd, monthly_expenses, expected_ratio, expected_status)
    (0, 4000, 0.0, "Vulnerable"),
    (47999, 4000, 1.0, "Vulnerable"),      # Rounds to 1.0 but actual < 1, status depends on impl
    (48000, 4000, 1.0, "Fragile"),         # Exactly 1 year
    (48001, 4000, 1.0, "Fragile"),         # Just over 1 year
    (143999, 4000, 3.0, "Fragile"),        # Rounds to 3.0 but actual < 3
    (144000, 4000, 3.0, "Robust"),         # Exactly 3 years
    (144001, 4000, 3.0, "Robust"),         # Just over 3 years
    (288000, 4000, 6.0, "Antifragile"),    # Exactly 6 years
    (960000, 4000, 20.0, "Generationally Sovereign"),  # Exactly 20 years
]


# ============================================================================
# Wallet Composition Variants
# ============================================================================

# All-hard-money wallet (Bitcoin only)
WALLET_BITCOIN_ONLY = _make_categories(
    hard_money=[
        {"ticker": "goBTC", "name": "goBTC", "amount": 1.0, "usd_value": 95000},
    ],
)

# All-stablecoins wallet
WALLET_STABLECOINS_ONLY = _make_categories(
    dollars=[
        {"ticker": "USDC", "name": "USDC", "amount": 50000, "usd_value": 50000},
        {"ticker": "USDt", "name": "Tether", "amount": 25000, "usd_value": 25000},
        {"ticker": "DAI", "name": "DAI", "amount": 10000, "usd_value": 10000},
    ],
)

# All-ALGO wallet
WALLET_ALGO_ONLY = _make_categories(
    algo=[
        {"ticker": "ALGO", "name": "Algorand (PARTICIPATING)", "amount": 500000, "usd_value": 175000},
        {"ticker": "xALGO", "name": "xAlgo", "amount": 100000, "usd_value": 38000},
    ],
)

# Pure gold wallet
WALLET_GOLD_ONLY = _make_categories(
    hard_money=[
        {"ticker": "GOLD$", "name": "Meld Gold", "amount": 1000, "usd_value": 85000},
        {"ticker": "XAUT", "name": "Tether Gold", "amount": 200, "usd_value": 17000},
    ],
)

# All shitcoins (no real value preservation)
WALLET_SHITCOINS_ONLY = _make_categories(
    shitcoin=[
        {"ticker": "MEME", "name": "Meme Coin", "amount": 1000000, "usd_value": 500},
        {"ticker": "RNDM", "name": "Random", "amount": 100000, "usd_value": 100},
        {"ticker": "FAKE", "name": "Fake Token", "amount": 5000000, "usd_value": 250},
    ],
)

# Empty wallet
WALLET_EMPTY = _make_categories()

# Mixed with LP decomposed assets (realistic DeFi user)
WALLET_DEFI_USER = _make_categories(
    hard_money=[
        {"ticker": "goBTC", "name": "goBTC", "amount": 0.05, "usd_value": 4750},
    ],
    algo=[
        {"ticker": "ALGO", "name": "Algorand (PARTICIPATING)", "amount": 30000, "usd_value": 10500},
        {"ticker": "xALGO", "name": "xAlgo", "amount": 20000, "usd_value": 7600},
        {"ticker": "fALGO", "name": "Folks ALGO", "amount": 10000, "usd_value": 3500},
    ],
    dollars=[
        {"ticker": "USDC", "name": "USDC", "amount": 15000, "usd_value": 15000},
        {"ticker": "fUSDC", "name": "Folks USDC", "amount": 5000, "usd_value": 5000},
    ],
    shitcoin=[
        {"ticker": "FOLKS", "name": "Folks Finance", "amount": 5000, "usd_value": 250},
    ],
)


# ============================================================================
# Helper Functions for Building Custom Scenarios
# ============================================================================

def make_wallet_with_portfolio(
    target_portfolio_usd: float,
    allocation: Optional[Dict[str, float]] = None,
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Generate a wallet with a target USD portfolio value and optional allocation.

    Args:
        target_portfolio_usd: Total portfolio value in USD
        allocation: Percentage allocation per category, e.g.,
            {"hard_money": 0.6, "algo": 0.2, "dollars": 0.15, "shitcoin": 0.05}
            If not provided, defaults to 100% hard_money.

    Returns:
        Categories dict with computed asset values.
    """
    if allocation is None:
        allocation = {"hard_money": 1.0, "algo": 0.0, "dollars": 0.0, "shitcoin": 0.0}

    # Normalize allocation to 100%
    total_alloc = sum(allocation.values())
    if total_alloc > 0:
        allocation = {k: v / total_alloc for k, v in allocation.items()}

    categories = {"hard_money": [], "algo": [], "dollars": [], "shitcoin": []}

    # Default tickers per category
    default_tickers = {
        "hard_money": ("goBTC", "goBTC", 95000.0),  # ticker, name, price
        "algo": ("ALGO", "Algorand", 0.35),
        "dollars": ("USDC", "USDC", 1.0),
        "shitcoin": ("RNDM", "Random Token", 0.01),
    }

    for cat, pct in allocation.items():
        if pct <= 0:
            continue
        value = target_portfolio_usd * pct
        ticker, name, price = default_tickers[cat]
        amount = value / price if price > 0 else 0
        categories[cat].append({
            "ticker": ticker,
            "name": name,
            "amount": round(amount, 8),
            "usd_value": round(value, 2),
        })

    return categories


def make_sovereignty_result(
    portfolio_usd: float,
    monthly_expenses: float,
    algo_price: float = 0.35,
) -> Dict[str, Any]:
    """
    Compute the expected SovereigntyData fields for a given scenario.

    Returns a dict matching the SovereigntyData model fields.
    """
    annual = monthly_expenses * 12
    ratio = round(portfolio_usd / annual, 2) if annual > 0 else 0.0

    if ratio >= 20:
        status = "Generationally Sovereign"
    elif ratio >= 6:
        status = "Antifragile"
    elif ratio >= 3:
        status = "Robust"
    elif ratio >= 1:
        status = "Fragile"
    else:
        status = "Vulnerable"

    return {
        "monthly_fixed_expenses": monthly_expenses,
        "annual_fixed_expenses": annual,
        "algo_price": algo_price,
        "portfolio_usd": portfolio_usd,
        "sovereignty_ratio": ratio,
        "sovereignty_status": status,
        "years_of_runway": ratio,
    }


def calculate_portfolio_total(categories: Dict[str, List[Dict]]) -> float:
    """Sum all usd_value fields across all categories."""
    return _portfolio_total(categories)


# ============================================================================
# Algorand Account Data Builders (for analyze_wallet mocking)
# ============================================================================

def make_account_data(
    algo_microalgos: int = 0,
    participating: bool = False,
    assets: Optional[List[Dict]] = None,
) -> Dict[str, Any]:
    """
    Build a mock Algorand account data response.

    Args:
        algo_microalgos: ALGO balance in microAlgos (1 ALGO = 1,000,000 microAlgos)
        participating: Whether the account is participating in consensus
        assets: List of ASA holdings, each with 'asset-id' and 'amount'

    Returns:
        Dict matching the Algorand node account response format
    """
    data: Dict[str, Any] = {
        "amount": algo_microalgos,
        "status": "Online" if participating else "Offline",
        "assets": assets or [],
    }

    if participating:
        data["participation"] = {
            "vote-first-valid": 1000,
            "vote-last-valid": 1000000,
        }

    return data


def make_asset_details(
    name: str,
    ticker: str,
    decimals: int = 6,
    creator: str = "CREATOR_ADDR",
) -> Dict[str, Any]:
    """
    Build a mock Algorand asset details response.

    Args:
        name: Full asset name
        ticker: Unit name / ticker
        decimals: Number of decimal places
        creator: Creator address

    Returns:
        Dict matching the Algorand node asset details response
    """
    return {
        "params": {
            "name": name,
            "unit-name": ticker,
            "decimals": decimals,
            "creator": creator,
        }
    }


# ============================================================================
# Known Asset Details Registry
# ============================================================================

KNOWN_ASSET_DETAILS = {
    386192725: make_asset_details("goBTC", "goBTC", 8),
    1058926737: make_asset_details("Wrapped BTC", "WBTC", 8),
    246516580: make_asset_details("Meld Gold", "GOLD$", 6),
    246519683: make_asset_details("Meld Silver", "SILVER$", 6),
    31566704: make_asset_details("USDC", "USDC", 6),
    312769: make_asset_details("Tether USDt", "USDT", 6),
    1134696561: make_asset_details("xAlgo", "xALGO", 6),
}
