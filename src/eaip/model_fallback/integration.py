"""Integration layer — ModelFallbackRuntimeModule for kernel lifecycle."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

from eaip.capabilities.capability import Capability, CapabilityStatus
from eaip.logging.context import get_logger
from eaip.model_fallback.health import ModelFallbackHealthCheck
from eaip.model_fallback.service import ModelFallbackService

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel


class ModelFallbackRuntimeModule:
    """RuntimeModule that bootstraps the model fallback subsystem."""

    name: str = "model_fallback"

    def __init__(self, service: ModelFallbackService | None = None) -> None:
        """Initialize the runtime module with an optional service instance."""
        self._service = service or ModelFallbackService()
        self._health_check = ModelFallbackHealthCheck(service=self._service)
        self._startup_duration: float = 0.0
        self._log = get_logger("eaip.model_fallback.integration")

    @property
    def service(self) -> ModelFallbackService:
        """Return the underlying ModelFallbackService instance."""
        return self._service

    async def start(self, kernel: RuntimeKernel) -> None:
        """Start the model fallback module."""
        t0 = time.monotonic()
        self._log.info("model_fallback.module.start")

        kernel.platform.health.register(self._health_check)
        kernel.platform.capabilities.register(
            Capability(
                name="model_fallback:framework",
                title="Model Fallback Framework",
                status=CapabilityStatus.ENABLED,
                tags=("model-fallback", "resilience", "degradation"),
            )
        )

        self._startup_duration = time.monotonic() - t0
        self._log.info(
            "model_fallback.module.complete",
            duration_s=round(self._startup_duration, 3),
        )

    async def stop(self, _kernel: RuntimeKernel) -> None:
        """Shut down the model fallback module."""
        self._log.info("model_fallback.module.stop")


__all__ = ["ModelFallbackRuntimeModule"]
