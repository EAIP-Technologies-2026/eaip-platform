"""Runtime manager — introspection and control of the running platform."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from eaip.admin.events import AdminActionExecuted, CapabilityToggled, PluginReloaded
from eaip.admin.models import AdminAction, RuntimeSnapshot
from eaip.logging.context import get_logger

if TYPE_CHECKING:
    from eaip.events.bus import EventBus
    from eaip.health.checks import HealthReport
    from eaip.platform.platform import Platform
    from eaip.runtime.kernel import RuntimeKernel
    from eaip.settings.core_settings import PlatformSettings


class RuntimeManager:
    """Provides runtime introspection and administrative control.

    Exposes snapshot capture, capability toggling, plugin reload, and
    health summary aggregation.
    """

    def __init__(
        self,
        kernel: RuntimeKernel,
        event_bus: EventBus | None = None,
    ) -> None:
        """Initialize RuntimeManager.

        Args:
            kernel: The runtime kernel to manage.
            event_bus: Optional event bus for publishing admin events.
        """
        self._kernel = kernel
        self._event_bus = event_bus
        self._log = get_logger("eaip.admin.manager")

    @property
    def platform(self) -> Platform:
        """Return the underlying platform."""
        return self._kernel.platform

    async def get_snapshot(self) -> RuntimeSnapshot:
        """Capture the current runtime state.

        Collects component states from the health reporter, the active
        capability list, and module registration.

        Returns:
            A RuntimeSnapshot of the current state.
        """
        platform = self.platform
        health_report = await platform.health.report()

        component_states: dict[str, str] = {}
        self._collect_states(health_report, component_states)

        capabilities = list(platform.capabilities.all())
        active_capabilities = [c.name for c in capabilities if c.status == "enabled"]

        active_modules = list(self._kernel._modules.keys())

        uptime = 0.0

        return RuntimeSnapshot(
            component_states=component_states,
            health_status=health_report.status.value,
            active_modules=active_modules,
            active_capabilities=active_capabilities,
            uptime_seconds=uptime,
        )

    async def toggle_capability(self, name: str, enable: bool) -> bool:
        """Enable or disable a capability.

        Args:
            name: The name of the capability.
            enable: True to enable, False to disable.

        Returns:
            True if the operation succeeded.

        Raises:
            ValueError: If the capability is not found.
        """
        platform = self.platform
        registry = platform.capabilities
        try:
            if enable:
                registry.enable(name)
            else:
                registry.disable(name)
        except LookupError as exc:
            raise ValueError(f"Capability {name!r} not found") from exc

        action = AdminAction(
            action_id=f"toggle-{name}-{id(self)}",
            action_type="toggle_capability",
            target=f"capability:{name}",
            performed_by="system",
            details={"name": name, "enabled": enable},
            result="success",
        )
        if self._event_bus is not None:
            await self._event_bus.publish(
                CapabilityToggled(
                    name=name,
                    enabled=enable,
                    toggled_by=action.performed_by,
                )
            )
            await self._event_bus.publish(
                AdminActionExecuted(
                    action_id=action.action_id,
                    action_type=action.action_type,
                    target=action.target,
                    performed_by=action.performed_by,
                    result=action.result,
                    details=action.details,
                )
            )

        self._log.info("admin.capability_toggled", name=name, enabled=enable)
        return True

    async def reload_plugin(self, plugin_name: str) -> bool:
        """Reload a plugin by name.

        Args:
            plugin_name: The name of the plugin to reload.

        Returns:
            True if the plugin was reloaded successfully.
        """
        platform = self.platform
        loader = platform.plugin_loader
        try:
            await loader.deactivate(plugin_name, platform)
            await loader.activate(plugin_name, platform)
            success = True
            message = "ok"
        except Exception as exc:
            success = False
            message = str(exc)

        if self._event_bus is not None:
            await self._event_bus.publish(
                PluginReloaded(
                    plugin_name=plugin_name,
                    success=success,
                    message=message,
                )
            )

        self._log.info(
            "admin.plugin_reloaded",
            plugin_name=plugin_name,
            success=success,
        )
        return success

    async def get_config(self) -> PlatformSettings:
        """Get the current runtime configuration.

        Returns:
            The PlatformSettings instance.
        """
        return self.platform.settings

    def list_active_modules(self) -> list[str]:
        """List names of all active runtime modules.

        Returns:
            A list of module names registered in the kernel.
        """
        return list(self._kernel._modules.keys())

    def list_active_capabilities(self) -> list[str]:
        """List names of all active (enabled) capabilities.

        Returns:
            A list of enabled capability names.
        """
        capabilities = list(self.platform.capabilities.all())
        return [c.name for c in capabilities if c.status == "enabled"]

    def get_health_summary(self) -> dict[str, Any]:
        """Return an aggregated health summary string.

        Returns:
            A dictionary describing health across all checked components.
        """
        return {"status": "unknown", "summary": "Aggregated health not yet available"}

    @staticmethod
    def _collect_states(
        report: HealthReport,
        accumulator: dict[str, str],
    ) -> None:
        accumulator[report.component] = report.status.value
        for child in report.children:
            RuntimeManager._collect_states(child, accumulator)
