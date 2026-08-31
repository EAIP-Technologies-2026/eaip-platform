"""Quality engine runtime module — wires TestEngine, QualityGateService, etc."""

from __future__ import annotations

from typing import TYPE_CHECKING

from eaip.quality.coverage import CoverageAnalyzer
from eaip.quality.engine import TestEngine
from eaip.quality.gates import QualityGateService
from eaip.quality.health import QualityHealthCheck
from eaip.quality.regression import RegressionDetector

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel


class QualityRuntimeModule:
    name: str = "quality"

    def __init__(self) -> None:
        self.engine = TestEngine()
        self.gate_service = QualityGateService()
        self.coverage_analyzer = CoverageAnalyzer()
        self.regression_detector = RegressionDetector()
        self.health_check = QualityHealthCheck(
            self.engine,
            self.gate_service,
            self.coverage_analyzer,
            self.regression_detector,
        )

    async def start(self, kernel: RuntimeKernel) -> None:
        kernel.register_module("quality.engine", self.engine)
        kernel.register_module("quality.gate_service", self.gate_service)
        kernel.register_module("quality.coverage_analyzer", self.coverage_analyzer)
        kernel.register_module("quality.regression_detector", self.regression_detector)

    async def stop(self, kernel: RuntimeKernel) -> None:
        pass
