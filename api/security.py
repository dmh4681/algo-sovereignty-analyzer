"""
Security Middleware - Rate Limiting and Security Headers
=========================================================

This module provides security middleware for the Algorand Sovereignty Analyzer API,
including rate limiting (per-IP and per-wallet), security headers, and input validation.

Features:
    - Multi-tier rate limiting (per-IP and per-wallet address)
    - Endpoint-specific rate limits (stricter for expensive operations)
    - Sliding window rate limiting with burst protection
    - Comprehensive security headers (CSP, XSS protection, etc.)
    - Rate limit statistics and monitoring

Rate Limit Tiers:
    - /analyze: 30 req/min per IP, 60 req/min per wallet
    - /agent/advice: 10 req/min per IP (AI is expensive)
    - /history: 60 req/min per IP
    - Default: 100 req/min per IP

Environment Variables:
    RATE_LIMIT_ENABLED: "true" (default) or "false" to disable
    RATE_LIMIT_ANALYZE: Override /analyze rate limit (default: 30)
    RATE_LIMIT_ADVICE: Override /agent/advice rate limit (default: 10)
    RATE_LIMIT_DEFAULT: Override default rate limit (default: 100)

Usage:
    The middleware is automatically applied in api/main.py:

    app.add_middleware(RateLimitMiddleware)
    app.add_middleware(SecurityHeadersMiddleware)

See Also:
    - api/main.py: Middleware registration
    - core/cache.py: Caching layer (works with rate limiting to reduce load)
"""

import os
import re
import time
import json
import hashlib
import logging
from collections import defaultdict
from typing import Dict, Tuple, Optional, Any, List
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

# Configure module logger
logger = logging.getLogger("api.security")


# =============================================================================
# Rate Limit Configuration
# =============================================================================

class RateLimitTier(Enum):
    """Rate limit tiers for different endpoint types."""
    ANALYZE = "analyze"       # Wallet analysis (expensive)
    AI_ADVICE = "ai_advice"   # AI coaching (very expensive)
    HISTORY = "history"       # Historical data
    NETWORK = "network"       # Network stats
    DEFAULT = "default"       # All other endpoints


@dataclass
class EndpointRateConfig:
    """Rate limit configuration for an endpoint tier."""
    requests_per_minute: int
    requests_per_hour: int = 0  # 0 = no hourly limit
    burst_limit: int = 5       # Max requests in 1 second
    per_wallet_minute: int = 0  # Per-wallet limit (0 = disabled)

    def __post_init__(self):
        # Default hourly to 20x minute if not specified
        if self.requests_per_hour == 0:
            self.requests_per_hour = self.requests_per_minute * 20


# Endpoint-specific rate limit configurations
RATE_LIMIT_CONFIGS: Dict[RateLimitTier, EndpointRateConfig] = {
    RateLimitTier.ANALYZE: EndpointRateConfig(
        requests_per_minute=int(os.environ.get("RATE_LIMIT_ANALYZE", 30)),
        burst_limit=3,
        per_wallet_minute=60  # Allow more requests for the same wallet
    ),
    RateLimitTier.AI_ADVICE: EndpointRateConfig(
        requests_per_minute=int(os.environ.get("RATE_LIMIT_ADVICE", 10)),
        burst_limit=2,
        per_wallet_minute=20
    ),
    RateLimitTier.HISTORY: EndpointRateConfig(
        requests_per_minute=60,
        burst_limit=10,
        per_wallet_minute=120
    ),
    RateLimitTier.NETWORK: EndpointRateConfig(
        requests_per_minute=60,
        burst_limit=10
    ),
    RateLimitTier.DEFAULT: EndpointRateConfig(
        requests_per_minute=int(os.environ.get("RATE_LIMIT_DEFAULT", 100)),
        burst_limit=10
    ),
}

# Path to tier mapping
ENDPOINT_TIERS: Dict[str, RateLimitTier] = {
    "/api/v1/analyze": RateLimitTier.ANALYZE,
    "/api/v1/agent/advice": RateLimitTier.AI_ADVICE,
    "/api/v1/history": RateLimitTier.HISTORY,
    "/api/v1/network": RateLimitTier.NETWORK,
}


@dataclass
class RateLimitConfig:
    """Global rate limit configuration (legacy support)."""
    requests_per_minute: int = 60
    requests_per_hour: int = 1000
    burst_limit: int = 10  # Max requests in a 1-second burst


@dataclass
class ClientState:
    """Tracks rate limit state for a client."""
    minute_requests: int = 0
    hour_requests: int = 0
    minute_reset: float = 0
    hour_reset: float = 0
    last_request: float = 0
    burst_count: int = 0


@dataclass
class WalletState:
    """Tracks rate limit state per wallet address."""
    minute_requests: int = 0
    minute_reset: float = 0
    last_request: float = 0


@dataclass
class RateLimitStats:
    """Statistics for rate limiting monitoring."""
    total_requests: int = 0
    allowed_requests: int = 0
    blocked_requests: int = 0
    blocked_by_ip: int = 0
    blocked_by_wallet: int = 0
    blocked_by_burst: int = 0

    @property
    def block_rate(self) -> float:
        if self.total_requests == 0:
            return 0.0
        return self.blocked_requests / self.total_requests

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_requests": self.total_requests,
            "allowed_requests": self.allowed_requests,
            "blocked_requests": self.blocked_requests,
            "blocked_by_ip": self.blocked_by_ip,
            "blocked_by_wallet": self.blocked_by_wallet,
            "blocked_by_burst": self.blocked_by_burst,
            "block_rate": round(self.block_rate, 4),
            "block_rate_percent": f"{self.block_rate:.2%}"
        }


class AdvancedRateLimiter:
    """
    Advanced rate limiter with per-IP and per-wallet limiting.

    Features:
        - Endpoint-specific rate limits
        - Per-IP rate limiting (default)
        - Per-wallet rate limiting (for wallet-specific endpoints)
        - Burst protection
        - Statistics tracking
        - Automatic cleanup of old state
    """

    def __init__(self):
        self.enabled = os.environ.get("RATE_LIMIT_ENABLED", "true").lower() != "false"
        self.clients: Dict[str, Dict[str, ClientState]] = defaultdict(lambda: defaultdict(ClientState))
        self.wallets: Dict[str, WalletState] = defaultdict(WalletState)
        self.stats = RateLimitStats()
        self.tier_stats: Dict[RateLimitTier, RateLimitStats] = {
            tier: RateLimitStats() for tier in RateLimitTier
        }
        self._last_cleanup = time.time()
        self._cleanup_interval = 300  # 5 minutes

    def _get_client_id(self, request: Request) -> str:
        """Get unique client identifier from IP or forwarded header."""
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            ip = forwarded.split(",")[0].strip()
        else:
            ip = request.client.host if request.client else "unknown"
        # Hash IP for privacy in logs
        return hashlib.sha256(ip.encode()).hexdigest()[:16]

    def _get_tier(self, path: str) -> RateLimitTier:
        """Determine rate limit tier based on request path."""
        # Check exact matches first
        if path in ENDPOINT_TIERS:
            return ENDPOINT_TIERS[path]

        # Check prefixes for nested routes
        for endpoint_path, tier in ENDPOINT_TIERS.items():
            if path.startswith(endpoint_path):
                return tier

        return RateLimitTier.DEFAULT

    def _extract_wallet_address(self, request: Request) -> Optional[str]:
        """Extract wallet address from request (path params or body)."""
        # Try path parameters first
        path = request.url.path

        # Pattern: /api/v1/something/{address}/...
        # or /api/v1/analyze with address in body
        address_pattern = re.compile(r'/api/v1/[^/]+/([A-Z2-7]{58})')
        match = address_pattern.search(path)
        if match:
            return match.group(1)

        # For POST requests, we can't easily get the body in middleware
        # The wallet address will be tracked separately in the route handler
        return None

    def _cleanup_old_state(self):
        """Periodically clean up old rate limit state."""
        now = time.time()
        if now - self._last_cleanup < self._cleanup_interval:
            return

        self._last_cleanup = now
        cutoff = now - 3600  # Remove entries older than 1 hour

        # Clean up client state
        clients_to_remove = []
        for client_id, tiers in self.clients.items():
            all_old = True
            for tier_name, state in tiers.items():
                if state.last_request > cutoff:
                    all_old = False
                    break
            if all_old:
                clients_to_remove.append(client_id)

        for client_id in clients_to_remove:
            del self.clients[client_id]

        # Clean up wallet state
        wallets_to_remove = [
            addr for addr, state in self.wallets.items()
            if state.last_request < cutoff
        ]
        for addr in wallets_to_remove:
            del self.wallets[addr]

        if clients_to_remove or wallets_to_remove:
            logger.debug(f"Rate limiter cleanup: removed {len(clients_to_remove)} clients, {len(wallets_to_remove)} wallets")

    def check_rate_limit(
        self,
        request: Request,
        wallet_address: Optional[str] = None
    ) -> Tuple[bool, Dict[str, str], Optional[str]]:
        """
        Check if request should be rate limited.

        Args:
            request: The incoming request
            wallet_address: Optional wallet address for per-wallet limiting

        Returns:
            Tuple of (is_allowed, headers_dict, block_reason)
        """
        if not self.enabled:
            return True, {}, None

        self._cleanup_old_state()

        client_id = self._get_client_id(request)
        tier = self._get_tier(request.url.path)
        config = RATE_LIMIT_CONFIGS[tier]

        # Get or create client state for this tier
        state = self.clients[client_id][tier.value]
        now = time.time()

        # Reset minute window
        if now - state.minute_reset >= 60:
            state.minute_requests = 0
            state.minute_reset = now

        # Reset hour window
        if now - state.hour_reset >= 3600:
            state.hour_requests = 0
            state.hour_reset = now

        # Check burst (requests in last second)
        if now - state.last_request < 1:
            state.burst_count += 1
        else:
            state.burst_count = 1
        state.last_request = now

        # Track statistics
        self.stats.total_requests += 1
        self.tier_stats[tier].total_requests += 1

        # Check burst limit
        if state.burst_count > config.burst_limit:
            self.stats.blocked_requests += 1
            self.stats.blocked_by_burst += 1
            self.tier_stats[tier].blocked_requests += 1
            self.tier_stats[tier].blocked_by_burst += 1

            headers = self._build_headers(config, state, now)
            return False, headers, "burst_limit_exceeded"

        # Check per-minute limit
        if state.minute_requests >= config.requests_per_minute:
            self.stats.blocked_requests += 1
            self.stats.blocked_by_ip += 1
            self.tier_stats[tier].blocked_requests += 1
            self.tier_stats[tier].blocked_by_ip += 1

            headers = self._build_headers(config, state, now)
            return False, headers, "minute_limit_exceeded"

        # Check per-hour limit
        if config.requests_per_hour > 0 and state.hour_requests >= config.requests_per_hour:
            self.stats.blocked_requests += 1
            self.stats.blocked_by_ip += 1
            self.tier_stats[tier].blocked_requests += 1
            self.tier_stats[tier].blocked_by_ip += 1

            headers = self._build_headers(config, state, now)
            return False, headers, "hour_limit_exceeded"

        # Check per-wallet limit (if applicable)
        if wallet_address and config.per_wallet_minute > 0:
            wallet_state = self.wallets[wallet_address]

            # Reset wallet minute window
            if now - wallet_state.minute_reset >= 60:
                wallet_state.minute_requests = 0
                wallet_state.minute_reset = now
            wallet_state.last_request = now

            if wallet_state.minute_requests >= config.per_wallet_minute:
                self.stats.blocked_requests += 1
                self.stats.blocked_by_wallet += 1
                self.tier_stats[tier].blocked_requests += 1
                self.tier_stats[tier].blocked_by_wallet += 1

                headers = self._build_headers(config, state, now)
                headers["X-RateLimit-Wallet-Remaining"] = "0"
                return False, headers, "wallet_limit_exceeded"

            wallet_state.minute_requests += 1

        # Request allowed
        state.minute_requests += 1
        state.hour_requests += 1

        self.stats.allowed_requests += 1
        self.tier_stats[tier].allowed_requests += 1

        headers = self._build_headers(config, state, now)
        return True, headers, None

    def _build_headers(
        self,
        config: EndpointRateConfig,
        state: ClientState,
        now: float
    ) -> Dict[str, str]:
        """Build rate limit response headers."""
        remaining = max(0, config.requests_per_minute - state.minute_requests)
        reset_time = int(state.minute_reset + 60 - now)

        return {
            "X-RateLimit-Limit": str(config.requests_per_minute),
            "X-RateLimit-Remaining": str(remaining),
            "X-RateLimit-Reset": str(max(0, reset_time)),
        }

    def check_wallet_rate_limit(
        self,
        wallet_address: str,
        tier: RateLimitTier = RateLimitTier.ANALYZE
    ) -> Tuple[bool, int]:
        """
        Check rate limit for a specific wallet address.

        This can be called from route handlers after extracting the wallet
        from the request body.

        Args:
            wallet_address: The Algorand wallet address
            tier: Rate limit tier to use

        Returns:
            Tuple of (is_allowed, remaining_requests)
        """
        if not self.enabled:
            return True, 999

        config = RATE_LIMIT_CONFIGS[tier]
        if config.per_wallet_minute == 0:
            return True, 999

        wallet_state = self.wallets[wallet_address]
        now = time.time()

        # Reset minute window
        if now - wallet_state.minute_reset >= 60:
            wallet_state.minute_requests = 0
            wallet_state.minute_reset = now

        remaining = config.per_wallet_minute - wallet_state.minute_requests

        if wallet_state.minute_requests >= config.per_wallet_minute:
            return False, 0

        wallet_state.minute_requests += 1
        wallet_state.last_request = now
        return True, remaining - 1

    def get_stats(self) -> Dict[str, Any]:
        """Get rate limiting statistics."""
        tier_stats = {
            tier.value: stats.to_dict()
            for tier, stats in self.tier_stats.items()
        }

        return {
            "enabled": self.enabled,
            "overall": self.stats.to_dict(),
            "by_tier": tier_stats,
            "active_clients": len(self.clients),
            "tracked_wallets": len(self.wallets)
        }


# Global rate limiter instances
rate_limiter = AdvancedRateLimiter()

# Legacy rate limiter for backwards compatibility
_legacy_rate_limiter: Optional[Any] = None


def get_rate_limiter() -> AdvancedRateLimiter:
    """Get the global rate limiter instance."""
    return rate_limiter


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware to enforce rate limits.

    This middleware checks rate limits before processing each request.
    It supports endpoint-specific limits and per-wallet tracking.
    """

    # Paths that bypass rate limiting
    EXEMPT_PATHS = frozenset([
        "/",
        "/health",
        "/health/config",
        "/docs",
        "/redoc",
        "/openapi.json",
    ])

    async def dispatch(self, request: Request, call_next) -> Response:
        # Skip rate limiting for exempt paths
        if request.url.path in self.EXEMPT_PATHS:
            return await call_next(request)

        # Extract wallet address from path if present
        wallet_address = self._extract_wallet_from_path(request.url.path)

        is_allowed, headers, block_reason = rate_limiter.check_rate_limit(
            request,
            wallet_address=wallet_address
        )

        if not is_allowed:
            error_messages = {
                "burst_limit_exceeded": "Too many requests in quick succession. Please slow down.",
                "minute_limit_exceeded": "Rate limit exceeded. Please wait before making more requests.",
                "hour_limit_exceeded": "Hourly rate limit exceeded. Please try again later.",
                "wallet_limit_exceeded": "Too many requests for this wallet. Please wait before retrying.",
            }

            error_body = {
                "success": False,
                "error": {
                    "code": "RATE_LIMIT_EXCEEDED",
                    "message": error_messages.get(block_reason, "Rate limit exceeded."),
                    "details": {
                        "reason": block_reason,
                        "retry_after": headers.get("X-RateLimit-Reset", "60")
                    }
                }
            }

            response = Response(
                content=json.dumps(error_body),
                status_code=429,
                media_type="application/json",
            )
            for key, value in headers.items():
                response.headers[key] = value
            response.headers["Retry-After"] = headers.get("X-RateLimit-Reset", "60")

            # Log rate limit hit
            client_ip_hash = hashlib.sha256(
                (request.client.host if request.client else "unknown").encode()
            ).hexdigest()[:8]
            logger.warning(
                f"Rate limit exceeded: {request.url.path} client={client_ip_hash} reason={block_reason}"
            )

            return response

        response = await call_next(request)

        # Add rate limit headers to successful responses
        for key, value in headers.items():
            response.headers[key] = value

        return response

    def _extract_wallet_from_path(self, path: str) -> Optional[str]:
        """Extract Algorand wallet address from URL path."""
        # Pattern matches 58-character base32 strings
        address_pattern = re.compile(r'([A-Z2-7]{58})')
        match = address_pattern.search(path)
        return match.group(1) if match else None


# =============================================================================
# Security Headers
# =============================================================================

SECURITY_HEADERS = {
    # Prevent clickjacking
    "X-Frame-Options": "DENY",
    # Prevent MIME type sniffing
    "X-Content-Type-Options": "nosniff",
    # Enable XSS filter
    "X-XSS-Protection": "1; mode=block",
    # Referrer policy
    "Referrer-Policy": "strict-origin-when-cross-origin",
    # Permissions policy (disable unnecessary features)
    "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
    # Content Security Policy
    "Content-Security-Policy": (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data: https:; "
        "font-src 'self'; "
        "connect-src 'self' https:; "
        "frame-ancestors 'none';"
    ),
}


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware to add security headers to all responses."""

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)

        # Add security headers
        for header, value in SECURITY_HEADERS.items():
            response.headers[header] = value

        return response


# =============================================================================
# Input Validation Helpers
# =============================================================================

def validate_algorand_address(address: str) -> bool:
    """
    Validate Algorand address format.
    - Must be exactly 58 characters
    - Must contain only base32 characters (A-Z, 2-7)
    """
    if not address or len(address) != 58:
        return False

    valid_chars = set("ABCDEFGHIJKLMNOPQRSTUVWXYZ234567")
    return all(c in valid_chars for c in address.upper())


def sanitize_string(value: str, max_length: int = 1000) -> str:
    """Sanitize string input by removing control characters and limiting length."""
    if not value:
        return ""
    # Remove control characters except newlines and tabs
    sanitized = "".join(
        char for char in value
        if char.isprintable() or char in "\n\t"
    )
    return sanitized[:max_length].strip()
