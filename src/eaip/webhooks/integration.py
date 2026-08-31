"""Runtime module integration for the webhook dispatcher."""

from __future__ import annotations

from typing import TYPE_CHECKING

from eaip.capabilities.capability import Capability, CapabilityStatus
from eaip.logging.context import get_logger
from eaip.webhooks.dispatcher import WebhookDispatcher
from eaip.webhooks.health import WebhookHealthCheck
from eaip.webhooks.models import WebhookConfig

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel


class WebhookRuntimeModule:
    """Runtime module that registers the webhook dispatcher with the kernel."""

    name: str = "webhooks"

    def __init__(
        self,
        config: WebhookConfig | None = None,
        dispatcher: WebhookDispatcher | None = None,
    ) -> None:
        self._config = config or WebhookConfig()
        self._dispatcher = dispatcher or WebhookDispatcher(config=self._config)
        self._log = get_logger("eaip.webhooks.integration")

    @property
    def dispatcher(self) -> WebhookDispatcher:
        return self._dispatcher

    async def start(self, kernel: RuntimeKernel) -> None:
        self._log.info("webhooks.module.starting")
        platform = kernel.platform
        capability = Capability(
            name="eaip.webhooks",
            title="Webhook Dispatcher",
            description="Reliable webhook dispatch with retry queues, delivery receipts, HMAC signing, and delivery tracking",
            version="0.1.0",
            status=CapabilityStatus.ENABLED,
            tags=("webhooks", "dispatch", "signing", "retry", "delivery"),
        )
        platform.capabilities.register(capability)
        platform.health.register(WebhookHealthCheck(dispatcher=self._dispatcher))
        self._log.info("webhooks.module.started")

    async def stop(self, kernel: RuntimeKernel) -> None:
        self._log.info("webhooks.module.stopping")


__all__ = ["WebhookRuntimeModule"]
