"""Tests for :mod:`eaip.throttle.health`."""

from __future__ import annotations

import pytest

from eaip.throttle.health import ThrottleHealthCheck


class TestThrottleHealthCheck:
    """Tests for :class:`eaip.throttle.health.ThrottleHealthCheck`."""

    @pytest.mark.asyncio
    async def test_healthy(self) -> None:
        """Test that the health check returns healthy."""
        check = ThrottleHealthCheck()
        report = await check.check()
        assert report.component == "throttle"
        assert report.status.value == "healthy"
