"""Integration layer — DataQualityRuntimeModule for kernel lifecycle."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

from eaip.dataquality.health import DataQualityHealthCheck
from eaip.dataquality.quality_service import DataQualityService
from eaip.dataquality.rule_engine import QualityRuleEngine
from eaip.health.checks import HealthCheck
from eaip.logging.context import get_logger

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel


class DataQualityRuntimeModule:
    """RuntimeModule that bootstraps the Data Quality subsystem during kernel start."""

    name: str = "dataquality"

    def __init__(
        self,
        rule_engine: QualityRuleEngine | None = None,
        quality_service: DataQualityService | None = None,
    ) -> None:
        """Initialize the data quality runtime module."""
        self._rule_engine = rule_engine or QualityRuleEngine()
        self._quality_service = quality_service or DataQualityService(rule_engine=self._rule_engine)
        self._started = False
        self._startup_duration: float = 0.0
        self._log = get_logger("eaip.dataquality.integration")

    @property
    def rule_engine(self) -> QualityRuleEngine:
        """Return the rule engine."""
        return self._rule_engine

    @property
    def quality_service(self) -> DataQualityService:
        """Return the quality service."""
        return self._quality_service

    @property
    def startup_duration(self) -> float:
        """Return the startup duration."""
        return self._startup_duration

    async def start(self, kernel: RuntimeKernel | None = None) -> None:
        """Start the data quality module."""
        t0 = time.monotonic()
        self._log.info("dataquality.integration.start")

        if kernel is not None:
            kernel.platform.health.register(self._health_check())

        self._startup_duration = time.monotonic() - t0
        self._started = True
        self._log.info(
            "dataquality.integration.complete",
            duration_s=round(self._startup_duration, 3),
        )

    async def stop(self, _kernel: RuntimeKernel | None = None) -> None:
        """Stop the data quality module."""
        self._log.info("dataquality.integration.stop")
        self._started = False

    def _health_check(self) -> HealthCheck:
        rules = self._rule_engine.list_rules()
        active_rules = sum(1 for r in rules if r.enabled)
        return DataQualityHealthCheck(
            active_rules=active_rules,
            active_checks=0,
            last_check_passed=True,
        )


__all__ = ["DataQualityRuntimeModule"]
