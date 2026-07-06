"""Plugin runtime — bridges platform-level plugins into the runtime kernel.

The :class:`RuntimePluginAdapter` wraps a :class:`~eaip.plugins.plugin.Plugin`
into a :class:`~eaip.runtime.module.RuntimeModule` so that plugins can
participate in the runtime lifecycle alongside first-party kernel modules.

This allows plugins to:

* Declare **dependencies** on other modules or plugins.
* Receive a **RuntimeContext** during activation.
* Be **ordered** by the dependency graph alongside native modules.
* Register **health checks** through the standard module mechanism.

Usage::

    adapter = RuntimePluginAdapter(plugin, platform)
    host.add_module(adapter)
    await host.start()  # activates plugin as part of startup
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from eaip.plugins.plugin import Plugin

if TYPE_CHECKING:  # pragma: no cover
    from eaip.platform.platform import Platform
    from eaip.runtime.context import RuntimeContext
    from eaip.runtime.host import RuntimeHost


class RuntimePluginAdapter:
    """Adapts a :class:`~eaip.plugins.plugin.Plugin` into the
    :class:`~eaip.runtime.module.RuntimeModule` protocol.

    The adapter's ``name`` is taken from the plugin's manifest.  The
    plugin's ``activate`` / ``deactivate`` methods are called when the
    host starts / stops this module.

    Parameters
    ----------
    plugin:
        The plugin instance to adapt.
    platform:
        The :class:`~eaip.platform.platform.Platform` to pass to the
        plugin's ``activate`` and ``deactivate`` methods.
    """

    def __init__(self, plugin: Plugin, platform: Platform) -> None:
        self._plugin = plugin
        self._platform = platform
        self._activated = False

    # ------------------------------------------------------------------
    # RuntimeModule protocol
    # ------------------------------------------------------------------

    @property
    def name(self) -> str:
        """Module name derived from the plugin manifest."""
        return self._plugin.manifest.name

    @property
    def dependencies(self) -> tuple[str, ...]:
        """Plugins declare no runtime dependencies by default."""
        return ()

    async def on_start(self, host: RuntimeHost, ctx: RuntimeContext) -> None:
        """Activate the plugin when the host starts this module."""
        if not self._activated:
            await self._plugin.activate(self._platform)
            self._activated = True

    async def on_stop(self, host: RuntimeHost, ctx: RuntimeContext) -> None:
        """Deactivate the plugin when the host stops this module."""
        if self._activated:
            try:
                await self._plugin.deactivate(self._platform)
            finally:
                self._activated = False


__all__ = ["RuntimePluginAdapter"]
