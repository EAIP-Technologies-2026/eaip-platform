"""FaaS runtime module."""

from __future__ import annotations

from typing import TYPE_CHECKING

from eaip.capabilities.capability import Capability, CapabilityStatus
from eaip.faas.health import FaaSHealthCheck
from eaip.faas.models import FaaSConfig
from eaip.faas.runtime import FaaSRuntime
from eaip.logging.context import get_logger

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel


class FaaSRuntimeModule:
    name: str = "faas"

    def __init__(
        self,
        config: FaaSConfig | None = None,
        runtime: FaaSRuntime | None = None,
    ) -> None:
        self._config = config or FaaSConfig()
        self._runtime = runtime or FaaSRuntime(config=self._config)
        self._health_check = FaaSHealthCheck(self._runtime)
        self._log = get_logger("eaip.faas.integration")

    @property
    def config(self) -> FaaSConfig:
        return self._config

    @property
    def runtime(self) -> FaaSRuntime:
        return self._runtime

    @property
    def health_check(self) -> FaaSHealthCheck:
        return self._health_check

    async def start(self, kernel: RuntimeKernel) -> None:
        self._log.info("faas.module.starting")
        platform = kernel.platform

        capability = Capability(
            name="eaip.faas",
            title="Function as a Service Runtime",
            description=(
                "Function lifecycle management, execution, sandbox isolation, and auto-scaling"
            ),
            version="0.1.0",
            status=CapabilityStatus.ENABLED,
            tags=("faas", "function", "runtime", "serverless"),
        )
        platform.capabilities.register(capability)
        platform.health.register(self._health_check)
        kernel.register_module("faas.runtime", self._runtime)
        self._log.info("faas.module.started")

    async def stop(self, kernel: RuntimeKernel) -> None:
        self._log.info("faas.module.stopping")


__all__ = ["FaaSRuntimeModule"]
