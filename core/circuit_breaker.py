"""
Circuit Breaker Pattern - Prevents cascading failures for external API calls.

States:
  CLOSED   - Normal operation. Requests pass through. Failures are counted.
  OPEN     - Circuit tripped. Requests fail immediately without calling the
             external service. After ``recovery_timeout`` seconds the breaker
             moves to HALF_OPEN.
  HALF_OPEN - A single probe request is allowed through. Success → CLOSED;
             failure → OPEN (reset timer).

Typical usage::

    breaker = CircuitBreaker(name="FRED", failure_threshold=3, recovery_timeout=60)

    try:
        result = breaker.call(lambda: requests.get(...))
    except CircuitOpenError:
        # Fast-fail path — use cached/fallback data
        result = None
"""

import logging
import threading
import time
from enum import Enum
from typing import Callable, Optional, Any

logger = logging.getLogger("core.circuit_breaker")


class CircuitState(str, Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitOpenError(Exception):
    """Raised when a call is rejected because the circuit is OPEN."""

    def __init__(self, name: str, retry_after: float):
        self.name = name
        self.retry_after = retry_after
        super().__init__(
            f"Circuit '{name}' is OPEN. Retry after {retry_after:.1f}s."
        )


class CircuitBreaker:
    """
    Thread-safe circuit breaker for a single external dependency.

    Args:
        name: Human-readable name used in log messages (e.g. "FRED").
        failure_threshold: Consecutive failures required to OPEN the circuit.
        recovery_timeout: Seconds to wait in OPEN state before moving to
            HALF_OPEN and allowing a probe request.
        success_threshold: Consecutive successes in HALF_OPEN required to
            return to CLOSED state.
    """

    def __init__(
        self,
        name: str,
        failure_threshold: int = 3,
        recovery_timeout: float = 60.0,
        success_threshold: int = 1,
    ) -> None:
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.success_threshold = success_threshold

        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._opened_at: Optional[float] = None
        self._last_failure_exc: Optional[Exception] = None
        self._lock = threading.Lock()

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    @property
    def state(self) -> CircuitState:
        with self._lock:
            return self._effective_state()

    def call(self, func: Callable[[], Any]) -> Any:
        """
        Execute *func* with circuit-breaker protection.

        Raises:
            CircuitOpenError: If the circuit is currently OPEN.
            Exception: Any exception raised by *func* (after recording the
                failure and potentially opening the circuit).
        """
        with self._lock:
            state = self._effective_state()

            if state == CircuitState.OPEN:
                retry_after = self._seconds_until_recovery()
                raise CircuitOpenError(self.name, retry_after)

            if state == CircuitState.HALF_OPEN:
                logger.info("Circuit '%s' is HALF_OPEN — sending probe request", self.name)

        try:
            result = func()
        except Exception as exc:
            self._on_failure(exc)
            raise

        self._on_success()
        return result

    def reset(self) -> None:
        """Manually reset the circuit to CLOSED state (admin action)."""
        with self._lock:
            self._transition_to_closed()
        logger.info("Circuit '%s' manually reset to CLOSED", self.name)

    def status(self) -> dict:
        """Return a JSON-serialisable status snapshot."""
        with self._lock:
            state = self._effective_state()
            snap = {
                "name": self.name,
                "state": state.value,
                "failure_count": self._failure_count,
                "failure_threshold": self.failure_threshold,
                "recovery_timeout": self.recovery_timeout,
                "success_threshold": self.success_threshold,
            }
            if state == CircuitState.OPEN and self._opened_at is not None:
                snap["retry_after_seconds"] = max(0.0, self._seconds_until_recovery())
                snap["opened_at"] = self._opened_at
            if self._last_failure_exc is not None:
                snap["last_error"] = str(self._last_failure_exc)
        return snap

    # ------------------------------------------------------------------
    # Private helpers (must be called with _lock held)
    # ------------------------------------------------------------------

    def _effective_state(self) -> CircuitState:
        """
        Return the current logical state, auto-advancing OPEN → HALF_OPEN
        once the recovery timeout has elapsed.
        """
        if self._state == CircuitState.OPEN and self._opened_at is not None:
            if time.monotonic() - self._opened_at >= self.recovery_timeout:
                # Transition without holding the lock on _transition methods
                # (caller already holds it).
                self._state = CircuitState.HALF_OPEN
                self._success_count = 0
                logger.info(
                    "Circuit '%s' moved to HALF_OPEN after %.0fs recovery timeout",
                    self.name,
                    self.recovery_timeout,
                )
        return self._state

    def _seconds_until_recovery(self) -> float:
        if self._opened_at is None:
            return 0.0
        elapsed = time.monotonic() - self._opened_at
        return max(0.0, self.recovery_timeout - elapsed)

    def _on_failure(self, exc: Exception) -> None:
        with self._lock:
            self._last_failure_exc = exc
            self._failure_count += 1
            self._success_count = 0

            if self._state == CircuitState.HALF_OPEN:
                # Probe failed — reopen
                self._transition_to_open()
                logger.warning(
                    "Circuit '%s' probe FAILED (%s: %s) — back to OPEN",
                    self.name, type(exc).__name__, exc,
                )
            elif self._failure_count >= self.failure_threshold:
                self._transition_to_open()
                logger.error(
                    "Circuit '%s' OPENED after %d consecutive failures "
                    "(last: %s: %s). Will retry after %.0fs.",
                    self.name,
                    self._failure_count,
                    type(exc).__name__,
                    exc,
                    self.recovery_timeout,
                )
            else:
                logger.warning(
                    "Circuit '%s' failure %d/%d: %s: %s",
                    self.name,
                    self._failure_count,
                    self.failure_threshold,
                    type(exc).__name__,
                    exc,
                )

    def _on_success(self) -> None:
        with self._lock:
            if self._state == CircuitState.HALF_OPEN:
                self._success_count += 1
                if self._success_count >= self.success_threshold:
                    self._transition_to_closed()
                    logger.info(
                        "Circuit '%s' CLOSED after %d successful probe(s)",
                        self.name, self._success_count,
                    )
            elif self._state == CircuitState.CLOSED:
                # Reset rolling failure counter on any success
                if self._failure_count > 0:
                    logger.debug(
                        "Circuit '%s' success — reset failure count (was %d)",
                        self.name, self._failure_count,
                    )
                self._failure_count = 0

    def _transition_to_open(self) -> None:
        self._state = CircuitState.OPEN
        self._opened_at = time.monotonic()

    def _transition_to_closed(self) -> None:
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._opened_at = None
        self._last_failure_exc = None
