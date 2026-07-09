"""Runtime integration — PluginRuntimeModule, health check, metrics, event hooks."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

from eaip.events.event import DomainEvent
from eaip.health.checks import HealthCheck, HealthReport, HealthStatus
from eaip.logging.context import get_logger
from eaip.plugins.lifecycle import PluginLifecycleManager

if TYPE_CHECKING:
    from eaip.metrics.metrics import Meter
    from eaip.platform.platform import Platform
    from eaip.runtime.kernel import RuntimeKernel


class PluginHealthCheck(HealthCheck):
    """Health check that reports plugin subsystem status."""

    name: str = "plugins"

    def __init__(self, lifecycle: PluginLifecycleManager) -> None:
        """Initialize the health check.

        Args:
            lifecycle: The plugin lifecycle manager.
        """
        self._lifecycle = lifecycle

    async def check(self) -> HealthReport:
        """Run the plugin health check.

        Returns:
            A HealthReport describing plugin subsystem health.
        """
        installed = self._lifecycle.loader.count()
        activated = self._lifecycle.loader.activated_count

        if installed == 0:
            return HealthReport(
                component="plugins",
                status=HealthStatus.HEALTHY,
                message="no plugins installed",
                details={"installed": 0, "activated": 0},
            )

        all_activated = installed == activated
        status = HealthStatus.HEALTHY if all_activated else HealthStatus.DEGRADED
        message = (
            f"all {installed} plugins activated"
            if all_activated
            else f"{activated}/{installed} plugins activated"
        )
        return HealthReport(
            component="plugins",
            status=status,
            message=message,
            details={
                "installed": installed,
                "activated": activated,
                    "plugin_names": self._lifecycle.loader.activated,
            },
        )


class PluginRuntimeModule:
    """RuntimeModule that manages plugins during kernel boot and shutdown.

    Attaches to the kernel lifecycle:
    - On start: discovers, installs, validates, and activates plugins.
    - On stop: deactivates all plugins.

    Also registers a PluginHealthCheck and publishes plugin lifecycle
    events to the EventBus.
    """

    name: str = "plugins"

    def __init__(
        self,
        lifecycle: PluginLifecycleManager,
        platform: Platform,
    ) -> None:
        """Initialize the PluginRuntimeModule.

        Args:
            lifecycle: The plugin lifecycle manager.
            platform: The platform instance.
        """
        self._lifecycle = lifecycle
        self._platform = platform
        self._log = get_logger("eaip.runtime.plugin_integration")
        self._startup_duration: float = 0.0

    @property
    def startup_duration(self) -> float:
        """Return the last plugin startup duration in seconds."""
        return self._startup_duration

    async def start(self, _kernel: RuntimeKernel) -> None:
        """Discover, install, and activate plugins during kernel boot.

        Args:
            kernel: The runtime kernel.
        """
        self._log.info("plugin.module.start")
        t0 = time.monotonic()

        installed = await self._lifecycle.discover_and_install()
        if not installed:
            self._log.info("plugin.module.no_plugins_discovered")
            self._startup_duration = time.monotonic() - t0
            return

        dep_errors = self._lifecycle.validate_dependencies()
        if dep_errors:
            self._log.error(
                "plugin.module.dependency_errors",
                count=len(dep_errors),
                errors=dep_errors,
            )

        try:
            await self._lifecycle.activate_all(self._platform)
        except BaseException as exc:
            self._log.error("plugin.module.activate_failed", error=repr(exc))

        self._startup_duration = time.monotonic() - t0
        self._log.info(
            "plugin.module.complete",
            installed=self._lifecycle.loader.count(),
                activated=self._lifecycle.loader.activated_count,
            duration_s=round(self._startup_duration, 3),
        )

    async def stop(self, _kernel: RuntimeKernel) -> None:
        """Deactivate all plugins during kernel shutdown.

        Args:
            kernel: The runtime kernel.
        """
        self._log.info("plugin.module.stop")
        await self._lifecycle.deactivate_all(self._platform)
        self._log.info("plugin.module.stopped")


# ---------------------------------------------------------------------------
# Plugin domain events
# ---------------------------------------------------------------------------


class PluginInstalled(DomainEvent):
    """Emitted when a plugin is installed."""

    name: str
    version: str


class PluginActivated(DomainEvent):
    """Emitted when a plugin is activated."""

    name: str
    version: str


class PluginDeactivated(DomainEvent):
    """Emitted when a plugin is deactivated."""

    name: str


# ---------------------------------------------------------------------------
# Convenience wire-up helpers
# ---------------------------------------------------------------------------


def register_plugin_health_check(
    kernel: RuntimeKernel,
    lifecycle: PluginLifecycleManager,
) -> None:
    """Register a PluginHealthCheck with the platform's health reporter.

    Args:
        kernel: The runtime kernel.
        lifecycle: The plugin lifecycle manager.
    """
    check = PluginHealthCheck(lifecycle)
    kernel.platform.health.register(check)


def register_plugin_metrics(
    meter: Meter,
) -> None:
    """Record plugin-related gauges on the given meter.

    Creates:
    - ``plugin.installed`` (gauge)
    - ``plugin.activated`` (gauge)

    Args:
        meter: The meter to register gauges on.
    """
    meter.gauge("plugin.installed", labels={"component": "plugins"}).set(0)
    meter.gauge("plugin.activated", labels={"component": "plugins"}).set(0)


__all__ = [
    "PluginActivated",
    "PluginDeactivated",
    "PluginHealthCheck",
    "PluginInstalled",
    "PluginRuntimeModule",
    "register_plugin_health_check",
    "register_plugin_metrics",
]
