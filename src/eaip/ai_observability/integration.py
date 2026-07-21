from __future__ import annotations

from typing import TYPE_CHECKING

from eaip.ai_observability.health import AiObservabilityHealthCheck
from eaip.ai_observability.models import AiObservabilityConfig
from eaip.ai_observability.service import AiObservabilityService
from eaip.capabilities.capability import Capability, CapabilityStatus
from eaip.logging.context import get_logger

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel


class AiObservabilityRuntimeModule:
    name: str = "ai_observability"

    def __init__(
        self,
        config: AiObservabilityConfig | None = None,
        service: AiObservabilityService | None = None,
    ) -> None:
        self._config = config or AiObservabilityConfig()
        self._service = service or AiObservabilityService(config=self._config)
        self._log = get_logger("eaip.ai_observability.integration")

    @property
    def service(self) -> AiObservabilityService:
        return self._service

    async def start(self, kernel: RuntimeKernel) -> None:
        self._log.info("ai_observability.module.starting")
        platform = kernel.platform
        capability = Capability(
            name="eaip.ai_observability",
            title="AI Observability",
            description="Tracing, metrics, reporting, alerting, and dashboards for AI model calls",
            version="0.1.0",
            status=CapabilityStatus.ENABLED,
            tags=("ai", "observability", "tracing", "monitoring", "llm"),
        )
        platform.capabilities.register(capability)
        platform.health.register(
            AiObservabilityHealthCheck(
                trace_count=len(self._service.get_trace_spans("")),
                model_call_count=len(self._service.list_model_calls()),
                alert_count=len(self._service.list_alerts()),
            ),
        )
        self._log.info("ai_observability.module.started")

    async def stop(self, _kernel: RuntimeKernel) -> None:
        self._log.info("ai_observability.module.stopping")


__all__ = ["AiObservabilityRuntimeModule"]
