"""Health check for the quality & testing framework."""

from __future__ import annotations

from eaip.health.checks import HealthReport, HealthStatus
from eaip.quality.coverage import CoverageAnalyzer
from eaip.quality.engine import TestEngine
from eaip.quality.gates import QualityGateService
from eaip.quality.regression import RegressionDetector


class QualityHealthCheck:
    name: str = "quality"

    def __init__(
        self,
        engine: TestEngine,
        gates: QualityGateService,
        coverage: CoverageAnalyzer,
        regression: RegressionDetector,
    ) -> None:
        self._engine = engine
        self._gates = gates
        self._coverage = coverage
        self._regression = regression

    async def check(self) -> HealthReport:
        details: dict[str, object] = {}
        try:
            test_count = len(self._engine.list_test_cases())
            details["test_case_count"] = test_count
        except Exception as exc:
            return HealthReport(
                component=self.name,
                status=HealthStatus.UNHEALTHY,
                message=f"Test engine unavailable: {exc}",
                details={"error": str(exc)},
            )
        try:
            details["suite_count"] = len(self._engine.list_suites())
        except Exception as exc:
            details["suite_error"] = str(exc)
        try:
            details["gate_count"] = len(self._gates.list_gates())
        except Exception as exc:
            details["gate_error"] = str(exc)
        try:
            details["regression_count"] = len(await self._regression.list_regressions())
        except Exception as exc:
            details["regression_error"] = str(exc)

        status = HealthStatus.HEALTHY
        messages: list[str] = []
        if test_count == 0:
            status = HealthStatus.DEGRADED
            messages.append("No test cases registered")

        return HealthReport(
            component=self.name,
            status=status,
            message="; ".join(messages) if messages else "Quality framework healthy",
            details=details,
        )
