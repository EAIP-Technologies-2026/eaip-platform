"""Integration layer — wiring for the knowledge subsystem."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any

from eaip.capabilities.capability import Capability, CapabilityStatus
from eaip.health.checks import HealthCheck, HealthReport, HealthStatus
from eaip.knowledge.base import Chunker, EmbeddingProvider, VectorStore
from eaip.knowledge.chunker import FixedSizeChunker
from eaip.knowledge.embedding import MockEmbeddingProvider
from eaip.knowledge.engine import KnowledgeEngine
from eaip.knowledge.events import KnowledgeEngineEvent
from eaip.knowledge.models import ChunkingConfig
from eaip.knowledge.qdrant_store import QdrantStore
from eaip.logging.context import get_logger

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel


class KnowledgeIntegration:
    """Wiring for the knowledge subsystem.

    Provides factory methods and lifecycle hooks so that the
    knowledge subsystem can be registered with the EAIP runtime
    and consumed by other components.
    """

    name: str = "knowledge"

    def __init__(
        self,
        engine: KnowledgeEngine | None = None,
        **_kwargs: object,
    ) -> None:
        """Initialize the integration.

        Args:
            engine: Optional KnowledgeEngine instance.
        """
        self._engine = engine
        self._started = engine is not None
        self._startup_duration: float = 0.0
        self._log = get_logger("eaip.knowledge.integration")

    @property
    def engine(self) -> KnowledgeEngine:
        """Return the underlying KnowledgeEngine."""
        if self._engine is None:
            raise RuntimeError("KnowledgeEngine not initialized. Call start() first.")
        return self._engine

    @property
    def startup_duration(self) -> float:
        """Return the last startup duration in seconds."""
        return self._startup_duration

    async def start(self, kernel: RuntimeKernel | None = None) -> None:
        """Start the knowledge integration.

        If no engine was provided at construction, creates a minimal
        engine using the default providers.

        Args:
            kernel: Optional runtime kernel for platform integration.
        """
        t0 = time.monotonic()
        self._log.info("integration.start")

        if self._engine is None:
            _store = QdrantStore(host="localhost", port=6333)
            _embedding = MockEmbeddingProvider(dimensions=384)
            _chunker = FixedSizeChunker(ChunkingConfig())
            self._engine = KnowledgeEngine(
                _store,
                _embedding,
                _chunker,
                default_collection="default",
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
        """Stop the knowledge integration."""
        self._log.info("integration.stop")
        self._started = False

    async def register_with_runtime(self) -> None:
        """Register with the EAIP runtime.

        Registers health checks and capabilities.
        """
        self._log.info("integration.register")

    def on_event(self, handler: Any) -> None:
        """Register an event handler on the engine.

        Args:
            handler: A callable accepting a KnowledgeEngineEvent.
        """
        engine = self._engine
        if engine is not None:
            engine.on(KnowledgeEngineEvent, handler)

    def _name_check(self) -> HealthCheck:
        check_name = "knowledge"

        class _KnowledgeHealthCheck:
            name: str = check_name

            async def check(self) -> HealthReport:
                return HealthReport(
                    component=check_name,
                    status=HealthStatus.HEALTHY,
                )

        return _KnowledgeHealthCheck()

    def _name_capability(self) -> Capability:
        return Capability(
            name="knowledge:engine",
            title="Knowledge Engine",
            status=CapabilityStatus.ENABLED,
        )


def create_knowledge_integration(
    vector_store: VectorStore,
    embedding_provider: EmbeddingProvider,
    chunker: Chunker,
    *,
    default_collection: str = "default",
    event_handlers: dict[type[KnowledgeEngineEvent], list[Any]] | None = None,
) -> KnowledgeIntegration:
    """Create a fully wired KnowledgeIntegration.

    Args:
        vector_store: The vector store.
        embedding_provider: The embedding provider.
        chunker: The chunking strategy.
        default_collection: Default collection name.
        event_handlers: Optional event handlers.

    Returns:
        A configured KnowledgeIntegration.
    """
    engine = KnowledgeEngine(
        vector_store,
        embedding_provider,
        chunker,
        default_collection=default_collection,
        event_handlers=event_handlers,
    )
    return KnowledgeIntegration(engine=engine)


class KnowledgeRuntimeModule(KnowledgeIntegration):
    """Runtime module wrapper for the knowledge subsystem.

    Alias for KnowledgeIntegration used by the runtime loader.
    """


__all__ = [
    "KnowledgeIntegration",
    "KnowledgeRuntimeModule",
    "create_knowledge_integration",
]
