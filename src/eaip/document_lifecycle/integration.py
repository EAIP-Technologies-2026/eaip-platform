"""Runtime module integration for the document lifecycle subsystem."""

from __future__ import annotations

from typing import TYPE_CHECKING

from eaip.capabilities.capability import Capability, CapabilityStatus
from eaip.document_lifecycle.health import DocumentLifecycleHealthCheck
from eaip.document_lifecycle.models import DocumentLifecycleConfig
from eaip.document_lifecycle.service import DocumentLifecycleService
from eaip.logging.context import get_logger

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel


class DocumentLifecycleRuntimeModule:
    """Runtime module for the document lifecycle subsystem."""

    name: str = "document_lifecycle"

    def __init__(
        self,
        config: DocumentLifecycleConfig | None = None,
        service: DocumentLifecycleService | None = None,
    ) -> None:
        self._config = config or DocumentLifecycleConfig()
        self._service = service or DocumentLifecycleService(config=self._config)
        self._log = get_logger("eaip.document_lifecycle.integration")

    @property
    def service(self) -> DocumentLifecycleService:
        """Return the underlying DocumentLifecycleService."""
        return self._service

    async def start(self, kernel: RuntimeKernel) -> None:
        """Start the runtime module and register with the kernel."""
        self._log.info("document_lifecycle.module.starting")
        platform = kernel.platform
        cap_desc = (
            "Document lifecycle management with versioning, approvals, reviews, and retention"
        )
        capability = Capability(
            name="eaip.document_lifecycle",
            title="Document Lifecycle",
            description=cap_desc,
            version="0.1.0",
            status=CapabilityStatus.ENABLED,
            tags=(
                "document",
                "lifecycle",
                "versioning",
                "approval",
                "review",
                "retention",
            ),
        )
        platform.capabilities.register(capability)
        platform.health.register(DocumentLifecycleHealthCheck())
        self._log.info("document_lifecycle.module.started")

    async def stop(self, _kernel: RuntimeKernel) -> None:
        """Stop the runtime module."""
        self._log.info("document_lifecycle.module.stopping")


__all__ = ["DocumentLifecycleRuntimeModule"]
