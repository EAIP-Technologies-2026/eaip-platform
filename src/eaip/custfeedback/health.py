"""Health check for the customer feedback analyzer."""

from __future__ import annotations

from eaip.custfeedback.analyzer import FeedbackAnalyzer
from eaip.health.checks import HealthReport, HealthStatus


class FeedbackHealthCheck:
    name: str = "custfeedback"

    def __init__(self, analyzer: FeedbackAnalyzer) -> None:
        self._analyzer = analyzer

    async def check(self) -> HealthReport:
        details: dict[str, object] = {}
        try:
            items = await self._analyzer.list_feedback()
            details["feedback_count"] = len(items)
        except Exception as exc:
            return HealthReport(
                component=self.name,
                status=HealthStatus.UNHEALTHY,
                message=f"Feedback analyzer unavailable: {exc}",
                details={"error": str(exc)},
            )
        try:
            aggregates = await self._analyzer.list_aggregates()
            details["aggregate_count"] = len(aggregates)
        except Exception as exc:
            details["aggregate_error"] = str(exc)

        return HealthReport(
            component=self.name,
            status=HealthStatus.HEALTHY,
            message="Customer feedback analyzer healthy",
            details=details,
        )
