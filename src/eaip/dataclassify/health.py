"""Health check for the data classification module."""

from __future__ import annotations

from eaip.dataclassify.classifier import DataClassifier
from eaip.health.checks import HealthCheck, HealthReport, HealthStatus


class DataClassifyHealthCheck(HealthCheck):
    name: str = "dataclassify"

    def __init__(
        self,
        classifier: DataClassifier | None = None,
    ) -> None:
        self._classifier = classifier or DataClassifier()

    async def check(self) -> HealthReport:
        rules = await self._classifier.list_rules()
        return HealthReport(
            component=self.name,
            status=HealthStatus.HEALTHY,
            message=f"{len(rules)} classification rule(s) registered",
            details={
                "rules_total": len(rules),
                "confidence_threshold": self._classifier.config.confidence_threshold,
                "max_rules": self._classifier.config.max_rules,
            },
        )


__all__ = ["DataClassifyHealthCheck"]
