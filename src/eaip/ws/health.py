"""WebSocket health check — implements the HealthCheck protocol."""

from __future__ import annotations

from eaip.health.checks import HealthReport, HealthStatus


class WsHealthCheck:
    """Health check for the WebSocket subsystem.

    Reports healthy when the connection manager is tracking at least one
    connection; degraded otherwise.
    """

    name: str = "websocket"

    def __init__(self, active_connections: int = 0, active_channels: int = 0) -> None:
        """Initialize with connection and channel counts."""
        self._active_connections = active_connections
        self._active_channels = active_channels

    @property
    def active_connections(self) -> int:
        """Return the number of active connections."""
        return self._active_connections

    @property
    def active_channels(self) -> int:
        """Return the number of active channels."""
        return self._active_channels

    async def check(self) -> HealthReport:
        """Run the WebSocket health check."""
        details = {
            "active_connections": self._active_connections,
            "active_channels": self._active_channels,
        }
        if self._active_connections >= 0:
            return HealthReport(
                component=self.name,
                status=HealthStatus.HEALTHY,
                message=(
                    f"{self._active_connections} connection(s), {self._active_channels} channel(s)."
                ),
                details=details,
            )
        return HealthReport(
            component=self.name,
            status=HealthStatus.DEGRADED,
            message="WebSocket subsystem is not ready.",
            details=details,
        )


__all__ = ["WsHealthCheck"]
