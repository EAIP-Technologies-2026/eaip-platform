from __future__ import annotations

from typing import TYPE_CHECKING

from eaip.capabilities.capability import Capability, CapabilityStatus
from eaip.datapipeline.engine import PipelineEngine
from eaip.datapipeline.health import PipelineHealthCheck
from eaip.datapipeline.models import PipelineConfig
from eaip.logging.context import get_logger

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel


class PipelineRuntimeModule:
    name: str = "datapipeline"

    def __init__(
        self,
        config: PipelineConfig | None = None,
        engine: PipelineEngine | None = None,
    ) -> None:
        self._config = config or PipelineConfig()
        self._engine = engine or PipelineEngine(config=self._config)
        self._log = get_logger("eaip.datapipeline.integration")

    @property
    def engine(self) -> PipelineEngine:
        return self._engine

    async def start(self, kernel: RuntimeKernel) -> None:
        self._log.info("datapipeline.module.starting")
        platform = kernel.platform
        capability = Capability(
            name="eaip.datapipeline",
            title="Data Pipeline Engine",
            description="Data pipeline engine with source/sink definitions, transformation steps, execution, and scheduling",
            version="0.1.0",
            status=CapabilityStatus.ENABLED,
            tags=("datapipeline", "etl", "transformation", "scheduling", "lineage"),
        )
        platform.capabilities.register(capability)
        platform.health.register(PipelineHealthCheck(engine=self._engine))
        self._log.info("datapipeline.module.started")

    async def stop(self, kernel: RuntimeKernel) -> None:
        self._log.info("datapipeline.module.stopping")


__all__ = ["PipelineRuntimeModule"]
