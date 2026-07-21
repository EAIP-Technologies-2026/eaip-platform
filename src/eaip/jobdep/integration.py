"""Job dependency manager runtime module."""

from __future__ import annotations

from typing import TYPE_CHECKING

from eaip.capabilities.capability import Capability, CapabilityStatus
from eaip.jobdep.health import JobDepHealthCheck
from eaip.jobdep.manager import JobDependencyManager
from eaip.jobdep.models import JobDepConfig
from eaip.logging.context import get_logger

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel


class JobDepRuntimeModule:
    name: str = "jobdep"

    def __init__(
        self,
        config: JobDepConfig | None = None,
        manager: JobDependencyManager | None = None,
    ) -> None:
        self._config = config or JobDepConfig()
        self._manager = manager or JobDependencyManager(config=self._config)
        self._health_check = JobDepHealthCheck(self._manager)
        self._log = get_logger("eaip.jobdep.integration")

    @property
    def config(self) -> JobDepConfig:
        return self._config

    @property
    def manager(self) -> JobDependencyManager:
        return self._manager

    @property
    def health_check(self) -> JobDepHealthCheck:
        return self._health_check

    async def start(self, kernel: RuntimeKernel) -> None:
        self._log.info("jobdep.module.starting")
        platform = kernel.platform

        capability = Capability(
            name="eaip.jobdep",
            title="Job Dependency Manager",
            description="DAG-based job dependency resolution, scheduling, and lifecycle management",
            version="0.1.0",
            status=CapabilityStatus.ENABLED,
            tags=("job", "dependency", "dag", "scheduling"),
        )
        platform.capabilities.register(capability)
        platform.health.register(self._health_check)
        kernel.register_module("jobdep.manager", self._manager)
        self._log.info("jobdep.module.started")

    async def stop(self, kernel: RuntimeKernel) -> None:
        self._log.info("jobdep.module.stopping")


__all__ = ["JobDepRuntimeModule"]
