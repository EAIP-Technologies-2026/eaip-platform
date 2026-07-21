"""Runtime integration — DataSampleRuntimeModule for the EAIP kernel."""

from __future__ import annotations

from typing import TYPE_CHECKING

from eaip.capabilities.capability import Capability, CapabilityStatus
from eaip.datasample.health import DataSampleHealthCheck
from eaip.datasample.models import SamplingConfig
from eaip.datasample.sampler import DataSamplingService

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel

from eaip.logging.context import get_logger

logger = get_logger("eaip.datasample.integration")


class DataSampleRuntimeModule:
    name: str = "datasample"

    def __init__(
        self,
        config: SamplingConfig | None = None,
        sampler: DataSamplingService | None = None,
    ) -> None:
        self._config = config or SamplingConfig()
        self._sampler = sampler or DataSamplingService(config=self._config)
        self._health_check = DataSampleHealthCheck(sampler=self._sampler)

    async def start(self, kernel: RuntimeKernel) -> None:
        platform = kernel.platform
        capability = Capability(
            name="eaip.datasample",
            title="Data Sampling Service",
            description="Sample dataset records using random, stratified, or sequential strategies",
            version="0.1.0",
            status=CapabilityStatus.ENABLED,
            tags=("datasample", "sampling", "dataset", "filter"),
        )
        platform.capabilities.register(capability)
        platform.health.register(self._health_check)
        logger.info("datasample_module_started", sampler_ready=True)

    async def stop(self, kernel: RuntimeKernel) -> None:
        logger.info("datasample_module_stopped")

    @property
    def sampler(self) -> DataSamplingService:
        return self._sampler

    @property
    def health_check(self) -> DataSampleHealthCheck:
        return self._health_check


__all__ = ["DataSampleRuntimeModule"]
