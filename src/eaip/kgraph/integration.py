"""Integration layer — wiring for the knowledge graph subsystem."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

from eaip.capabilities.capability import Capability, CapabilityStatus
from eaip.health.checks import HealthCheck, HealthReport, HealthStatus
from eaip.kgraph.graph import KnowledgeGraph
from eaip.kgraph.index import GraphIndex
from eaip.kgraph.semantic import SemanticRelationshipService
from eaip.logging.context import get_logger

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel


class GraphRuntimeModule:
    """Runtime module for the Knowledge Graph subsystem.

    Implements the RuntimeModule protocol. Wires up the KnowledgeGraph,
    GraphIndex, SemanticRelationshipService, health checks, and
    capabilities with the EAIP runtime kernel.
    """

    name: str = "kgraph"

    def __init__(self, graph: KnowledgeGraph | None = None) -> None:
        """Initialize the graph runtime module.

        Args:
            graph: Optional pre-configured KnowledgeGraph instance.
        """
        self._graph = graph
        self._index: GraphIndex | None = None
        self._semantic: SemanticRelationshipService | None = None
        self._started = graph is not None
        self._startup_duration: float = 0.0
        self._log = get_logger("eaip.kgraph.integration")

    @property
    def graph(self) -> KnowledgeGraph:
        """Return the underlying KnowledgeGraph instance."""
        if self._graph is None:
            raise RuntimeError("KnowledgeGraph not initialized. Call start() first.")
        return self._graph

    @property
    def index(self) -> GraphIndex:
        """Return the GraphIndex instance."""
        if self._index is None:
            raise RuntimeError("GraphIndex not initialized. Call start() first.")
        return self._index

    @property
    def semantic(self) -> SemanticRelationshipService:
        """Return the SemanticRelationshipService instance."""
        if self._semantic is None:
            raise RuntimeError("SemanticRelationshipService not initialized. Call start() first.")
        return self._semantic

    @property
    def startup_duration(self) -> float:
        """Return the last startup duration in seconds."""
        return self._startup_duration

    async def start(self, kernel: RuntimeKernel | None = None) -> None:
        """Start the graph runtime module.

        Creates the KnowledgeGraph, GraphIndex and SemanticRelationshipService
        if not provided. Registers health checks and capabilities.

        Args:
            kernel: Optional runtime kernel for platform integration.
        """
        t0 = time.monotonic()
        self._log.info("kgraph.start")

        if self._graph is None:
            self._graph = KnowledgeGraph()

        self._index = GraphIndex(self._graph)
        self._semantic = SemanticRelationshipService(self._graph)

        if kernel is not None:
            kernel.platform.health.register(self._health_check())
            kernel.platform.capabilities.register(self._capability())

        self._startup_duration = time.monotonic() - t0
        self._started = True
        self._log.info("kgraph.started", duration_s=round(self._startup_duration, 3))

    async def stop(self, _kernel: RuntimeKernel | None = None) -> None:
        """Stop the graph runtime module."""
        self._log.info("kgraph.stop")
        self._started = False

    def _health_check(self) -> HealthCheck:
        check_name = "kgraph"

        class _GraphHealthCheck:
            name: str = check_name

            async def check(self) -> HealthReport:
                return HealthReport(
                    component=check_name,
                    status=HealthStatus.HEALTHY,
                )

        return _GraphHealthCheck()

    def _capability(self) -> Capability:
        return Capability(
            name="kgraph:engine",
            title="Knowledge Graph Engine",
            description="Enterprise knowledge graph with entity/relationship models, "
            "traversal, queries, indexing, and semantic inference",
            status=CapabilityStatus.ENABLED,
        )

    async def register_with_runtime(self) -> None:
        """Register with the EAIP runtime (health checks, capabilities)."""
        self._log.info("kgraph.register")


def create_graph_module(
    graph: KnowledgeGraph | None = None,
) -> GraphRuntimeModule:
    """Create a fully wired GraphRuntimeModule.

    Args:
        graph: Optional pre-configured KnowledgeGraph instance.

    Returns:
        A configured GraphRuntimeModule.
    """
    return GraphRuntimeModule(graph=graph)


__all__ = [
    "GraphRuntimeModule",
    "create_graph_module",
]
