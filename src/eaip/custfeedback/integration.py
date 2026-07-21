"""Customer feedback analyzer runtime module."""

from __future__ import annotations

from typing import TYPE_CHECKING

from eaip.custfeedback.analyzer import FeedbackAnalyzer
from eaip.custfeedback.health import FeedbackHealthCheck

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel


class FeedbackRuntimeModule:
    name: str = "custfeedback"

    def __init__(self) -> None:
        self.analyzer = FeedbackAnalyzer()
        self.health_check = FeedbackHealthCheck(self.analyzer)

    async def start(self, kernel: RuntimeKernel) -> None:
        kernel.register_module("custfeedback.analyzer", self.analyzer)

    async def stop(self, kernel: RuntimeKernel) -> None:
        pass
