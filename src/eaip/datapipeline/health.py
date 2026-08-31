from __future__ import annotations

from typing import TYPE_CHECKING

from eaip.health.checks import HealthReport, HealthStatus

if TYPE_CHECKING:
    from eaip.datapipeline.engine import PipelineEngine


class PipelineHealthCheck:
    name: str = "datapipeline"

    def __init__(self, engine: PipelineEngine | None = None) -> None:
        from eaip.datapipeline.engine import PipelineEngine

        self._engine = engine or PipelineEngine()

    async def check(self) -> HealthReport:
        error_details: list[str] = []
        source_count = len(self._engine._sources)
        sink_count = len(self._engine._sinks)
        pipeline_count = len(self._engine._pipelines)
        active_executions = len(self._engine._active_executions)

        if source_count == 0:
            error_details.append("No data sources registered")
        if sink_count == 0:
            error_details.append("No data sinks registered")
        if pipeline_count == 0:
            error_details.append("No pipelines registered")

        status = HealthStatus.HEALTHY
        if error_details:
            status = HealthStatus.DEGRADED

        return HealthReport(
            component="datapipeline",
            status=status,
            message="; ".join(error_details) if error_details else "Data pipeline is operational",
            details={
                "sources_registered": source_count,
                "sinks_registered": sink_count,
                "pipelines_registered": pipeline_count,
                "executions_active": active_executions,
            },
        )


__all__ = ["PipelineHealthCheck"]
