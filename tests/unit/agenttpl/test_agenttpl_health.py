"""Tests for :mod:`eaip.agenttpl.health`."""

from __future__ import annotations

import pytest

from eaip.agenttpl.health import AgentTemplateHealthCheck


class TestAgentTemplateHealthCheck:
    """Tests for :class:`eaip.agenttpl.health.AgentTemplateHealthCheck`."""

    @pytest.mark.asyncio
    async def test_healthy(self) -> None:
        """Test that the health check returns healthy."""
        check = AgentTemplateHealthCheck()
        report = await check.check()
        assert report.component == "agenttpl"
        assert report.status.value == "healthy"
