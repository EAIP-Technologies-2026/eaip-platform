"""Runtime integration — MigrationRuntimeModule for the EAIP kernel."""

from __future__ import annotations

from typing import TYPE_CHECKING

from eaip.capabilities.capability import Capability, CapabilityStatus
from eaip.datamigrate.engine import MigrationEngine
from eaip.datamigrate.health import MigrationHealthCheck
from eaip.datamigrate.models import MigrationConfig
from eaip.datamigrate.transforms import DataTransformer

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel

from eaip.logging.context import get_logger

logger = get_logger("eaip.datamigrate.integration")


class MigrationRuntimeModule:
    name: str = "datamigrate"

    def __init__(
        self,
        config: MigrationConfig | None = None,
        engine: MigrationEngine | None = None,
        transformer: DataTransformer | None = None,
    ) -> None:
        self._config = config or MigrationConfig()
        self._engine = engine or MigrationEngine()
        self._transformer = transformer or DataTransformer()
        self._health_check = MigrationHealthCheck(engine=self._engine)

    async def start(self, kernel: RuntimeKernel) -> None:
        platform = kernel.platform
        capability = Capability(
            name="eaip.datamigrate",
            title="Data Migration Service",
            description="Schema migration, data transformation, rollback, and version tracking",
            version="0.1.0",
            status=CapabilityStatus.ENABLED,
            tags=("datamigrate", "migration", "schema", "transform", "rollback"),
        )
        platform.capabilities.register(capability)
        platform.health.register(self._health_check)
        logger.info(
            "datamigrate_module_started",
            engine_ready=True,
            transformer_ready=True,
        )

    async def stop(self, kernel: RuntimeKernel) -> None:
        logger.info("datamigrate_module_stopped")

    @property
    def engine(self) -> MigrationEngine:
        return self._engine

    @property
    def transformer(self) -> DataTransformer:
        return self._transformer

    @property
    def config(self) -> MigrationConfig:
        return self._config

    @property
    def health_check(self) -> MigrationHealthCheck:
        return self._health_check


__all__ = ["MigrationRuntimeModule"]
