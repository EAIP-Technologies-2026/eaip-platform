"""Tests for :mod:`eaip.curation.health`."""

from __future__ import annotations

import pytest

from eaip.curation.health import CurationHealthCheck


class TestCurationHealthCheck:
    @pytest.mark.asyncio
    async def test_healthy_few_pending(self) -> None:
        check = CurationHealthCheck(pending_count=3, total_submissions=100)
        report = await check.check()
        assert report.component == "curation"
        assert report.status.value == "healthy"

    @pytest.mark.asyncio
    async def test_degraded_many_pending(self) -> None:
        check = CurationHealthCheck(pending_count=15, total_submissions=100)
        report = await check.check()
        assert report.status.value == "degraded"
        assert "pending" in report.message

    @pytest.mark.asyncio
    async def test_details(self) -> None:
        check = CurationHealthCheck(pending_count=5, total_submissions=50)
        report = await check.check()
        assert report.details["pending_count"] == 5
        assert report.details["total_submissions"] == 50
