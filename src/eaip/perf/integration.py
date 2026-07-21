"""Performance management runtime module — wires BenchmarkEngine, LoadTestOrchestrator, etc."""

from __future__ import annotations

from typing import TYPE_CHECKING

from eaip.perf.benchmarks import BenchmarkEngine
from eaip.perf.health import PerfHealthCheck
from eaip.perf.load_testing import LoadTestOrchestrator
from eaip.perf.regression import RegressionDetector

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel


class PerfRuntimeModule:
    name: str = "perf"

    def __init__(self) -> None:
        self.engine = BenchmarkEngine()
        self.orchestrator = LoadTestOrchestrator()
        self.regression_detector = RegressionDetector(engine=self.engine)
        self.health_check = PerfHealthCheck(
            self.engine,
            self.orchestrator,
            self.regression_detector,
        )

    async def start(self, kernel: RuntimeKernel) -> None:
        kernel.register_module("perf.engine", self.engine)
        kernel.register_module("perf.orchestrator", self.orchestrator)
        kernel.register_module("perf.regression_detector", self.regression_detector)

    async def stop(self, kernel: RuntimeKernel) -> None:
        pass
