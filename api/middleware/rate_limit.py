"""
Sliding window rate limiter with tiered limits.

STANDARD tier: 60 requests/minute (default for all endpoints)
EXPENSIVE tier: 10 requests/minute (wallet analysis, AI advice)
"""
import time
import hashlib
from collections import defaultdict, deque
from threading import Lock
from typing import Dict, Tuple

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse, Response


# Tier definitions
STANDARD_LIMIT = 60  # requests per minute
EXPENSIVE_LIMIT = 10  # requests per minute
WINDOW_SECONDS = 60

# Paths excluded from rate limiting entirely
EXCLUDED_PATHS = frozenset([
    "/",
    "/health",
    "/health/config",
    "/docs",
    "/openapi.json",
])

# Path prefixes that use the EXPENSIVE tier
EXPENSIVE_PREFIXES = (
    "/api/v1/analyze",
    "/api/v1/agent/advice",
    "/api/v1/defi/sovereignty-cost",
)


def _get_client_ip(request: Request) -> str:
    """Extract client IP from request, respecting X-Forwarded-For."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _hash_ip(ip: str) -> str:
    """Hash IP for use as dict key."""
    return hashlib.sha256(ip.encode()).hexdigest()[:16]


def _is_expensive(path: str) -> bool:
    """Check if the request path matches an expensive endpoint."""
    return path.startswith(EXPENSIVE_PREFIXES)


class SlidingWindowRateLimitMiddleware(BaseHTTPMiddleware):
    """
    In-memory sliding window rate limiter with two tiers.

    Tracks per-IP request timestamps in a sliding 60-second window.
    Each tier (STANDARD, EXPENSIVE) has its own counter per client.
    """

    def __init__(self, app):
        super().__init__(app)
        # client_id -> deque of timestamps
        self._standard_windows: Dict[str, deque] = defaultdict(deque)
        self._expensive_windows: Dict[str, deque] = defaultdict(deque)
        self._lock = Lock()
        self._request_counter = 0

    def _prune_and_count(self, window: deque, now: float) -> int:
        """Remove expired timestamps and return current count."""
        cutoff = now - WINDOW_SECONDS
        while window and window[0] <= cutoff:
            window.popleft()
        return len(window)

    def _cleanup_stale(self, now: float) -> None:
        """Remove IPs not seen in 10 minutes to prevent unbounded growth."""
        stale_cutoff = now - 600  # 10 minutes
        for windows in (self._standard_windows, self._expensive_windows):
            stale_keys = [
                k for k, v in windows.items()
                if not v or v[-1] < stale_cutoff
            ]
            for k in stale_keys:
                del windows[k]

    def _check(
        self, client_id: str, now: float, expensive: bool
    ) -> Tuple[bool, int, int]:
        """
        Check rate limit for a client.

        Returns (allowed, remaining, retry_after_seconds).
        """
        with self._lock:
            self._request_counter += 1
            if self._request_counter % 100 == 0:
                self._cleanup_stale(now)

            if expensive:
                window = self._expensive_windows[client_id]
                limit = EXPENSIVE_LIMIT
            else:
                window = self._standard_windows[client_id]
                limit = STANDARD_LIMIT

            count = self._prune_and_count(window, now)

            if count >= limit:
                retry_after = int(window[0] + WINDOW_SECONDS - now) + 1
                return False, 0, max(1, retry_after)

            window.append(now)
            remaining = limit - count - 1
            return True, remaining, 0

    async def dispatch(self, request: Request, call_next) -> Response:
        path = request.url.path

        if path in EXCLUDED_PATHS:
            return await call_next(request)

        ip = _get_client_ip(request)
        client_id = _hash_ip(ip)
        now = time.time()
        expensive = _is_expensive(path)

        allowed, remaining, retry_after = self._check(client_id, now, expensive)

        tier = "EXPENSIVE" if expensive else "STANDARD"
        limit = EXPENSIVE_LIMIT if expensive else STANDARD_LIMIT

        if not allowed:
            return JSONResponse(
                status_code=429,
                content={
                    "success": False,
                    "error": {
                        "code": "RATE_LIMIT_EXCEEDED",
                        "message": f"Rate limit exceeded ({tier}: {limit}/min). Please retry after {retry_after}s.",
                    },
                },
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Limit": str(limit),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(retry_after),
                },
            )

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        return response
