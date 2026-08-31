"""Runtime kernel that orchestrates lifecycle, modules, hooks, and scheduling."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING, Any

from opentelemetry import trace
from opentelemetry.trace import SpanKind, StatusCode

from eaip.exceptions.domain import LifecycleError
from eaip.lifecycle.phases import LifecyclePhase
from eaip.logging.context import get_logger
from eaip.runtime.context import RuntimeContext, current_context
from eaip.runtime.hooks import HookPoint, HookRegistry, RuntimeHook
from eaip.runtime.scheduler import Scheduler

if TYPE_CHECKING:
    from eaip.platform.platform import Platform


class RuntimeKernel:
    """Central runtime controller managing lifecycle, modules, hooks, and the scheduler."""

    def __init__(self, platform: Platform) -> None:
        """Wrap a *platform* and initialise all runtime subsystems."""
        self._platform = platform
        self._hooks = HookRegistry()
        self._scheduler = Scheduler()
        self._modules: dict[str, object] = {}
        self._phase: LifecyclePhase = LifecyclePhase.CREATED
        self._log = get_logger("eaip.runtime.kernel")
        self._run_id: str | None = None

    @property
    def platform(self) -> Platform:
        """Return the underlying platform."""
        return self._platform

    @property
    def phase(self) -> LifecyclePhase:
        """Return the current lifecycle phase."""
        return self._phase

    @property
    def scheduler(self) -> Scheduler:
        """Return the scheduler instance."""
        return self._scheduler

    @property
    def hooks(self) -> HookRegistry:
        """Return the hook registry."""
        return self._hooks

    def register_module(self, name: str, module: object) -> None:
        """Register a module by *name*; raises on duplicate or empty name."""
        if not name or name in self._modules:
            raise ValueError(f"module {name!r} already registered or empty")
        self._modules[name] = module

    def get_module(self, name: str) -> object | None:
        """Return a registered module or None."""
        return self._modules.get(name)

    def add_hook(
        self,
        name: str,
        fn: Callable[..., Awaitable[None]],
        hook_point: HookPoint,
        order: int = 100,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Register a lifecycle hook."""
        self._hooks.register(
            RuntimeHook(
                name=name,
                fn=fn,
                hook_point=hook_point,
                order=order,
                metadata=metadata or {},
            )
        )

    async def boot(self, *, context: RuntimeContext | None = None) -> None:
        """Transition from CREATED to RUNNING, invoking hooks and starting subsystems."""
        if self._phase is not LifecyclePhase.CREATED:
            raise LifecycleError(
                f"cannot boot kernel in phase {self._phase}",
                context={"phase": str(self._phase)},
            )
        tracer = trace.get_tracer("eaip.runtime.kernel")
        ctx = context or current_context()
        ctx.bind()
        self._phase = LifecyclePhase.STARTING
        self._log.info("kernel.boot.start")

        with tracer.start_as_current_span("kernel.boot", kind=SpanKind.INTERNAL) as span:
            hook_failures = await self._hooks.run(HookPoint.PRE_START, kernel=self)
            if hook_failures:
                self._phase = LifecyclePhase.FAILED
                span.set_status(StatusCode.ERROR, f"{len(hook_failures)} pre-start hook(s) failed")
                self._log.error("kernel.boot.pre_start_failed", count=len(hook_failures))
                raise LifecycleError(
                    f"{len(hook_failures)} pre-start hook(s) failed",
                    context={"failures": [str(e) for e in hook_failures]},
                )

            await self._platform.start()
            await self._scheduler.start()

            hook_failures = await self._hooks.run(HookPoint.POST_START, kernel=self)
            if hook_failures:
                span.add_event("post_start_failures", {"count": str(len(hook_failures))})
                self._log.warning("kernel.boot.post_start_failures", count=len(hook_failures))

            self._phase = LifecyclePhase.RUNNING
            span.set_attribute("kernel.phase", str(self._phase))
            self._log.info("kernel.boot.complete")

    async def shutdown(self) -> None:
        """Transition from RUNNING to STOPPED, stopping subsystems and invoking hooks."""
        if self._phase not in {LifecyclePhase.RUNNING, LifecyclePhase.FAILED}:
            return
        tracer = trace.get_tracer("eaip.runtime.kernel")
        self._phase = LifecyclePhase.STOPPING
        self._log.info("kernel.shutdown.start")

        with tracer.start_as_current_span("kernel.shutdown", kind=SpanKind.INTERNAL) as span:
            hook_failures = await self._hooks.run(HookPoint.PRE_STOP, kernel=self)
            if hook_failures:
                span.add_event("pre_stop_failures", {"count": str(len(hook_failures))})
                self._log.warning("kernel.shutdown.pre_stop_failures", count=len(hook_failures))

            await self._scheduler.stop()
            await self._platform.stop()

            hook_failures = await self._hooks.run(HookPoint.POST_STOP, kernel=self)
            if hook_failures:
                span.add_event("post_stop_failures", {"count": str(len(hook_failures))})
                self._log.warning("kernel.shutdown.post_stop_failures", count=len(hook_failures))

            self._phase = LifecyclePhase.STOPPED
            span.set_attribute("kernel.phase", str(self._phase))
            self._log.info("kernel.shutdown.complete")

    async def __aenter__(self) -> RuntimeKernel:
        """Boot on entry."""
        await self.boot()
        return self

    async def __aexit__(self, *_: object) -> None:
        """Shut down on exit."""
        await self.shutdown()
