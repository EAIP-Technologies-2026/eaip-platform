"""Tests for :mod:`eaip.agentperf.health`."""

from __future__ import annotations

import pytest

from eaip.agentperf.health import AgentPerfHealthCheck


class TestAgentPerfHealthCheck:
    @pytest.mark.asyncio
    async def test_healthy(self) -> None:
        check = AgentPerfHealthCheck(execution_count=100, agent_count=5)
        report = await check.check()
        assert report.component == "agentperf"
        assert report.status.value == "healthy"

    @pytest.mark.asyncio
    async def test_empty(self) -> None:
        check = AgentPerfHealthCheck(execution_count=0, agent_count=0)
        report = await check.check()
        assert report.status.value == "healthy"

    @pytest.mark.asyncio
    async def test_details(self) -> None:
        check = AgentPerfHealthCheck(execution_count=50, agent_count=3)
        report = await check.check()
        assert report.details["execution_count"] == 50
        assert report.details["agent_count"] == 3
