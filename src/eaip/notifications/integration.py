"""Runtime module integration for the notification engine."""

from __future__ import annotations

from typing import TYPE_CHECKING

from eaip.capabilities.capability import Capability, CapabilityStatus
from eaip.logging.context import get_logger
from eaip.notifications.engine import NotificationEngine
from eaip.notifications.health import NotificationHealthCheck
from eaip.notifications.models import NotificationConfig

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel


class NotificationRuntimeModule:
    """Runtime module that registers the notification engine with the kernel."""

    name: str = "notifications"

    def __init__(
        self,
        config: NotificationConfig | None = None,
        engine: NotificationEngine | None = None,
    ) -> None:
        self._config = config or NotificationConfig()
        self._engine = engine or NotificationEngine(config=self._config)
        self._log = get_logger("eaip.notifications.integration")

    @property
    def engine(self) -> NotificationEngine:
        return self._engine

    async def start(self, kernel: RuntimeKernel) -> None:
        self._log.info("notifications.module.starting")
        platform = kernel.platform
        capability = Capability(
            name="eaip.notifications",
            title="Notification Engine",
            description="Multi-channel notification dispatch with templates, preferences, digests, and delivery tracking",
            version="0.1.0",
            status=CapabilityStatus.ENABLED,
            tags=("notifications", "email", "sms", "push", "digest", "templates"),
        )
        platform.capabilities.register(capability)
        platform.health.register(NotificationHealthCheck(engine=self._engine))
        self._log.info("notifications.module.started")

    async def stop(self, kernel: RuntimeKernel) -> None:
        self._log.info("notifications.module.stopping")


__all__ = ["NotificationRuntimeModule"]
