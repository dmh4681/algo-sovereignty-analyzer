"""
Security middleware for rate limiting and security headers.
"""
import time
import hashlib
from collections import defaultdict
from typing import Dict, Tuple, Optional
from dataclasses import dataclass, field
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response


# =============================================================================
# Rate Limiting
# =============================================================================

@dataclass
class RateLimitConfig:
    """Configuration for rate limiting."""
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


class RateLimiter:
    """In-memory rate limiter using sliding window."""

    def __init__(self, config: Optional[RateLimitConfig] = None):
        self.config = config or RateLimitConfig()
        self.clients: Dict[str, ClientState] = defaultdict(ClientState)

    def _get_client_id(self, request: Request) -> str:
        """Get unique client identifier from IP or forwarded header."""
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            ip = forwarded.split(",")[0].strip()
        else:
            ip = request.client.host if request.client else "unknown"
        # Hash IP for privacy in logs
        return hashlib.sha256(ip.encode()).hexdigest()[:16]

    def check_rate_limit(self, request: Request) -> Tuple[bool, Dict[str, int]]:
        """
        Check if request should be rate limited.
        Returns (is_allowed, headers_dict).
        """
        client_id = self._get_client_id(request)
        state = self.clients[client_id]
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

        # Check limits
        is_allowed = (
            state.minute_requests < self.config.requests_per_minute
            and state.hour_requests < self.config.requests_per_hour
            and state.burst_count <= self.config.burst_limit
        )

        if is_allowed:
            state.minute_requests += 1
            state.hour_requests += 1

        # Calculate remaining
        remaining_minute = max(0, self.config.requests_per_minute - state.minute_requests)
        reset_time = int(state.minute_reset + 60 - now)

        headers = {
            "X-RateLimit-Limit": str(self.config.requests_per_minute),
            "X-RateLimit-Remaining": str(remaining_minute),
            "X-RateLimit-Reset": str(max(0, reset_time)),
        }

        return is_allowed, headers


# Global rate limiter instance
rate_limiter = RateLimiter()


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware to enforce rate limits."""

    async def dispatch(self, request: Request, call_next) -> Response:
        # Skip rate limiting for health checks
        if request.url.path in ["/", "/health", "/docs", "/openapi.json"]:
            return await call_next(request)

        is_allowed, headers = rate_limiter.check_rate_limit(request)

        if not is_allowed:
            response = Response(
                content='{"detail": "Rate limit exceeded. Please slow down."}',
                status_code=429,
                media_type="application/json",
            )
            for key, value in headers.items():
                response.headers[key] = value
            response.headers["Retry-After"] = headers.get("X-RateLimit-Reset", "60")
            return response

        response = await call_next(request)

        # Add rate limit headers to successful responses
        for key, value in headers.items():
            response.headers[key] = value

        return response


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
