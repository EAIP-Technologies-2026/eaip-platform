"""Runtime module integration for the audit viewer subsystem."""

from __future__ import annotations

from typing import TYPE_CHECKING

from eaip.auditview.health import AuditViewHealthCheck
from eaip.logging.context import get_logger

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel


class AuditViewRuntimeModule:
    name: str = "auditview"

    def __init__(self) -> None:
        self._health_check = AuditViewHealthCheck()
        self._log = get_logger("eaip.auditview.integration")

    @property
    def health_check(self) -> AuditViewHealthCheck:
        return self._health_check

    async def start(self, kernel: RuntimeKernel) -> None:
        self._log.info("auditview.module.starting")
        kernel.platform.health.register(self._health_check)
        self._log.info("auditview.module.started")

    async def stop(self, _kernel: RuntimeKernel) -> None:
        self._log.info("auditview.module.stopping")


__all__ = ["AuditViewRuntimeModule"]
