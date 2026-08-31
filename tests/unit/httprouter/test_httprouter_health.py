"""Tests for :mod:`eaip.httprouter.health`."""

from __future__ import annotations

import pytest

from eaip.httprouter.health import HTTPRouterHealthCheck


class TestHTTPRouterHealthCheck:
    @pytest.mark.asyncio
    async def test_healthy(self) -> None:
        check = HTTPRouterHealthCheck()
        report = await check.check()
        assert report.component == "httprouter"
        assert report.status.value == "healthy"
