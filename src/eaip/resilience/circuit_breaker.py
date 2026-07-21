"""Circuit breaker pattern for fault-tolerant execution."""

from __future__ import annotations

import time
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict

from eaip.logging.context import get_logger


class CircuitState(StrEnum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreakerConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    failure_threshold: int = 5
    recovery_timeout_seconds: float = 30.0
    half_open_max_attempts: int = 3
    consecutive_successes_to_close: int = 2


class CircuitBreaker:
    """Circuit breaker for protecting downstream services from cascading failures."""

    def __init__(
        self,
        name: str,
        config: CircuitBreakerConfig | None = None,
        *,
        event_bus: Any = None,
        meter: Any = None,
    ) -> None:
        self._name = name
        self._config = config or CircuitBreakerConfig()
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time: float = 0.0
        self._last_state_change: float = time.monotonic()
        self._event_bus = event_bus
        self._meter = meter
        self._log = get_logger(f"eaip.resilience.circuit_breaker.{name}")

    @property
    def name(self) -> str:
        return self._name

    @property
    def state(self) -> CircuitState:
        if self._state is CircuitState.OPEN:
            if time.monotonic() - self._last_state_change >= self._config.recovery_timeout_seconds:
                self._transition(CircuitState.HALF_OPEN)
        return self._state

    async def call(self, coro_fn: Any, fallback: Any = None) -> Any:
        current = self.state
        if current is CircuitState.OPEN:
            self._log.warning("circuit.open", name=self._name)
            if fallback is not None:
                return fallback() if callable(fallback) else fallback
            raise CircuitBreakerOpenError(self._name)

        coro = coro_fn() if callable(coro_fn) else coro_fn
        try:
            result = await coro
            self._on_success()
            return result
        except Exception:
            self._on_failure()
            if fallback is not None:
                return fallback() if callable(fallback) else fallback
            raise

    def _on_success(self) -> None:
        if self._state is CircuitState.HALF_OPEN:
            self._success_count += 1
            if self._success_count >= self._config.consecutive_successes_to_close:
                self._transition(CircuitState.CLOSED)
        else:
            self._failure_count = max(0, self._failure_count - 1)

    def _on_failure(self) -> None:
        self._failure_count += 1
        self._last_failure_time = time.monotonic()
        if (
            self._state is CircuitState.HALF_OPEN
            or self._failure_count >= self._config.failure_threshold
        ):
            self._transition(CircuitState.OPEN)

    def _transition(self, new_state: CircuitState) -> None:
        old_state = self._state
        self._state = new_state
        self._last_state_change = time.monotonic()
        if new_state is CircuitState.CLOSED:
            self._failure_count = 0
            self._success_count = 0
        self._log.info(
            "circuit.transition",
            name=self._name,
            from_state=old_state,
            to_state=new_state,
        )

    def reset(self) -> None:
        self._transition(CircuitState.CLOSED)

    def get_metrics(self) -> dict[str, object]:
        return {
            "name": self._name,
            "state": self._state.value,
            "failure_count": self._failure_count,
            "success_count": self._success_count,
            "last_failure_time": self._last_failure_time,
        }


class CircuitBreakerOpenError(Exception):
    def __init__(self, name: str) -> None:
        self.circuit_name = name
        super().__init__(f"circuit breaker {name!r} is open")


__all__ = [
    "CircuitBreaker",
    "CircuitBreakerConfig",
    "CircuitBreakerOpenError",
    "CircuitState",
]
