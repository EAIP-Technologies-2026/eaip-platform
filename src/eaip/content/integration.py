"""Runtime module integration for the content registry."""

from __future__ import annotations

from typing import TYPE_CHECKING

from eaip.capabilities.capability import Capability, CapabilityStatus
from eaip.content.health import ContentHealthCheck
from eaip.content.models import ContentConfig
from eaip.content.registry import ContentRegistry
from eaip.content.versioning import ContentVersioning
from eaip.content.workflow import PublishingWorkflowEngine
from eaip.logging.context import get_logger

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel


class ContentRuntimeModule:
    name: str = "content"

    def __init__(
        self,
        config: ContentConfig | None = None,
        registry: ContentRegistry | None = None,
        versioning: ContentVersioning | None = None,
        workflow_engine: PublishingWorkflowEngine | None = None,
    ) -> None:
        self._config = config or ContentConfig()
        self._registry = registry or ContentRegistry(config=self._config)
        self._versioning = versioning or ContentVersioning(config=self._config)
        self._workflow_engine = workflow_engine or PublishingWorkflowEngine()
        self._log = get_logger("eaip.content.integration")

    @property
    def registry(self) -> ContentRegistry:
        return self._registry

    @property
    def versioning(self) -> ContentVersioning:
        return self._versioning

    @property
    def workflow_engine(self) -> PublishingWorkflowEngine:
        return self._workflow_engine

    async def start(self, kernel: RuntimeKernel) -> None:
        self._log.info("content.module.starting")
        platform = kernel.platform
        capability = Capability(
            name="eaip.content",
            title="Content Registry",
            description="Managed content registry with versioning, publishing workflow, and content delivery",
            version="0.1.0",
            status=CapabilityStatus.ENABLED,
            tags=("content", "registry", "versioning", "publishing", "workflow"),
        )
        platform.capabilities.register(capability)
        platform.health.register(ContentHealthCheck())
        self._log.info("content.module.started")

    async def stop(self, kernel: RuntimeKernel) -> None:
        self._log.info("content.module.stopping")


__all__ = ["ContentRuntimeModule"]
