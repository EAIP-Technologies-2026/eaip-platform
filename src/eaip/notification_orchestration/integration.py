"""RuntimeKernel integration — registers NotificationOrchestrationService as a RuntimeModule."""

from __future__ import annotations

from typing import TYPE_CHECKING

from eaip.capabilities.capability import Capability, CapabilityStatus
from eaip.logging.context import get_logger
from eaip.notification_orchestration.health import NotificationOrchestrationHealthCheck
from eaip.notification_orchestration.service import NotificationOrchestrationService

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel


class NotificationOrchestrationRuntimeModule:
    """Runtime module that registers the notification orchestration capability."""

    name: str = "notification_orchestration"

    def __init__(self, service: NotificationOrchestrationService | None = None) -> None:
        """Initialize the runtime module with an optional service instance."""
        self._service = service or NotificationOrchestrationService()
        self._log = get_logger("eaip.notification_orchestration.integration")

    @property
    def service(self) -> NotificationOrchestrationService:
        """Return the underlying orchestration service."""
        return self._service

    async def start(self, kernel: RuntimeKernel) -> None:
        """Start the module and register capability and health check with the kernel."""
        self._log.info("notification_orchestration.module.starting")
        platform = kernel.platform
        capability = Capability(
            name="eaip.notification_orchestration",
            title="Notification Orchestration",
            description="Rule-based notification routing, escalation, digests, and scheduling",
            version="0.1.0",
            status=CapabilityStatus.ENABLED,
            tags=("notification", "orchestration", "routing", "escalation", "digest", "scheduling"),
        )
        platform.capabilities.register(capability)
        platform.health.register(NotificationOrchestrationHealthCheck(service=self._service))
        self._log.info("notification_orchestration.module.started")

    async def stop(self, _kernel: RuntimeKernel) -> None:
        """Stop the module gracefully."""
        self._log.info("notification_orchestration.module.stopping")


__all__ = ["NotificationOrchestrationRuntimeModule"]
