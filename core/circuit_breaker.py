"""
Circuit Breaker Pattern - Prevents cascading failures from external API outages.

The circuit breaker wraps external service calls and tracks failure rates.
When failures exceed the threshold, the circuit "opens" and requests fail fast
(no waiting for timeouts), allowing the failing service time to recover.

States:
    CLOSED  - Normal operation. Calls pass through. Failures are counted.
    OPEN    - Failure threshold exceeded. Calls fail immediately (fast-fail).
              After `recovery_timeout` seconds, transitions to HALF_OPEN.
    HALF_OPEN - Recovery probe state. A limited number of calls are allowed
              through to test if the service has recovered. On success,
              transitions back to CLOSED. On failure, back to OPEN.

Usage::

    from core.circuit_breaker import get_circuit_breaker, CircuitOpenError

    cb = get_circuit_breaker("coingecko")

    try:
        result = cb.call(lambda: requests.get(url, timeout=5))
    except CircuitOpenError:
        # Circuit is open - use fallback immediately, no network call
        result = fallback_value
    except Exception as e:
        # Actual service error (circuit recorded the failure)
        result = fallback_value

Integration with retry_with_backoff::

    cb = get_circuit_breaker("vestige")

    def fetch():
        return retry_with_backoff(_do_fetch, max_retries=3, ...)

    try:
        result = cb.call(fetch)
    except CircuitOpenError:
        return fallback

Configuration per service (defaults are conservative for pricing APIs):
    - failure_threshold: 5 failures in the window before opening
    - recovery_timeout: 60 seconds in OPEN state before probing
    - window_seconds: 120 second rolling window for failure counting
    - half_open_max_calls: 1 probe call allowed in HALF_OPEN
    - success_threshold: 2 consecutive successes to fully close
"""

import logging
import threading
import time
from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, Optional

logger = logging.getLogger("core.circuit_breaker")


class CircuitState(Enum):
    """Possible states for a circuit breaker."""
    CLOSED = "closed"        # Normal operation
    OPEN = "open"            # Failing fast, service is down
    HALF_OPEN = "half_open"  # Probing for recovery


class CircuitOpenError(Exception):
    """
    Raised when a call is attempted while the circuit breaker is OPEN.

    Callers should treat this as a signal to use a fallback immediately
    rather than waiting for a timeout.
    """

    def __init__(self, service_name: str, retry_after: Optional[float] = None):
        self.service_name = service_name
        self.retry_after = retry_after
        msg = f"Circuit breaker OPEN for '{service_name}'"
        if retry_after is not None:
            msg += f" (retry after {retry_after:.0f}s)"
        super().__init__(msg)


@dataclass
class CircuitBreakerConfig:
    """Configuration for a circuit breaker instance."""
    failure_threshold: int = 5
    """Number of failures in the window before opening the circuit."""

    recovery_timeout: float = 60.0
    """Seconds to wait in OPEN state before transitioning to HALF_OPEN."""

    window_seconds: float = 120.0
    """Rolling time window (seconds) for counting failures."""

    half_open_max_calls: int = 1
    """Maximum concurrent calls allowed in HALF_OPEN state."""

    success_threshold: int = 2
    """Consecutive successes in HALF_OPEN needed to close the circuit."""


@dataclass
class CircuitBreakerStats:
    """Runtime statistics for a circuit breaker."""
    state: str
    failure_count: int
    success_count: int
    total_calls: int
    rejected_calls: int
    last_failure_time: Optional[float]
    last_success_time: Optional[float]
    opened_at: Optional[float]
    half_open_successes: int

    def to_dict(self) -> Dict[str, Any]:
        now = time.time()
        result = {
            "state": self.state,
            "failure_count_in_window": self.failure_count,
            "consecutive_successes": self.success_count,
            "total_calls": self.total_calls,
            "rejected_calls": self.rejected_calls,
            "half_open_successes": self.half_open_successes,
        }
        if self.last_failure_time:
            result["seconds_since_last_failure"] = round(now - self.last_failure_time, 1)
        if self.last_success_time:
            result["seconds_since_last_success"] = round(now - self.last_success_time, 1)
        if self.opened_at and self.state == CircuitState.OPEN.value:
            result["seconds_open"] = round(now - self.opened_at, 1)
        return result


class CircuitBreaker:
    """
    Thread-safe circuit breaker for a single external service.

    Tracks failures in a rolling time window. When `failure_threshold` is
    reached, the circuit opens and subsequent calls raise `CircuitOpenError`
    until the service has time to recover.
    """

    def __init__(self, name: str, config: Optional[CircuitBreakerConfig] = None):
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self._lock = threading.RLock()
        self._state = CircuitState.CLOSED

        # Rolling failure window: each entry is a timestamp of a failure
        self._failure_timestamps: deque = deque()

        # Recovery tracking
        self._opened_at: Optional[float] = None
        self._half_open_calls: int = 0        # calls currently in-flight in HALF_OPEN
        self._half_open_successes: int = 0    # consecutive successes in HALF_OPEN

        # Diagnostics
        self._total_calls: int = 0
        self._rejected_calls: int = 0
        self._last_failure_time: Optional[float] = None
        self._last_success_time: Optional[float] = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def state(self) -> CircuitState:
        with self._lock:
            return self._get_state()

    def call(self, func: Callable[[], Any]) -> Any:
        """
        Execute `func` with circuit breaker protection.

        Raises:
            CircuitOpenError: If the circuit is OPEN (fast-fail).
            Exception: Any exception raised by `func` (circuit records failure).

        Returns:
            The return value of `func()` on success.
        """
        with self._lock:
            state = self._get_state()
            self._total_calls += 1

            if state == CircuitState.OPEN:
                self._rejected_calls += 1
                retry_after = self._seconds_until_half_open()
                raise CircuitOpenError(self.name, retry_after=retry_after)

            if state == CircuitState.HALF_OPEN:
                if self._half_open_calls >= self.config.half_open_max_calls:
                    self._rejected_calls += 1
                    raise CircuitOpenError(self.name, retry_after=0)
                self._half_open_calls += 1

        # Execute outside lock so we don't hold it during a blocking I/O call
        try:
            result = func()
        except Exception as exc:
            self._record_failure(exc)
            raise

        self._record_success()
        return result

    def get_stats(self) -> CircuitBreakerStats:
        """Return a snapshot of the current circuit breaker statistics."""
        with self._lock:
            state = self._get_state()
            return CircuitBreakerStats(
                state=state.value,
                failure_count=self._failure_count_in_window(),
                success_count=self._half_open_successes,
                total_calls=self._total_calls,
                rejected_calls=self._rejected_calls,
                last_failure_time=self._last_failure_time,
                last_success_time=self._last_success_time,
                opened_at=self._opened_at,
                half_open_successes=self._half_open_successes,
            )

    def reset(self) -> None:
        """Manually reset circuit to CLOSED state (for testing / admin use)."""
        with self._lock:
            self._state = CircuitState.CLOSED
            self._failure_timestamps.clear()
            self._opened_at = None
            self._half_open_calls = 0
            self._half_open_successes = 0
            logger.info("Circuit breaker '%s' manually reset to CLOSED", self.name)

    # ------------------------------------------------------------------
    # Internal state machine
    # ------------------------------------------------------------------

    def _get_state(self) -> CircuitState:
        """Compute the effective state, handling automatic OPEN→HALF_OPEN transition."""
        if self._state == CircuitState.OPEN:
            if self._opened_at is not None:
                elapsed = time.time() - self._opened_at
                if elapsed >= self.config.recovery_timeout:
                    logger.info(
                        "Circuit breaker '%s' transitioning OPEN→HALF_OPEN after %.0fs",
                        self.name, elapsed,
                    )
                    self._state = CircuitState.HALF_OPEN
                    self._half_open_calls = 0
                    self._half_open_successes = 0
        return self._state

    def _failure_count_in_window(self) -> int:
        """Count failures within the rolling time window, pruning old entries."""
        cutoff = time.time() - self.config.window_seconds
        while self._failure_timestamps and self._failure_timestamps[0] < cutoff:
            self._failure_timestamps.popleft()
        return len(self._failure_timestamps)

    def _record_failure(self, exc: Exception) -> None:
        with self._lock:
            now = time.time()
            self._last_failure_time = now
            self._failure_timestamps.append(now)

            current_state = self._get_state()

            if current_state == CircuitState.HALF_OPEN:
                # Any failure in HALF_OPEN sends us back to OPEN
                self._half_open_calls = max(0, self._half_open_calls - 1)
                self._open_circuit(now)
                logger.warning(
                    "Circuit breaker '%s' HALF_OPEN→OPEN (probe failed: %s: %s)",
                    self.name, type(exc).__name__, exc,
                )
            elif current_state == CircuitState.CLOSED:
                count = self._failure_count_in_window()
                if count >= self.config.failure_threshold:
                    self._open_circuit(now)
                    logger.warning(
                        "Circuit breaker '%s' CLOSED→OPEN (%d failures in %.0fs window)",
                        self.name, count, self.config.window_seconds,
                    )

    def _record_success(self) -> None:
        with self._lock:
            self._last_success_time = time.time()

            current_state = self._get_state()

            if current_state == CircuitState.HALF_OPEN:
                self._half_open_calls = max(0, self._half_open_calls - 1)
                self._half_open_successes += 1
                if self._half_open_successes >= self.config.success_threshold:
                    self._state = CircuitState.CLOSED
                    self._failure_timestamps.clear()
                    self._opened_at = None
                    self._half_open_successes = 0
                    logger.info(
                        "Circuit breaker '%s' HALF_OPEN→CLOSED (service recovered)",
                        self.name,
                    )

    def _open_circuit(self, now: float) -> None:
        self._state = CircuitState.OPEN
        self._opened_at = now

    def _seconds_until_half_open(self) -> Optional[float]:
        if self._opened_at is None:
            return None
        elapsed = time.time() - self._opened_at
        remaining = self.config.recovery_timeout - elapsed
        return max(0.0, remaining)


# =============================================================================
# Registry - process-wide singleton registry of named circuit breakers
# =============================================================================

class CircuitBreakerRegistry:
    """
    Process-wide registry of named circuit breakers.

    Use `get_circuit_breaker(name)` rather than instantiating directly.
    """

    # Per-service configuration overrides (tuned for the pricing APIs)
    _SERVICE_CONFIGS: Dict[str, CircuitBreakerConfig] = {
        # CoinGecko - public, rate-limited, slow to recover on 429 bursts
        "coingecko": CircuitBreakerConfig(
            failure_threshold=4,
            recovery_timeout=90.0,
            window_seconds=120.0,
            half_open_max_calls=1,
            success_threshold=2,
        ),
        # Coinbase - generally reliable, short recovery window
        "coinbase": CircuitBreakerConfig(
            failure_threshold=5,
            recovery_timeout=45.0,
            window_seconds=120.0,
            half_open_max_calls=1,
            success_threshold=2,
        ),
        # Vestige Labs - Algorand-native, can be slow during high network activity
        "vestige": CircuitBreakerConfig(
            failure_threshold=5,
            recovery_timeout=60.0,
            window_seconds=120.0,
            half_open_max_calls=1,
            success_threshold=2,
        ),
        # Yahoo Finance - may be blocked or rate-limited aggressively
        "yahoo_finance": CircuitBreakerConfig(
            failure_threshold=3,
            recovery_timeout=120.0,
            window_seconds=180.0,
            half_open_max_calls=1,
            success_threshold=2,
        ),
        # Algorand node - critical path, be conservative
        "algorand_node": CircuitBreakerConfig(
            failure_threshold=3,
            recovery_timeout=30.0,
            window_seconds=60.0,
            half_open_max_calls=1,
            success_threshold=1,
        ),
        # Anthropic / Claude AI - 60s calls, generous recovery
        "anthropic": CircuitBreakerConfig(
            failure_threshold=3,
            recovery_timeout=120.0,
            window_seconds=300.0,
            half_open_max_calls=1,
            success_threshold=1,
        ),
    }

    def __init__(self):
        self._breakers: Dict[str, CircuitBreaker] = {}
        self._lock = threading.Lock()

    def get(self, name: str, config: Optional[CircuitBreakerConfig] = None) -> CircuitBreaker:
        """
        Get or create a named circuit breaker.

        Args:
            name: Unique service identifier (e.g. "coingecko", "vestige").
            config: Optional config override. If omitted, uses service-specific
                    defaults from _SERVICE_CONFIGS, or generic defaults.

        Returns:
            The CircuitBreaker instance for `name`.
        """
        with self._lock:
            if name not in self._breakers:
                resolved_config = config or self._SERVICE_CONFIGS.get(name) or CircuitBreakerConfig()
                self._breakers[name] = CircuitBreaker(name, resolved_config)
                logger.debug("Registered circuit breaker '%s'", name)
            return self._breakers[name]

    def get_all_states(self) -> Dict[str, Dict[str, Any]]:
        """
        Return a dict of all registered circuit breakers and their current stats.
        Suitable for a health-check or status API endpoint.
        """
        with self._lock:
            names = list(self._breakers.keys())

        return {
            name: self._breakers[name].get_stats().to_dict()
            for name in names
        }

    def reset_all(self) -> None:
        """Reset all circuit breakers to CLOSED (for testing)."""
        with self._lock:
            for cb in self._breakers.values():
                cb.reset()


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------

_registry = CircuitBreakerRegistry()


def get_circuit_breaker(name: str, config: Optional[CircuitBreakerConfig] = None) -> CircuitBreaker:
    """
    Get (or create) a named circuit breaker from the global registry.

    Args:
        name: Service identifier. Pre-configured services:
              "coingecko", "coinbase", "vestige", "yahoo_finance",
              "algorand_node", "anthropic".
        config: Optional config override for new breakers.

    Returns:
        CircuitBreaker instance.
    """
    return _registry.get(name, config)


def get_all_circuit_breaker_states() -> Dict[str, Dict[str, Any]]:
    """Return current stats for all registered circuit breakers."""
    return _registry.get_all_states()
