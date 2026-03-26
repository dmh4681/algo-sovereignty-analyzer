"""
Circuit Breaker Pattern - Protect external API calls from cascading failures.

States:
  CLOSED    — Normal operation; requests pass through. Failures are counted.
  OPEN      — Too many failures recorded; requests are immediately rejected
              without hitting the remote service. A recovery timeout is started.
  HALF_OPEN — Recovery timeout expired; one probe request is allowed through.
              Success → CLOSED (counters reset).
              Failure → OPEN (timeout restarts).

Usage::

    breaker = CircuitBreaker(
        name="fred-api",
        failure_threshold=5,     # open after 5 consecutive failures
        success_threshold=2,     # close after 2 consecutive successes in HALF_OPEN
        recovery_timeout=60.0,   # seconds before attempting a probe in OPEN
    )

    try:
        result = breaker.call(lambda: requests.get(...))
    except CircuitOpenError:
        # Fast-fail: use cached data or return None
        result = None
    except Exception:
        # Actual error from the remote call
        raise
"""

import logging
import threading
import time
from enum import Enum
from typing import Callable, Optional, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitOpenError(Exception):
    """Raised when a call is rejected because the circuit is OPEN."""

    def __init__(self, name: str, retry_after: float) -> None:
        self.name = name
        self.retry_after = retry_after
        super().__init__(
            f"Circuit '{name}' is OPEN. Retry after {retry_after:.1f}s."
        )


class CircuitBreaker:
    """
    Thread-safe circuit breaker for protecting external API calls.

    Args:
        name: Human-readable identifier used in log messages.
        failure_threshold: Number of consecutive failures that trip the circuit
            to OPEN. Default: 5.
        success_threshold: Number of consecutive successes in HALF_OPEN needed
            to close the circuit again. Default: 2.
        recovery_timeout: Seconds to wait in OPEN state before allowing a probe
            request (transition to HALF_OPEN). Default: 60.0.
        excluded_exceptions: Exception types that should *not* count as failures
            (e.g. ValueError for bad input — the API itself is not at fault).
    """

    def __init__(
        self,
        name: str,
        *,
        failure_threshold: int = 5,
        success_threshold: int = 2,
        recovery_timeout: float = 60.0,
        excluded_exceptions: tuple = (),
    ) -> None:
        self.name = name
        self.failure_threshold = failure_threshold
        self.success_threshold = success_threshold
        self.recovery_timeout = recovery_timeout
        self.excluded_exceptions = excluded_exceptions

        self._state = CircuitState.CLOSED
        self._failure_count: int = 0
        self._success_count: int = 0
        self._opened_at: Optional[float] = None
        self._lock = threading.Lock()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def state(self) -> CircuitState:
        return self._state

    def call(self, func: Callable[[], T]) -> T:
        """
        Execute *func* through the circuit breaker.

        Raises:
            CircuitOpenError: If the circuit is OPEN and the recovery timeout
                has not yet elapsed.
            Exception: Any exception raised by *func* itself (after the breaker
                records the failure).
        """
        with self._lock:
            self._maybe_transition_to_half_open()

            if self._state == CircuitState.OPEN:
                elapsed = time.monotonic() - self._opened_at  # type: ignore[operator]
                retry_after = max(0.0, self.recovery_timeout - elapsed)
                raise CircuitOpenError(self.name, retry_after)

        # Execute the call *outside* the lock so we don't block other threads
        # for the duration of the network request.
        try:
            result = func()
        except Exception as exc:
            if not isinstance(exc, self.excluded_exceptions):
                self._record_failure(exc)
            raise

        self._record_success()
        return result

    def reset(self) -> None:
        """Manually close the circuit and reset all counters (e.g. after maintenance)."""
        with self._lock:
            self._transition_to(CircuitState.CLOSED)

    # ------------------------------------------------------------------
    # State machine helpers (must be called with self._lock held)
    # ------------------------------------------------------------------

    def _maybe_transition_to_half_open(self) -> None:
        """If OPEN and recovery timeout has elapsed, move to HALF_OPEN."""
        if self._state == CircuitState.OPEN:
            elapsed = time.monotonic() - self._opened_at  # type: ignore[operator]
            if elapsed >= self.recovery_timeout:
                self._transition_to(CircuitState.HALF_OPEN)

    def _record_failure(self, exc: Exception) -> None:
        with self._lock:
            self._success_count = 0
            self._failure_count += 1
            logger.warning(
                "Circuit '%s' — failure %d/%d: %s: %s",
                self.name,
                self._failure_count,
                self.failure_threshold,
                type(exc).__name__,
                exc,
            )
            if self._state == CircuitState.HALF_OPEN:
                # Any single failure in HALF_OPEN immediately reopens the circuit.
                self._transition_to(CircuitState.OPEN)
            elif self._state == CircuitState.CLOSED:
                if self._failure_count >= self.failure_threshold:
                    self._transition_to(CircuitState.OPEN)

    def _record_success(self) -> None:
        with self._lock:
            self._failure_count = 0
            if self._state == CircuitState.HALF_OPEN:
                self._success_count += 1
                logger.info(
                    "Circuit '%s' — probe success %d/%d in HALF_OPEN",
                    self.name,
                    self._success_count,
                    self.success_threshold,
                )
                if self._success_count >= self.success_threshold:
                    self._transition_to(CircuitState.CLOSED)
            # In CLOSED state successes just keep the failure counter at 0

    def _transition_to(self, new_state: CircuitState) -> None:
        """Perform state transition and emit a log line."""
        old_state = self._state
        self._state = new_state

        if new_state == CircuitState.OPEN:
            self._opened_at = time.monotonic()
            self._success_count = 0
            logger.error(
                "Circuit '%s' OPENED after %d failure(s). "
                "No FRED API calls for %.0fs.",
                self.name,
                self._failure_count,
                self.recovery_timeout,
            )
        elif new_state == CircuitState.HALF_OPEN:
            self._success_count = 0
            logger.info(
                "Circuit '%s' → HALF_OPEN (recovery timeout elapsed). "
                "Sending probe request.",
                self.name,
            )
        elif new_state == CircuitState.CLOSED:
            self._failure_count = 0
            self._success_count = 0
            self._opened_at = None
            logger.info(
                "Circuit '%s' CLOSED (was %s). Normal operation resumed.",
                self.name,
                old_state.value,
            )

    # ------------------------------------------------------------------
    # Diagnostics
    # ------------------------------------------------------------------

    def status(self) -> dict:
        """Return a snapshot of the breaker's current state for health checks."""
        with self._lock:
            info: dict = {
                "name": self.name,
                "state": self._state.value,
                "failure_count": self._failure_count,
                "success_count": self._success_count,
                "failure_threshold": self.failure_threshold,
                "success_threshold": self.success_threshold,
                "recovery_timeout": self.recovery_timeout,
            }
            if self._opened_at is not None:
                elapsed = time.monotonic() - self._opened_at
                info["seconds_open"] = round(elapsed, 1)
                info["retry_in"] = round(
                    max(0.0, self.recovery_timeout - elapsed), 1
                )
            return info
