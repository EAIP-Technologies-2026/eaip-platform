"""Cross-region replicator runtime module."""

from __future__ import annotations

from typing import TYPE_CHECKING

from eaip.crossreg.health import CrossRegHealthCheck
from eaip.crossreg.replicator import CrossRegionReplicator

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel


class CrossRegRuntimeModule:
    name: str = "crossreg"

    def __init__(self) -> None:
        self.replicator = CrossRegionReplicator()
        self.health_check = CrossRegHealthCheck(self.replicator)

    async def start(self, kernel: RuntimeKernel) -> None:
        kernel.register_module("crossreg.replicator", self.replicator)

    async def stop(self, kernel: RuntimeKernel) -> None:
        pass
