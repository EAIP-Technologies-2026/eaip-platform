"""Adapter that wraps the platform's CircuitBreaker for mesh-level circuit breaking."""

from __future__ import annotations

from typing import Any

from eaip.logging.context import get_logger
from eaip.mesh.events import CircuitBreakerReset, CircuitBreakerTripped
from eaip.mesh.exceptions import CircuitBreakerOpenError
from eaip.resilience.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitState,
)


class CircuitBreakerIntegration:
    """Integrates circuit breakers with the service mesh.

    Wraps :class:`eaip.resilience.circuit_breaker.CircuitBreaker` per service
    and emits domain events on state transitions.
    """

    def __init__(self, event_bus: Any = None) -> None:
        self._breakers: dict[str, CircuitBreaker] = {}
        self._log = get_logger("eaip.mesh.circuit_integration")
        self._event_bus = event_bus

    def integrate_circuit_breaker(
        self,
        service_name: str,
        config: dict[str, Any] | None = None,
    ) -> CircuitBreaker:
        if config is None:
            config = {}
        cb_config = CircuitBreakerConfig(
            failure_threshold=config.get("failure_threshold", 5),
            recovery_timeout_seconds=config.get("recovery_timeout_seconds", 30.0),
            half_open_max_attempts=config.get("half_open_max_attempts", 3),
            consecutive_successes_to_close=config.get("consecutive_successes_to_close", 2),
        )
        cb = CircuitBreaker(service_name, cb_config)
        self._breakers[service_name] = cb
        self._log.info("circuit.integrated", service=service_name)
        return cb

    def check_circuit(self, service_name: str) -> CircuitBreaker:
        cb = self._breakers.get(service_name)
        if cb is None:
            cb = self.integrate_circuit_breaker(service_name)
        state = cb.state
        if state is CircuitState.OPEN:
            raise CircuitBreakerOpenError(
                f"Circuit breaker is open for {service_name!r}.",
                context={"service_name": service_name},
            )
        return cb

    def record_success(self, service_name: str) -> None:
        cb = self._breakers.get(service_name)
        if cb is None:
            return
        was_open = cb.state is CircuitState.OPEN
        cb._on_success()
        if was_open and cb.state is CircuitState.CLOSED and self._event_bus is not None:
            self._event_bus.publish(CircuitBreakerReset(service_name=service_name))

    def record_failure(self, service_name: str) -> None:
        cb = self._breakers.get(service_name)
        if cb is None:
            cb = self.integrate_circuit_breaker(service_name)
        was_closed = cb.state is CircuitState.CLOSED
        cb._on_failure()
        if was_closed and cb.state is CircuitState.OPEN:
            if self._event_bus is not None:
                self._event_bus.publish(
                    CircuitBreakerTripped(
                        service_name=service_name,
                        failure_count=cb.get_metrics().get("failure_count", 0) or 0,  # type: ignore[arg-type]
                    )
                )

    def get_circuit_state(self, service_name: str) -> CircuitState | None:
        cb = self._breakers.get(service_name)
        if cb is None:
            return None
        return cb.state

    def get_breaker(self, service_name: str) -> CircuitBreaker | None:
        return self._breakers.get(service_name)


__all__ = ["CircuitBreakerIntegration"]
