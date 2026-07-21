"""Runtime module integration for the export & reporting engine."""

from __future__ import annotations

from typing import TYPE_CHECKING

from eaip.capabilities.capability import Capability, CapabilityStatus
from eaip.export.delivery import DeliveryService
from eaip.export.engine import ExportEngine
from eaip.export.health import ExportHealthCheck
from eaip.export.models import ExportConfig
from eaip.export.scheduler import ExportScheduler
from eaip.logging.context import get_logger

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel


class ExportRuntimeModule:
    name: str = "export"

    def __init__(
        self,
        config: ExportConfig | None = None,
        engine: ExportEngine | None = None,
        scheduler: ExportScheduler | None = None,
        delivery: DeliveryService | None = None,
    ) -> None:
        self._config = config or ExportConfig()
        self._engine = engine or ExportEngine(config=self._config)
        self._scheduler = scheduler or ExportScheduler()
        self._delivery = delivery or DeliveryService()
        self._log = get_logger("eaip.export.integration")

    @property
    def engine(self) -> ExportEngine:
        return self._engine

    @property
    def scheduler(self) -> ExportScheduler:
        return self._scheduler

    @property
    def delivery(self) -> DeliveryService:
        return self._delivery

    async def start(self, kernel: RuntimeKernel) -> None:
        self._log.info("export.module.starting")
        platform = kernel.platform
        capability = Capability(
            name="eaip.export",
            title="Data Export & Reporting Engine",
            description="Report definitions, scheduled exports, format converters, and delivery channels",
            version="0.1.0",
            status=CapabilityStatus.ENABLED,
            tags=("export", "reporting", "scheduler", "delivery", "formats"),
        )
        platform.capabilities.register(capability)
        platform.health.register(ExportHealthCheck(engine=self._engine))
        self._log.info("export.module.started")

    async def stop(self, kernel: RuntimeKernel) -> None:
        self._log.info("export.module.stopping")


__all__ = ["ExportRuntimeModule"]
