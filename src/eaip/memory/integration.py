"""Integration layer — wiring for the memory subsystem."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any

from eaip.capabilities.capability import Capability, CapabilityStatus
from eaip.health.checks import HealthCheck, HealthReport, HealthStatus
from eaip.logging.context import get_logger
from eaip.memory.engine import MemoryEngine
from eaip.memory.events import MemoryEngineEvent
from eaip.memory.models import MemoryConfig, RetentionConfig
from eaip.memory.store import InMemoryStore

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel


class MemoryIntegration:
    """Wiring for the memory subsystem.

    Provides factory methods and lifecycle hooks so that the
    memory subsystem can be registered with the EAIP runtime
    and consumed by other components.
    """

    name: str = "memory"

    def __init__(
        self,
        engine: MemoryEngine | None = None,
        **_kwargs: object,
    ) -> None:
        """Initialize the integration.

        Args:
            engine: Optional MemoryEngine instance.
        """
        self._engine = engine
        self._started = engine is not None
        self._startup_duration: float = 0.0
        self._log = get_logger("eaip.memory.integration")

    @property
    def engine(self) -> MemoryEngine:
        """Return the underlying MemoryEngine."""
        if self._engine is None:
            raise RuntimeError("MemoryEngine not initialized. Call start() first.")
        return self._engine

    @property
    def startup_duration(self) -> float:
        """Return the last startup duration in seconds."""
        return self._startup_duration

    async def start(self, kernel: RuntimeKernel | None = None) -> None:
        """Start the memory integration.

        If no engine was provided at construction, creates a minimal
        engine using the default in-memory store.

        Args:
            kernel: Optional runtime kernel for platform integration.
        """
        t0 = time.monotonic()
        self._log.info("integration.start")

        if self._engine is None:
            _store = InMemoryStore()
            self._engine = MemoryEngine(
                _store,
                config=MemoryConfig(),
                retention=RetentionConfig(),
            )

        health = await self._engine.health()
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
        """Stop the memory integration."""
        self._log.info("integration.stop")
        self._started = False

    def on_event(self, handler: Any) -> None:
        """Register an event handler on the engine.

        Args:
            handler: A callable accepting a MemoryEngineEvent.
        """
        engine = self._engine
        if engine is not None:
            engine.on(MemoryEngineEvent, handler)

    def _name_check(self) -> HealthCheck:
        check_name = "memory"

        class _MemoryHealthCheck:
            name: str = check_name

            async def check(self) -> HealthReport:
                return HealthReport(
                    component=check_name,
                    status=HealthStatus.HEALTHY,
                )

        return _MemoryHealthCheck()

    def _name_capability(self) -> Capability:
        return Capability(
            name="memory:engine",
            title="Memory Engine",
            status=CapabilityStatus.ENABLED,
        )


def create_memory_integration(
    store: Any = None,
    *,
    config: MemoryConfig | None = None,
    retention: RetentionConfig | None = None,
) -> MemoryIntegration:
    """Create a fully wired MemoryIntegration.

    Args:
        store: Optional memory store (defaults to InMemoryStore).
        config: Optional memory engine configuration.
        retention: Optional retention configuration.

    Returns:
        A configured MemoryIntegration.
    """
    _store = store or InMemoryStore()
    _engine = MemoryEngine(
        _store,
        config=config or MemoryConfig(),
        retention=retention or RetentionConfig(),
    )
    return MemoryIntegration(engine=_engine)


class MemoryRuntimeModule(MemoryIntegration):
    """Runtime module wrapper for the memory subsystem.

    Alias for MemoryIntegration used by the runtime loader.
    """


__all__ = [
    "MemoryIntegration",
    "MemoryRuntimeModule",
    "create_memory_integration",
]
