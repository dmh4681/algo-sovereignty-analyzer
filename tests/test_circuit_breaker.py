"""
Tests for core.circuit_breaker — circuit breaker state machine.
"""

import time
import pytest
from unittest.mock import patch, MagicMock

from core.circuit_breaker import CircuitBreaker, CircuitOpenError, CircuitState


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_breaker(**kwargs) -> CircuitBreaker:
    defaults = dict(
        name="test",
        failure_threshold=3,
        success_threshold=2,
        recovery_timeout=60.0,
    )
    defaults.update(kwargs)
    return CircuitBreaker(**defaults)


def _failing_call():
    raise ConnectionError("simulated network error")


def _success_call():
    return "ok"


# ---------------------------------------------------------------------------
# CLOSED state
# ---------------------------------------------------------------------------

class TestClosedState:
    def test_initial_state_is_closed(self):
        breaker = _make_breaker()
        assert breaker.state == CircuitState.CLOSED

    def test_success_stays_closed(self):
        breaker = _make_breaker()
        result = breaker.call(_success_call)
        assert result == "ok"
        assert breaker.state == CircuitState.CLOSED

    def test_failure_below_threshold_stays_closed(self):
        breaker = _make_breaker(failure_threshold=3)
        for _ in range(2):
            with pytest.raises(ConnectionError):
                breaker.call(_failing_call)
        assert breaker.state == CircuitState.CLOSED

    def test_failure_at_threshold_opens_circuit(self):
        breaker = _make_breaker(failure_threshold=3)
        for _ in range(3):
            with pytest.raises(ConnectionError):
                breaker.call(_failing_call)
        assert breaker.state == CircuitState.OPEN

    def test_success_resets_failure_counter(self):
        breaker = _make_breaker(failure_threshold=3)
        # Two failures then a success should NOT open the circuit
        for _ in range(2):
            with pytest.raises(ConnectionError):
                breaker.call(_failing_call)
        breaker.call(_success_call)
        # One more failure — still below threshold from a clean slate
        with pytest.raises(ConnectionError):
            breaker.call(_failing_call)
        assert breaker.state == CircuitState.CLOSED


# ---------------------------------------------------------------------------
# OPEN state
# ---------------------------------------------------------------------------

class TestOpenState:
    def _open_breaker(self, **kwargs) -> CircuitBreaker:
        breaker = _make_breaker(**kwargs)
        for _ in range(breaker.failure_threshold):
            with pytest.raises(Exception):
                breaker.call(_failing_call)
        assert breaker.state == CircuitState.OPEN
        return breaker

    def test_open_circuit_raises_circuit_open_error(self):
        breaker = self._open_breaker()
        with pytest.raises(CircuitOpenError):
            breaker.call(_success_call)

    def test_circuit_open_error_has_retry_after(self):
        breaker = self._open_breaker(recovery_timeout=60.0)
        try:
            breaker.call(_success_call)
        except CircuitOpenError as e:
            assert e.retry_after > 0
            assert e.retry_after <= 60.0

    def test_call_not_forwarded_when_open(self):
        breaker = self._open_breaker()
        mock_fn = MagicMock(return_value="should not be called")
        with pytest.raises(CircuitOpenError):
            breaker.call(mock_fn)
        mock_fn.assert_not_called()


# ---------------------------------------------------------------------------
# HALF_OPEN state
# ---------------------------------------------------------------------------

class TestHalfOpenState:
    def _open_breaker_at_time(self, monotonic_value: float, **kwargs) -> CircuitBreaker:
        breaker = _make_breaker(**kwargs)
        for _ in range(breaker.failure_threshold):
            with pytest.raises(Exception):
                breaker.call(_failing_call)
        # Patch _opened_at so the recovery timeout appears elapsed
        breaker._opened_at = monotonic_value - breaker.recovery_timeout - 1
        return breaker

    def test_transitions_to_half_open_after_timeout(self):
        breaker = self._open_breaker_at_time(time.monotonic())
        # The transition happens inside call()
        with pytest.raises(ConnectionError):
            breaker.call(_failing_call)
        # Failed probe → back to OPEN (not HALF_OPEN)
        assert breaker.state == CircuitState.OPEN

    def test_successful_probe_increments_success_count(self):
        breaker = self._open_breaker_at_time(time.monotonic(), success_threshold=2)
        # First probe succeeds → HALF_OPEN, success_count = 1
        result = breaker.call(_success_call)
        assert result == "ok"
        assert breaker.state == CircuitState.HALF_OPEN
        assert breaker._success_count == 1

    def test_enough_successes_close_circuit(self):
        breaker = self._open_breaker_at_time(time.monotonic(), success_threshold=2)
        breaker.call(_success_call)  # success 1 → HALF_OPEN
        breaker.call(_success_call)  # success 2 → CLOSED
        assert breaker.state == CircuitState.CLOSED

    def test_failed_probe_reopens_circuit(self):
        breaker = self._open_breaker_at_time(time.monotonic(), success_threshold=2)
        # One success to enter HALF_OPEN properly
        breaker.call(_success_call)
        assert breaker.state == CircuitState.HALF_OPEN
        # Then a failure
        with pytest.raises(ConnectionError):
            breaker.call(_failing_call)
        assert breaker.state == CircuitState.OPEN


# ---------------------------------------------------------------------------
# Manual reset
# ---------------------------------------------------------------------------

class TestReset:
    def test_reset_closes_open_circuit(self):
        breaker = _make_breaker()
        for _ in range(breaker.failure_threshold):
            with pytest.raises(Exception):
                breaker.call(_failing_call)
        assert breaker.state == CircuitState.OPEN
        breaker.reset()
        assert breaker.state == CircuitState.CLOSED

    def test_reset_clears_counters(self):
        breaker = _make_breaker()
        for _ in range(breaker.failure_threshold):
            with pytest.raises(Exception):
                breaker.call(_failing_call)
        breaker.reset()
        assert breaker._failure_count == 0
        assert breaker._success_count == 0
        assert breaker._opened_at is None


# ---------------------------------------------------------------------------
# Excluded exceptions
# ---------------------------------------------------------------------------

class TestExcludedExceptions:
    def test_excluded_exception_does_not_count_as_failure(self):
        breaker = _make_breaker(failure_threshold=3, excluded_exceptions=(ValueError,))

        def bad_input():
            raise ValueError("bad input — client error, not FRED's fault")

        for _ in range(10):
            with pytest.raises(ValueError):
                breaker.call(bad_input)

        # Should still be CLOSED — ValueError is excluded
        assert breaker.state == CircuitState.CLOSED

    def test_non_excluded_exception_counts_as_failure(self):
        breaker = _make_breaker(failure_threshold=3, excluded_exceptions=(ValueError,))

        def network_error():
            raise ConnectionError("server down")

        for _ in range(3):
            with pytest.raises(ConnectionError):
                breaker.call(network_error)

        assert breaker.state == CircuitState.OPEN


# ---------------------------------------------------------------------------
# Status dict
# ---------------------------------------------------------------------------

class TestStatus:
    def test_status_returns_dict_with_required_keys(self):
        breaker = _make_breaker()
        s = breaker.status()
        assert s["name"] == "test"
        assert s["state"] == "closed"
        assert "failure_count" in s
        assert "success_count" in s
        assert "failure_threshold" in s
        assert "success_threshold" in s
        assert "recovery_timeout" in s

    def test_open_status_includes_retry_info(self):
        breaker = _make_breaker()
        for _ in range(breaker.failure_threshold):
            with pytest.raises(Exception):
                breaker.call(_failing_call)
        s = breaker.status()
        assert s["state"] == "open"
        assert "seconds_open" in s
        assert "retry_in" in s


# ---------------------------------------------------------------------------
# FRED API integration — _fetch_from_fred uses the circuit breaker
# ---------------------------------------------------------------------------

class TestFredIntegration:
    """Verify that inflation_data._fetch_from_fred propagates circuit breaker behaviour."""

    def test_fetch_returns_none_when_circuit_open(self):
        """When the FRED circuit is OPEN, _fetch_from_fred must return None gracefully."""
        from core import inflation_data

        # Force the circuit open
        original_state = inflation_data._fred_circuit_breaker._state
        inflation_data._fred_circuit_breaker._state = CircuitState.OPEN
        inflation_data._fred_circuit_breaker._opened_at = time.monotonic()

        try:
            with patch.dict("os.environ", {"FRED_API_KEY": "dummy"}):
                result = inflation_data._fetch_from_fred("CPIAUCSL")
            assert result is None
        finally:
            inflation_data._fred_circuit_breaker.reset()

    def test_fetch_returns_none_when_no_api_key(self):
        from core import inflation_data
        import os
        with patch.dict("os.environ", {}, clear=True):
            # Ensure FRED_API_KEY is absent
            os.environ.pop("FRED_API_KEY", None)
            # Re-evaluate the module-level constant via a fresh call
            with patch.object(inflation_data, "FRED_API_KEY", ""):
                result = inflation_data._fetch_from_fred("CPIAUCSL")
        assert result is None

    def test_fetch_records_failure_on_network_error(self):
        """A network error in _do_fred_request should increment the breaker's failure count."""
        from core import inflation_data

        inflation_data._fred_circuit_breaker.reset()
        initial_failures = inflation_data._fred_circuit_breaker._failure_count

        with patch.object(inflation_data, "FRED_API_KEY", "dummy"), \
             patch("core.inflation_data._do_fred_request", side_effect=ConnectionError("down")):
            result = inflation_data._fetch_from_fred("CPIAUCSL")

        assert result is None
        # After 3 retries all failing, failure_count should have increased
        assert inflation_data._fred_circuit_breaker._failure_count > initial_failures
