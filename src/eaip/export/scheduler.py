"""Export scheduler — cron-based scheduling for report exports."""

from __future__ import annotations

from eaip.export.exceptions import ScheduleNotFoundError
from eaip.export.models import ReportDefinition


class ExportScheduler:
    def __init__(self) -> None:
        self._scheduled: dict[str, ReportDefinition] = {}
        self._job_counts: dict[str, int] = {}

    def schedule_report(self, report: ReportDefinition) -> ReportDefinition:
        self._scheduled[report.id] = report
        self._job_counts[report.id] = 0
        return report

    def unschedule_report(self, report_id: str) -> None:
        if report_id not in self._scheduled:
            raise ScheduleNotFoundError(f"Scheduled report not found: {report_id}")
        del self._scheduled[report_id]
        self._job_counts.pop(report_id, None)

    def list_scheduled(self) -> list[ReportDefinition]:
        return list(self._scheduled.values())

    def get_scheduled(self, report_id: str) -> ReportDefinition:
        report = self._scheduled.get(report_id)
        if report is None:
            raise ScheduleNotFoundError(f"Scheduled report not found: {report_id}")
        return report

    def check_due_exports(self) -> list[ReportDefinition]:
        return [r for r in self._scheduled.values() if r.enabled and r.schedule_cron]

    def increment_job_count(self, report_id: str) -> int:
        self._job_counts[report_id] = self._job_counts.get(report_id, 0) + 1
        return self._job_counts[report_id]

    def get_job_count(self, report_id: str) -> int:
        return self._job_counts.get(report_id, 0)

    @property
    def scheduled_count(self) -> int:
        return len(self._scheduled)


__all__ = ["ExportScheduler"]
