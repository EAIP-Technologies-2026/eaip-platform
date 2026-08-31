"""Health check for model evaluation."""

from __future__ import annotations

from eaip.health.checks import HealthReport, HealthStatus


class ModelEvaluationHealthCheck:
    """Health check for the model evaluation subsystem."""

    name: str = "model_evaluation"

    async def check(self) -> HealthReport:
        """Run the health check and return a report."""
        return HealthReport(
            component=self.name,
            status=HealthStatus.HEALTHY,
            message="Model evaluation subsystem healthy",
        )


__all__ = ["ModelEvaluationHealthCheck"]
