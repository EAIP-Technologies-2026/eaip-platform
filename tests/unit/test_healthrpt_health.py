"""Tests for :mod:`eaip.healthrpt.health`."""

from __future__ import annotations

import pytest

from eaip.healthrpt.health import HealthRptHealthCheck


class TestHealthRptHealthCheck:
    @pytest.mark.asyncio
    async def test_healthy(self) -> None:
        check = HealthRptHealthCheck(component_count=5, report_count=20)
        report = await check.check()
        assert report.component == "healthrpt"
        assert report.status.value == "healthy"

    @pytest.mark.asyncio
    async def test_empty(self) -> None:
        check = HealthRptHealthCheck(component_count=0, report_count=0)
        report = await check.check()
        assert report.status.value == "healthy"

    @pytest.mark.asyncio
    async def test_details(self) -> None:
        check = HealthRptHealthCheck(component_count=3, report_count=15)
        report = await check.check()
        assert report.details["component_count"] == 3
        assert report.details["report_count"] == 15
