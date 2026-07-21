"""Feedback collection runtime module."""

from __future__ import annotations

from typing import TYPE_CHECKING

from eaip.feedback.health import FeedbackHealthCheck
from eaip.logging.context import get_logger

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel


class FeedbackRuntimeModule:
    """Runtime module for feedback collection."""

    name: str = "feedback"

    def __init__(self) -> None:
        """Initialize the feedback runtime module."""
        self._health_check = FeedbackHealthCheck()
        self._log = get_logger("eaip.feedback.integration")

    @property
    def health_check(self) -> FeedbackHealthCheck:
        """Return the feedback health check instance."""
        return self._health_check

    async def start(self, kernel: RuntimeKernel) -> None:
        """Register the module with the kernel."""
        self._log.info("feedback.module.starting")
        kernel.platform.health.register(self._health_check)
        self._log.info("feedback.module.started")

    async def stop(self, _kernel: RuntimeKernel) -> None:
        """Shut down the module."""
        self._log.info("feedback.module.stopping")


__all__ = ["FeedbackRuntimeModule"]
