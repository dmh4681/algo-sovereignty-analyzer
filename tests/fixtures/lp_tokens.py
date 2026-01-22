"""
Fixtures for LP Token parsing tests.

This module provides mock API responses and test data for LP token tests,
covering various DEX formats (Tinyman, Pact, Humble), malformed responses,
and edge cases.
"""


# ============================================================================
# Valid LP Token Responses
# ============================================================================

TINYMAN_V2_ALGO_USDC = {
    "params": {
        "name": "TinymanPool2.0 ALGO-USDC",
        "unit-name": "TMPOOL2",
        "decimals": 6,
        "creator": "POOL_ADDRESS_ALGO_USDC",
        "total": 1000000000000
    }
}

TINYMAN_V2_XALGO_ALGO = {
    "params": {
        "name": "TinymanPool2.0 XALGO-ALGO",
        "unit-name": "TMPOOL2",
        "decimals": 6,
        "creator": "POOL_ADDRESS_XALGO_ALGO",
        "total": 500000000000
    }
}

TINYMAN_V1_BTC_ALGO = {
    "params": {
        "name": "TinymanPool goBTC-ALGO",
        "unit-name": "TM1POOL",
        "decimals": 6,
        "creator": "POOL_ADDRESS_BTC_ALGO",
        "total": 10000000000
    }
}

PACT_LP_ALGO_USDC = {
    "params": {
        "name": "PACT ALGO/USDC LP",
        "unit-name": "PACT LP",
        "decimals": 6,
        "creator": "PACT_POOL_ADDRESS",
        "total": 2000000000000
    }
}

HUMBLE_LP_GOLD_ALGO = {
    "params": {
        "name": "GOLD$-ALGO Pool",
        "unit-name": "hLP",
        "decimals": 6,
        "creator": "HUMBLE_POOL_ADDRESS",
        "total": 100000000000
    }
}

FOLKS_LP_FUSDC_FALGO = {
    "params": {
        "name": "fUSDC / fALGO",
        "unit-name": "FLP",
        "decimals": 6,
        "creator": "FOLKS_POOL_ADDRESS",
        "total": 500000000000
    }
}


# ============================================================================
# Pool State Responses (from Tinyman SDK)
# ============================================================================

POOL_STATE_ALGO_USDC = {
    "total_supply": 1000000.0,
    "reserve1": 5000000.0,  # 5M ALGO
    "reserve2": 1500000.0   # 1.5M USDC
}

POOL_STATE_XALGO_ALGO = {
    "total_supply": 500000.0,
    "reserve1": 1000000.0,  # 1M xALGO
    "reserve2": 1000000.0   # 1M ALGO
}

POOL_STATE_ZERO_SUPPLY = {
    "total_supply": 0.0,
    "reserve1": 0.0,
    "reserve2": 0.0
}

POOL_STATE_EMPTY_RESERVES = {
    "total_supply": 1000000.0,
    "reserve1": 0.0,
    "reserve2": 0.0
}


# ============================================================================
# Account Responses (for pool asset discovery)
# ============================================================================

POOL_ACCOUNT_TWO_ASSETS = {
    "address": "POOL_ADDRESS_ALGO_USDC",
    "amount": 1000000,  # ALGO
    "assets": [
        {"asset-id": 31566704, "amount": 1500000000000},  # USDC
        {"asset-id": 12345678, "amount": 5000000000000}   # Other token
    ]
}

POOL_ACCOUNT_ONE_ASSET = {
    "address": "POOL_ADDRESS_ALGO_ONLY",
    "amount": 5000000000,  # ALGO
    "assets": [
        {"asset-id": 31566704, "amount": 1500000000000}  # USDC only
    ]
}

POOL_ACCOUNT_NO_ASSETS = {
    "address": "POOL_ADDRESS_EMPTY",
    "amount": 0,
    "assets": []
}

POOL_ACCOUNT_ZERO_BALANCE_ASSETS = {
    "address": "POOL_ADDRESS_ZERO",
    "amount": 0,
    "assets": [
        {"asset-id": 31566704, "amount": 0},
        {"asset-id": 12345678, "amount": 0}
    ]
}


# ============================================================================
# Malformed / Edge Case Responses
# ============================================================================

MALFORMED_NO_PARAMS = {
    "asset-index": 12345
    # Missing "params" key entirely
}

MALFORMED_EMPTY_PARAMS = {
    "params": {}
}

MALFORMED_NO_NAME = {
    "params": {
        "unit-name": "TMPOOL2",
        "decimals": 6,
        "creator": "SOME_ADDRESS"
    }
}

MALFORMED_NO_UNIT_NAME = {
    "params": {
        "name": "TinymanPool2.0 ALGO-USDC",
        "decimals": 6,
        "creator": "SOME_ADDRESS"
    }
}

MALFORMED_NO_CREATOR = {
    "params": {
        "name": "TinymanPool2.0 ALGO-USDC",
        "unit-name": "TMPOOL2",
        "decimals": 6
    }
}

MALFORMED_INVALID_NAME_FORMAT = {
    "params": {
        "name": "TinymanPool2.0",  # Missing pair info
        "unit-name": "TMPOOL2",
        "decimals": 6,
        "creator": "POOL_ADDRESS"
    }
}

MALFORMED_SINGLE_ASSET_NAME = {
    "params": {
        "name": "TinymanPool2.0 ALGO",  # Only one asset
        "unit-name": "TMPOOL2",
        "decimals": 6,
        "creator": "POOL_ADDRESS"
    }
}


# ============================================================================
# Non-LP Token Responses (for negative testing)
# ============================================================================

REGULAR_TOKEN_USDC = {
    "params": {
        "name": "USDC",
        "unit-name": "USDC",
        "decimals": 6,
        "creator": "CIRCLE_ADDRESS",
        "total": 1000000000000000
    }
}

REGULAR_TOKEN_ALGO = {
    "params": {
        "name": "Algorand",
        "unit-name": "ALGO",
        "decimals": 6,
        "creator": "ALGORAND_FOUNDATION",
        "total": 10000000000000000
    }
}

NFT_TOKEN = {
    "params": {
        "name": "CoolPunk #1234",
        "unit-name": "PUNK",
        "decimals": 0,
        "creator": "NFT_CREATOR",
        "total": 1
    }
}


# ============================================================================
# LP Token Detection Test Cases
# ============================================================================

LP_TOKEN_DETECTION_POSITIVE = [
    # (ticker, name, description)
    ("TMPOOL2", "TinymanPool2.0 ALGO-USDC", "Tinyman V2 standard"),
    ("TMPOOL", "TinymanPool ALGO-USDC", "Tinyman V1 standard"),
    ("TM1POOL", "TinymanPool1.1 BTC-ALGO", "Tinyman V1.1"),
    ("TM1.1POOL", "TinymanPool BTC-ALGO", "Tinyman version variant"),
    ("PACT LP", "PACT ALGO/USDC LP", "Pact LP token"),
    ("PLP", "Pact Liquidity Pool", "Pact PLP variant"),
    ("PACT-ALGO-USDC", "Pact Pool", "Pact with pair in ticker"),
    ("hLP", "GOLD$-ALGO Pool", "Humble LP token"),
    ("ALGO-USDC-LP", "Liquidity Pool", "Generic LP suffix"),
    ("FLP", "fUSDC / fALGO", "Folks Finance LP"),
    ("LP", "xALGO / ALGO", "Generic with slash pair"),
]

LP_TOKEN_DETECTION_NEGATIVE = [
    # (ticker, name, description)
    ("USDC", "USDC", "Stablecoin"),
    ("ALGO", "Algorand", "Native token"),
    ("goBTC", "goBitcoin", "Wrapped Bitcoin"),
    ("GOLD$", "Meld Gold", "Gold token"),
    ("NFD", "NFDomain", "NFT domain"),
    ("FOLKS", "Folks Finance", "Governance token"),
    ("YLDY", "Yieldly", "DeFi token"),
]


# ============================================================================
# Price Function Mock Data
# ============================================================================

MOCK_PRICES = {
    "ALGO": 0.35,
    "USDC": 1.00,
    "XALGO": 0.38,
    "FUSDC": 1.00,
    "FALGO": 0.35,
    "goBTC": 45000.00,
    "GOLD$": 2000.00,
    "SILVER$": 25.00,
}


def mock_get_price(ticker: str, asset_id: int = None) -> float:
    """Mock price function for testing."""
    return MOCK_PRICES.get(ticker.upper(), 0.0)


def mock_get_price_partial(ticker: str, asset_id: int = None) -> float:
    """Mock price function that only knows some assets."""
    partial_prices = {"ALGO": 0.35, "USDC": 1.00}
    return partial_prices.get(ticker.upper(), 0.0)


def mock_get_price_none(ticker: str, asset_id: int = None) -> float:
    """Mock price function that returns 0 for all assets."""
    return 0.0


# ============================================================================
# Classification Function Mock Data
# ============================================================================

CATEGORY_MAP = {
    "ALGO": "algo",
    "XALGO": "algo",
    "FALGO": "algo",
    "USDC": "dollars",
    "FUSDC": "dollars",
    "goBTC": "hard_money",
    "GOLD$": "hard_money",
    "SILVER$": "hard_money",
}


def mock_classify_fn(asset_id: int, name: str, ticker: str) -> str:
    """Mock classification function for testing."""
    return CATEGORY_MAP.get(ticker.upper(), "shitcoin")
