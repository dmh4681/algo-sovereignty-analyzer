"""
Multi-chain support for Sovereignty Analyzer.

This module provides chain abstraction to support multiple blockchains:
- Algorand (current)
- Bitcoin (planned)
- Lightning Network (planned)
"""

from .chain_base import ChainAnalyzer, ChainType, ChainConfig
from .algorand_chain import AlgorandChainAnalyzer

__all__ = [
    'ChainAnalyzer',
    'ChainType',
    'ChainConfig',
    'AlgorandChainAnalyzer',
]
