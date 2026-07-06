"""RuntimeKernel — top-level orchestrator for the EAIP runtime layer.

The :class:`RuntimeKernel` is the single entry point that composes:

* :class:`~eaip.runtime.host.RuntimeHost` — orchestrates module lifecycle.
* :class:`~eaip.runtime.registry.RuntimeRegistry` — central module metadata.
* :class:`~eaip.runtime.bootstrap.BootstrapManager` — pre/post start hooks.
* :class:`~eaip.runtime.composition.CompositionRoot` — platform wiring.

Usage
-----
::

    kernel = RuntimeKernel(
        host=RuntimeHost(platform=platform),
        registry=RuntimeRegistry(),
        bootstrap=BootstrapManager(),
    )
    kernel.root = CompositionRoot(platform=platform, kernel=kernel)
    kernel.root.wire()

    async with kernel:
        ...

Or use :class:`RuntimeBuilder` for a fluent API:

::

    from eaip.runtime.builder import RuntimeBuilder

    kernel = (
        RuntimeBuilder(platform)
        .with_module(MyModule())
        .build()
    )
    async with kernel:
        ...
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from eaip.logging.context import get_logger
from eaip.runtime.context import RuntimeContext, reset_context, set_context

if TYPE_CHECKING:
    from eaip.runtime.bootstrap import BootstrapManager
    from eaip.runtime.composition import CompositionRoot
    from eaip.runtime.host import RuntimeHost
    from eaip.runtime.registry import RuntimeRegistry


class RuntimeKernel:
    """Top-level runtime kernel that orchestrates modules, bootstrap, and wiring.

    Parameters
    ----------
    host:
        The :class:`~eaip.runtime.host.RuntimeHost` that manages module lifecycle.
    registry:
        The :class:`~eaip.runtime.registry.RuntimeRegistry` for module metadata.
    bootstrap:
        The :class:`~eaip.runtime.bootstrap.BootstrapManager` for pre/post hooks.
    context:
        Baseline :class:`~eaip.runtime.context.RuntimeContext` for the kernel's
        lifecycle passes.
    """

    def __init__(
        self,
        *,
        host: RuntimeHost,
        registry: RuntimeRegistry,
        bootstrap: BootstrapManager,
        context: RuntimeContext | None = None,
    ) -> None:
        self._host = host
        self._registry = registry
        self._bootstrap = bootstrap
        self._base_ctx = context or RuntimeContext.create(environment="local")
        self._root: CompositionRoot | None = None
        self._running = False
        self._log = get_logger("eaip.runtime.kernel")

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def host(self) -> RuntimeHost:
        return self._host

    @property
    def registry(self) -> RuntimeRegistry:
        return self._registry

    @property
    def bootstrap(self) -> BootstrapManager:
        return self._bootstrap

    @property
    def root(self) -> CompositionRoot | None:
        return self._root

    @root.setter
    def root(self, value: CompositionRoot) -> None:
        self._root = value

    @property
    def is_running(self) -> bool:
        return self._running

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def start(self) -> None:
        """Start the kernel: pre-start hooks → host start → post-start hooks.

        Raises :class:`~eaip.exceptions.domain.LifecycleError` if any phase
        fails.  On failure, already-started modules are rolled back by the
        host and post-start hooks are skipped.
        """
        if self._running:
            self._log.warning("runtime.kernel.already_running")
            return

        ctx = self._base_ctx.derive()
        token = set_context(ctx)

        self._log.info(
            "runtime.kernel.starting",
            modules=self._host.module_names,
        )

        try:
            await self._bootstrap.run_pre_start(self, ctx)
            await self._host.start()
            await self._bootstrap.run_post_start(self, ctx)

            for name in self._host.module_names:
                self._registry.register_module(self._host.get_module(name))

        except Exception:
            self._log.error("runtime.kernel.start_failed")
            reset_context(token)
            raise

        self._running = True
        self._log.info("runtime.kernel.running")
        reset_context(token)

    async def stop(self) -> None:
        """Stop the kernel: host stop → cleanup.

        Idempotent: calling :meth:`stop` on an already-stopped kernel is safe.
        """
        if not self._running and not self._host.is_running:
            return

        ctx = self._base_ctx.derive()
        token = set_context(ctx)

        self._log.info("runtime.kernel.stopping")
        try:
            await self._host.stop()
        finally:
            self._registry.clear()
            self._running = False
            self._log.info("runtime.kernel.stopped")
            reset_context(token)

    async def __aenter__(self) -> RuntimeKernel:
        await self.start()
        return self

    async def __aexit__(self, *_: object) -> None:
        await self.stop()


__all__ = ["RuntimeKernel"]
