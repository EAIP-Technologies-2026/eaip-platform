"""Integration layer — SecdistRuntimeModule for kernel lifecycle."""

from __future__ import annotations

from typing import TYPE_CHECKING

from eaip.logging.context import get_logger
from eaip.secdist.distributor import SecretDistributor
from eaip.secdist.health import SecdistHealthCheck

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel


class SecdistRuntimeModule:
    """RuntimeModule that bootstraps the secrets distribution subsystem."""

    name: str = "secdist"

    def __init__(self, distributor: SecretDistributor | None = None) -> None:
        self._distributor = distributor or SecretDistributor()
        self._log = get_logger("eaip.secdist.integration")

    @property
    def distributor(self) -> SecretDistributor:
        return self._distributor

    async def start(self, kernel: RuntimeKernel) -> None:
        """Start the secrets distribution module."""
        self._log.info("secdist.module.starting")
        targets = await self._distributor.list_targets()
        health_check = SecdistHealthCheck(
            target_count=len(targets),
            distribution_count=0,
        )
        kernel.platform.health.register(health_check)
        self._log.info("secdist.module.started")

    async def stop(self, _kernel: RuntimeKernel) -> None:
        """Shut down the secrets distribution module."""
        self._log.info("secdist.module.stopping")


__all__ = ["SecdistRuntimeModule"]
