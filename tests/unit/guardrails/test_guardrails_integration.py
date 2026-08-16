"""Tests for :mod:`eaip.guardrails.integration`."""

from __future__ import annotations

from typing import Any

import pytest

from eaip.guardrails.health import GuardrailHealthCheck
from eaip.guardrails.integration import GuardrailRuntimeModule


class _MockHealthReporter:
    def __init__(self) -> None:
        self.registered: list[Any] = []

    def register(self, check: Any) -> None:
        self.registered.append(check)


class _MockPlatform:
    def __init__(self) -> None:
        self.health = _MockHealthReporter()


class _MockKernel:
    def __init__(self) -> None:
        self._platform = _MockPlatform()

    @property
    def platform(self) -> _MockPlatform:
        return self._platform


class TestGuardrailRuntimeModule:
    """Tests for :class:`eaip.guardrails.integration.GuardrailRuntimeModule`."""

    def test_instantiation(self) -> None:
        """Test creating a module instance."""
        module = GuardrailRuntimeModule()
        assert module.name == "guardrails"
        assert isinstance(module.health_check, GuardrailHealthCheck)

    @pytest.mark.asyncio
    async def test_health_check_healthy(self) -> None:
        """Test that the health check returns healthy."""
        module = GuardrailRuntimeModule()
        report = await module.health_check.check()
        assert report.component == "guardrails"
        assert report.status.value == "healthy"

    @pytest.mark.asyncio
    async def test_start_initializes_engine(self) -> None:
        """Test that start() initializes the GuardrailsEngine."""
        module = GuardrailRuntimeModule()
        kernel = _MockKernel()
        await module.start(kernel)
        assert module.engine is not None
        assert len(kernel.platform.health.registered) == 1

    @pytest.mark.asyncio
    async def test_start_registers_health_check(self) -> None:
        """Test that start() registers the health check."""
        module = GuardrailRuntimeModule()
        kernel = _MockKernel()
        await module.start(kernel)
        registered = kernel.platform.health.registered[0]
        assert isinstance(registered, GuardrailHealthCheck)
