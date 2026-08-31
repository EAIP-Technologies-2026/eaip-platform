from __future__ import annotations

from eaip.health.checks import HealthReport, HealthStatus


class AiObservabilityHealthCheck:
    name: str = "ai_observability"

    def __init__(
        self,
        trace_count: int = 0,
        model_call_count: int = 0,
        alert_count: int = 0,
    ) -> None:
        self._trace_count = trace_count
        self._model_call_count = model_call_count
        self._alert_count = alert_count

    async def check(self) -> HealthReport:
        details: list[str] = []

        if self._trace_count == 0:
            details.append("No traces recorded")
        if self._model_call_count == 0:
            details.append("No model calls logged")
        if self._alert_count == 0:
            details.append("No alerts configured")

        status = HealthStatus.HEALTHY
        if details:
            status = HealthStatus.DEGRADED

        return HealthReport(
            component="ai_observability",
            status=status,
            message="; ".join(details) if details else "AI Observability subsystem is operational",
            details={
                "traces_total": self._trace_count,
                "model_calls_total": self._model_call_count,
                "alerts_total": self._alert_count,
            },
        )


__all__ = ["AiObservabilityHealthCheck"]
