"""Runtime module integration for the import/export engine."""

from __future__ import annotations

from typing import TYPE_CHECKING

from eaip.capabilities.capability import Capability, CapabilityStatus
from eaip.import_export.health import ImportExportHealthCheck
from eaip.import_export.models import ImportExportConfig
from eaip.import_export.service import ImportExportService
from eaip.logging.context import get_logger

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel


class ImportExportRuntimeModule:
    name: str = "import_export"

    def __init__(
        self,
        config: ImportExportConfig | None = None,
        service: ImportExportService | None = None,
    ) -> None:
        self._config = config or ImportExportConfig()
        self._service = service or ImportExportService(config=self._config)
        self._log = get_logger("eaip.import_export.integration")

    @property
    def service(self) -> ImportExportService:
        return self._service

    async def start(self, kernel: RuntimeKernel) -> None:
        self._log.info("import_export.module.starting")
        platform = kernel.platform
        capability = Capability(
            name="eaip.import_export",
            title="Import/Export Engine",
            description="Import jobs, export jobs, format conversion, scheduling, and validation",
            version="0.1.0",
            status=CapabilityStatus.ENABLED,
            tags=("import", "export", "scheduler", "validation", "formats"),
        )
        platform.capabilities.register(capability)
        platform.health.register(ImportExportHealthCheck(service=self._service))
        self._log.info("import_export.module.started")

    async def stop(self, _kernel: RuntimeKernel) -> None:
        self._log.info("import_export.module.stopping")


__all__ = ["ImportExportRuntimeModule"]
