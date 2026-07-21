"""Runtime module integration for the contract management service."""

from __future__ import annotations

from typing import TYPE_CHECKING

from eaip.capabilities.capability import Capability, CapabilityStatus
from eaip.contract.health import ContractHealthCheck
from eaip.contract.manager import ContractManager
from eaip.contract.models import ContractConfig
from eaip.logging.context import get_logger

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel


class ContractRuntimeModule:
    name: str = "contract"

    def __init__(
        self,
        config: ContractConfig | None = None,
        manager: ContractManager | None = None,
    ) -> None:
        self._config = config or ContractConfig()
        self._manager = manager or ContractManager()
        self._log = get_logger("eaip.contract.integration")

    @property
    def manager(self) -> ContractManager:
        return self._manager

    async def start(self, kernel: RuntimeKernel) -> None:
        self._log.info("contract.module.starting")
        platform = kernel.platform
        capability = Capability(
            name="eaip.contract",
            title="Contract Management Service",
            description="Contract lifecycle management, versioning, approval workflows, and expiration tracking",
            version="0.1.0",
            status=CapabilityStatus.ENABLED,
            tags=("contract", "lifecycle", "versioning", "approval"),
        )
        platform.capabilities.register(capability)
        platform.health.register(ContractHealthCheck())
        self._log.info("contract.module.started")

    async def stop(self, kernel: RuntimeKernel) -> None:
        self._log.info("contract.module.stopping")


__all__ = ["ContractRuntimeModule"]
