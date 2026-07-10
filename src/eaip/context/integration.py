"""Integration layer — wiring for the context & prompt intelligence subsystem."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

from eaip.capabilities.capability import Capability, CapabilityStatus
from eaip.context.builder import ContextBuilder
from eaip.context.compression import ContextCompressor
from eaip.context.health import ContextHealthCheck
from eaip.context.registry import PromptRegistry
from eaip.context.templates import PromptManager
from eaip.health.checks import HealthReport
from eaip.logging.context import get_logger

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel


class ContextRuntimeModule:
    """Runtime module for the context & prompt intelligence subsystem.

    Wires the PromptRegistry, PromptManager, ContextBuilder, and
    ContextCompressor into the EAIP runtime, registering health
    checks and capabilities.
    """

    name: str = "context"

    def __init__(
        self,
        registry: PromptRegistry | None = None,
        builder: ContextBuilder | None = None,
        compressor: ContextCompressor | None = None,
        manager: PromptManager | None = None,
        **_kwargs: object,
    ) -> None:
        """Initialize the ContextRuntimeModule.

        Args:
            registry: Optional PromptRegistry instance.
            builder: Optional ContextBuilder instance.
            compressor: Optional ContextCompressor instance.
            manager: Optional PromptManager instance.
        """
        self._registry = registry or PromptRegistry()
        self._manager = manager or PromptManager(registry=self._registry)
        self._builder = builder
        self._compressor = compressor
        self._started = False
        self._startup_duration: float = 0.0
        self._log = get_logger("eaip.context.integration")

    @property
    def registry(self) -> PromptRegistry:
        """Return the PromptRegistry."""
        return self._registry

    @property
    def manager(self) -> PromptManager:
        """Return the PromptManager."""
        return self._manager

    @property
    def builder(self) -> ContextBuilder:
        """Return the ContextBuilder.

        Raises:
            RuntimeError: If not started.
        """
        if self._builder is None:
            raise RuntimeError("ContextBuilder not initialized. Call start() first.")
        return self._builder

    @property
    def compressor(self) -> ContextCompressor:
        """Return the ContextCompressor.

        Raises:
            RuntimeError: If not started.
        """
        if self._compressor is None:
            raise RuntimeError("ContextCompressor not initialized. Call start() first.")
        return self._compressor

    @property
    def startup_duration(self) -> float:
        """Return the last startup duration in seconds."""
        return self._startup_duration

    async def start(self, kernel: RuntimeKernel | None = None) -> None:
        """Start the context runtime module.

        Initializes default components if none were provided and
        registers health checks and capabilities with the kernel.

        Args:
            kernel: Optional runtime kernel for platform integration.
        """
        t0 = time.monotonic()
        self._log.info("integration.start")

        if self._builder is None:
            self._builder = ContextBuilder()

        if self._compressor is None:
            self._compressor = ContextCompressor()

        self._started = True

        if kernel is not None:
            kernel.platform.health.register(_ContextSystemHealthCheck(self._registry))
            kernel.platform.capabilities.register(self._capability())

        self._startup_duration = time.monotonic() - t0
        self._log.info(
            "integration.complete",
            duration_s=round(self._startup_duration, 3),
        )

    async def stop(self, _kernel: RuntimeKernel | None = None) -> None:
        """Stop the context runtime module.

        Args:
            _kernel: Optional runtime kernel (unused).
        """
        self._log.info("integration.stop")
        self._started = False

    def _capability(self) -> Capability:
        """Create the capability descriptor for this module.

        Returns:
            A Capability instance.
        """
        return Capability(
            name="context:engine",
            title="Context & Prompt Intelligence",
            status=CapabilityStatus.ENABLED,
        )


class _ContextSystemHealthCheck:
    """Ad-hoc health check that wraps ContextHealthCheck for registration."""

    name: str = "context"

    def __init__(self, registry: PromptRegistry) -> None:
        """Initialize the health check.

        Args:
            registry: The PromptRegistry instance.
        """
        self._check = ContextHealthCheck(registry)

    async def check(self) -> HealthReport:
        """Delegate to ContextHealthCheck.check.

        Returns:
            A HealthReport.
        """
        return await self._check.check()


def create_context_integration(
    *,
    registry: PromptRegistry | None = None,
    builder: ContextBuilder | None = None,
    compressor: ContextCompressor | None = None,
    manager: PromptManager | None = None,
) -> ContextRuntimeModule:
    """Create a fully wired ContextRuntimeModule.

    Args:
        registry: Optional PromptRegistry.
        builder: Optional ContextBuilder.
        compressor: Optional ContextCompressor.
        manager: Optional PromptManager.

    Returns:
        A configured ContextRuntimeModule.
    """
    return ContextRuntimeModule(
        registry=registry,
        builder=builder,
        compressor=compressor,
        manager=manager,
    )


__all__ = [
    "ContextRuntimeModule",
    "create_context_integration",
]
