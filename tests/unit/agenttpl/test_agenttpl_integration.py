"""Tests for :mod:`eaip.agenttpl.integration`."""

from __future__ import annotations

import pytest

from eaip.agenttpl.health import AgentTemplateHealthCheck
from eaip.agenttpl.integration import AgentTemplateRuntimeModule


class TestAgentTemplateRuntimeModule:
    """Tests for :class:`eaip.agenttpl.integration.AgentTemplateRuntimeModule`."""

    def test_instantiation(self) -> None:
        """Test creating a module instance."""
        module = AgentTemplateRuntimeModule()
        assert module.name == "agenttpl"
        assert isinstance(module.health_check, AgentTemplateHealthCheck)

    @pytest.mark.asyncio
    async def test_health_check_healthy(self) -> None:
        """Test that the health check returns healthy."""
        module = AgentTemplateRuntimeModule()
        report = await module.health_check.check()
        assert report.component == "agenttpl"
        assert report.status.value == "healthy"
