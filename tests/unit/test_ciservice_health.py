"""Tests for :mod:`eaip.ciservice.health`."""

from __future__ import annotations

import pytest

from eaip.ciservice.health import CIHealthCheck


class TestCIHealthCheck:
    @pytest.mark.asyncio
    async def test_healthy_with_pipelines(self) -> None:
        check = CIHealthCheck(pipeline_count=3, active_builds=2)
        report = await check.check()
        assert report.component == "ciservice"
        assert report.status.value == "healthy"

    @pytest.mark.asyncio
    async def test_degraded_no_pipelines(self) -> None:
        check = CIHealthCheck(pipeline_count=0, active_builds=0)
        report = await check.check()
        assert report.status.value == "degraded"
        assert "No pipelines configured" in report.message

    @pytest.mark.asyncio
    async def test_details(self) -> None:
        check = CIHealthCheck(pipeline_count=5, active_builds=1)
        report = await check.check()
        assert report.details["pipeline_count"] == 5
        assert report.details["active_builds"] == 1
