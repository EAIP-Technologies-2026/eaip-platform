from __future__ import annotations

from datetime import UTC, datetime

from eaip.adapters.llm.models import LLMRequest, LLMResponse, RunContext
from eaip.health.checks import HealthReport, HealthStatus


class StubLLMAdapter:
    """Stub LLM adapter for demo/testing without a real LLM backend.

    Returns canned responses that SimpleLLMPlanner and StepExecutor
    can consume without an actual model endpoint.
    """

    name = "stub"
    version = "0.1.0"

    async def complete(
        self,
        request: LLMRequest,
        *,
        context: RunContext | None = None,
    ) -> LLMResponse:
        purpose = (request.metadata or {}).get("purpose", "")
        if purpose == "planning":
            content = (
                "STEP 1: llm_completion | respond | Respond to the query based on the goal."
            )
        else:
            last = request.messages[-1] if request.messages else None
            user_text = last.content if last else ""
            content = f"[StubLLM] Processed: {user_text[:200]}"

        return LLMResponse(
            model=request.model,
            provider="stub",
            adapter=self.name,
            content=content,
            finish_reason="stop",
            usage={"prompt_tokens": 0, "completion_tokens": 0},
            timestamp=datetime.now(UTC),
        )

    async def health(self) -> HealthReport:
        return HealthReport(
            component="llm.stub",
            status=HealthStatus.HEALTHY,
            message="Stub LLM adapter is operational",
        )


__all__ = ["StubLLMAdapter"]
