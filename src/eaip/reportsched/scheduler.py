"""ReportScheduler — schedule, generate, and manage report executions."""

from __future__ import annotations

from eaip.logging.context import get_logger
from eaip.reportsched.events import ReportFailed, ReportGenerated, ReportScheduled
from eaip.reportsched.exceptions import ReportGenerationError, ReportNotFoundError, SchedulerError
from eaip.reportsched.models import ReportDefinition, ReportExecution, SchedulerConfig
from eaip.shared.time import utc_now


class ReportScheduler:
    """Central service for scheduling and generating reports."""

    def __init__(self, config: SchedulerConfig | None = None) -> None:
        self._config = config or SchedulerConfig()
        self._definitions: dict[str, ReportDefinition] = {}
        self._executions: dict[str, ReportExecution] = {}
        self._log = get_logger("eaip.reportsched.scheduler")

    @property
    def config(self) -> SchedulerConfig:
        return self._config

    async def create_definition(self, definition: ReportDefinition) -> ReportDefinition:
        """Create a new report definition."""
        self._definitions[definition.id] = definition
        ReportScheduled(
            report_id=definition.id,
            name=definition.name,
            report_format=definition.format,
            cron=definition.schedule_cron,
        )
        self._log.info(
            "reportsched.definition.created", report_id=definition.id, name=definition.name
        )
        return definition

    async def get_definition(self, report_id: str) -> ReportDefinition:
        """Get a report definition by ID."""
        definition = self._definitions.get(report_id)
        if definition is None:
            raise ReportNotFoundError(f"Report definition not found: {report_id}")
        return definition

    async def update_definition(self, report_id: str, **changes: object) -> ReportDefinition:
        """Update an existing report definition."""
        existing = self._definitions.get(report_id)
        if existing is None:
            raise ReportNotFoundError(f"Report definition not found: {report_id}")
        updated = existing.model_copy(update=changes)
        self._definitions[report_id] = updated
        self._log.info("reportsched.definition.updated", report_id=report_id)
        return updated

    async def list_definitions(self, enabled_only: bool = False) -> list[ReportDefinition]:
        """List all report definitions."""
        result = list(self._definitions.values())
        if enabled_only:
            result = [d for d in result if d.enabled]
        return result

    async def generate_report(self, report_id: str) -> ReportExecution:
        """Generate a report for the given definition."""
        definition = self._definitions.get(report_id)
        if definition is None:
            raise ReportNotFoundError(f"Report definition not found: {report_id}")
        if not definition.enabled:
            raise SchedulerError(f"Report definition is disabled: {report_id}")

        execution = ReportExecution(
            id=f"exec_{utc_now().timestamp():.0f}",
            report_id=report_id,
            status="running",
            started_at=utc_now(),
        )
        self._executions[execution.id] = execution

        try:
            output_path = f"{self._config.output_directory}/{report_id}/{execution.id}.{definition.format.value}"
            completed = execution.model_copy(
                update={
                    "status": "completed",
                    "completed_at": utc_now(),
                    "output_path": output_path,
                }
            )
            self._executions[execution.id] = completed
            ReportGenerated(
                report_id=report_id,
                execution_id=execution.id,
                output_path=output_path,
            )
            self._log.info(
                "reportsched.report.generated", report_id=report_id, execution_id=execution.id
            )
            return completed
        except Exception as exc:
            failed = execution.model_copy(
                update={
                    "status": "failed",
                    "completed_at": utc_now(),
                    "error": str(exc),
                }
            )
            self._executions[execution.id] = failed
            ReportFailed(report_id=report_id, execution_id=execution.id, error=str(exc))
            raise ReportGenerationError(f"Report generation failed: {exc}") from exc

    async def get_execution(self, execution_id: str) -> ReportExecution:
        """Get an execution record by ID."""
        execution = self._executions.get(execution_id)
        if execution is None:
            raise ReportNotFoundError(f"Execution not found: {execution_id}")
        return execution

    async def list_executions(
        self, report_id: str | None = None, status: str | None = None
    ) -> list[ReportExecution]:
        """List execution records, optionally filtered."""
        result = list(self._executions.values())
        if report_id is not None:
            result = [e for e in result if e.report_id == report_id]
        if status is not None:
            result = [e for e in result if e.status == status]
        return sorted(result, key=lambda e: e.created_at, reverse=True)

    async def get_statistics(self) -> dict[str, object]:
        """Return summary statistics about the scheduler."""
        total_defs = len(self._definitions)
        total_execs = len(self._executions)
        by_status: dict[str, int] = {}
        for exec_ in self._executions.values():
            by_status[exec_.status] = by_status.get(exec_.status, 0) + 1
        return {
            "total_definitions": total_defs,
            "total_executions": total_execs,
            "by_status": by_status,
        }


__all__ = ["ReportScheduler"]
