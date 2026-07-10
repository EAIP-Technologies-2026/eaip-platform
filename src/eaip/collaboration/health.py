"""Collaboration health check — reports subsystem health."""

from __future__ import annotations

from eaip.health.checks import HealthCheck, HealthReport, HealthStatus


class CollaborationHealthCheck(HealthCheck):
    """Reports collaboration subsystem health based on sessions and tasks."""

    name: str = "eaip.collaboration"

    def __init__(
        self,
        session_count: int = 0,
        active_sessions: int = 0,
        failed_sessions: int = 0,
        pending_approvals: int = 0,
    ) -> None:
        self._session_count = session_count
        self._active_sessions = active_sessions
        self._failed_sessions = failed_sessions
        self._pending_approvals = pending_approvals

    async def check(self) -> HealthReport:
        details = {
            "session_count": self._session_count,
            "active_sessions": self._active_sessions,
            "failed_sessions": self._failed_sessions,
            "pending_approvals": self._pending_approvals,
        }
        if self._failed_sessions > 0:
            return HealthReport(
                component="CollaborationRuntime",
                status=HealthStatus.DEGRADED,
                details=details,
                message=f"{self._failed_sessions} failed session(s) detected",
            )
        if self._active_sessions > 0 and self._session_count == 0:
            return HealthReport(
                component="CollaborationRuntime",
                status=HealthStatus.DEGRADED,
                details=details,
                message="active sessions with no total session count",
            )
        return HealthReport(
            component="CollaborationRuntime",
            status=HealthStatus.HEALTHY,
            details=details,
        )


__all__ = ["CollaborationHealthCheck"]
