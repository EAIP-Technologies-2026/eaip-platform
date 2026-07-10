"""KnowledgeFederation — federated search across collections and memory stores."""

from __future__ import annotations

import time
from collections.abc import Sequence
from typing import Any

from eaip.knowledge.events import FederatedSearchExecuted
from eaip.knowledge.models import (
    AssembledContext,
    RetrievalResult,
    RetrievedChunk,
)
from eaip.knowledge.retrieval_engine import RetrievalEngine
from eaip.knowledge.search_strategies import RerankingStrategy, SimpleReranker
from eaip.logging.context import get_logger


class KnowledgeFederation:
    """Federated search across multiple knowledge collections and memory stores.

    Supports:
    - Department brain retrieval (scoped to department collections)
    - Enterprise brain retrieval (cross-department, cross-collection)
    - Federated search across knowledge engine + memory engine
    - Result aggregation, deduplication, and score normalization
    """

    def __init__(
        self,
        retrieval_engine: RetrievalEngine,
        *,
        memory_search_fn: Any | None = None,
        reranker: RerankingStrategy | None = None,
        event_publisher: Any | None = None,
    ) -> None:
        """Initialize the KnowledgeFederation.

        Args:
            retrieval_engine: The RetrievalEngine for knowledge collection searches.
            memory_search_fn: Optional async callable ``(query_str, top_k) -> RetrievalResult``
                for searching the memory engine.
            reranker: Optional reranking strategy for merged results.
            event_publisher: Optional event publisher.
        """
        self._retrieval_engine = retrieval_engine
        self._memory_search_fn = memory_search_fn
        self._reranker = reranker or SimpleReranker()
        self._event_publisher = event_publisher
        self._log = get_logger("eaip.knowledge.federation")

    async def search_collections(
        self,
        query_str: str,
        collections: Sequence[str],
        *,
        top_k: int = 10,
        score_threshold: float = 0.0,
        enable_reranking: bool = True,
    ) -> RetrievalResult:
        """Federated search across multiple knowledge collections.

        Args:
            query_str: The search query.
            collections: Collection names to search.
            top_k: Maximum results in the merged result.
            score_threshold: Minimum score threshold.
            enable_reranking: Whether to apply reranking after merge.

        Returns:
            An aggregated RetrievalResult across all collections.
        """
        t0 = time.monotonic()

        self._log.info(
            "federation.search_collections",
            collections=list(collections),
            query=query_str[:80],
        )

        all_chunks: list[RetrievedChunk] = []
        for coll in collections:
            try:
                result = await self._retrieval_engine.search(
                    query_str,
                    collection=coll,
                    top_k=top_k,
                    score_threshold=score_threshold,
                    enable_reranking=False,
                )
                all_chunks.extend(result.chunks)
            except Exception as exc:
                self._log.warning(
                    "federation.search_collections.skipped",
                    collection=coll,
                    error=str(exc),
                )

        merged = await self._merge_and_normalize(
            all_chunks, query_str, top_k, score_threshold, enable_reranking,
        )
        duration = (time.monotonic() - t0) * 1000

        self._publish_event(FederatedSearchExecuted(
            query=query_str,
            sources=tuple(collections),
            result_count=merged.total_results,
            duration_ms=duration,
        ))

        return RetrievalResult(
            query=query_str,
            collection=",".join(collections),
            chunks=merged.chunks,
            context=merged.context,
            total_results=merged.total_results,
            duration_ms=duration,
        )

    async def search_all(
        self,
        query_str: str,
        *,
        top_k: int = 10,
        score_threshold: float = 0.0,
    ) -> RetrievalResult:
        """Federated search across ALL known collections.

        Uses the retrieval engine's vector store to discover collections.

        Args:
            query_str: The search query.
            top_k: Maximum results in the merged result.
            score_threshold: Minimum score threshold.

        Returns:
            An aggregated RetrievalResult across all collections.
        """
        try:
            collections = await self._retrieval_engine._vector_store.list_collections()
        except Exception:
            collections = ["default"]

        return await self.search_collections(
            query_str,
            collections,
            top_k=top_k,
            score_threshold=score_threshold,
            enable_reranking=True,
        )

    async def search_knowledge_and_memory(
        self,
        query_str: str,
        *,
        collections: Sequence[str] | None = None,
        top_k: int = 10,
        score_threshold: float = 0.0,
        memory_top_k: int = 5,
    ) -> RetrievalResult:
        """Federated search across knowledge collections and memory.

        Args:
            query_str: The search query.
            collections: Knowledge collections to search. If None, searches all.
            top_k: Maximum results in the merged result.
            score_threshold: Minimum score threshold.
            memory_top_k: Maximum results from the memory engine.

        Returns:
            An aggregated RetrievalResult from both knowledge and memory.
        """
        t0 = time.monotonic()

        knowledge_task = self.search_collections(
            query_str,
            collections or ["default"],
            top_k=top_k,
            score_threshold=score_threshold,
            enable_reranking=False,
        )

        memory_result: RetrievalResult | None = None
        if self._memory_search_fn is not None:
            try:
                memory_result = await self._memory_search_fn(query_str, memory_top_k)
            except Exception as exc:
                self._log.warning("federation.memory_search_failed", error=str(exc))

        knowledge_result = await knowledge_task

        all_chunks = list(knowledge_result.chunks)
        if memory_result is not None:
            all_chunks.extend(memory_result.chunks)

        merged = await self._merge_and_normalize(
            all_chunks, query_str, top_k, score_threshold, enable_reranking=True,
        )
        duration = (time.monotonic() - t0) * 1000

        src_list: list[str] = list(collections or ["default"])
        if memory_result is not None:
            src_list.append("memory")

        self._publish_event(FederatedSearchExecuted(
            query=query_str,
            sources=tuple(src_list),
            result_count=merged.total_results,
            duration_ms=duration,
        ))

        return RetrievalResult(
            query=query_str,
            collection=",".join(src_list),
            chunks=merged.chunks,
            context=merged.context,
            total_results=merged.total_results,
            duration_ms=duration,
        )

    async def search_department_brain(
        self,
        query_str: str,
        department: str,
        *,
        top_k: int = 10,
    ) -> RetrievalResult:
        """Search within a department's knowledge collections.

        Args:
            query_str: The search query.
            department: The department identifier.
            top_k: Maximum results.

        Returns:
            A RetrievalResult scoped to the department.
        """
        collections = [f"dept_{department}", f"dept_{department}_knowledge"]
        return await self.search_collections(
            query_str,
            collections,
            top_k=top_k,
            enable_reranking=True,
        )

    async def search_enterprise_brain(
        self,
        query_str: str,
        *,
        top_k: int = 10,
    ) -> RetrievalResult:
        """Enterprise-wide search across all knowledge.

        Args:
            query_str: The search query.
            top_k: Maximum results.

        Returns:
            A RetrievalResult spanning the entire enterprise knowledge base.
        """
        return await self.search_all(query_str, top_k=top_k)

    async def _merge_and_normalize(
        self,
        chunks: list[RetrievedChunk],
        query: str,
        top_k: int,
        score_threshold: float,
        enable_reranking: bool,
    ) -> RetrievalResult:
        if not chunks:
            return RetrievalResult(query=query, chunks=(), total_results=0)

        chunks = self._deduplicate(chunks)
        self._normalize_scores(chunks)

        if enable_reranking:
            chunks = await self._reranker.rerank(chunks, query)

        chunks = [c for c in chunks if c.score >= score_threshold]
        chunks = chunks[:top_k]
        chunks_tuple = tuple(chunks)

        context = self._assemble_context(chunks_tuple)

        return RetrievalResult(
            query=query,
            chunks=chunks_tuple,
            context=context,
            total_results=len(chunks_tuple),
        )

    @staticmethod
    def _deduplicate(chunks: list[RetrievedChunk]) -> list[RetrievedChunk]:
        seen: set[str] = set()
        unique: list[RetrievedChunk] = []
        for c in chunks:
            key = c.chunk_id or c.content[:100]
            if key not in seen:
                seen.add(key)
                unique.append(c)
        return unique

    @staticmethod
    def _normalize_scores(chunks: list[RetrievedChunk]) -> None:
        if not chunks:
            return

        min_score = min(c.score for c in chunks)
        max_score = max(c.score for c in chunks)
        score_range = max_score - min_score

        if score_range < 1e-10:
            for i, c in enumerate(chunks):
                chunks[i] = RetrievedChunk(
                    chunk_id=c.chunk_id,
                    document_id=c.document_id,
                    collection=c.collection,
                    content=c.content,
                    score=1.0 - (i / max(len(chunks) - 1, 1)),
                    metadata=c.metadata,
                    attribution=c.attribution,
                )
        else:
            for i, c in enumerate(chunks):
                normalized = (c.score - min_score) / score_range
                chunks[i] = RetrievedChunk(
                    chunk_id=c.chunk_id,
                    document_id=c.document_id,
                    collection=c.collection,
                    content=c.content,
                    score=normalized,
                    metadata=c.metadata,
                    attribution=c.attribution,
                )

    @staticmethod
    def _assemble_context(chunks: tuple[RetrievedChunk, ...]) -> AssembledContext | None:
        if not chunks:
            return None
        context_parts = [c.content for c in chunks]
        return AssembledContext(
            context="\n\n".join(context_parts),
            chunks=chunks,
            chunk_count=len(chunks),
            token_estimate=sum(len(c.content.split()) for c in chunks),
        )

    def _publish_event(self, event: object) -> None:
        if self._event_publisher is not None:
            try:
                self._event_publisher(event)
            except Exception:
                self._log.warning("federation.event_publish_failed")


__all__ = ["KnowledgeFederation"]
