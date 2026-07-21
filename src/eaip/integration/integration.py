"""Runtime module integration for the integration hub."""

from __future__ import annotations

from typing import TYPE_CHECKING

from eaip.capabilities.capability import Capability, CapabilityStatus
from eaip.integration.catalog import IntegrationCatalog
from eaip.integration.health import IntegrationHealthCheck
from eaip.integration.hub import IntegrationHub
from eaip.integration.models import IntegrationConfig
from eaip.integration.transform import MessageTransformationService
from eaip.integration.webhooks import WebhookManager
from eaip.logging.context import get_logger

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel


class IntegrationRuntimeModule:
    name: str = "integration"

    def __init__(
        self,
        config: IntegrationConfig | None = None,
        hub: IntegrationHub | None = None,
        webhook_manager: WebhookManager | None = None,
        transform_service: MessageTransformationService | None = None,
        catalog: IntegrationCatalog | None = None,
    ) -> None:
        self._config = config or IntegrationConfig()
        self._hub = hub or IntegrationHub()
        self._webhook_manager = webhook_manager or WebhookManager()
        self._transform_service = transform_service or MessageTransformationService()
        self._catalog = catalog or IntegrationCatalog(hub=self._hub)
        self._log = get_logger("eaip.integration.integration")

    @property
    def hub(self) -> IntegrationHub:
        return self._hub

    @property
    def webhook_manager(self) -> WebhookManager:
        return self._webhook_manager

    @property
    def transform_service(self) -> MessageTransformationService:
        return self._transform_service

    @property
    def catalog(self) -> IntegrationCatalog:
        return self._catalog

    async def start(self, kernel: RuntimeKernel) -> None:
        self._log.info("integration.module.starting")
        platform = kernel.platform
        capability = Capability(
            name="eaip.integration",
            title="Enterprise Integration Hub",
            description="External system connectors, webhook receiver, message transformation, routing rules, and integration catalog",
            version="0.1.0",
            status=CapabilityStatus.ENABLED,
            tags=("integration", "connectors", "webhooks", "routing", "transformation", "catalog"),
        )
        platform.capabilities.register(capability)
        platform.health.register(IntegrationHealthCheck(hub=self._hub))
        self._log.info("integration.module.started")

    async def stop(self, kernel: RuntimeKernel) -> None:
        self._log.info("integration.module.stopping")


__all__ = ["IntegrationRuntimeModule"]
