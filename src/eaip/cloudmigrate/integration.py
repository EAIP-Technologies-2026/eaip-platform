"""Runtime integration — MigrationRuntimeModule for kernel lifecycle."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

from eaip.capabilities.capability import Capability, CapabilityStatus
from eaip.cloudmigrate.assistant import CloudMigrationAssistant
from eaip.cloudmigrate.health import MigrationHealthCheck
from eaip.cloudmigrate.models import MigrationConfig
from eaip.logging.context import get_logger

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel


class MigrationRuntimeModule:
    """RuntimeModule that registers the cloud migration assistant with the kernel."""

    name: str = "cloudmigrate"

    def __init__(self, config: MigrationConfig | None = None) -> None:
        self._config = config or MigrationConfig()
        self._assistant: CloudMigrationAssistant | None = None
        self._health_check: MigrationHealthCheck | None = None
        self._startup_duration: float = 0.0
        self._log = get_logger("eaip.cloudmigrate.integration")

    async def start(self, kernel: RuntimeKernel) -> None:
        t0 = time.monotonic()
        self._log.info("cloudmigrate.module.start")

        self._assistant = CloudMigrationAssistant(config=self._config)
        self._health_check = MigrationHealthCheck()

        kernel.platform.health.register(self._health_check)
        kernel.platform.capabilities.register(
            Capability(
                name="cloudmigrate:assistant",
                title="Cloud Migration Assistant",
                status=CapabilityStatus.ENABLED,
                tags=("migration", "cloud", "assessment"),
            )
        )

        self._startup_duration = time.monotonic() - t0
        self._log.info(
            "cloudmigrate.module.complete",
            duration_s=round(self._startup_duration, 3),
        )

    async def stop(self, _kernel: RuntimeKernel) -> None:
        self._log.info("cloudmigrate.module.stop")
