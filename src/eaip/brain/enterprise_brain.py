"""EnterpriseBrain — centralized intelligence layer for knowledge, memory, context, and agents."""

from __future__ import annotations

import time
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from eaip.brain.events import (
    BrainContextBuilt,
    BrainKnowledgeRetrieved,
    BrainMemoryRetrieved,
    BrainQueryExecuted,
)
from eaip.brain.exceptions import BrainQueryError, BrainSourceUnavailableError
from eaip.brain.models import BrainQuery, BrainResult, BrainSource, EnterpriseBrainConfig
from eaip.logging.context import get_logger

if TYPE_CHECKING:
    from eaip.agents.runtime import AgentRuntime
    from eaip.context.builder import ContextBuilder
    from eaip.knowledge.engine import KnowledgeEngine
    from eaip.memory.engine import MemoryEngine


class EnterpriseBrain:
    """Centralized intelligence layer that orchestrates knowledge, memory,
    context, and agent insights across the entire enterprise.
    """

    def __init__(
        self,
        knowledge_engine: KnowledgeEngine | None = None,
        memory_engine: MemoryEngine | None = None,
        context_builder: ContextBuilder | None = None,
        agent_runtime: AgentRuntime | None = None,
        *,
        config: EnterpriseBrainConfig | None = None,
        event_publisher: Callable[[object], None] | None = None,
    ) -> None:
        """Initialize the EnterpriseBrain.

        Args:
            knowledge_engine: Optional KnowledgeEngine instance.
            memory_engine: Optional MemoryEngine instance.
            context_builder: Optional ContextBuilder instance.
            agent_runtime: Optional AgentRuntime instance.
            config: Optional brain configuration.
            event_publisher: Optional callable for publishing domain events.
        """
        self._knowledge = knowledge_engine
        self._memory = memory_engine
        self._context = context_builder
        self._agents = agent_runtime
        self._config = config or EnterpriseBrainConfig()
        self._event_publisher = event_publisher or (lambda _: None)
        self._log = get_logger("eaip.brain.enterprise_brain")

    @property
    def config(self) -> EnterpriseBrainConfig:
        """Return the current configuration."""
        return self._config

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def query(self, brain_query: BrainQuery) -> BrainResult:
        """Query all knowledge bases, memory, and context.

        Args:
            brain_query: The query parameters.

        Returns:
            A BrainResult with merged, ranked sources.

        Raises:
            BrainQueryError: If the query fails.
        """
        t0 = time.monotonic()
        self._log.info("brain.query.start", query=brain_query.query[:100])

        all_sources: list[BrainSource] = []

        try:
            if brain_query.include_knowledge:
                sources = await self._query_knowledge(brain_query)
                all_sources.extend(sources)

            if brain_query.include_memory:
                sources = await self._query_memory(brain_query)
                all_sources.extend(sources)

            if brain_query.include_context:
                sources = await self._query_context(brain_query)
                all_sources.extend(sources)
        except Exception as exc:
            raise BrainQueryError(
                f"Brain query failed: {exc}",
                context={"query": brain_query.query},
            ) from exc

        all_sources = self._deduplicate(all_sources)
        all_sources = self._filter_by_threshold(all_sources, brain_query.score_threshold)
        all_sources.sort(key=lambda s: s.relevance_score, reverse=True)

        if self._config.enable_reranking:
            all_sources = self._rerank(all_sources)

        top_k = brain_query.top_k or self._config.default_top_k
        all_sources = all_sources[:top_k]

        confidence = self._compute_confidence(all_sources)
        answer = self._build_answer(all_sources)
        token_count = sum(len(s.content_preview.split()) for s in all_sources)

        duration_ms = (time.monotonic() - t0) * 1000.0

        self._event_publisher(
            BrainQueryExecuted(
                query=brain_query.query,
                source_count=len(all_sources),
                duration_ms=duration_ms,
                confidence=confidence,
            )
        )

        self._log.info(
            "brain.query.complete",
            sources=len(all_sources),
            confidence=round(confidence, 3),
            duration_ms=round(duration_ms, 1),
        )

        return BrainResult(
            query=brain_query.query,
            answer=answer,
            confidence=confidence,
            sources=tuple(all_sources),
            duration_ms=duration_ms,
            token_count=token_count,
        )

    async def query_knowledge(
        self,
        query: str,
        collections: tuple[str, ...] = (),
    ) -> list[BrainSource]:
        """Query the Knowledge Engine.

        Args:
            query: The search query.
            collections: Optional collection names to scope the query.

        Returns:
            A list of BrainSource items from knowledge.
        """
        return await self._query_knowledge(BrainQuery(query=query, collection_names=collections))

    async def query_memory(self, query: str, scope: Any = None) -> list[BrainSource]:
        """Query the Memory Engine.

        Args:
            query: The search query.
            scope: Optional memory scope.

        Returns:
            A list of BrainSource items from memory.
        """
        return await self._query_memory(BrainQuery(query=query), scope=scope)

    async def query_context(self, query: str) -> list[BrainSource]:
        """Build relevant context.

        Args:
            query: The context query.

        Returns:
            A list of BrainSource items from context assembly.
        """
        return await self._query_context(BrainQuery(query=query))

    async def query_agents(
        self,
        query: str,
        agent_ids: tuple[str, ...] = (),
    ) -> list[BrainSource]:
        """Delegate a query to the Agent Runtime.

        Args:
            query: The query to delegate.
            agent_ids: Specific agent IDs to target.

        Returns:
            A list of BrainSource items from agent responses.
        """
        return await self._query_agents(BrainQuery(query=query), agent_ids=agent_ids)

    async def health(self) -> dict[str, Any]:
        """Return health status for this brain.

        Returns:
            A dict with health information.
        """
        details: dict[str, Any] = {
            "status": "healthy",
            "knowledge_configured": self._knowledge is not None,
            "memory_configured": self._memory is not None,
            "context_configured": self._context is not None,
            "agents_configured": self._agents is not None,
        }
        return details

    # ------------------------------------------------------------------
    # Internal source queries
    # ------------------------------------------------------------------

    async def _query_knowledge(
        self,
        brain_query: BrainQuery,
    ) -> list[BrainSource]:
        """Query knowledge engine and return BrainSource items."""
        sources: list[BrainSource] = []
        engine = self._knowledge
        if engine is None:
            return sources

        t0 = time.monotonic()
        try:
            collections = brain_query.collection_names or ("default",)
            for collection in collections:
                if hasattr(engine, "search"):
                    result = await engine.search(
                        brain_query.query,
                        top_k=brain_query.top_k,
                        collection=collection,
                    )
                    for chunk in getattr(result, "chunks", result or []):
                        content = _extract_content(chunk)
                        if content:
                            sources.append(
                                BrainSource(
                                    source_type="knowledge",
                                    source_id=getattr(chunk, "chunk_id", ""),
                                    content_preview=content[: self._config.max_tokens_per_source],
                                    relevance_score=getattr(chunk, "score", 0.0),
                                    collection=collection,
                                )
                            )
        except Exception as exc:
            self._log.warning("knowledge.query.failed", error=str(exc))
            raise BrainSourceUnavailableError(
                f"Knowledge source unavailable: {exc}",
            ) from exc

        duration_ms = (time.monotonic() - t0) * 1000.0
        self._event_publisher(
            BrainKnowledgeRetrieved(
                query=brain_query.query,
                collections=brain_query.collection_names,
                result_count=len(sources),
                duration_ms=duration_ms,
            )
        )
        return sources

    async def _query_memory(
        self,
        brain_query: BrainQuery,
        scope: Any = None,
    ) -> list[BrainSource]:
        """Query memory engine and return BrainSource items."""
        sources: list[BrainSource] = []
        engine = self._memory
        if engine is None:
            return sources

        t0 = time.monotonic()
        try:
            if hasattr(engine, "search_memories"):
                from eaip.memory.models import MemoryQuery

                mem_query = MemoryQuery(
                    query=brain_query.query,
                    top_k=brain_query.top_k,
                    scopes=(scope,) if scope is not None else (),
                )
                result = await engine.search_memories(mem_query)
                for item in getattr(result, "results", result or []):
                    memory = getattr(item, "memory", item)
                    content = _extract_content(memory)
                    if content:
                        sources.append(
                            BrainSource(
                                source_type="memory",
                                source_id=getattr(memory, "memory_id", ""),
                                content_preview=content[: self._config.max_tokens_per_source],
                                relevance_score=getattr(item, "score", 0.0),
                                collection="memory",
                            )
                        )
        except Exception as exc:
            self._log.warning("memory.query.failed", error=str(exc))
            raise BrainSourceUnavailableError(
                f"Memory source unavailable: {exc}",
            ) from exc

        duration_ms = (time.monotonic() - t0) * 1000.0
        self._event_publisher(
            BrainMemoryRetrieved(
                query=brain_query.query,
                result_count=len(sources),
                duration_ms=duration_ms,
            )
        )
        return sources

    async def _query_context(
        self,
        brain_query: BrainQuery,
    ) -> list[BrainSource]:
        """Build context and return BrainSource items."""
        sources: list[BrainSource] = []
        builder = self._context
        if builder is None:
            return sources

        t0 = time.monotonic()
        try:
            if hasattr(builder, "assemble"):
                context = await builder.assemble(query=brain_query.query)
                for doc in getattr(context, "documents", context or []):
                    content = _extract_content(doc)
                    if content:
                        sources.append(
                            BrainSource(
                                source_type="context",
                                source_id=getattr(doc, "source", ""),
                                content_preview=content[: self._config.max_tokens_per_source],
                                relevance_score=getattr(doc, "relevance_score", 0.0),
                                collection="context",
                            )
                        )
        except Exception as exc:
            self._log.warning("context.build.failed", error=str(exc))

        duration_ms = (time.monotonic() - t0) * 1000.0
        document_count = getattr(context, "document_count", 0) if "context" in dir() else 0
        total_tokens = getattr(context, "total_tokens", 0) if "context" in dir() else 0
        self._event_publisher(
            BrainContextBuilt(
                query=brain_query.query,
                document_count=document_count,
                total_tokens=total_tokens,
                duration_ms=duration_ms,
            )
        )
        return sources

    async def _query_agents(
        self,
        brain_query: BrainQuery,
        agent_ids: tuple[str, ...] = (),
    ) -> list[BrainSource]:
        """Query agent runtime and return BrainSource items."""
        sources: list[BrainSource] = []
        runtime = self._agents
        if runtime is None:
            return sources

        try:
            if hasattr(runtime, "list_runs"):
                runs = runtime.list_runs()
                for run in runs:
                    output = getattr(run, "result", "") or ""
                    if output and brain_query.query.lower() in output.lower():
                        sources.append(
                            BrainSource(
                                source_type="agent",
                                source_id=getattr(run, "id", ""),
                                content_preview=output[: self._config.max_tokens_per_source],
                                relevance_score=1.0,
                                collection=getattr(run, "agent_id", ""),
                            )
                        )
        except Exception as exc:
            self._log.warning("agents.query.failed", error=str(exc))

        return sources

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _deduplicate(self, sources: list[BrainSource]) -> list[BrainSource]:
        """Remove duplicates by source_id within the same source_type."""
        seen: set[tuple[str, str]] = set()
        deduped: list[BrainSource] = []
        for s in sources:
            key = (s.source_type, s.source_id)
            if key not in seen:
                seen.add(key)
                deduped.append(s)
        return deduped

    def _filter_by_threshold(
        self,
        sources: list[BrainSource],
        threshold: float,
    ) -> list[BrainSource]:
        """Filter sources below a relevance score threshold."""
        if threshold <= 0.0:
            return sources
        return [s for s in sources if s.relevance_score >= threshold]

    def _rerank(self, sources: list[BrainSource]) -> list[BrainSource]:
        """Apply cross-source reranking logic."""
        return sorted(sources, key=lambda s: s.relevance_score, reverse=True)

    def _compute_confidence(self, sources: list[BrainSource]) -> float:
        """Compute overall confidence from source scores."""
        if not sources:
            return 0.0
        weights = {"knowledge": 1.0, "memory": 0.8, "context": 0.9, "agent": 0.7}
        total_weight = 0.0
        weighted_sum = 0.0
        for s in sources:
            w = weights.get(s.source_type, 0.5)
            weighted_sum += s.relevance_score * w
            total_weight += w
        if total_weight == 0.0:
            return 0.0
        return min(1.0, weighted_sum / total_weight)

    def _build_answer(self, sources: list[BrainSource]) -> str:
        """Build a summary answer from source content."""
        if not sources:
            return ""
        parts: list[str] = []
        for s in sources[:3]:
            preview = s.content_preview[:200].strip()
            if preview:
                parts.append(f"[{s.source_type}]: {preview}")
        return "\n\n".join(parts) if parts else ""


def _extract_content(item: Any) -> str:
    """Extract textual content from a result item."""
    if isinstance(item, str):
        return item
    if isinstance(item, dict):
        return str(item.get("content", item.get("text", "")))
    for attr in ("content", "text", "page_content"):
        candidate = getattr(item, attr, None)
        if isinstance(candidate, str) and candidate:
            return candidate
    return str(item)


__all__ = ["EnterpriseBrain"]
