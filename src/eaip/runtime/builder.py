"""RuntimeBuilder — fluent construction of a configured :class:`RuntimeKernel`.

Typical usage::

    from eaip.runtime.builder import RuntimeBuilder

    kernel = (
        RuntimeBuilder(platform)
        .with_module(MyModule())
        .with_module(OtherModule())
        .with_plugin(my_plugin)
        .on_pre_start("validate_config", lambda k, ctx: ...)
        .build()
    )
    async with kernel:
        ...
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Self

from eaip.runtime.bootstrap import BootstrapHook
from eaip.runtime.composition import CompositionRoot
from eaip.runtime.hooks import ObservabilityHooks
from eaip.runtime.kernel import RuntimeKernel
from eaip.runtime.registry import RuntimeRegistry

if TYPE_CHECKING:
    from eaip.platform.platform import Platform
    from eaip.plugins.plugin import Plugin
    from eaip.runtime.context import RuntimeContext
    from eaip.runtime.host import RuntimeHost
    from eaip.runtime.module import RuntimeModule


class RuntimeBuilder:
    """Fluent builder for constructing a :class:`RuntimeKernel`.

    Parameters
    ----------
    platform:
        The :class:`~eaip.platform.platform.Platform` instance.
    """

    def __init__(self, platform: Platform) -> None:
        self._platform = platform
        self._modules: list[RuntimeModule] = []
        self._plugins: list[Plugin] = []
        self._hooks: ObservabilityHooks | None = None
        self._context: RuntimeContext | None = None
        self._pre_start_hooks: list[tuple[str, BootstrapHook]] = []
        self._post_start_hooks: list[tuple[str, BootstrapHook]] = []

    # ------------------------------------------------------------------
    # Configuration
    # ------------------------------------------------------------------

    def with_module(self, module: RuntimeModule) -> Self:
        """Register a :class:`~eaip.runtime.module.RuntimeModule`."""
        self._modules.append(module)
        return self

    def with_plugin(self, plugin: Plugin) -> Self:
        """Register a :class:`~eaip.plugins.plugin.Plugin`.

        The plugin is wrapped in a :class:`RuntimePluginAdapter` at build time.
        """
        self._plugins.append(plugin)
        return self

    def with_hooks(self, hooks: ObservabilityHooks) -> Self:
        """Set custom :class:`~eaip.runtime.hooks.ObservabilityHooks`."""
        self._hooks = hooks
        return self

    def with_context(self, ctx: RuntimeContext) -> Self:
        """Set the baseline :class:`~eaip.runtime.context.RuntimeContext`."""
        self._context = ctx
        return self

    def on_pre_start(self, name: str, fn: BootstrapHook) -> Self:
        """Register a pre-start bootstrap hook."""
        self._pre_start_hooks.append((name, fn))
        return self

    def on_post_start(self, name: str, fn: BootstrapHook) -> Self:
        """Register a post-start bootstrap hook."""
        self._post_start_hooks.append((name, fn))
        return self

    # ------------------------------------------------------------------
    # Build
    # ------------------------------------------------------------------

    def build(self) -> RuntimeKernel:
        """Construct and return a fully wired :class:`RuntimeKernel`.

        The builder creates:

        1. A :class:`~eaip.runtime.host.RuntimeHost`.
        2. A :class:`~eaip.runtime.registry.RuntimeRegistry`.
        3. A :class:`~eaip.runtime.bootstrap.BootstrapManager`.
        4. A :class:`~eaip.runtime.composition.CompositionRoot` that wires the
           kernel into the platform lifecycle.

        Modules and plugins are registered with the host; bootstrap hooks
        are registered with the manager.
        """
        from eaip.runtime.host import RuntimeHost
        from eaip.runtime.plugin import RuntimePluginAdapter

        # 1. Create the host.
        host = RuntimeHost(
            platform=self._platform,
            hooks=self._hooks,
            context=self._context,
        )

        # 2. Register modules.
        for mod in self._modules:
            host.add_module(mod)

        # 3. Register plugins as modules.
        for plugin in self._plugins:
            host.add_plugin(plugin)

        # 4. Create registry.
        registry = RuntimeRegistry()

        # 5. Create bootstrap manager.
        from eaip.runtime.bootstrap import BootstrapManager

        bootstrap = BootstrapManager()
        for name, fn in self._pre_start_hooks:
            bootstrap.add_pre_start(name, fn)
        for name, fn in self._post_start_hooks:
            bootstrap.add_post_start(name, fn)

        # 6. Create the kernel.
        kernel = RuntimeKernel(
            host=host,
            registry=registry,
            bootstrap=bootstrap,
            context=self._context,
        )

        # 7. Create and wire the composition root.
        root = CompositionRoot(platform=self._platform, kernel=kernel)
        root.wire()
        kernel.root = root

        return kernel


__all__ = ["RuntimeBuilder"]
