"""
Sliding window rate limiter with tiered limits and per-wallet tracking.

STANDARD tier: 60 requests/minute (default for all endpoints)
EXPENSIVE tier: 10 requests/minute (wallet analysis, AI advice)
WALLET tier:    20 requests/minute per wallet address (analysis endpoints)
"""
import re
import json
import time
import hashlib
from collections import defaultdict, deque
from threading import Lock
from typing import Dict, Tuple, Optional

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse, Response
from starlette.types import Message


# Tier definitions
STANDARD_LIMIT = 60   # requests per minute per IP
EXPENSIVE_LIMIT = 10  # requests per minute per IP (expensive endpoints)
WALLET_LIMIT = 20     # requests per minute per wallet address
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
    "/api/v1/advisor",
    "/api/v1/defi/sovereignty-cost",
)

# POST endpoints where the wallet address lives in the JSON body
WALLET_BODY_PATHS = frozenset([
    "/api/v1/analyze",
])

# Regex to extract a wallet address from GET URL paths such as:
#   /api/v1/analyze/quick/{address}
#   /api/v1/history/{address}
#   /api/v1/assets/{address}/{category}
#   /api/v1/wallet/{address}/...
_WALLET_IN_PATH_RE = re.compile(
    r"/api/v1/(?:analyze/quick|history|assets|wallet)/([A-Z2-7]{58})(?:/|$)"
)

# Algorand address validation: 58 base32 chars
_ALGORAND_ADDR_RE = re.compile(r"^[A-Z2-7]{58}$")


def _get_client_ip(request: Request) -> str:
    """Extract client IP from request, respecting X-Forwarded-For."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _hash_key(value: str) -> str:
    """Hash a string for use as a dict key (privacy-preserving)."""
    return hashlib.sha256(value.encode()).hexdigest()[:16]


def _is_expensive(path: str) -> bool:
    """Check if the request path matches an expensive endpoint."""
    return path.startswith(EXPENSIVE_PREFIXES)


def _extract_wallet_from_path(path: str) -> Optional[str]:
    """Extract an Algorand wallet address embedded in a URL path segment."""
    m = _WALLET_IN_PATH_RE.search(path)
    return m.group(1) if m else None


async def _extract_wallet_from_body(request: Request) -> Optional[str]:
    """
    Extract wallet address from a POST JSON body without consuming the stream.

    Reads the raw bytes, parses JSON to find 'address', then re-injects the
    bytes back into the request so FastAPI can read the body normally.
    """
    try:
        body_bytes: bytes = await request.body()
        if not body_bytes:
            return None

        # Re-inject body so downstream handlers can read it
        async def _replay() -> Message:
            return {"type": "http.request", "body": body_bytes, "more_body": False}

        request._receive = _replay  # type: ignore[attr-defined]

        data = json.loads(body_bytes)
        address = data.get("address", "")
        if isinstance(address, str) and _ALGORAND_ADDR_RE.match(address):
            return address
    except Exception:
        pass
    return None


class SlidingWindowRateLimitMiddleware(BaseHTTPMiddleware):
    """
    In-memory sliding window rate limiter with three tiers:

    * STANDARD  — 60 req/min per IP (all endpoints)
    * EXPENSIVE — 10 req/min per IP (analysis, AI advice)
    * WALLET    — 20 req/min per wallet address (analysis endpoints only)

    The wallet tier prevents a single address from being hammered regardless
    of how many different IPs are making the requests.
    """

    def __init__(self, app):
        super().__init__(app)
        # client_id -> deque of timestamps
        self._standard_windows: Dict[str, deque] = defaultdict(deque)
        self._expensive_windows: Dict[str, deque] = defaultdict(deque)
        self._wallet_windows: Dict[str, deque] = defaultdict(deque)
        self._lock = Lock()
        self._request_counter = 0

    def _prune_and_count(self, window: deque, now: float) -> int:
        """Remove expired timestamps and return current count."""
        cutoff = now - WINDOW_SECONDS
        while window and window[0] <= cutoff:
            window.popleft()
        return len(window)

    def _cleanup_stale(self, now: float) -> None:
        """Remove keys not seen in 10 minutes to prevent unbounded growth."""
        stale_cutoff = now - 600  # 10 minutes
        for windows in (self._standard_windows, self._expensive_windows, self._wallet_windows):
            stale_keys = [
                k for k, v in windows.items()
                if not v or v[-1] < stale_cutoff
            ]
            for k in stale_keys:
                del windows[k]

    def _check(
        self,
        client_id: str,
        wallet_key: Optional[str],
        now: float,
        expensive: bool,
    ) -> Tuple[bool, str, int, int, int]:
        """
        Check both IP-level and wallet-level rate limits atomically.

        Returns:
            (allowed, reason, ip_remaining, wallet_remaining, retry_after_seconds)
            reason is "" when allowed, "IP" or "WALLET" when denied.
        """
        with self._lock:
            self._request_counter += 1
            if self._request_counter % 100 == 0:
                self._cleanup_stale(now)

            # --- IP-level check ---
            if expensive:
                ip_window = self._expensive_windows[client_id]
                ip_limit = EXPENSIVE_LIMIT
            else:
                ip_window = self._standard_windows[client_id]
                ip_limit = STANDARD_LIMIT

            ip_count = self._prune_and_count(ip_window, now)

            if ip_count >= ip_limit:
                retry_after = int(ip_window[0] + WINDOW_SECONDS - now) + 1
                return False, "IP", 0, WALLET_LIMIT, max(1, retry_after)

            # --- Wallet-level check (only when we have an address) ---
            wallet_remaining = WALLET_LIMIT
            if wallet_key is not None:
                wallet_window = self._wallet_windows[wallet_key]
                wallet_count = self._prune_and_count(wallet_window, now)

                if wallet_count >= WALLET_LIMIT:
                    retry_after = int(wallet_window[0] + WINDOW_SECONDS - now) + 1
                    return False, "WALLET", ip_limit - ip_count - 1, 0, max(1, retry_after)

                wallet_window.append(now)
                wallet_remaining = WALLET_LIMIT - wallet_count - 1

            # Commit IP slot only after both checks pass
            ip_window.append(now)
            ip_remaining = ip_limit - ip_count - 1
            return True, "", ip_remaining, wallet_remaining, 0

    async def dispatch(self, request: Request, call_next) -> Response:
        path = request.url.path

        if path in EXCLUDED_PATHS:
            return await call_next(request)

        ip = _get_client_ip(request)
        client_id = _hash_key(ip)
        now = time.time()
        expensive = _is_expensive(path)

        # Extract wallet address (try path first, then body for POST endpoints)
        wallet_address = _extract_wallet_from_path(path)
        if wallet_address is None and path in WALLET_BODY_PATHS:
            wallet_address = await _extract_wallet_from_body(request)

        wallet_key = _hash_key(wallet_address) if wallet_address else None

        allowed, reason, ip_remaining, wallet_remaining, retry_after = self._check(
            client_id, wallet_key, now, expensive
        )

        tier = "EXPENSIVE" if expensive else "STANDARD"
        ip_limit = EXPENSIVE_LIMIT if expensive else STANDARD_LIMIT

        if not allowed:
            if reason == "WALLET":
                message = (
                    f"Rate limit exceeded for this wallet address "
                    f"({WALLET_LIMIT}/min). Please retry after {retry_after}s."
                )
                error_code = "WALLET_RATE_LIMIT_EXCEEDED"
            else:
                message = (
                    f"Rate limit exceeded ({tier}: {ip_limit}/min). "
                    f"Please retry after {retry_after}s."
                )
                error_code = "RATE_LIMIT_EXCEEDED"

            return JSONResponse(
                status_code=429,
                content={
                    "success": False,
                    "error": {
                        "code": error_code,
                        "message": message,
                    },
                },
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Limit": str(ip_limit),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(retry_after),
                },
            )

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(ip_limit)
        response.headers["X-RateLimit-Remaining"] = str(ip_remaining)
        if wallet_key is not None:
            response.headers["X-RateLimit-Wallet-Remaining"] = str(wallet_remaining)
        return response
