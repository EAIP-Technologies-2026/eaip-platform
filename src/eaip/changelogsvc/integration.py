"""Runtime integration — ChangeLogRuntimeModule for kernel lifecycle."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

from eaip.capabilities.capability import Capability, CapabilityStatus
from eaip.changelogsvc.health import ChangeLogHealthCheck
from eaip.changelogsvc.models import ChangeLogConfig
from eaip.changelogsvc.service import ChangeLogService
from eaip.logging.context import get_logger

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel


class ChangeLogRuntimeModule:
    """RuntimeModule that registers the change log service with the kernel."""

    name: str = "changelogsvc"

    def __init__(self, config: ChangeLogConfig | None = None) -> None:
        self._config = config or ChangeLogConfig()
        self._service: ChangeLogService | None = None
        self._health_check: ChangeLogHealthCheck | None = None
        self._startup_duration: float = 0.0
        self._log = get_logger("eaip.changelogsvc.integration")

    async def start(self, kernel: RuntimeKernel) -> None:
        t0 = time.monotonic()
        self._log.info("changelogsvc.module.start")

        self._service = ChangeLogService(config=self._config)
        self._health_check = ChangeLogHealthCheck()

        kernel.platform.health.register(self._health_check)
        kernel.platform.capabilities.register(
            Capability(
                name="changelogsvc:service",
                title="Change Log Service",
                status=CapabilityStatus.ENABLED,
                tags=("changelog", "audit", "tracking"),
            )
        )

        self._startup_duration = time.monotonic() - t0
        self._log.info(
            "changelogsvc.module.complete",
            duration_s=round(self._startup_duration, 3),
        )

    async def stop(self, _kernel: RuntimeKernel) -> None:
        self._log.info("changelogsvc.module.stop")
