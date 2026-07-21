"""Integration layer — ComplianceRuntimeModule for kernel lifecycle."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

from eaip.compliance.framework import ComplianceFramework
from eaip.compliance.health import ComplianceHealthCheck
from eaip.health.checks import HealthCheck
from eaip.logging.context import get_logger

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel


class ComplianceRuntimeModule:
    """RuntimeModule that bootstraps the Compliance subsystem during kernel start."""

    name: str = "compliance"

    def __init__(self, framework: ComplianceFramework | None = None) -> None:
        """Initialize the compliance runtime module."""
        self._framework = framework or ComplianceFramework()
        self._started = False
        self._startup_duration: float = 0.0
        self._log = get_logger("eaip.compliance.integration")

    @property
    def framework(self) -> ComplianceFramework:
        """Return the compliance framework."""
        return self._framework

    @property
    def startup_duration(self) -> float:
        """Return the startup duration."""
        return self._startup_duration

    async def start(self, kernel: RuntimeKernel | None = None) -> None:
        """Start the compliance module."""
        t0 = time.monotonic()
        self._log.info("compliance.integration.start")

        if kernel is not None:
            kernel.platform.health.register(self._health_check())

        self._startup_duration = time.monotonic() - t0
        self._started = True
        self._log.info(
            "compliance.integration.complete",
            duration_s=round(self._startup_duration, 3),
        )

    async def stop(self, _kernel: RuntimeKernel | None = None) -> None:
        """Stop the compliance module."""
        self._log.info("compliance.integration.stop")
        self._started = False

    def _health_check(self) -> HealthCheck:
        regulations = self._framework.list_regulations()
        controls = self._framework.list_controls()
        return ComplianceHealthCheck(
            regulation_count=len(regulations),
            control_count=len(controls),
            last_scan_passed=True,
        )


__all__ = ["ComplianceRuntimeModule"]
