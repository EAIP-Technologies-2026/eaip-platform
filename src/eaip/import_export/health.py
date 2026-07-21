"""Health check for the import/export engine."""

from __future__ import annotations

from eaip.health.checks import HealthReport, HealthStatus
from eaip.import_export.models import ExportJobStatus, ImportJobStatus
from eaip.import_export.service import ImportExportService


class ImportExportHealthCheck:
    name: str = "import_export"

    def __init__(self, service: ImportExportService) -> None:
        self._service = service

    async def check(self) -> HealthReport:
        issues: list[str] = []
        imports = await self._service.list_import_jobs()
        exports = await self._service.list_export_jobs()
        schedules = await self._service.list_schedules()

        failed_imports = [j for j in imports if j.status == ImportJobStatus.FAILED]
        failed_exports = [j for j in exports if j.status == ExportJobStatus.FAILED]

        if not imports and not exports:
            issues.append("No import or export jobs registered")
        if not schedules:
            issues.append("No schedules configured")

        details: dict[str, object] = {
            "imports_total": len(imports),
            "imports_failed": len(failed_imports),
            "exports_total": len(exports),
            "exports_failed": len(failed_exports),
            "schedules_total": len(schedules),
        }

        status = HealthStatus.HEALTHY
        if issues:
            status = HealthStatus.DEGRADED
        if failed_imports or failed_exports:
            status = HealthStatus.UNHEALTHY
            if failed_imports:
                issues.append(f"{len(failed_imports)} failed import job(s)")
            if failed_exports:
                issues.append(f"{len(failed_exports)} failed export job(s)")

        return HealthReport(
            component="import_export",
            status=status,
            message="; ".join(issues) if issues else "Import/Export engine is operational",
            details=details,
        )


__all__ = ["ImportExportHealthCheck"]
