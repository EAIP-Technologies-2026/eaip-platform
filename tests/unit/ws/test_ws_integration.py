from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from eaip.ws.channel_manager import ChannelManager
from eaip.ws.connection_manager import ConnectionManager
from eaip.ws.integration import WsRuntimeModule
from eaip.ws.push_service import PushService


class TestWsIntegration:
    def test_default_initialization(self) -> None:
        mod = WsRuntimeModule()
        assert mod.name == "websocket"
        assert isinstance(mod.connection_manager, ConnectionManager)
        assert isinstance(mod.channel_manager, ChannelManager)
        assert isinstance(mod.push_service, PushService)

    def test_custom_initialization(self) -> None:
        cm = ConnectionManager()
        chm = ChannelManager()
        ps = PushService(channel_manager=chm, connection_manager=cm)
        mod = WsRuntimeModule(
            connection_manager=cm,
            channel_manager=chm,
            push_service=ps,
        )
        assert mod.connection_manager is cm
        assert mod.channel_manager is chm
        assert mod.push_service is ps

    def test_startup_duration_default(self) -> None:
        mod = WsRuntimeModule()
        assert mod.startup_duration == 0.0

    @pytest.mark.asyncio
    async def test_start_with_kernel(self) -> None:
        mod = WsRuntimeModule()
        kernel = MagicMock()
        kernel.platform.health.register = MagicMock()
        await mod.start(kernel)
        assert mod.startup_duration > 0.0
        kernel.platform.health.register.assert_called_once()

    @pytest.mark.asyncio
    async def test_stop(self) -> None:
        mod = WsRuntimeModule()
        await mod.stop()

    @pytest.mark.asyncio
    async def test_start_without_kernel(self) -> None:
        mod = WsRuntimeModule()
        await mod.start()
        assert mod.startup_duration > 0.0

    @pytest.mark.asyncio
    async def test_health_check_registration(self) -> None:
        mod = WsRuntimeModule()
        kernel = MagicMock()
        kernel.platform.health.register = MagicMock()
        await mod.start(kernel)
        registered_check = kernel.platform.health.register.call_args[0][0]
        assert registered_check.name == "websocket"
