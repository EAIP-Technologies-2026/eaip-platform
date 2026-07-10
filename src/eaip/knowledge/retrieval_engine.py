"""RetrievalEngine — hybrid search, reranking, multi-collection, and federated retrieval."""

from __future__ import annotations

import time
from collections.abc import Sequence
from typing import Any

from eaip.knowledge.base import EmbeddingProvider, VectorStore
from eaip.knowledge.events import HybridSearchExecuted, RetrievalExecuted
from eaip.knowledge.exceptions import RetrievalError
from eaip.knowledge.models import (
    AssembledContext,
    RetrievalQuery,
    RetrievalResult,
    RetrievedChunk,
    SourceAttribution,
)
from eaip.knowledge.search_strategies import (
    HybridSearchStrategy,
    KeywordSearchStrategy,
    RerankingStrategy,
    SemanticSearchStrategy,
    SimpleReranker,
)
from eaip.logging.context import get_logger


class RetrievalEngine:
    """Orchestrates hybrid search, reranking, multi-collection, and federated retrieval.

    Combines semantic (vector) search with keyword (BM25-like) search,
    applies configurable reranking, and supports searching across
    multiple collections or sources (knowledge + memory).
    """

    def __init__(
        self,
        vector_store: VectorStore,
        embedding_provider: EmbeddingProvider,
        *,
        default_top_k: int = 10,
        default_score_threshold: float = 0.0,
        default_alpha: float = 0.5,
        reranker: RerankingStrategy | None = None,
        event_publisher: Any | None = None,
    ) -> None:
        self._vector_store = vector_store
        self._embedding_provider = embedding_provider
        self._default_top_k = default_top_k
        self._default_score_threshold = default_score_threshold
        self._default_alpha = default_alpha
        self._reranker = reranker or SimpleReranker()
        self._event_publisher = event_publisher
        self._log = get_logger("eaip.knowledge.retrieval_engine")

        self._semantic_strategy = SemanticSearchStrategy(vector_store, embedding_provider)
        self._keyword_strategy = KeywordSearchStrategy()
        self._hybrid_strategy = HybridSearchStrategy(
            semantic_strategy=self._semantic_strategy,
            keyword_strategy=self._keyword_strategy,
        )

    async def search(
        self,
        query_str: str,
        *,
        collection: str | None = None,
        top_k: int | None = None,
        score_threshold: float | None = None,
        alpha: float | None = None,
        filter_metadata: dict[str, Any] | None = None,
        enable_reranking: bool = True,
    ) -> RetrievalResult:
        """Execute a hybrid search against a single collection.

        Args:
            query_str: The search query.
            collection: Target collection name (defaults to "default").
            top_k: Maximum number of results.
            score_threshold: Minimum score threshold.
            alpha: Weight for semantic vs keyword (0.0 = keyword only, 1.0 = semantic only).
            filter_metadata: Optional metadata filters.
            enable_reranking: Whether to apply reranking.

        Returns:
            A RetrievalResult with matched chunks.
        """
        t0 = time.monotonic()
        coll = collection or "default"
        k = top_k or self._default_top_k
        thr = score_threshold if score_threshold is not None else self._default_score_threshold
        a = alpha if alpha is not None else self._default_alpha

        self._log.info(
            "retrieval_engine.search",
            collection=coll,
            query=query_str[:80],
            top_k=k,
            alpha=a,
        )

        try:
            query = RetrievalQuery(
                query=query_str,
                collection=coll,
                top_k=k,
                score_threshold=thr,
                filter_metadata=filter_metadata or {},
                hybrid=True,
                alpha=a,
            )

            query_vec = await self._embed(query_str)
            query = RetrievalQuery(
                query=query.query,
                vector=query_vec,
                top_k=query.top_k,
                score_threshold=query.score_threshold,
                filter_metadata=query.filter_metadata,
                hybrid=query.hybrid,
                alpha=query.alpha,
            )

            raw_results = await self._vector_store.search(coll, query)

            chunks = [self._dict_to_chunk(r, coll) for r in raw_results]

            if enable_reranking and chunks:
                chunks = await self._reranker.rerank(chunks, query_str)
                chunks = [c for c in chunks if c.score >= thr]
                chunks = chunks[:k]

            chunks_tuple = tuple(chunks)
            hit_count = len(chunks_tuple)

            context = self._assemble_context(chunks_tuple)

            duration = (time.monotonic() - t0) * 1000

            evt = HybridSearchExecuted(
                query=query_str,
                collection=coll,
                result_count=hit_count,
                duration_ms=duration,
                alpha=a,
            )
            self._publish_event(evt)

            self._log.info(
                "retrieval_engine.search.complete",
                collection=coll,
                hits=hit_count,
                duration_ms=duration,
            )

            return RetrievalResult(
                query=query_str,
                collection=coll,
                chunks=chunks_tuple,
                context=context,
                total_results=hit_count,
                duration_ms=duration,
            )

        except RetrievalError:
            raise
        except Exception as exc:
            raise RetrievalError(f"Hybrid search failed: {exc}") from exc

    async def search_semantic(
        self,
        query_str: str,
        *,
        collection: str | None = None,
        top_k: int | None = None,
    ) -> RetrievalResult:
        """Execute a pure semantic (vector) search.

        Args:
            query_str: The search query.
            collection: Target collection name.
            top_k: Maximum number of results.

        Returns:
            A RetrievalResult with matched chunks.
        """
        t0 = time.monotonic()
        coll = collection or "default"
        k = top_k or self._default_top_k

        try:
            raw = await self._semantic_strategy.search(
                query_str,
                coll,
                RetrievalQuery(query=query_str, top_k=k),
            )
            result = self._raw_to_result(raw, query_str, coll, t0)
            self._publish_event(RetrievalExecuted(
                query=query_str,
                collection=coll,
                result_count=result.total_results,
                duration_ms=result.duration_ms,
            ))
            return result
        except Exception as exc:
            raise RetrievalError(f"Semantic search failed: {exc}") from exc

    async def search_keyword(
        self,
        query_str: str,
        *,
        collection: str | None = None,
        top_k: int | None = None,
    ) -> RetrievalResult:
        """Execute a pure keyword search.

        Args:
            query_str: The search query.
            collection: Target collection name.
            top_k: Maximum number of results.

        Returns:
            A RetrievalResult with matched chunks.
        """
        t0 = time.monotonic()
        coll = collection or "default"
        k = top_k or self._default_top_k

        try:
            raw = await self._keyword_strategy.search(
                query_str,
                coll,
                RetrievalQuery(query=query_str, top_k=k),
            )
            return self._raw_to_result(raw, query_str, coll, t0)
        except Exception as exc:
            raise RetrievalError(f"Keyword search failed: {exc}") from exc

    async def search_multi(
        self,
        query_str: str,
        collections: Sequence[str],
        *,
        top_k: int | None = None,
        score_threshold: float | None = None,
        enable_reranking: bool = True,
    ) -> RetrievalResult:
        """Search across multiple collections and aggregate results.

        Args:
            query_str: The search query.
            collections: Collection names to search.
            top_k: Maximum results per collection (final results are merged and trimmed).
            score_threshold: Minimum score threshold.
            enable_reranking: Whether to apply reranking.

        Returns:
            An aggregated RetrievalResult.
        """
        t0 = time.monotonic()
        k = top_k or self._default_top_k
        thr = score_threshold if score_threshold is not None else self._default_score_threshold

        all_chunks: list[RetrievedChunk] = []
        for coll in collections:
            try:
                result = await self.search(
                    query_str,
                    collection=coll,
                    top_k=k,
                    score_threshold=thr,
                    enable_reranking=False,
                )
                all_chunks.extend(result.chunks)
            except Exception as exc:
                self._log.warning(
                    "retrieval_engine.search_multi.skipped",
                    collection=coll,
                    error=str(exc),
                )

        all_chunks = self._deduplicate(all_chunks)

        if enable_reranking and all_chunks:
            all_chunks = await self._reranker.rerank(all_chunks, query_str)
            all_chunks = [c for c in all_chunks if c.score >= thr]

        all_chunks = all_chunks[:k]
        chunks_tuple = tuple(all_chunks)

        duration = (time.monotonic() - t0) * 1000

        return RetrievalResult(
            query=query_str,
            collection=",".join(collections),
            chunks=chunks_tuple,
            context=self._assemble_context(chunks_tuple),
            total_results=len(chunks_tuple),
            duration_ms=duration,
        )

    async def _embed(self, text: str) -> tuple[float, ...]:
        vectors = await self._embedding_provider.embed([text])
        return vectors[0] if vectors else tuple[float]()

    def _dict_to_chunk(self, data: dict[str, object], collection: str) -> RetrievedChunk:
        data_payload: Any = data.get("payload", {}) or {}
        payload: dict[str, Any] = dict(data_payload)
        doc_id = str(payload.get("document_id", "") or "")
        content = str(payload.get("content", "") or "")
        chunk_index = int(payload.get("chunk_index", 0) or 0)
        source = str(payload.get("source", "") or "")
        title = str(payload.get("title", "") or "")
        chunk_id = str(data.get("id", "") or "")
        score_val: Any = data.get("score", 0.0)
        score = float(score_val) if score_val else 0.0

        attribution = SourceAttribution(
            document_id=doc_id,
            document_title=title,
            collection=collection,
            chunk_index=chunk_index,
            source=source,
            score=score,
        )
        return RetrievedChunk(
            chunk_id=chunk_id,
            document_id=doc_id,
            collection=collection,
            content=content,
            score=score,
            metadata=payload,
            attribution=attribution,
        )

    def _assemble_context(self, chunks: tuple[RetrievedChunk, ...]) -> AssembledContext | None:
        if not chunks:
            return None
        context_parts = [c.content for c in chunks]
        return AssembledContext(
            context="\n\n".join(context_parts),
            chunks=chunks,
            chunk_count=len(chunks),
            token_estimate=sum(len(c.content.split()) for c in chunks),
        )

    def _deduplicate(self, chunks: list[RetrievedChunk]) -> list[RetrievedChunk]:
        seen: set[str] = set()
        unique: list[RetrievedChunk] = []
        for c in chunks:
            key = c.chunk_id or c.content[:100]
            if key not in seen:
                seen.add(key)
                unique.append(c)
        return unique

    def _raw_to_result(
        self,
        raw: RetrievalResult,
        query_str: str,
        collection: str,
        t0: float,
    ) -> RetrievalResult:
        duration = (time.monotonic() - t0) * 1000
        return RetrievalResult(
            query=query_str,
            collection=collection,
            chunks=raw.chunks,
            context=self._assemble_context(raw.chunks),
            total_results=len(raw.chunks),
            duration_ms=duration,
        )

    def _publish_event(self, event: object) -> None:
        if self._event_publisher is not None:
            try:
                self._event_publisher(event)
            except Exception:
                self._log.warning("retrieval_engine.event_publish_failed")


__all__ = ["RetrievalEngine"]
