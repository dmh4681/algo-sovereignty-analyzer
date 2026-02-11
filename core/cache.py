"""
Comprehensive Caching Layer for Algorand Sovereignty Analyzer
=============================================================

This module provides a flexible caching system with TTL support, designed to reduce
external API calls and improve response times. The cache is implemented as an
in-memory store with optional Redis backend support for production deployments.

Features:
    - Configurable TTL per data type (prices, analysis, network stats)
    - Per-wallet cache keys for analysis results
    - Cache statistics and monitoring endpoints
    - Automatic cache invalidation strategies
    - Thread-safe operations
    - Redis-ready design (can be upgraded without code changes)

Cache Categories and Default TTLs:
    - PRICE_LIVE: 60 seconds (real-time prices from external APIs)
    - PRICE_HISTORICAL: 3600 seconds (historical price data)
    - ANALYSIS: 900 seconds (15 min wallet analysis results)
    - NETWORK_STATS: 60 seconds (Algorand network statistics)
    - CLASSIFICATION: 3600 seconds (asset classification lookups)

Usage:
    from core.cache import cache, CacheConfig

    # Get/set with automatic TTL
    price = cache.get("price:btc")
    if price is None:
        price = fetch_btc_price()
        cache.set("price:btc", price, ttl=CacheConfig.PRICE_LIVE_TTL)

    # Wallet-specific caching
    analysis = cache.get_analysis("ALGO_ADDRESS")
    if analysis is None:
        analysis = perform_analysis("ALGO_ADDRESS")
        cache.set_analysis("ALGO_ADDRESS", analysis)

    # Cache statistics
    stats = cache.get_stats()
    print(f"Hit rate: {stats['hit_rate']:.2%}")

Environment Variables:
    CACHE_BACKEND: "memory" (default) or "redis"
    REDIS_URL: Redis connection URL (if using Redis backend)
    CACHE_MAX_SIZE: Maximum number of entries for memory cache (default: 10000)
    CACHE_PRICE_TTL: Override default price TTL in seconds
    CACHE_ANALYSIS_TTL: Override default analysis TTL in seconds

See Also:
    - api/routes.py: Uses cache for API response caching
    - core/pricing.py: Uses cache for price data
    - docs/API-REFERENCE.md: Cache configuration documentation
"""

import os
import time
import threading
import hashlib
import logging
from typing import Any, Dict, Optional, TypeVar, Generic, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from collections import OrderedDict

# Configure module logger
logger = logging.getLogger("core.cache")

T = TypeVar('T')


class CacheCategory(Enum):
    """Cache categories with semantic meaning for different data types."""
    PRICE_LIVE = "price_live"           # Real-time prices (short TTL)
    PRICE_HISTORICAL = "price_hist"      # Historical prices (longer TTL)
    ANALYSIS = "analysis"                # Wallet analysis results
    NETWORK_STATS = "network"            # Network statistics
    CLASSIFICATION = "classification"    # Asset classifications
    ARBITRAGE = "arbitrage"              # Premium/arbitrage calculations
    GENERAL = "general"                  # General purpose cache


@dataclass
class CacheConfig:
    """
    Cache configuration with configurable TTL values.

    TTL values can be overridden via environment variables for production tuning.
    """
    # Default TTL values in seconds
    PRICE_LIVE_TTL: int = int(os.environ.get("CACHE_PRICE_TTL", 60))
    PRICE_HISTORICAL_TTL: int = int(os.environ.get("CACHE_HISTORICAL_TTL", 3600))
    ANALYSIS_TTL: int = int(os.environ.get("CACHE_ANALYSIS_TTL", 900))  # 15 minutes
    NETWORK_STATS_TTL: int = int(os.environ.get("CACHE_NETWORK_TTL", 60))
    CLASSIFICATION_TTL: int = int(os.environ.get("CACHE_CLASSIFICATION_TTL", 3600))
    ARBITRAGE_TTL: int = int(os.environ.get("CACHE_ARBITRAGE_TTL", 120))  # 2 minutes

    # Memory cache settings
    MAX_SIZE: int = int(os.environ.get("CACHE_MAX_SIZE", 10000))
    CLEANUP_INTERVAL: int = 300  # Run cleanup every 5 minutes

    # Category-specific TTL mapping
    CATEGORY_TTL: Dict[CacheCategory, int] = field(default_factory=lambda: {
        CacheCategory.PRICE_LIVE: 60,
        CacheCategory.PRICE_HISTORICAL: 3600,
        CacheCategory.ANALYSIS: 900,
        CacheCategory.NETWORK_STATS: 60,
        CacheCategory.CLASSIFICATION: 3600,
        CacheCategory.ARBITRAGE: 120,
        CacheCategory.GENERAL: 300,
    })


@dataclass
class CacheEntry:
    """A single cache entry with value, expiration, and metadata."""
    value: Any
    expires_at: float  # Unix timestamp
    created_at: float
    category: CacheCategory
    hits: int = 0

    @property
    def is_expired(self) -> bool:
        return time.time() > self.expires_at

    @property
    def ttl_remaining(self) -> float:
        """Remaining TTL in seconds."""
        return max(0, self.expires_at - time.time())


@dataclass
class CacheStats:
    """Cache statistics for monitoring and debugging."""
    hits: int = 0
    misses: int = 0
    sets: int = 0
    evictions: int = 0
    expirations: int = 0
    invalidations: int = 0

    @property
    def total_requests(self) -> int:
        return self.hits + self.misses

    @property
    def hit_rate(self) -> float:
        if self.total_requests == 0:
            return 0.0
        return self.hits / self.total_requests

    def to_dict(self) -> Dict[str, Any]:
        return {
            "hits": self.hits,
            "misses": self.misses,
            "sets": self.sets,
            "evictions": self.evictions,
            "expirations": self.expirations,
            "invalidations": self.invalidations,
            "total_requests": self.total_requests,
            "hit_rate": round(self.hit_rate, 4),
            "hit_rate_percent": f"{self.hit_rate:.2%}"
        }


class MemoryCache:
    """
    Thread-safe in-memory cache with TTL support and LRU eviction.

    This is the default cache backend. It provides fast access for single-instance
    deployments. For multi-instance deployments, upgrade to Redis.

    Features:
        - Per-key TTL with automatic expiration
        - LRU eviction when max size is reached
        - Background cleanup of expired entries
        - Comprehensive statistics tracking
        - Category-based TTL defaults
    """

    def __init__(self, config: Optional[CacheConfig] = None):
        self.config = config or CacheConfig()
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = threading.RLock()
        self._stats = CacheStats()
        self._last_cleanup = time.time()

        # Per-category statistics
        self._category_stats: Dict[CacheCategory, CacheStats] = {
            cat: CacheStats() for cat in CacheCategory
        }

    def _make_key(self, key: str, category: CacheCategory) -> str:
        """Create a namespaced cache key."""
        return f"{category.value}:{key}"

    def _cleanup_expired(self) -> int:
        """Remove expired entries. Returns count of removed entries."""
        removed = 0
        with self._lock:
            # Only run cleanup periodically
            if time.time() - self._last_cleanup < self.config.CLEANUP_INTERVAL:
                return 0

            self._last_cleanup = time.time()
            expired_keys = [k for k, v in self._cache.items() if v.is_expired]

            for key in expired_keys:
                entry = self._cache.pop(key, None)
                if entry:
                    self._stats.expirations += 1
                    self._category_stats[entry.category].expirations += 1
                    removed += 1

        if removed > 0:
            logger.debug(f"Cache cleanup removed {removed} expired entries")

        return removed

    def _evict_lru(self, count: int = 1) -> int:
        """Evict least recently used entries. Returns count evicted."""
        evicted = 0
        with self._lock:
            while evicted < count and self._cache:
                key, entry = self._cache.popitem(last=False)
                self._stats.evictions += 1
                self._category_stats[entry.category].evictions += 1
                evicted += 1

        return evicted

    def get(
        self,
        key: str,
        category: CacheCategory = CacheCategory.GENERAL,
        default: Optional[T] = None
    ) -> Optional[T]:
        """
        Get a value from the cache.

        Args:
            key: Cache key
            category: Cache category for namespacing
            default: Value to return if key not found or expired

        Returns:
            Cached value or default
        """
        full_key = self._make_key(key, category)

        with self._lock:
            entry = self._cache.get(full_key)

            if entry is None:
                self._stats.misses += 1
                self._category_stats[category].misses += 1
                return default

            if entry.is_expired:
                del self._cache[full_key]
                self._stats.misses += 1
                self._stats.expirations += 1
                self._category_stats[category].misses += 1
                self._category_stats[category].expirations += 1
                return default

            # Move to end (most recently used)
            self._cache.move_to_end(full_key)
            entry.hits += 1
            self._stats.hits += 1
            self._category_stats[category].hits += 1

            return entry.value

    def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        category: CacheCategory = CacheCategory.GENERAL
    ) -> None:
        """
        Set a value in the cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (uses category default if None)
            category: Cache category for namespacing and TTL defaults
        """
        full_key = self._make_key(key, category)

        # Use category default TTL if not specified
        if ttl is None:
            ttl = self.config.CATEGORY_TTL.get(category, 300)

        now = time.time()
        entry = CacheEntry(
            value=value,
            expires_at=now + ttl,
            created_at=now,
            category=category
        )

        with self._lock:
            # Check if we need to evict
            if len(self._cache) >= self.config.MAX_SIZE and full_key not in self._cache:
                self._evict_lru(max(1, self.config.MAX_SIZE // 10))

            self._cache[full_key] = entry
            self._cache.move_to_end(full_key)
            self._stats.sets += 1
            self._category_stats[category].sets += 1

        # Periodic cleanup
        self._cleanup_expired()

    def delete(self, key: str, category: CacheCategory = CacheCategory.GENERAL) -> bool:
        """
        Delete a key from the cache.

        Returns:
            True if key was deleted, False if not found
        """
        full_key = self._make_key(key, category)

        with self._lock:
            if full_key in self._cache:
                entry = self._cache.pop(full_key)
                self._stats.invalidations += 1
                self._category_stats[entry.category].invalidations += 1
                return True
            return False

    def invalidate_pattern(self, pattern: str) -> int:
        """
        Invalidate all keys matching a pattern (prefix match).

        Args:
            pattern: Key prefix to match (e.g., "analysis:" to clear all analysis cache)

        Returns:
            Number of keys invalidated
        """
        count = 0
        with self._lock:
            keys_to_delete = [k for k in self._cache.keys() if k.startswith(pattern)]
            for key in keys_to_delete:
                entry = self._cache.pop(key)
                self._stats.invalidations += 1
                self._category_stats[entry.category].invalidations += 1
                count += 1

        if count > 0:
            logger.info(f"Invalidated {count} cache entries matching pattern '{pattern}'")

        return count

    def invalidate_category(self, category: CacheCategory) -> int:
        """
        Invalidate all entries in a category.

        Args:
            category: Category to invalidate

        Returns:
            Number of keys invalidated
        """
        return self.invalidate_pattern(f"{category.value}:")

    def clear(self) -> int:
        """
        Clear all cache entries.

        Returns:
            Number of entries cleared
        """
        with self._lock:
            count = len(self._cache)
            self._cache.clear()
            self._stats.invalidations += count
            logger.info(f"Cleared all {count} cache entries")
            return count

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self._lock:
            category_stats = {
                cat.value: stats.to_dict()
                for cat, stats in self._category_stats.items()
            }

            return {
                "overall": self._stats.to_dict(),
                "by_category": category_stats,
                "size": len(self._cache),
                "max_size": self.config.MAX_SIZE,
                "utilization": len(self._cache) / self.config.MAX_SIZE if self.config.MAX_SIZE > 0 else 0
            }

    def get_entry_info(self, key: str, category: CacheCategory = CacheCategory.GENERAL) -> Optional[Dict[str, Any]]:
        """Get detailed info about a cache entry (for debugging)."""
        full_key = self._make_key(key, category)

        with self._lock:
            entry = self._cache.get(full_key)
            if entry is None:
                return None

            return {
                "key": full_key,
                "category": entry.category.value,
                "created_at": datetime.fromtimestamp(entry.created_at).isoformat(),
                "expires_at": datetime.fromtimestamp(entry.expires_at).isoformat(),
                "ttl_remaining": round(entry.ttl_remaining, 1),
                "is_expired": entry.is_expired,
                "hits": entry.hits
            }


class SovereigntyCache:
    """
    High-level caching interface for the Sovereignty Analyzer.

    This class provides convenient methods for caching different types of data
    used in the application, with appropriate TTLs and key generation.

    Features:
        - Wallet-specific analysis caching
        - Price data caching with short TTL
        - Network stats caching
        - Automatic key generation from wallet addresses
    """

    def __init__(self, backend: Optional[MemoryCache] = None):
        self._backend = backend or MemoryCache()

    def _hash_address(self, address: str) -> str:
        """Create a shorter hash of wallet address for cache keys."""
        return hashlib.sha256(address.encode()).hexdigest()[:16]

    # =========================================================================
    # Price Caching
    # =========================================================================

    def get_price(self, ticker: str) -> Optional[float]:
        """Get cached price for a ticker."""
        return self._backend.get(ticker.upper(), CacheCategory.PRICE_LIVE)

    def set_price(self, ticker: str, price: float, ttl: Optional[int] = None) -> None:
        """Cache a price with live price TTL."""
        self._backend.set(
            ticker.upper(),
            price,
            ttl=ttl or CacheConfig.PRICE_LIVE_TTL,
            category=CacheCategory.PRICE_LIVE
        )

    def get_historical_price(self, ticker: str, date: str) -> Optional[float]:
        """Get cached historical price."""
        key = f"{ticker.upper()}:{date}"
        return self._backend.get(key, CacheCategory.PRICE_HISTORICAL)

    def set_historical_price(self, ticker: str, date: str, price: float) -> None:
        """Cache a historical price (long TTL)."""
        key = f"{ticker.upper()}:{date}"
        self._backend.set(
            key,
            price,
            category=CacheCategory.PRICE_HISTORICAL
        )

    def invalidate_prices(self) -> int:
        """Invalidate all cached prices."""
        return self._backend.invalidate_category(CacheCategory.PRICE_LIVE)

    # =========================================================================
    # Wallet Analysis Caching
    # =========================================================================

    def get_analysis(self, address: str) -> Optional[Dict[str, Any]]:
        """Get cached wallet analysis (memory first, then disk)."""
        key = self._hash_address(address)
        result = self._backend.get(key, CacheCategory.ANALYSIS)
        if result is not None:
            return result

        # Fall through to disk cache
        try:
            from core.persistence import get_persistence
            disk_result = get_persistence().get_analysis(address)
            if disk_result is not None:
                # Promote back to memory cache
                self._backend.set(key, disk_result, ttl=CacheConfig.ANALYSIS_TTL, category=CacheCategory.ANALYSIS)
                return disk_result
        except Exception:
            pass  # Disk cache is best-effort

        return None

    def set_analysis(self, address: str, analysis: Dict[str, Any], ttl: Optional[int] = None) -> None:
        """Cache wallet analysis results (disk first, then memory).

        Persists to disk before memory so that a disk failure can be reflected
        in a shorter memory TTL, preventing stale data from being served
        indefinitely if the disk cache is unavailable.
        """
        key = self._hash_address(address)
        effective_ttl = ttl or CacheConfig.ANALYSIS_TTL

        # Persist to disk first
        try:
            from core.persistence import get_persistence
            get_persistence().set_analysis(address, analysis)
        except Exception as e:
            # Disk failed — reduce memory TTL so stale data expires sooner
            logger.warning(f"Disk persist failed for {address[:8]}…, reducing memory TTL: {e}")
            effective_ttl = min(effective_ttl, 300)  # Cap at 5 minutes

        self._backend.set(
            key,
            analysis,
            ttl=effective_ttl,
            category=CacheCategory.ANALYSIS
        )

    def invalidate_analysis(self, address: str) -> bool:
        """Invalidate cached analysis for a specific wallet."""
        key = self._hash_address(address)
        return self._backend.delete(key, CacheCategory.ANALYSIS)

    def invalidate_all_analyses(self) -> int:
        """Invalidate all cached wallet analyses."""
        return self._backend.invalidate_category(CacheCategory.ANALYSIS)

    # =========================================================================
    # Network Stats Caching
    # =========================================================================

    def get_network_stats(self, key: str = "global") -> Optional[Dict[str, Any]]:
        """Get cached network statistics."""
        return self._backend.get(key, CacheCategory.NETWORK_STATS)

    def set_network_stats(self, stats: Dict[str, Any], key: str = "global", ttl: Optional[int] = None) -> None:
        """Cache network statistics."""
        self._backend.set(
            key,
            stats,
            ttl=ttl or CacheConfig.NETWORK_STATS_TTL,
            category=CacheCategory.NETWORK_STATS
        )

    # =========================================================================
    # Arbitrage/Premium Caching
    # =========================================================================

    def get_arbitrage(self, key: str) -> Optional[Dict[str, Any]]:
        """Get cached arbitrage/premium data."""
        return self._backend.get(key, CacheCategory.ARBITRAGE)

    def set_arbitrage(self, key: str, data: Dict[str, Any], ttl: Optional[int] = None) -> None:
        """Cache arbitrage/premium calculations."""
        self._backend.set(
            key,
            data,
            ttl=ttl or CacheConfig.ARBITRAGE_TTL,
            category=CacheCategory.ARBITRAGE
        )

    # =========================================================================
    # General Caching
    # =========================================================================

    def get(self, key: str, default: Optional[T] = None) -> Optional[T]:
        """Get a general cached value."""
        return self._backend.get(key, CacheCategory.GENERAL, default)

    def set(self, key: str, value: Any, ttl: int = 300) -> None:
        """Set a general cached value."""
        self._backend.set(key, value, ttl=ttl, category=CacheCategory.GENERAL)

    def delete(self, key: str) -> bool:
        """Delete a general cached value."""
        return self._backend.delete(key, CacheCategory.GENERAL)

    # =========================================================================
    # Statistics & Management
    # =========================================================================

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return self._backend.get_stats()

    def clear_all(self) -> int:
        """Clear all cache entries."""
        return self._backend.clear()


# =============================================================================
# Global Cache Instance
# =============================================================================

# Singleton cache instance for the application
_cache_instance: Optional[SovereigntyCache] = None
_cache_lock = threading.Lock()


def get_cache() -> SovereigntyCache:
    """
    Get the global cache instance (singleton pattern).

    This function is thread-safe and will create the cache on first call.

    Returns:
        SovereigntyCache instance
    """
    global _cache_instance

    if _cache_instance is None:
        with _cache_lock:
            if _cache_instance is None:
                backend = os.environ.get("CACHE_BACKEND", "memory").lower()

                if backend == "redis":
                    # Future: implement Redis backend
                    logger.warning("Redis backend not yet implemented, falling back to memory")
                    _cache_instance = SovereigntyCache(MemoryCache())
                else:
                    _cache_instance = SovereigntyCache(MemoryCache())

                logger.info(f"Initialized cache with {backend} backend")

    return _cache_instance


# Convenience alias
cache = get_cache()


# =============================================================================
# Cache Decorator
# =============================================================================

def cached(
    category: CacheCategory = CacheCategory.GENERAL,
    ttl: Optional[int] = None,
    key_prefix: str = "",
    key_builder: Optional[Callable[..., str]] = None
):
    """
    Decorator for caching function results.

    Args:
        category: Cache category for the result
        ttl: Custom TTL in seconds (uses category default if None)
        key_prefix: Prefix for the cache key
        key_builder: Custom function to build cache key from args

    Example:
        @cached(category=CacheCategory.PRICE_LIVE, ttl=60)
        def get_btc_price():
            return fetch_btc_price_from_api()

        @cached(key_builder=lambda addr: f"analysis:{addr[:8]}")
        def analyze_wallet(addr: str):
            return perform_analysis(addr)
    """
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            # Build cache key
            if key_builder:
                cache_key = key_builder(*args, **kwargs)
            else:
                # Default key: prefix + function name + args hash
                arg_str = f"{args}:{sorted(kwargs.items())}"
                arg_hash = hashlib.md5(arg_str.encode()).hexdigest()[:8]
                cache_key = f"{key_prefix}{func.__name__}:{arg_hash}"

            # Check cache
            cache_instance = get_cache()
            cached_value = cache_instance._backend.get(cache_key, category)

            if cached_value is not None:
                return cached_value

            # Execute function and cache result
            result = func(*args, **kwargs)

            if result is not None:
                cache_instance._backend.set(cache_key, result, ttl=ttl, category=category)

            return result

        # Preserve function metadata
        wrapper.__name__ = func.__name__
        wrapper.__doc__ = func.__doc__

        return wrapper

    return decorator
