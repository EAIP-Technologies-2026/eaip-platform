"""Runtime integration — DataMaskRuntimeModule for the EAIP kernel."""

from __future__ import annotations

from typing import TYPE_CHECKING

from eaip.capabilities.capability import Capability, CapabilityStatus
from eaip.datamask.anonymization import AnonymizationService
from eaip.datamask.health import DataMaskHealthCheck
from eaip.datamask.masking import DataMaskingService
from eaip.datamask.models import MaskingConfig
from eaip.datamask.pii import PiiDetector

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel

from eaip.logging.context import get_logger

logger = get_logger("eaip.datamask.integration")


class DataMaskRuntimeModule:
    name: str = "datamask"

    def __init__(
        self,
        config: MaskingConfig | None = None,
        masking_service: DataMaskingService | None = None,
        pii_detector: PiiDetector | None = None,
        anonymization_service: AnonymizationService | None = None,
    ) -> None:
        self._config = config or MaskingConfig()
        self._masking = masking_service or DataMaskingService(config=self._config)
        self._pii = pii_detector or PiiDetector()
        self._anonymization = anonymization_service or AnonymizationService(
            masking_service=self._masking,
        )
        self._health_check = DataMaskHealthCheck(masking_service=self._masking)

    async def start(self, kernel: RuntimeKernel) -> None:
        platform = kernel.platform
        capability = Capability(
            name="eaip.datamask",
            title="Data Masking & Anonymization",
            description="PII detection, field-level masking, anonymization jobs, and data classification",
            version="0.1.0",
            status=CapabilityStatus.ENABLED,
            tags=("datamask", "pii", "anonymization", "masking", "redaction"),
        )
        platform.capabilities.register(capability)
        platform.health.register(self._health_check)
        logger.info(
            "datamask_module_started",
            masking_ready=True,
            pii_ready=True,
            anonymization_ready=True,
        )

    async def stop(self, kernel: RuntimeKernel) -> None:
        logger.info("datamask_module_stopped")

    @property
    def masking(self) -> DataMaskingService:
        return self._masking

    @property
    def pii(self) -> PiiDetector:
        return self._pii

    @property
    def anonymization(self) -> AnonymizationService:
        return self._anonymization

    @property
    def health_check(self) -> DataMaskHealthCheck:
        return self._health_check


__all__ = ["DataMaskRuntimeModule"]
