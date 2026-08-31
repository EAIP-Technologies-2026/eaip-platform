"""Health check for the IP reputation service."""

from __future__ import annotations

from eaip.health.checks import HealthReport, HealthStatus
from eaip.iprep.service import IPReputationService


class IPRepHealthCheck:
    name: str = "iprep"

    def __init__(self, service: IPReputationService) -> None:
        self._service = service

    async def check(self) -> HealthReport:
        details: dict[str, object] = {}
        try:
            blocklist = await self._service.list_blocklist()
            details["blocklist_count"] = len(blocklist)
        except Exception as exc:
            return HealthReport(
                component=self.name,
                status=HealthStatus.UNHEALTHY,
                message=f"IP reputation service unavailable: {exc}",
                details={"error": str(exc)},
            )

        status = HealthStatus.HEALTHY
        messages: list[str] = []

        return HealthReport(
            component=self.name,
            status=status,
            message="; ".join(messages) if messages else "IP reputation service healthy",
            details=details,
        )


__all__ = ["IPRepHealthCheck"]
