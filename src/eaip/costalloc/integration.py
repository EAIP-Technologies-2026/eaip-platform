"""Cost allocation runtime module."""

from __future__ import annotations

from typing import TYPE_CHECKING

from eaip.costalloc.allocator import CostAllocationService
from eaip.costalloc.health import CostAllocHealthCheck

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel


class CostAllocRuntimeModule:
    name: str = "costalloc"

    def __init__(self) -> None:
        self.service = CostAllocationService()
        self.health_check = CostAllocHealthCheck(self.service)

    async def start(self, kernel: RuntimeKernel) -> None:
        kernel.register_module("costalloc.service", self.service)

    async def stop(self, kernel: RuntimeKernel) -> None:
        pass
