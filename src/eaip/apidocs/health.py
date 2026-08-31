"""API Documentation health check."""

from __future__ import annotations

from eaip.health.checks import HealthCheck, HealthReport, HealthStatus


class ApiDocsHealthCheck(HealthCheck):
    name: str = "eaip.apidocs"

    def __init__(
        self,
        registered_endpoints: int = 0,
        published_docs: int = 0,
        changelogs: int = 0,
    ) -> None:
        self._registered_endpoints = registered_endpoints
        self._published_docs = published_docs
        self._changelogs = changelogs

    async def check(self) -> HealthReport:
        details = {
            "registered_endpoints": self._registered_endpoints,
            "published_docs": self._published_docs,
            "changelogs": self._changelogs,
        }
        return HealthReport(
            component="ApiDocsGenerator",
            status=HealthStatus.HEALTHY,
            details=details,
        )


__all__ = ["ApiDocsHealthCheck"]
