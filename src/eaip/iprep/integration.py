"""IP reputation runtime module."""

from __future__ import annotations

from typing import TYPE_CHECKING

from eaip.capabilities.capability import Capability, CapabilityStatus
from eaip.iprep.health import IPRepHealthCheck
from eaip.iprep.models import ReputationConfig
from eaip.iprep.service import IPReputationService
from eaip.logging.context import get_logger

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel


class IPRepRuntimeModule:
    name: str = "iprep"

    def __init__(
        self,
        config: ReputationConfig | None = None,
        service: IPReputationService | None = None,
    ) -> None:
        self._config = config or ReputationConfig()
        self._service = service or IPReputationService(config=self._config)
        self._health_check = IPRepHealthCheck(self._service)
        self._log = get_logger("eaip.iprep.integration")

    @property
    def config(self) -> ReputationConfig:
        return self._config

    @property
    def service(self) -> IPReputationService:
        return self._service

    @property
    def health_check(self) -> IPRepHealthCheck:
        return self._health_check

    async def start(self, kernel: RuntimeKernel) -> None:
        self._log.info("iprep.module.starting")
        platform = kernel.platform

        capability = Capability(
            name="eaip.iprep",
            title="IP Reputation Service",
            description="IP address reputation checking, blocklist management, and threat intelligence",
            version="0.1.0",
            status=CapabilityStatus.ENABLED,
            tags=("ip", "reputation", "blocklist", "threat"),
        )
        platform.capabilities.register(capability)
        platform.health.register(self._health_check)
        kernel.register_module("iprep.service", self._service)
        self._log.info("iprep.module.started")

    async def stop(self, kernel: RuntimeKernel) -> None:
        self._log.info("iprep.module.stopping")


__all__ = ["IPRepRuntimeModule"]
