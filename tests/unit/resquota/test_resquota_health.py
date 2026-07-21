"""Tests for :mod:`eaip.resquota.health`."""

from __future__ import annotations

import pytest

from eaip.resquota.health import QuotaHealthCheck


class TestQuotaHealthCheck:
    """Tests for :class:`eaip.resquota.health.QuotaHealthCheck`."""

    @pytest.mark.asyncio
    async def test_healthy(self) -> None:
        """Test that the health check returns healthy."""
        check = QuotaHealthCheck()
        report = await check.check()
        assert report.component == "resquota"
        assert report.status.value == "healthy"
