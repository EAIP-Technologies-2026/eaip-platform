"""Runtime integration — KnowledgePermissionRuntimeModule for kernel lifecycle."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

from eaip.knowledge_permissions.health import KnowledgePermissionHealthCheck
from eaip.knowledge_permissions.service import KnowledgePermissionService
from eaip.logging.context import get_logger

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel


class KnowledgePermissionRuntimeModule:
    """RuntimeModule that manages knowledge permissions during kernel boot.

    - On start: initialises the permission service and registers the health check.
    - On stop: disables all permission policies.
    """

    name: str = "knowledge_permissions"

    def __init__(
        self,
        service: KnowledgePermissionService | None = None,
    ) -> None:
        self._service = service or KnowledgePermissionService()
        self._log = get_logger("eaip.runtime.knowledge_permissions_integration")
        self._startup_duration: float = 0.0

    @property
    def startup_duration(self) -> float:
        return self._startup_duration

    @property
    def service(self) -> KnowledgePermissionService:
        return self._service

    async def start(self, kernel: RuntimeKernel) -> None:
        self._log.info("knowledge_permissions.module.start")
        t0 = time.monotonic()

        check = KnowledgePermissionHealthCheck(self._service)
        kernel.platform.health.register(check)

        self._startup_duration = time.monotonic() - t0
        self._log.info(
            "knowledge_permissions.module.complete",
            duration_s=round(self._startup_duration, 3),
        )

    async def stop(self, _kernel: RuntimeKernel) -> None:
        self._log.info("knowledge_permissions.module.stop")
        updated = self._service.update_config(enabled=False)
        self._service._config = updated
        self._log.info("knowledge_permissions.module.stopped")


__all__ = ["KnowledgePermissionRuntimeModule"]
