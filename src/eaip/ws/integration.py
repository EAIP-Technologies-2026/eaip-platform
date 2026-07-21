"""Integration layer — WsRuntimeModule for kernel lifecycle."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

from eaip.health.checks import HealthCheck
from eaip.logging.context import get_logger
from eaip.ws.channel_manager import ChannelManager
from eaip.ws.connection_manager import ConnectionManager
from eaip.ws.health import WsHealthCheck
from eaip.ws.push_service import PushService

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel


class WsRuntimeModule:
    """RuntimeModule that bootstraps the WebSocket subsystem during kernel start."""

    name: str = "websocket"

    def __init__(
        self,
        connection_manager: ConnectionManager | None = None,
        channel_manager: ChannelManager | None = None,
        push_service: PushService | None = None,
    ) -> None:
        """Initialize with optional managers."""
        self._connection_manager = connection_manager or ConnectionManager()
        self._channel_manager = channel_manager or ChannelManager()
        self._push_service = push_service or PushService(
            channel_manager=self._channel_manager,
            connection_manager=self._connection_manager,
        )
        self._started = False
        self._startup_duration: float = 0.0
        self._log = get_logger("eaip.ws.integration")

    @property
    def connection_manager(self) -> ConnectionManager:
        """Return the connection manager."""
        return self._connection_manager

    @property
    def channel_manager(self) -> ChannelManager:
        """Return the channel manager."""
        return self._channel_manager

    @property
    def push_service(self) -> PushService:
        """Return the push service."""
        return self._push_service

    @property
    def startup_duration(self) -> float:
        """Return the startup duration in seconds."""
        return self._startup_duration

    async def start(self, kernel: RuntimeKernel | None = None) -> None:
        """Start the module and register health check."""
        t0 = time.monotonic()
        self._log.info("ws.integration.start")

        if kernel is not None:
            kernel.platform.health.register(self._health_check())

        self._startup_duration = time.monotonic() - t0
        self._started = True
        self._log.info(
            "ws.integration.complete",
            duration_s=round(self._startup_duration, 3),
        )

    async def stop(self, _kernel: RuntimeKernel | None = None) -> None:
        """Stop the module."""
        self._log.info("ws.integration.stop")
        self._started = False

    def _health_check(self) -> HealthCheck:
        """Create a health check instance."""
        return WsHealthCheck(
            active_connections=len(self._connection_manager.list_connections()),
            active_channels=len(self._channel_manager.list_channels()),
        )


__all__ = ["WsRuntimeModule"]
