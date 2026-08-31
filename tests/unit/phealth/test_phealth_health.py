"""Tests for :mod:`eaip.phealth.health`."""

from __future__ import annotations

import pytest

from eaip.phealth.health import PlatformHealthHealthCheck


class TestPlatformHealthHealthCheck:
    """Tests for :class:`eaip.phealth.health.PlatformHealthHealthCheck`."""

    @pytest.mark.asyncio
    async def test_healthy(self) -> None:
        """Test that the health check returns healthy."""
        check = PlatformHealthHealthCheck()
        report = await check.check()
        assert report.component == "phealth"
        assert report.status.value == "healthy"
