"""Health check for the export & reporting engine."""

from __future__ import annotations

from eaip.export.engine import ExportEngine
from eaip.health.checks import HealthReport, HealthStatus


class ExportHealthCheck:
    name: str = "export"

    def __init__(self, engine: ExportEngine) -> None:
        self._engine = engine

    async def check(self) -> HealthReport:
        issues: list[str] = []
        reports = self._engine.list_reports()
        jobs = self._engine.list_jobs()

        enabled_reports = [r for r in reports if r.enabled]
        failed_jobs = [j for j in jobs if j.status == "failed"]

        if not reports:
            issues.append("No report definitions registered")
        if not enabled_reports:
            issues.append("No enabled reports")

        details: dict[str, object] = {
            "reports_total": len(reports),
            "reports_enabled": len(enabled_reports),
            "jobs_total": len(jobs),
            "jobs_failed": len(failed_jobs),
        }

        status = HealthStatus.HEALTHY
        if issues:
            status = HealthStatus.DEGRADED
        if failed_jobs:
            status = HealthStatus.UNHEALTHY
            issues.append(f"{len(failed_jobs)} failed export job(s)")

        return HealthReport(
            component="export",
            status=status,
            message="; ".join(issues) if issues else "Export engine is operational",
            details=details,
        )


__all__ = ["ExportHealthCheck"]
