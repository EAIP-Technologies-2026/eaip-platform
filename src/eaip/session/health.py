"""Health checks for the session subsystem."""

from __future__ import annotations

from typing import Any

from eaip.health.checks import HealthReport, HealthStatus
from eaip.logging.context import get_logger

from eaip.session.manager import SessionManager


class SessionHealthCheck:
    """Health checker for the session subsystem.

    Reports session store size, active sessions, and overall health.
    Implements the :class:`HealthCheck` protocol.
    """

    name: str = "session"

    def __init__(self, manager: SessionManager) -> None:
        """Initialize the health check.

        Args:
            manager: The SessionManager instance to monitor.
        """
        self._manager = manager
        self._log = get_logger("eaip.session.health")

    async def check(self) -> HealthReport:
        """Execute a health check.

        Returns:
            A HealthReport with status information.
        """
        self._log.debug("health.check.start")

        details: dict[str, Any] = {"subsystem": "session"}

        try:
            active = await self._manager.get_active_sessions()
            all_sessions = await self._manager.list_sessions()
            details["active_sessions"] = len(active)
            details["total_sessions"] = len(all_sessions)
            details["status"] = "healthy"
            status = HealthStatus.HEALTHY
        except Exception as exc:
            details["error"] = str(exc)
            status = HealthStatus.UNHEALTHY

        result = HealthReport(
            component="session",
            status=status,
            details=details,
        )

        self._log.debug("health.check.complete", status=status.value)
        return result


__all__ = ["SessionHealthCheck"]
