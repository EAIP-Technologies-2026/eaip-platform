"""Model evaluation runtime module."""

from __future__ import annotations

from typing import TYPE_CHECKING

from eaip.logging.context import get_logger
from eaip.model_evaluation.health import ModelEvaluationHealthCheck

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel


class ModelEvaluationRuntimeModule:
    """Runtime module for model evaluation."""

    name: str = "model_evaluation"

    def __init__(self) -> None:
        """Initialize the model evaluation runtime module."""
        self._health_check = ModelEvaluationHealthCheck()
        self._log = get_logger("eaip.model_evaluation.integration")

    @property
    def health_check(self) -> ModelEvaluationHealthCheck:
        """Return the model evaluation health check instance."""
        return self._health_check

    async def start(self, kernel: RuntimeKernel) -> None:
        """Register the module with the kernel."""
        self._log.info("model_evaluation.module.starting")
        kernel.platform.health.register(self._health_check)
        self._log.info("model_evaluation.module.started")

    async def stop(self, _kernel: RuntimeKernel) -> None:
        """Shut down the module."""
        self._log.info("model_evaluation.module.stopping")


__all__ = ["ModelEvaluationRuntimeModule"]
