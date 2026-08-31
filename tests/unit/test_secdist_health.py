"""Tests for :mod:`eaip.secdist.health`."""

from __future__ import annotations

import pytest

from eaip.secdist.health import SecdistHealthCheck


class TestSecdistHealthCheck:
    @pytest.mark.asyncio
    async def test_healthy_with_targets(self) -> None:
        check = SecdistHealthCheck(target_count=3, distribution_count=10)
        report = await check.check()
        assert report.component == "secdist"
        assert report.status.value == "healthy"

    @pytest.mark.asyncio
    async def test_degraded_no_targets(self) -> None:
        check = SecdistHealthCheck(target_count=0, distribution_count=0)
        report = await check.check()
        assert report.component == "secdist"
        assert report.status.value == "degraded"

    @pytest.mark.asyncio
    async def test_details_included(self) -> None:
        check = SecdistHealthCheck(target_count=2, distribution_count=5)
        report = await check.check()
        assert report.details["target_count"] == 2
        assert report.details["distribution_count"] == 5
