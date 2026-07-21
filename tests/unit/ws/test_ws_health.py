from __future__ import annotations

import anyio
import pytest

from eaip.ws.health import WsHealthCheck


class TestWsHealth:
    @pytest.mark.asyncio
    async def test_healthy(self) -> None:
        check = WsHealthCheck(active_connections=5, active_channels=3)
        report = await check.check()
        assert report.component == "websocket"
        assert report.status.value == "healthy"
        assert "5 connection(s)" in report.message

    @pytest.mark.asyncio
    async def test_degraded_zero_connections(self) -> None:
        check = WsHealthCheck(active_connections=0, active_channels=0)
        report = await check.check()
        assert report.status.value == "healthy"

    def test_name(self) -> None:
        check = WsHealthCheck()
        assert check.name == "websocket"

    def test_properties(self) -> None:
        check = WsHealthCheck(active_connections=10, active_channels=5)
        assert check.active_connections == 10
        assert check.active_channels == 5

    def test_defaults(self) -> None:
        check = WsHealthCheck()
        assert check.active_connections == 0
        assert check.active_channels == 0

    def test_details_in_report(self) -> None:
        check = WsHealthCheck(active_connections=3, active_channels=2)
        report = anyio.run(check.check)
        assert report.details["active_connections"] == 3
        assert report.details["active_channels"] == 2
