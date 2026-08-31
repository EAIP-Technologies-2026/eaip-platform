"""Tests for circuit breaker."""

from __future__ import annotations

import pytest

from eaip.resilience.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitBreakerOpenError,
    CircuitState,
)


async def _ok() -> str:
    return "ok"


async def _fail() -> None:
    raise RuntimeError("fail")


class TestCircuitBreaker:
    @pytest.mark.asyncio
    async def test_initial_state_closed(self) -> None:
        cb = CircuitBreaker("test")
        assert cb.state is CircuitState.CLOSED

    @pytest.mark.asyncio
    async def test_successful_call(self) -> None:
        cb = CircuitBreaker("test")
        result = await cb.call(_ok)
        assert result == "ok"
        assert cb.state is CircuitState.CLOSED

    @pytest.mark.asyncio
    async def test_opens_after_threshold(self) -> None:
        cb = CircuitBreaker(
            "test",
            CircuitBreakerConfig(failure_threshold=3, recovery_timeout_seconds=60),
        )

        for _ in range(3):
            with pytest.raises(RuntimeError):
                await cb.call(_fail)
        assert cb.state is CircuitState.OPEN

    @pytest.mark.asyncio
    async def test_open_rejects_immediately(self) -> None:
        cb = CircuitBreaker(
            "test",
            CircuitBreakerConfig(failure_threshold=1, recovery_timeout_seconds=60),
        )

        with pytest.raises(RuntimeError):
            await cb.call(_fail)
        with pytest.raises(CircuitBreakerOpenError):
            await cb.call(_ok)

    @pytest.mark.asyncio
    async def test_fallback_on_open(self) -> None:
        cb = CircuitBreaker(
            "test",
            CircuitBreakerConfig(failure_threshold=1, recovery_timeout_seconds=60),
        )

        with pytest.raises(RuntimeError):
            await cb.call(_fail)

        result = await cb.call(_fail, fallback="fallback_value")
        assert result == "fallback_value"

    @pytest.mark.asyncio
    async def test_reset(self) -> None:
        cb = CircuitBreaker(
            "test",
            CircuitBreakerConfig(failure_threshold=1, recovery_timeout_seconds=60),
        )

        with pytest.raises(RuntimeError):
            await cb.call(_fail)
        assert cb.state is CircuitState.OPEN
        cb.reset()
        assert cb.state is CircuitState.CLOSED

    def test_get_metrics(self) -> None:
        cb = CircuitBreaker("test")
        metrics = cb.get_metrics()
        assert metrics["name"] == "test"
        assert metrics["state"] == "closed"
