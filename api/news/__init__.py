"""
News Curator Module
Analyzes precious metals news through a sovereignty lens using Claude AI
"""

from .aggregator import NewsAggregator
from .curator import MetalsCurator

__all__ = ['NewsAggregator', 'MetalsCurator']
