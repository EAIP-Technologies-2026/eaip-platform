"""CompositionRoot — wires the runtime kernel into the platform lifecycle.

The :class:`CompositionRoot` is responsible for:

1. Registering the kernel's :class:`RuntimeDiagnostics` as a health check
   on the platform :class:`~eaip.health.reporter.HealthReporter`.
2. Adding the kernel's own lifecycle (start/stop) as a platform lifecycle
   hook so that the platform start/stop cascades into the kernel.
3. Publishing a ``KernelStarted`` / ``KernelStopped`` domain event on the
   platform event bus.

This class is used internally by :class:`RuntimeBuilder` but can be used
standalone for advanced wiring scenarios.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from eaip.exceptions.domain import DuplicateRegistrationError
from eaip.health.checks import HealthReport
from eaip.logging.context import get_logger
from eaip.runtime.health import RuntimeDiagnostics
from eaip.runtime.kernel_events import KernelStarted, KernelStopped

if TYPE_CHECKING:
    from eaip.platform.platform import Platform
    from eaip.runtime.host import RuntimeHost
    from eaip.runtime.kernel import RuntimeKernel


class _KernelDiagnosticsAdapter:
    """Adapts RuntimeDiagnostics to the HealthCheck protocol."""

    def __init__(self, diag: RuntimeDiagnostics) -> None:
        self.name = "runtime.kernel"
        self._diag = diag

    async def check(self) -> HealthReport:
        return await self._diag.diagnose()


class CompositionRoot:
    """Wires a :class:`RuntimeKernel` into a :class:`~eaip.platform.platform.Platform`.

    Parameters
    ----------
    platform:
        The platform instance to wire into.
    kernel:
        The runtime kernel instance to wire.
    """

    def __init__(self, *, platform: Platform, kernel: RuntimeKernel) -> None:
        self._platform = platform
        self._kernel = kernel
        self._log = get_logger("eaip.runtime.composition")

    def wire(self) -> None:
        """Perform all wiring.  Must be called before the kernel starts.

        Wiring is idempotent: calling it multiple times is safe.
        """
        self._wire_health()
        self._wire_lifecycle()

    def _wire_health(self) -> None:
        diag = RuntimeDiagnostics(
            loader=self._kernel.host._loader,
            hooks=self._kernel.host._hooks,
        )
        adapter = _KernelDiagnosticsAdapter(diag)
        try:
            self._platform.health.register(adapter)
        except DuplicateRegistrationError:
            pass

    def _wire_lifecycle(self) -> None:
        host = self._kernel.host

        async def _kernel_start() -> None:
            await self._kernel.start()
            await self._platform.events.publish(
                KernelStarted(
                    module_count=len(host.module_names),
                )
            )

        async def _kernel_stop() -> None:
            await self._platform.events.publish(KernelStopped())
            await self._kernel.stop()

        self._platform.lifecycle.add(
            name="runtime.kernel.start",
            start=_kernel_start,
            stop=_kernel_stop,
        )


__all__ = ["CompositionRoot"]
