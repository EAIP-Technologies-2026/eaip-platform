"""Tests for :mod:`eaip.helmrepo.health`."""

from __future__ import annotations

import pytest

from eaip.helmrepo.health import HelmChartHealthCheck


class TestHelmChartHealthCheck:
    @pytest.mark.asyncio
    async def test_healthy(self) -> None:
        check = HelmChartHealthCheck()
        report = await check.check()
        assert report.component == "helmrepo"
        assert report.status.value == "healthy"
