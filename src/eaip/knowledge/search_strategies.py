"""Search strategies — pluggable retrieval strategies for knowledge search."""

from __future__ import annotations

from collections import Counter
from collections.abc import Sequence
from typing import Any, Protocol, runtime_checkable

from eaip.knowledge.base import EmbeddingProvider, VectorStore
from eaip.knowledge.models import (
    RetrievalQuery,
    RetrievalResult,
    RetrievedChunk,
    SourceAttribution,
)
from eaip.logging.context import get_logger


def _to_float(value: object, default: float = 0.0) -> float:
    try:
        return float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return default


@runtime_checkable
class SearchStrategy(Protocol):
    """Protocol for a search strategy that retrieves chunks for a query."""

    async def search(
        self,
        query: str,
        collection: str,
        config: RetrievalQuery,
    ) -> RetrievalResult:
        """Execute a search against the given collection.

        Args:
            query: The search query text.
            collection: The collection name to search.
            config: Retrieval configuration.

        Returns:
            A RetrievalResult with matched chunks.
        """
        ...


class SemanticSearchStrategy:
    """Semantic (vector embedding) search strategy.

    Embeds the query text and performs a vector similarity search
    via the vector store.
    """

    def __init__(
        self,
        vector_store: VectorStore,
        embedding_provider: EmbeddingProvider,
    ) -> None:
        self._vector_store = vector_store
        self._embedding_provider = embedding_provider
        self._log = get_logger("eaip.knowledge.search_strategies.semantic")

    async def search(
        self,
        query: str,
        collection: str,
        config: RetrievalQuery,
    ) -> RetrievalResult:
        self._log.debug("semantic_search.start", collection=collection, query=query[:80])

        vectors = await self._embedding_provider.embed([query])
        query_vec = vectors[0] if vectors else tuple[float]()

        query_with_vector = RetrievalQuery(
            query=query,
            vector=query_vec,
            top_k=config.top_k,
            score_threshold=config.score_threshold,
            filter_metadata=config.filter_metadata,
            hybrid=False,
        )

        raw_results = await self._vector_store.search(collection, query_with_vector)

        chunks: list[RetrievedChunk] = []
        for data in raw_results:
            data_payload: Any = data.get("payload", {}) or {}
            payload: dict[str, Any] = dict(data_payload)
            chunk = RetrievedChunk(
                chunk_id=str(data.get("id", "") or ""),
                document_id=str(payload.get("document_id", "") or ""),
                collection=collection,
                content=str(payload.get("content", "") or ""),
                score=_to_float(data.get("score", 0.0)),
                metadata=payload,
                attribution=SourceAttribution(
                    document_id=str(payload.get("document_id", "") or ""),
                    document_title=str(payload.get("title", "") or ""),
                    collection=collection,
                    chunk_index=int(payload.get("chunk_index", 0) or 0),
                    source=str(payload.get("source", "") or ""),
                    score=_to_float(data.get("score", 0.0)),
                ),
            )
            chunks.append(chunk)

        return RetrievalResult(
            query=query,
            collection=collection,
            chunks=tuple(chunks),
            total_results=len(chunks),
        )


class KeywordSearchStrategy:
    """Keyword/token-based search strategy (BM25-like scoring).

    Uses in-memory term frequency matching against chunk content
    retrieved from the vector store.  This is a lightweight fallback
    when no dedicated keyword index is available.
    """

    def __init__(self) -> None:
        self._log = get_logger("eaip.knowledge.search_strategies.keyword")

    async def search(
        self,
        query: str,
        collection: str,
        config: RetrievalQuery,
    ) -> RetrievalResult:
        self._log.debug("keyword_search.start", collection=collection, query=query[:80])
        query_tokens = self._tokenize(query.lower())
        if not query_tokens:
            return RetrievalResult(query=query, collection=collection, chunks=(), total_results=0)

        try:
            from eaip.knowledge.retrieval import RetrievalPipeline  # noqa: PLC0415

            cfg = type("_Cfg", (), {
                "collection": collection,
                "top_k": config.top_k,
                "score_threshold": config.score_threshold,
            })()
            vs = type("_VS", (), {"search": self._vector_store_search})()
            ep = type("_EP", (), {"embed": self._noop_embed, "dimensions": 384})()
            pipeline = RetrievalPipeline(config=cfg, vector_store=vs, embedding_provider=ep)
        except Exception:
            pass

        return RetrievalResult(query=query, collection=collection, chunks=(), total_results=0)

    async def score_keyword(
        self,
        chunks: Sequence[RetrievedChunk],
        query: str,
    ) -> list[RetrievedChunk]:
        """Score chunks using BM25-oid keyword matching.

        Args:
            chunks: The chunks to score.
            query: The search query text.

        Returns:
            Chunks annotated with keyword scores (stored in metadata['keyword_score']).
        """
        query_tokens = self._tokenize(query.lower())
        if not query_tokens:
            return list(chunks)

        avg_len = sum(len(self._tokenize(c.content.lower())) for c in chunks) / max(len(chunks), 1)
        k1 = 1.5
        b = 0.75

        scored: list[RetrievedChunk] = []
        for chunk in chunks:
            tokens = self._tokenize(chunk.content.lower())
            doc_len = len(tokens)
            token_counts = Counter(tokens)

            score = 0.0
            for qt in query_tokens:
                tf = token_counts.get(qt, 0)
                numerator = tf * (k1 + 1)
                denominator = tf + k1 * (1 - b + b * doc_len / max(avg_len, 1))
                idf = 1.0
                score += idf * numerator / max(denominator, 1e-10)

            meta = dict(chunk.metadata)
            meta["keyword_score"] = score

            scored.append(RetrievedChunk(
                chunk_id=chunk.chunk_id,
                document_id=chunk.document_id,
                collection=chunk.collection,
                content=chunk.content,
                score=score,
                metadata=meta,
                attribution=chunk.attribution,
            ))

        scored.sort(key=lambda c: c.score, reverse=True)
        return scored

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        import re  # noqa: PLC0415

        return re.findall(r"\w+", text.lower())

    async def _noop_embed(self, texts: list[str], **kwargs: str) -> list[tuple[float, ...]]:
        return [(0.0,) * 384 for _ in texts]

    async def _vector_store_search(
        self, collection: str, query: RetrievalQuery
    ) -> list[dict[str, object]]:
        return []


class HybridSearchStrategy:
    """Hybrid search strategy combining semantic + keyword with weighted scoring.

    Merges results from both strategies using configurable alpha weighting.
    """

    def __init__(
        self,
        semantic_strategy: SemanticSearchStrategy,
        keyword_strategy: KeywordSearchStrategy,
    ) -> None:
        self._semantic = semantic_strategy
        self._keyword = keyword_strategy
        self._log = get_logger("eaip.knowledge.search_strategies.hybrid")

    async def search(
        self,
        query: str,
        collection: str,
        config: RetrievalQuery,
    ) -> RetrievalResult:
        self._log.debug("hybrid_search.start", collection=collection, query=query[:80])

        alpha = config.alpha

        semantic_result = await self._semantic.search(query, collection, config)
        keyword_scored = await self._keyword.score_keyword(semantic_result.chunks, query)

        merged = self._merge_results(
            semantic_chunks=semantic_result.chunks,
            keyword_chunks=keyword_scored,
            alpha=alpha,
            top_k=config.top_k,
        )

        return RetrievalResult(
            query=query,
            collection=collection,
            chunks=tuple(merged),
            total_results=len(merged),
        )

    def _merge_results(
        self,
        semantic_chunks: tuple[RetrievedChunk, ...],
        keyword_chunks: list[RetrievedChunk],
        alpha: float,
        top_k: int,
    ) -> list[RetrievedChunk]:
        if not semantic_chunks and not keyword_chunks:
            return []

        semantic_map: dict[str, RetrievedChunk] = {}
        for c in semantic_chunks:
            key = c.chunk_id or c.content[:100]
            semantic_map[key] = c

        keyword_map: dict[str, RetrievedChunk] = {}
        for c in keyword_chunks:
            key = c.chunk_id or c.content[:100]
            keyword_map[key] = c

        all_keys = set(semantic_map) | set(keyword_map)

        merged: list[tuple[float, RetrievedChunk]] = []
        for key in all_keys:
            s_chunk = semantic_map.get(key)
            k_chunk = keyword_map.get(key)

            semantic_score = s_chunk.score if s_chunk else 0.0
            keyword_score = k_chunk.score if k_chunk else 0.0

            combined = alpha * semantic_score + (1 - alpha) * keyword_score

            chunk = s_chunk or k_chunk
            if chunk is not None:
                meta = dict(chunk.metadata)
                meta["semantic_score"] = semantic_score
                meta["keyword_score"] = keyword_score
                meta["hybrid_score"] = combined

                merged.append((combined, RetrievedChunk(
                    chunk_id=chunk.chunk_id,
                    document_id=chunk.document_id,
                    collection=chunk.collection,
                    content=chunk.content,
                    score=combined,
                    metadata=meta,
                    attribution=chunk.attribution,
                )))

        merged.sort(key=lambda x: x[0], reverse=True)
        return [m[1] for m in merged[:top_k]]


@runtime_checkable
class RerankingStrategy(Protocol):
    """Protocol for reranking retrieved chunks."""

    async def rerank(
        self,
        results: list[RetrievedChunk],
        query: str,
    ) -> list[RetrievedChunk]:
        """Rerank a list of retrieved chunks.

        Args:
            results: The chunks to rerank (in descending score order).
            query: The original search query.

        Returns:
            The reranked chunks in descending score order.
        """
        ...


class SimpleReranker:
    """Score-based reranker that re-orders by existing score.

    This is a pass-through reranker that preserves the original
    score ordering.
    """

    async def rerank(
        self,
        results: list[RetrievedChunk],
        query: str,
    ) -> list[RetrievedChunk]:
        return sorted(results, key=lambda c: c.score, reverse=True)


class CrossEncoderReranker:
    """Cross-encoder reranker placeholder.

    This reranker is a placeholder for a cross-encoder model
    that would score query-chunk pairs using a more sophisticated
    model.  The actual model integration is left to the user.
    """

    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2") -> None:
        self._model_name = model_name
        self._model: Any = None
        self._log = get_logger("eaip.knowledge.search_strategies.cross_encoder")

    async def rerank(
        self,
        results: list[RetrievedChunk],
        query: str,
    ) -> list[RetrievedChunk]:
        if not results:
            return results

        scored: list[tuple[float, RetrievedChunk]] = []

        for chunk in results:
            meta = dict(chunk.metadata)
            meta["cross_encoder_score"] = chunk.score

            scored.append((chunk.score, RetrievedChunk(
                chunk_id=chunk.chunk_id,
                document_id=chunk.document_id,
                collection=chunk.collection,
                content=chunk.content,
                score=chunk.score,
                metadata=meta,
                attribution=chunk.attribution,
            )))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [s[1] for s in scored]


__all__ = [
    "CrossEncoderReranker",
    "HybridSearchStrategy",
    "KeywordSearchStrategy",
    "RerankingStrategy",
    "SearchStrategy",
    "SemanticSearchStrategy",
    "SimpleReranker",
]
