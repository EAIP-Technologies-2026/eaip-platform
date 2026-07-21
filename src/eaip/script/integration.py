"""RuntimeKernel integration — registers ScriptRuntime as a RuntimeModule."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any

from eaip.capabilities.capability import Capability, CapabilityStatus
from eaip.logging.context import get_logger
from eaip.script.health import ScriptHealthCheck
from eaip.script.registry import FunctionRegistry
from eaip.script.runtime import ScriptRuntime

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel


class ScriptRuntimeModule:
    name: str = "script"

    def __init__(
        self,
        registry: FunctionRegistry | None = None,
        runtime: ScriptRuntime | None = None,
        event_bus: Any = None,
    ) -> None:
        self._event_bus = event_bus
        self._registry = registry or FunctionRegistry(event_bus=event_bus)
        self._runtime = runtime or ScriptRuntime(registry=self._registry, event_bus=event_bus)
        self._health_check = ScriptHealthCheck()
        self._log = get_logger("eaip.script.integration")

    @property
    def registry(self) -> FunctionRegistry:
        return self._registry

    @property
    def runtime(self) -> ScriptRuntime:
        return self._runtime

    async def start(self, kernel: RuntimeKernel) -> None:
        t0 = time.monotonic()
        self._log.info("script.module.start")

        kernel.platform.health.register(self._health_check)
        kernel.platform.capabilities.register(
            Capability(
                name="script:runtime",
                title="Script & Function Runtime",
                status=CapabilityStatus.ENABLED,
                tags=("script", "runtime"),
            )
        )

        kernel.register_module("script.registry", self._registry)
        kernel.register_module("script.runtime", self._runtime)

        self._log.info(
            "script.module.complete",
            duration_s=round(time.monotonic() - t0, 3),
        )

    async def stop(self, _kernel: RuntimeKernel) -> None:
        self._log.info("script.module.stop")


__all__ = ["ScriptRuntimeModule"]
