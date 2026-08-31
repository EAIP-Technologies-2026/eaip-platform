"""Health check for the performance management framework."""

from __future__ import annotations

from eaip.health.checks import HealthReport, HealthStatus
from eaip.perf.benchmarks import BenchmarkEngine
from eaip.perf.load_testing import LoadTestOrchestrator
from eaip.perf.regression import RegressionDetector


class PerfHealthCheck:
    name: str = "perf"

    def __init__(
        self,
        engine: BenchmarkEngine,
        orchestrator: LoadTestOrchestrator,
        regression: RegressionDetector,
    ) -> None:
        self._engine = engine
        self._orchestrator = orchestrator
        self._regression = regression

    async def check(self) -> HealthReport:
        details: dict[str, object] = {}
        try:
            benchmark_count = len(self._engine.list_benchmarks())
            details["benchmark_count"] = benchmark_count
        except Exception as exc:
            return HealthReport(
                component=self.name,
                status=HealthStatus.UNHEALTHY,
                message=f"Benchmark engine unavailable: {exc}",
                details={"error": str(exc)},
            )
        try:
            details["scenario_count"] = len(self._orchestrator.list_scenarios())
        except Exception as exc:
            details["scenario_error"] = str(exc)
        try:
            details["regression_count"] = len(await self._regression.list_regressions())
        except Exception as exc:
            details["regression_error"] = str(exc)

        status = HealthStatus.HEALTHY
        messages: list[str] = []
        if benchmark_count == 0:
            status = HealthStatus.DEGRADED
            messages.append("No benchmarks defined")

        return HealthReport(
            component=self.name,
            status=status,
            message="; ".join(messages) if messages else "Performance management healthy",
            details=details,
        )
