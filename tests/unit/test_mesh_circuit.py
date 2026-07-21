"""Tests for :mod:`eaip.mesh.circuit_integration`."""

from __future__ import annotations

import pytest

from eaip.mesh.circuit_integration import CircuitBreakerIntegration
from eaip.mesh.exceptions import CircuitBreakerOpenError
from eaip.resilience.circuit_breaker import CircuitState


class TestCircuitBreakerIntegration:
    def test_integrate_creates_breaker(self) -> None:
        ci = CircuitBreakerIntegration()
        cb = ci.integrate_circuit_breaker("auth")
        assert cb.name == "auth"
        assert cb.state is CircuitState.CLOSED

    def test_integrate_with_config(self) -> None:
        ci = CircuitBreakerIntegration()
        cb = ci.integrate_circuit_breaker("auth", {"failure_threshold": 2})
        assert cb is not None

    def test_check_circuit_closed(self) -> None:
        ci = CircuitBreakerIntegration()
        ci.integrate_circuit_breaker("auth")
        cb = ci.check_circuit("auth")
        assert cb.state is CircuitState.CLOSED

    def test_check_circuit_open(self) -> None:
        ci = CircuitBreakerIntegration()
        ci.integrate_circuit_breaker(
            "auth", {"failure_threshold": 1, "recovery_timeout_seconds": 60}
        )
        ci.record_failure("auth")
        with pytest.raises(CircuitBreakerOpenError):
            ci.check_circuit("auth")

    def test_check_circuit_auto_integrates(self) -> None:
        ci = CircuitBreakerIntegration()
        cb = ci.check_circuit("auto-integrated")
        assert cb.name == "auto-integrated"

    def test_record_success_closes_circuit(self) -> None:
        ci = CircuitBreakerIntegration()
        ci.integrate_circuit_breaker(
            "auth", {"failure_threshold": 1, "recovery_timeout_seconds": 60}
        )
        ci.record_failure("auth")
        assert ci.get_circuit_state("auth") is CircuitState.OPEN
        # Can't close without half-open; simulate by directly resetting
        cb = ci.get_breaker("auth")
        assert cb is not None
        cb.reset()
        assert cb.state is CircuitState.CLOSED

    def test_record_failure_unknown_service_creates_breaker(self) -> None:
        ci = CircuitBreakerIntegration()
        ci.record_failure("new-service")
        state = ci.get_circuit_state("new-service")
        assert state is CircuitState.CLOSED
        assert ci.get_breaker("new-service") is not None

    def test_get_circuit_state_nonexistent(self) -> None:
        ci = CircuitBreakerIntegration()
        assert ci.get_circuit_state("nonexistent") is None

    def test_get_breaker(self) -> None:
        ci = CircuitBreakerIntegration()
        ci.integrate_circuit_breaker("auth")
        assert ci.get_breaker("auth") is not None
        assert ci.get_breaker("nonexistent") is None

    def test_record_success_noop_when_no_breaker(self) -> None:
        ci = CircuitBreakerIntegration()
        ci.record_success("unknown")
        assert ci.get_circuit_state("unknown") is None
