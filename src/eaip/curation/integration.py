"""Integration layer — CurationRuntimeModule for kernel lifecycle."""

from __future__ import annotations

from typing import TYPE_CHECKING

from eaip.curation.curator import CurationService
from eaip.curation.health import CurationHealthCheck
from eaip.logging.context import get_logger

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel


class CurationRuntimeModule:
    """RuntimeModule that bootstraps the knowledge curation subsystem."""

    name: str = "curation"

    def __init__(self, service: CurationService | None = None) -> None:
        self._service = service or CurationService()
        self._log = get_logger("eaip.curation.integration")

    @property
    def service(self) -> CurationService:
        return self._service

    async def start(self, kernel: RuntimeKernel) -> None:
        """Start the knowledge curation module."""
        self._log.info("curation.module.starting")
        pending = await self._service.get_pending_reviews()
        all_submissions = await self._service.list_submissions()
        health_check = CurationHealthCheck(
            pending_count=len(pending),
            total_submissions=len(all_submissions),
        )
        kernel.platform.health.register(health_check)
        self._log.info("curation.module.started")

    async def stop(self, _kernel: RuntimeKernel) -> None:
        """Shut down the knowledge curation module."""
        self._log.info("curation.module.stopping")


__all__ = ["CurationRuntimeModule"]
