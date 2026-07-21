"""Runtime integration — ConfigBackupRuntimeModule for kernel lifecycle."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

from eaip.capabilities.capability import Capability, CapabilityStatus
from eaip.configbackup.health import ConfigBackupHealthCheck
from eaip.configbackup.models import BackupConfig
from eaip.configbackup.service import ConfigBackupService
from eaip.logging.context import get_logger

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel


class ConfigBackupRuntimeModule:
    """RuntimeModule that registers the config backup service with the kernel."""

    name: str = "configbackup"

    def __init__(self, config: BackupConfig | None = None) -> None:
        self._config = config or BackupConfig()
        self._service: ConfigBackupService | None = None
        self._health_check: ConfigBackupHealthCheck | None = None
        self._startup_duration: float = 0.0
        self._log = get_logger("eaip.configbackup.integration")

    async def start(self, kernel: RuntimeKernel) -> None:
        t0 = time.monotonic()
        self._log.info("configbackup.module.start")

        self._service = ConfigBackupService(config=self._config)
        self._health_check = ConfigBackupHealthCheck()

        kernel.platform.health.register(self._health_check)
        kernel.platform.capabilities.register(
            Capability(
                name="configbackup:service",
                title="Configuration Backup Service",
                status=CapabilityStatus.ENABLED,
                tags=("config", "backup", "snapshot"),
            )
        )

        self._startup_duration = time.monotonic() - t0
        self._log.info(
            "configbackup.module.complete",
            duration_s=round(self._startup_duration, 3),
        )

    async def stop(self, _kernel: RuntimeKernel) -> None:
        self._log.info("configbackup.module.stop")
