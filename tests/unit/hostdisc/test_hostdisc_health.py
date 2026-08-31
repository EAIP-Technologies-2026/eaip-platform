"""Tests for :mod:`eaip.hostdisc.health`."""

from __future__ import annotations

import pytest

from eaip.hostdisc.health import HostDiscoveryHealthCheck


class TestHostDiscoveryHealthCheck:
    @pytest.mark.asyncio
    async def test_healthy(self) -> None:
        check = HostDiscoveryHealthCheck()
        report = await check.check()
        assert report.component == "hostdisc"
        assert report.status.value == "healthy"
