"""RuntimeHost — the kernel that manages the full lifecycle of runtime modules.

:class:`RuntimeHost` is the central orchestrator for the Runtime Kernel layer
(Layer 2 of the EAIP constitution).  It sits above the :class:`Platform`
(composition root) and below the capability/adapter layers.

Responsibilities
----------------
1. **Module registration** — accept :class:`~eaip.runtime.module.RuntimeModule`
   instances via :class:`~eaip.runtime.loader.ModuleLoader`.
2. **Dependency resolution** — delegate to :class:`~eaip.runtime.graph.DependencyGraph`
   to compute a valid startup order (topological sort).
3. **Lifecycle orchestration** — start modules in dependency order; stop them
   in reverse order.  On start failure, roll back already-started modules.
4. **Context propagation** — bind a :class:`~eaip.runtime.context.RuntimeContext`
   for the startup and shutdown passes; modules receive it via ``on_start`` /
   ``on_stop``.
5. **Health integration** — register a
   :class:`~eaip.runtime.health.RuntimeHealthCheck` per module into the
   platform :class:`~eaip.health.reporter.HealthReporter`.
6. **Observability** — fire :class:`~eaip.runtime.hooks.ObservabilityHooks`
   at every lifecycle boundary.
7. **Event publishing** — publish typed :class:`~eaip.runtime.events.RuntimeEvent`
   instances onto the platform :class:`~eaip.events.bus.EventBus`.

Usage
-----
::

    host = RuntimeHost(platform=platform)
    host.add_module(TelemetryModule())
    host.add_module(SchedulerModule())

    async with host:
        # modules are running; platform health includes module checks
        ...

Or equivalently::

    await host.start()
    try:
        ...
    finally:
        await host.stop()
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from eaip.exceptions.domain import DuplicateRegistrationError
from eaip.logging.context import get_logger
from eaip.runtime.bus import RuntimeEventBus
from eaip.runtime.context import RuntimeContext, reset_context, set_context
from eaip.runtime.di import RuntimeContainer
from eaip.runtime.events import (
    ModuleStarted,
    ModuleStartFailed,
    ModuleStopFailed,
    ModuleStopped,
    RuntimeRunning,
    RuntimeStarting,
    RuntimeStopped,
    RuntimeStopping,
)
from eaip.runtime.exceptions import ModuleActivationError
from eaip.runtime.graph import DependencyGraph
from eaip.runtime.health import RuntimeHealthCheck
from eaip.runtime.hooks import ObservabilityHooks
from eaip.runtime.loader import ModuleLoader
from eaip.runtime.module import BaseRuntimeModule, RuntimeModule
from eaip.runtime.plugin import RuntimePluginAdapter

if TYPE_CHECKING:  # pragma: no cover
    from eaip.platform.platform import Platform
    from eaip.plugins.plugin import Plugin


class RuntimeHost:
    """Kernel-level orchestrator for runtime modules.

    Parameters
    ----------
    platform:
        The :class:`~eaip.platform.platform.Platform` this host operates within.
        The host reads subsystems (events, health, lifecycle) from the platform.
    hooks:
        Optional :class:`~eaip.runtime.hooks.ObservabilityHooks` for
        synchronous instrumentation.  If ``None``, a no-op instance is used.
    context:
        Optional baseline :class:`~eaip.runtime.context.RuntimeContext` to use
        for startup / shutdown passes.  If ``None``, a fresh context is created.
    """

    def __init__(
        self,
        *,
        platform: Platform,
        hooks: ObservabilityHooks | None = None,
        context: RuntimeContext | None = None,
    ) -> None:
        self._platform = platform
        self._hooks = hooks or ObservabilityHooks()
        self._base_ctx = context or RuntimeContext.create(
            environment=str(platform.settings.core.environment),
            tenant_id=None,
        )
        self._loader = ModuleLoader()
        self._events = RuntimeEventBus(self._platform.events)
        self._container = RuntimeContainer(self._platform.container)
        self._started: list[RuntimeModule] = []  # ordered list of started modules
        self._running = False
        self._log = get_logger("eaip.runtime.host")

    # ------------------------------------------------------------------
    # Module management
    # ------------------------------------------------------------------

    def add_module(self, module: RuntimeModule) -> None:
        """Register ``module`` with the loader.

        This may be called at any point before :meth:`start`.  After the host
        has started, adding new modules is not supported (raises
        :class:`~eaip.exceptions.domain.LifecycleError` indirectly via the
        underlying platform lifecycle manager).
        """
        if self._running:
            raise DuplicateRegistrationError(
                f"cannot add module {module.name!r} while the host is running; "
                "stop the host first",
                context={"module": module.name},
            )
        self._loader.register(module)

    def add_plugin(self, plugin: Plugin) -> RuntimeModule:
        """Wrap a :class:`~eaip.plugins.plugin.Plugin` as a module and register it.

        This is a convenience wrapper around :meth:`add_module` that adapts a
        :class:`~eaip.plugins.plugin.Plugin` to the
        :class:`~eaip.runtime.module.RuntimeModule` protocol via
        :class:`~eaip.runtime.plugin.RuntimePluginAdapter` before registration.

        Returns the adapter so callers can inspect its metadata.
        """
        adapter = RuntimePluginAdapter(plugin=plugin, platform=self._platform)
        self.add_module(adapter)
        return adapter

    def get_module(self, name: str) -> RuntimeModule | None:
        """Return the module registered under ``name``, or ``None``."""
        return self._loader.get(name)

    @property
    def module_names(self) -> list[str]:
        """Sorted list of registered module names."""
        return self._loader.names()

    @property
    def events(self) -> RuntimeEventBus:
        """Runtime event bus for subscribing and publishing domain events.

        This property returns a :class:`~eaip.runtime.bus.RuntimeEventBus`
        that wraps the platform event bus and automatically attaches the
        current :class:`~eaip.runtime.context.RuntimeContext` (``run_id``
        as ``correlation_id``) to every published event.
        """
        return self._events

    @property
    def container(self) -> RuntimeContainer:
        """Runtime DI container for resolving platform services.

        This property returns a :class:`~eaip.runtime.di.RuntimeContainer`
        that wraps the platform's :class:`~eaip.dependency_injection.container.Container`
        and provides module-scoped lifecycle tracking.
        """
        return self._container

    @property
    def is_running(self) -> bool:
        """``True`` once :meth:`start` has completed successfully."""
        return self._running

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def start(self) -> None:
        """Resolve dependency order and start all modules.

        Raises :class:`~eaip.runtime.exceptions.ModuleActivationError` if any
        module fails to start; modules that already started are rolled back.
        """
        modules = self._loader.all()
        graph = DependencyGraph(modules)
        ordered = graph.ordered()

        ctx = self._base_ctx.derive()
        token = set_context(ctx)

        try:
            self._log.info(
                "runtime.host.starting",
                module_count=len(ordered),
                run_id=ctx.run_id,
            )
            self._hooks.fire_host_starting(module_count=len(ordered), ctx=ctx)

            await self._platform.events.publish(
                RuntimeStarting(module_count=len(ordered))
            )

            try:
                for module in ordered:
                    await self._start_module(module, ctx)
            except Exception:
                # Roll back already-started modules in reverse order.
                rollback_ctx = ctx.derive()
                await self._rollback(rollback_ctx)
                raise

            self._running = True
            self._log.info("runtime.host.running", module_count=len(ordered))
            self._hooks.fire_host_running(module_count=len(ordered), ctx=ctx)
            await self._platform.events.publish(RuntimeRunning(module_count=len(ordered)))

        finally:
            reset_context(token)

    async def stop(self) -> None:
        """Stop all started modules in reverse startup order.

        Idempotent: calling :meth:`stop` on an already-stopped host is safe.
        """
        if not self._running and not self._started:
            return

        ctx = self._base_ctx.derive()
        token = set_context(ctx)

        try:
            self._log.info("runtime.host.stopping")
            self._hooks.fire_host_stopping(ctx=ctx)
            await self._platform.events.publish(RuntimeStopping())

            await self._rollback(ctx)
            self._running = False

            self._log.info("runtime.host.stopped")
            self._hooks.fire_host_stopped(ctx=ctx)
            await self._platform.events.publish(RuntimeStopped())

        finally:
            reset_context(token)

    async def __aenter__(self) -> RuntimeHost:
        await self.start()
        return self

    async def __aexit__(self, *_: object) -> None:
        await self.stop()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _start_module(self, module: RuntimeModule, ctx: RuntimeContext) -> None:
        name = module.name
        self._log.debug("runtime.module.starting", module=name)
        self._hooks.fire_module_starting(module=name, ctx=ctx)
        try:
            await module.on_start(self, ctx)
        except BaseException as exc:
            error_str = repr(exc)
            self._log.error("runtime.module.start_failed", module=name, error=error_str)
            self._hooks.fire_module_error(module=name, error=error_str, ctx=ctx)
            await self._platform.events.publish(
                ModuleStartFailed(module_name=name, error=error_str)
            )
            raise ModuleActivationError(
                f"module {name!r} failed to start",
                context={"module": name},
                cause=exc,
            ) from exc

        self._started.append(module)
        self._log.info("runtime.module.started", module=name)
        self._hooks.fire_module_started(module=name, ctx=ctx)
        await self._platform.events.publish(ModuleStarted(module_name=name))

        # Register health check if the module supports it.
        if isinstance(module, BaseRuntimeModule):
            try:
                check = RuntimeHealthCheck(name=name, module=module)
                self._platform.health.register(check)
            except DuplicateRegistrationError:
                # Health check already registered (e.g. from a previous run).
                pass

    async def _rollback(self, ctx: RuntimeContext) -> None:
        """Stop started modules in LIFO order, tolerating individual failures."""
        for module in reversed(self._started):
            name = module.name
            self._log.debug("runtime.module.stopping", module=name)
            self._hooks.fire_module_stopping(module=name, ctx=ctx)
            try:
                await module.on_stop(self, ctx)
            except BaseException as exc:
                error_str = repr(exc)
                self._log.error("runtime.module.stop_failed", module=name, error=error_str)
                self._hooks.fire_module_error(module=name, error=error_str, ctx=ctx)
                await self._platform.events.publish(
                    ModuleStopFailed(module_name=name, error=error_str)
                )
            else:
                self._log.info("runtime.module.stopped", module=name)
                self._hooks.fire_module_stopped(module=name, ctx=ctx)
                await self._platform.events.publish(ModuleStopped(module_name=name))
        self._started.clear()


__all__ = ["RuntimeHost"]
