"""Tests for :mod:`eaip.guardrails.integration`."""

from __future__ import annotations

import pytest

from eaip.guardrails.health import GuardrailHealthCheck
from eaip.guardrails.integration import GuardrailRuntimeModule


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
