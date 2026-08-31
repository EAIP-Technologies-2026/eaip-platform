"""Runtime module integration for content management."""

from __future__ import annotations

from typing import TYPE_CHECKING

from eaip.capabilities.capability import Capability, CapabilityStatus
from eaip.content_management.health import ContentManagementHealthCheck
from eaip.content_management.service import ContentManagementService
from eaip.logging.context import get_logger

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel


class ContentManagementRuntimeModule:
    name: str = "content_management"

    def __init__(
        self,
        service: ContentManagementService | None = None,
    ) -> None:
        self._service = service or ContentManagementService()
        self._log = get_logger("eaip.content_management.integration")

    @property
    def service(self) -> ContentManagementService:
        return self._service

    async def start(self, kernel: RuntimeKernel) -> None:
        self._log.info("content_management.module.starting")
        platform = kernel.platform
        capability = Capability(
            name="eaip.content_management",
            title="Content Management",
            description="Structured content management with collections, workflows, localization",
            version="0.1.0",
            status=CapabilityStatus.ENABLED,
            tags=("content", "management", "workflow", "localization", "delivery"),
        )
        platform.capabilities.register(capability)
        platform.health.register(ContentManagementHealthCheck())
        self._log.info("content_management.module.started")

    async def stop(self, _kernel: RuntimeKernel) -> None:
        self._log.info("content_management.module.stopping")


__all__ = ["ContentManagementRuntimeModule"]
