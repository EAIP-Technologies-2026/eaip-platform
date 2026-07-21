"""Tests for :mod:`eaip.xbridge.health`."""

from __future__ import annotations

import pytest

from eaip.xbridge.health import XBridgeHealthCheck


class TestXBridgeHealthCheck:
    @pytest.mark.asyncio
    async def test_healthy_with_connectors_and_routes(self) -> None:
        check = XBridgeHealthCheck(connector_count=3, route_count=5)
        report = await check.check()
        assert report.component == "xbridge"
        assert report.status.value == "healthy"

    @pytest.mark.asyncio
    async def test_degraded_no_connectors(self) -> None:
        check = XBridgeHealthCheck(connector_count=0, route_count=0)
        report = await check.check()
        assert report.status.value == "degraded"
        assert "No connectors" in report.message

    @pytest.mark.asyncio
    async def test_degraded_no_routes(self) -> None:
        check = XBridgeHealthCheck(connector_count=2, route_count=0)
        report = await check.check()
        assert report.status.value == "degraded"
        assert "No bridge routes" in report.message

    @pytest.mark.asyncio
    async def test_details(self) -> None:
        check = XBridgeHealthCheck(connector_count=2, route_count=3)
        report = await check.check()
        assert report.details["connector_count"] == 2
        assert report.details["route_count"] == 3
