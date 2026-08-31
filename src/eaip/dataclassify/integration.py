"""Runtime integration — DataClassifyRuntimeModule for the EAIP kernel."""

from __future__ import annotations

from typing import TYPE_CHECKING

from eaip.capabilities.capability import Capability, CapabilityStatus
from eaip.dataclassify.classifier import DataClassifier
from eaip.dataclassify.health import DataClassifyHealthCheck
from eaip.dataclassify.models import ClassifierConfig

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel

from eaip.logging.context import get_logger

logger = get_logger("eaip.dataclassify.integration")


class DataClassifyRuntimeModule:
    name: str = "dataclassify"

    def __init__(
        self,
        config: ClassifierConfig | None = None,
        classifier: DataClassifier | None = None,
    ) -> None:
        self._config = config or ClassifierConfig()
        self._classifier = classifier or DataClassifier(config=self._config)
        self._health_check = DataClassifyHealthCheck(classifier=self._classifier)

    async def start(self, kernel: RuntimeKernel) -> None:
        platform = kernel.platform
        capability = Capability(
            name="eaip.dataclassify",
            title="Data Classification Enhancer",
            description="Classify resources by sensitivity — PUBLIC, INTERNAL, CONFIDENTIAL, RESTRICTED",
            version="0.1.0",
            status=CapabilityStatus.ENABLED,
            tags=("dataclassify", "classification", "sensitivity"),
        )
        platform.capabilities.register(capability)
        platform.health.register(self._health_check)
        logger.info("dataclassify_module_started", classifier_ready=True)

    async def stop(self, kernel: RuntimeKernel) -> None:
        logger.info("dataclassify_module_stopped")

    @property
    def classifier(self) -> DataClassifier:
        return self._classifier

    @property
    def health_check(self) -> DataClassifyHealthCheck:
        return self._health_check


__all__ = ["DataClassifyRuntimeModule"]
