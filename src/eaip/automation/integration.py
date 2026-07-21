"""Runtime module integration for the automation runtime."""

from __future__ import annotations

from typing import TYPE_CHECKING

from eaip.automation.engine import AutomationEngine
from eaip.automation.health import AutomationHealthCheck
from eaip.automation.models import AutomationConfig
from eaip.capabilities.capability import Capability, CapabilityStatus
from eaip.logging.context import get_logger

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel


class AutomationRuntimeModule:
    name: str = "automation"

    def __init__(
        self,
        config: AutomationConfig | None = None,
        engine: AutomationEngine | None = None,
    ) -> None:
        self._config = config or AutomationConfig()
        self._engine = engine or AutomationEngine(config=self._config)
        self._log = get_logger("eaip.automation.integration")

    @property
    def engine(self) -> AutomationEngine:
        return self._engine

    async def start(self, kernel: RuntimeKernel) -> None:
        self._log.info("automation.module.starting")
        platform = kernel.platform
        capability = Capability(
            name="eaip.automation",
            title="Enterprise Automation Runtime",
            description="Rule-based automation engine with event triggers, scheduling, and execution history",
            version="0.1.0",
            status=CapabilityStatus.ENABLED,
            tags=("automation", "rules", "triggers", "scheduling", "workflow"),
        )
        platform.capabilities.register(capability)
        platform.health.register(AutomationHealthCheck(engine=self._engine))
        self._log.info("automation.module.started")

    async def stop(self, kernel: RuntimeKernel) -> None:
        self._log.info("automation.module.stopping")


__all__ = ["AutomationRuntimeModule"]
