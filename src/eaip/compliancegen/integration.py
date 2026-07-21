"""Runtime integration — ComplianceRuntimeModule for kernel lifecycle."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

from eaip.capabilities.capability import Capability, CapabilityStatus
from eaip.compliancegen.generator import ComplianceReportGenerator
from eaip.compliancegen.health import ComplianceHealthCheck
from eaip.compliancegen.models import GeneratorConfig
from eaip.logging.context import get_logger

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel


class ComplianceRuntimeModule:
    """RuntimeModule that registers the compliance report generator with the kernel."""

    name: str = "compliancegen"

    def __init__(self, config: GeneratorConfig | None = None) -> None:
        self._config = config or GeneratorConfig()
        self._generator: ComplianceReportGenerator | None = None
        self._health_check: ComplianceHealthCheck | None = None
        self._startup_duration: float = 0.0
        self._log = get_logger("eaip.compliancegen.integration")

    async def start(self, kernel: RuntimeKernel) -> None:
        t0 = time.monotonic()
        self._log.info("compliancegen.module.start")

        self._generator = ComplianceReportGenerator(config=self._config)
        self._health_check = ComplianceHealthCheck()

        kernel.platform.health.register(self._health_check)
        kernel.platform.capabilities.register(
            Capability(
                name="compliancegen:generator",
                title="Compliance Report Generator",
                status=CapabilityStatus.ENABLED,
                tags=("compliance", "audit", "reporting"),
            )
        )

        self._startup_duration = time.monotonic() - t0
        self._log.info(
            "compliancegen.module.complete",
            duration_s=round(self._startup_duration, 3),
        )

    async def stop(self, _kernel: RuntimeKernel) -> None:
        self._log.info("compliancegen.module.stop")
