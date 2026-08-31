"""Runtime module integration for the tenant subsystem."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from eaip.logging.context import get_logger
from eaip.tenants.health import TenantHealthCheck

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel


class TenantRuntimeModule:
    """RuntimeModule that registers the tenant subsystem into the kernel.

    On start, initializes tenant services (TenantManager, BillingService,
    TenantIsolationService, CrossTenantAnalytics) and registers health checks.
    On stop, performs cleanup of tenant resources.
    """

    name: str = "tenants"

    def __init__(self, health_check: TenantHealthCheck | None = None) -> None:
        self._health_check = health_check or TenantHealthCheck()
        self._log = get_logger("eaip.tenants.integration")
        self._started: bool = False
        self._manager: Any = None
        self._billing: Any = None
        self._isolation: Any = None
        self._analytics: Any = None

    async def start(self, kernel: RuntimeKernel) -> None:
        """Initialize tenant services and register health checks.

        Args:
            kernel: The runtime kernel.
        """
        from eaip.tenants.billing import BillingService
        from eaip.tenants.isolation import TenantIsolationService
        from eaip.tenants.manager import TenantManager
        from eaip.tenants.reporting import CrossTenantAnalytics

        # Access EventBus from kernel.platform (existing pattern)
        event_bus = kernel.platform.events if hasattr(kernel.platform, "events") else None

        self._manager = TenantManager(event_bus=event_bus)
        self._billing = BillingService(event_bus=event_bus)
        self._isolation = TenantIsolationService()
        self._analytics = CrossTenantAnalytics(
            tenant_manager=self._manager,
            billing_service=self._billing,
        )

        kernel.platform.health.register(self._health_check)
        self._started = True
        self._log.info("tenants.module.started")

    async def stop(self, kernel: RuntimeKernel) -> None:
        """Clean up tenant resources on shutdown.

        Args:
            kernel: The runtime kernel.
        """
        self._started = False
        self._log.info("tenants.module.stopped")

    @property
    def started(self) -> bool:
        """Return whether the module has been started."""
        return self._started

    @property
    def manager(self) -> Any:
        """Return the TenantManager instance."""
        return self._manager

    @property
    def billing(self) -> Any:
        """Return the BillingService instance."""
        return self._billing

    @property
    def isolation(self) -> Any:
        """Return the TenantIsolationService instance."""
        return self._isolation

    @property
    def analytics(self) -> Any:
        """Return the CrossTenantAnalytics instance."""
        return self._analytics
