"""Unified application lifecycle that coordinates Platform and RuntimeKernel."""

from __future__ import annotations

from typing import TYPE_CHECKING

from eaip.exceptions.domain import LifecycleError
from eaip.lifecycle.phases import LifecyclePhase
from eaip.logging.context import get_logger

if TYPE_CHECKING:
    from eaip.platform.platform import Platform
    from eaip.runtime.kernel import RuntimeKernel


class ApplicationLifecycle:
    """Coordinates Platform and optional RuntimeKernel into a single lifecycle.

    Manages the transitions: created -> starting -> running -> stopping -> stopped.
    """

    def __init__(
        self,
        platform: Platform,
        kernel: RuntimeKernel | None = None,
    ) -> None:
        """Wrap a *platform* and optional *kernel*.

        Args:
            platform: The EAIP Platform instance.
            kernel: Optional RuntimeKernel for runtime orchestration.
        """
        self._platform = platform
        self._kernel = kernel
        self._phase: LifecyclePhase = LifecyclePhase.CREATED
        self._log = get_logger("eaip.app.lifecycle")

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def platform(self) -> Platform:
        """Return the underlying platform."""
        return self._platform

    @property
    def kernel(self) -> RuntimeKernel | None:
        """Return the optional runtime kernel."""
        return self._kernel

    @property
    def phase(self) -> LifecyclePhase:
        """Return the current lifecycle phase."""
        return self._phase

    @property
    def is_running(self) -> bool:
        """Return True if the application is in RUNNING phase."""
        return self._phase is LifecyclePhase.RUNNING

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def start(self) -> None:
        """Start the platform and optionally the runtime kernel.

        Transitions: CREATED -> STARTING -> RUNNING.

        Raises:
            LifecycleError: If not in CREATED phase.
        """
        if self._phase is not LifecyclePhase.CREATED:
            raise LifecycleError(
                f"cannot start application in phase {self._phase}",
                context={"phase": str(self._phase)},
            )
        self._phase = LifecyclePhase.STARTING
        self._log.info("app.starting")

        try:
            if self._kernel is not None:
                # Kernel boot also starts the platform internally.
                await self._kernel.boot()
            else:
                await self._platform.start()
        except BaseException:
            self._phase = LifecyclePhase.FAILED
            self._log.error("app.start_failed")
            raise

        self._phase = LifecyclePhase.RUNNING
        self._log.info("app.running")

    async def stop(self) -> None:
        """Stop the runtime kernel and platform.

        Transitions: RUNNING/FAILED -> STOPPING -> STOPPED.

        Raises:
            LifecycleError: If in CREATED phase.
        """
        if self._phase is LifecyclePhase.CREATED:
            raise LifecycleError(
                "cannot stop application that has not started",
                context={"phase": str(self._phase)},
            )
        if self._phase is LifecyclePhase.STOPPED:
            return
        self._phase = LifecyclePhase.STOPPING
        self._log.info("app.stopping")

        try:
            if self._kernel is not None:
                await self._kernel.shutdown()
            else:
                await self._platform.stop()
        except BaseException as exc:
            self._log.error("app.stop_failed", error=repr(exc))

        self._phase = LifecyclePhase.STOPPED
        self._log.info("app.stopped")

    async def __aenter__(self) -> ApplicationLifecycle:
        """Start on context entry."""
        await self.start()
        return self

    async def __aexit__(self, *_: object) -> None:
        """Stop on context exit."""
        await self.stop()
