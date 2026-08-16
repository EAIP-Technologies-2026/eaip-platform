"""AI Guardrails runtime module."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from eaip.guardrails.health import GuardrailHealthCheck
from eaip.logging.context import get_logger

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel


class GuardrailRuntimeModule:
    """Runtime module for the AI Guardrails engine."""

    name: str = "guardrails"

    def __init__(self) -> None:
        """Initialize the guardrails runtime module."""
        self._health_check = GuardrailHealthCheck()
        self._log = get_logger("eaip.guardrails.integration")
        self._engine: Any = None

    @property
    def health_check(self) -> GuardrailHealthCheck:
        """Return the guardrails health check instance."""
        return self._health_check

    @property
    def engine(self) -> Any:
        """Return the GuardrailsEngine instance."""
        return self._engine

    async def start(self, kernel: RuntimeKernel) -> None:
        """Initialize the guardrails engine and register health check."""
        from eaip.guardrails.service import GuardrailsEngine

        self._log.info("guardrails.module.starting")
        self._engine = GuardrailsEngine()
        kernel.platform.health.register(self._health_check)
        self._log.info("guardrails.module.started")

    async def stop(self, _kernel: RuntimeKernel) -> None:
        """Shut down the module."""
        self._log.info("guardrails.module.stopping")


__all__ = ["GuardrailRuntimeModule"]
