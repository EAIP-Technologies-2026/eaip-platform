"""Health checks for the Prompt Registry subsystem."""

from __future__ import annotations

from typing import Any

from eaip.health.checks import HealthReport, HealthStatus
from eaip.logging.context import get_logger
from eaip.prompt_registry.service import PromptRegistryService


class PromptRegistryHealthCheck:
    """Health checker for the Prompt Registry subsystem."""

    name: str = "prompt_registry"

    def __init__(self, service: PromptRegistryService) -> None:
        """Initialize the health check.

        Args:
            service: The PromptRegistryService instance to monitor.
        """
        self._service = service
        self._log = get_logger("eaip.prompt_registry.health")

    async def check(self) -> HealthReport:
        """Execute a health check against the registry service."""
        self._log.debug("health.check.start")

        details: dict[str, Any] = {"subsystem": "prompt_registry"}

        try:
            prompts = await self._service.list_prompts()
            details["prompts"] = len(prompts)
            details["status"] = "healthy"
            status = HealthStatus.HEALTHY
        except Exception as exc:
            details["error"] = str(exc)
            status = HealthStatus.UNHEALTHY

        result = HealthReport(
            component="prompt_registry",
            status=status,
            details=details,
        )

        self._log.debug("health.check.complete", status=status.value)
        return result


__all__ = ["PromptRegistryHealthCheck"]
