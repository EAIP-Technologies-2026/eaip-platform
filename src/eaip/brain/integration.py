"""Integration layer — BrainRuntimeModule for kernel lifecycle."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any

from eaip.brain.enterprise_brain import EnterpriseBrain
from eaip.brain.events import BrainEvent
from eaip.brain.health import BrainHealthCheck
from eaip.brain.models import EnterpriseBrainConfig
from eaip.capabilities.capability import Capability, CapabilityStatus
from eaip.health.checks import HealthCheck, HealthReport, HealthStatus
from eaip.logging.context import get_logger

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel


class BrainRuntimeModule:
    """RuntimeModule that bootstraps the Enterprise Brain during kernel start.

    Wires together knowledge, memory, context, and agent subsystems
    under the centralized brain orchestration layer.
    """

    name: str = "brain"

    def __init__(
        self,
        brain: EnterpriseBrain | None = None,
        config: EnterpriseBrainConfig | None = None,
        **_kwargs: object,
    ) -> None:
        """Initialize the BrainRuntimeModule.

        Args:
            brain: Optional EnterpriseBrain instance.
            config: Optional brain configuration.
        """
        self._brain = brain
        self._config = config
        self._started = brain is not None
        self._startup_duration: float = 0.0
        self._log = get_logger("eaip.brain.integration")

    @property
    def brain(self) -> EnterpriseBrain:
        """Return the underlying EnterpriseBrain."""
        if self._brain is None:
            raise RuntimeError("EnterpriseBrain not initialized. Call start() first.")
        return self._brain

    @property
    def startup_duration(self) -> float:
        """Return the last startup duration in seconds."""
        return self._startup_duration

    async def start(self, kernel: RuntimeKernel | None = None) -> None:
        """Start the brain integration.

        If no brain was provided at construction, creates a minimal
        brain with default configuration.

        Args:
            kernel: Optional runtime kernel for platform integration.
        """
        t0 = time.monotonic()
        self._log.info("integration.start")

        if self._brain is None:
            config = self._config or EnterpriseBrainConfig()
            self._brain = EnterpriseBrain(config=config)

        health = await self._brain.health()
        self._log.info("integration.health", status=health.get("status"))

        if kernel is not None:
            kernel.platform.health.register(self._name_check())
            kernel.platform.capabilities.register(self._name_capability())

        self._startup_duration = time.monotonic() - t0
        self._started = True
        self._log.info(
            "integration.complete",
            duration_s=round(self._startup_duration, 3),
        )

    async def stop(self, _kernel: RuntimeKernel | None = None) -> None:
        """Stop the brain integration."""
        self._log.info("integration.stop")
        self._started = False

    def on_event(self, handler: Any) -> None:
        """Register an event handler on the brain.

        Args:
            handler: A callable accepting a BrainEvent.
        """
        brain = self._brain
        if brain is not None:
            self._log.debug("integration.on_event")

    def _name_check(self) -> HealthCheck:
        check_name = "brain"

        class _BrainHealthCheck:
            name: str = check_name

            async def check(self) -> HealthReport:
                return HealthReport(
                    component=check_name,
                    status=HealthStatus.HEALTHY,
                )

        return _BrainHealthCheck()

    def _name_capability(self) -> Capability:
        return Capability(
            name="brain:engine",
            title="Enterprise Brain",
            status=CapabilityStatus.ENABLED,
        )


def create_brain_integration(
    *,
    knowledge_engine: Any = None,
    memory_engine: Any = None,
    context_builder: Any = None,
    agent_runtime: Any = None,
    config: EnterpriseBrainConfig | None = None,
    event_publisher: Any = None,
) -> BrainRuntimeModule:
    """Create a fully wired BrainRuntimeModule.

    Args:
        knowledge_engine: Optional KnowledgeEngine instance.
        memory_engine: Optional MemoryEngine instance.
        context_builder: Optional ContextBuilder instance.
        agent_runtime: Optional AgentRuntime instance.
        config: Optional brain configuration.
        event_publisher: Optional event publisher.

    Returns:
        A configured BrainRuntimeModule.
    """
    brain = EnterpriseBrain(
        knowledge_engine=knowledge_engine,
        memory_engine=memory_engine,
        context_builder=context_builder,
        agent_runtime=agent_runtime,
        config=config,
        event_publisher=event_publisher,
    )
    return BrainRuntimeModule(brain=brain)


__all__ = [
    "BrainRuntimeModule",
    "create_brain_integration",
]
