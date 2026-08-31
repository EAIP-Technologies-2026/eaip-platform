"""Integration layer — wiring for the Prompt Registry subsystem."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

from eaip.capabilities.capability import Capability, CapabilityStatus
from eaip.health.checks import HealthReport
from eaip.logging.context import get_logger
from eaip.prompt_registry.health import PromptRegistryHealthCheck
from eaip.prompt_registry.models import PromptRegistryConfig
from eaip.prompt_registry.service import PromptRegistryService

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel


class PromptRegistryRuntimeModule:
    """Runtime module for the Prompt Registry subsystem."""

    name: str = "prompt_registry"

    def __init__(
        self,
        service: PromptRegistryService | None = None,
        config: PromptRegistryConfig | None = None,
        **_kwargs: object,
    ) -> None:
        """Initialize the PromptRegistryRuntimeModule.

        Args:
            service: Optional PromptRegistryService instance.
            config: Optional PromptRegistryConfig instance.
        """
        self._config = config or PromptRegistryConfig()
        self._service = service or PromptRegistryService(config=self._config)
        self._started = False
        self._startup_duration: float = 0.0
        self._log = get_logger("eaip.prompt_registry.integration")

    @property
    def service(self) -> PromptRegistryService:
        """Return the PromptRegistryService."""
        return self._service

    @property
    def startup_duration(self) -> float:
        """Return the last startup duration in seconds."""
        return self._startup_duration

    async def start(self, kernel: RuntimeKernel | None = None) -> None:
        """Start the prompt registry runtime module.

        Registers health checks and capabilities with the kernel.

        Args:
            kernel: Optional runtime kernel for platform integration.
        """
        t0 = time.monotonic()
        self._log.info("integration.start")

        self._started = True

        if kernel is not None:
            kernel.platform.health.register(
                _PromptRegistrySystemHealthCheck(self._service),
            )
            kernel.platform.capabilities.register(self._capability())

        self._startup_duration = time.monotonic() - t0
        self._log.info(
            "integration.complete",
            duration_s=round(self._startup_duration, 3),
        )

    async def stop(self, _kernel: RuntimeKernel | None = None) -> None:
        """Stop the prompt registry runtime module.

        Args:
            _kernel: Optional runtime kernel (unused).
        """
        self._log.info("integration.stop")
        self._started = False

    def _capability(self) -> Capability:
        return Capability(
            name="prompt_registry:engine",
            title="Prompt Registry",
            status=CapabilityStatus.ENABLED,
        )


class _PromptRegistrySystemHealthCheck:
    name: str = "prompt_registry"

    def __init__(self, service: PromptRegistryService) -> None:
        self._check = PromptRegistryHealthCheck(service)

    async def check(self) -> HealthReport:
        return await self._check.check()


def create_prompt_registry_integration(
    *,
    service: PromptRegistryService | None = None,
    config: PromptRegistryConfig | None = None,
) -> PromptRegistryRuntimeModule:
    """Create a fully wired PromptRegistryRuntimeModule.

    Args:
        service: Optional PromptRegistryService.
        config: Optional PromptRegistryConfig.

    Returns:
        A configured PromptRegistryRuntimeModule.
    """
    return PromptRegistryRuntimeModule(
        service=service,
        config=config,
    )


__all__ = [
    "PromptRegistryRuntimeModule",
    "create_prompt_registry_integration",
]
