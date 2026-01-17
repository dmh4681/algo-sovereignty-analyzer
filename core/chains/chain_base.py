"""
Base class and types for chain abstraction.

This module defines the interface that all chain analyzers must implement,
enabling multi-chain support for sovereignty analysis.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel


class ChainType(str, Enum):
    """Supported blockchain networks."""
    ALGORAND = "algorand"
    BITCOIN = "bitcoin"
    LIGHTNING = "lightning"


@dataclass
class ChainConfig:
    """Configuration for a blockchain connection."""
    chain_type: ChainType
    node_url: str
    auth_token: Optional[str] = None
    network: str = "mainnet"  # mainnet, testnet
    timeout_seconds: int = 30


class ChainAsset(BaseModel):
    """Represents an asset on any chain."""
    chain: ChainType
    asset_id: Optional[str] = None  # Chain-specific ID (ASA ID, UTXO, etc.)
    ticker: str
    name: str
    amount: float
    decimals: int = 0
    raw_amount: int = 0  # Amount in smallest unit
    metadata: Dict[str, Any] = {}


class ChainBalance(BaseModel):
    """Balance information for a chain account."""
    chain: ChainType
    address: str
    native_balance: float  # ALGO, BTC, etc.
    native_balance_raw: int  # In smallest unit (microalgos, satoshis)
    assets: List[ChainAsset] = []
    participation_status: Optional[str] = None  # Chain-specific status
    metadata: Dict[str, Any] = {}


class ChainAnalyzer(ABC):
    """
    Abstract base class for chain-specific analyzers.

    Each blockchain must implement this interface to be supported
    by the sovereignty analyzer.
    """

    def __init__(self, config: ChainConfig):
        self.config = config
        self.chain_type = config.chain_type

    @abstractmethod
    def validate_address(self, address: str) -> bool:
        """
        Validate if the given address is valid for this chain.

        Args:
            address: The address to validate

        Returns:
            True if valid, False otherwise
        """
        pass

    @abstractmethod
    def get_balance(self, address: str) -> ChainBalance:
        """
        Get the balance and assets for an address.

        Args:
            address: The address to query

        Returns:
            ChainBalance with native balance and all assets
        """
        pass

    @abstractmethod
    def get_asset_details(self, asset_id: str) -> Optional[ChainAsset]:
        """
        Get details for a specific asset.

        Args:
            asset_id: Chain-specific asset identifier

        Returns:
            ChainAsset with details, or None if not found
        """
        pass

    @abstractmethod
    def get_native_token_ticker(self) -> str:
        """
        Get the ticker symbol for the chain's native token.

        Returns:
            Ticker symbol (e.g., "ALGO", "BTC")
        """
        pass

    @abstractmethod
    def get_native_token_decimals(self) -> int:
        """
        Get the number of decimals for the native token.

        Returns:
            Number of decimal places (e.g., 6 for ALGO, 8 for BTC)
        """
        pass

    def raw_to_decimal(self, raw_amount: int, decimals: Optional[int] = None) -> float:
        """
        Convert raw amount to decimal representation.

        Args:
            raw_amount: Amount in smallest unit
            decimals: Number of decimal places (uses native if not specified)

        Returns:
            Decimal representation
        """
        if decimals is None:
            decimals = self.get_native_token_decimals()
        return raw_amount / (10 ** decimals)

    def decimal_to_raw(self, amount: float, decimals: Optional[int] = None) -> int:
        """
        Convert decimal amount to raw representation.

        Args:
            amount: Decimal amount
            decimals: Number of decimal places (uses native if not specified)

        Returns:
            Raw amount in smallest unit
        """
        if decimals is None:
            decimals = self.get_native_token_decimals()
        return int(amount * (10 ** decimals))


# Address validation patterns by chain
ADDRESS_PATTERNS: Dict[ChainType, Dict[str, Any]] = {
    ChainType.ALGORAND: {
        "length": 58,
        "charset": "ABCDEFGHIJKLMNOPQRSTUVWXYZ234567",
        "prefix": None,
    },
    ChainType.BITCOIN: {
        "legacy_prefix": ["1", "3"],
        "segwit_prefix": ["bc1"],
        "testnet_prefix": ["m", "n", "2", "tb1"],
        "min_length": 25,
        "max_length": 90,
    },
    ChainType.LIGHTNING: {
        "node_pubkey_length": 66,
        "invoice_prefix": "lnbc",
    },
}


def get_chain_analyzer(config: ChainConfig) -> ChainAnalyzer:
    """
    Factory function to get the appropriate chain analyzer.

    Args:
        config: Chain configuration

    Returns:
        ChainAnalyzer instance for the specified chain

    Raises:
        ValueError: If chain type is not supported
    """
    from .algorand_chain import AlgorandChainAnalyzer

    analyzers = {
        ChainType.ALGORAND: AlgorandChainAnalyzer,
        # ChainType.BITCOIN: BitcoinChainAnalyzer,  # Future
        # ChainType.LIGHTNING: LightningChainAnalyzer,  # Future
    }

    analyzer_class = analyzers.get(config.chain_type)
    if analyzer_class is None:
        raise ValueError(f"Unsupported chain type: {config.chain_type}")

    return analyzer_class(config)
