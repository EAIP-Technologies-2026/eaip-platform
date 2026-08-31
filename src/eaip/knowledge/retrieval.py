"""Retrieval — search and retrieve knowledge from the vector store."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any, cast

from eaip.knowledge.base import EmbeddingProvider, VectorStore
from eaip.knowledge.exceptions import RetrievalError
from eaip.knowledge.models import (
    AssembledContext,
    RetrievalConfig,
    RetrievalQuery,
    RetrievalResult,
    RetrievedChunk,
    SourceAttribution,
)
from eaip.logging.context import get_logger


def _result_to_chunk(data: dict[str, object]) -> RetrievedChunk:
    """Convert a raw search result dict to a RetrievedChunk."""
    payload = cast("dict[str, Any]", data.get("payload", {}) or {})
    doc_id = str(payload.get("document_id", ""))
    content = str(payload.get("content", ""))
    chunk_index = int(payload.get("chunk_index", 0))
    source = str(payload.get("source", ""))
    title = str(payload.get("title", ""))
    collection = str(payload.get("collection", ""))
    chunk_id = str(data.get("id", ""))
    score = float(cast("float", data.get("score", 0.0)))

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
        metadata=dict(payload) if isinstance(payload, dict) else {},
        attribution=attribution,
    )


class RetrievalPipeline:
    """RetrievalPipeline — search and retrieve knowledge from the vector store.

    Supports dense vector search, filtered search, hybrid search,
    and multi-collection (global) search.
    """

    def __init__(
        self,
        config: RetrievalConfig,
        vector_store: VectorStore,
        embedding_provider: EmbeddingProvider,
    ) -> None:
        """Initialize the retrieval pipeline.

        Args:
            config: Retrieval configuration.
            vector_store: The vector store to search.
            embedding_provider: The embedding provider for query encoding.
        """
        self._config = config
        self._vector_store = vector_store
        self._embedding_provider = embedding_provider
        self._log = get_logger("eaip.knowledge.retrieval")

    async def retrieve(
        self,
        query: RetrievalQuery,
        collection: str | None = None,
    ) -> RetrievalResult:
        """Execute a retrieval query.

        Args:
            query: The retrieval query.
            collection: Optional collection override.

        Returns:
            A RetrievalResult with matched chunks and metadata.

        Raises:
            RetrievalError: If retrieval fails.
        """
        coll = collection or self._config.collection
        self._log.info(
            "retrieval.start",
            collection=coll,
            query=query.query[:80],
        )

        try:
            query_vec = query.vector if query.vector else await self._embed(text=query.query)
            query_with_vector = RetrievalQuery(
                query=query.query,
                vector=query_vec,
                top_k=query.top_k or self._config.top_k,
                score_threshold=query.score_threshold or self._config.score_threshold,
                filter_metadata=query.filter_metadata,
                include_embeddings=query.include_embeddings,
                hybrid=query.hybrid,
            )

            results_data = await self._vector_store.search(coll, query_with_vector)

            chunks = tuple(_result_to_chunk(r) for r in results_data)
            hit_count = len(chunks)

            self._log.info(
                "retrieval.complete",
                collection=coll,
                hits=hit_count,
            )

            return RetrievalResult(
                query=query.query,
                chunks=chunks,
                total_results=hit_count,
                collection=coll,
            )

        except RetrievalError:
            raise
        except Exception as exc:
            raise RetrievalError(f"Retrieval failed: {exc}") from exc

    async def search_all(
        self,
        query: RetrievalQuery,
        collections: Sequence[str] | None = None,
    ) -> list[RetrievalResult]:
        """Search across multiple collections.

        Args:
            query: The retrieval query.
            collections: Optional list of collections to search.

        Returns:
            A list of RetrievalResult, one per collection.
        """
        colls: Sequence[str] = collections if collections else [self._config.collection]
        results: list[RetrievalResult] = []

        for coll in colls:
            try:
                result = await self.retrieve(query, collection=coll)
                results.append(result)
            except RetrievalError as exc:
                self._log.warning(
                    "retrieval.search_all.skipped",
                    collection=coll,
                    error=str(exc),
                )

        return results

    async def batch_retrieve(
        self,
        queries: Sequence[RetrievalQuery],
        collection: str | None = None,
    ) -> list[RetrievalResult]:
        """Execute multiple retrieval queries.

        Args:
            queries: A sequence of retrieval queries.
            collection: Optional collection override.

        Returns:
            A list of RetrievalResult, one per query.
        """
        coll = collection or self._config.collection
        results: list[RetrievalResult] = []

        for query in queries:
            try:
                result = await self.retrieve(query, collection=coll)
                results.append(result)
            except RetrievalError as exc:
                self._log.warning(
                    "retrieval.batch_retrieve.skipped",
                    query=query.query[:50],
                    error=str(exc),
                )
                results.append(
                    RetrievalResult(
                        query=query.query,
                        chunks=(),
                        total_results=0,
                        collection=coll,
                    )
                )

        return results

    async def _embed(self, text: str) -> tuple[float, ...]:
        """Embed a query text.

        Args:
            text: The text to embed.

        Returns:
            The embedding vector.
        """
        vectors = await self._embedding_provider.embed([text])
        return vectors[0] if vectors else tuple[float]()


class KnowledgeRetriever:
    """Simplified retriever for use in tests and runtime.

    Wraps a vector store and embedding provider to provide
    search and multi-collection search capabilities.
    """

    def __init__(
        self,
        vector_store: VectorStore,
        embedding_provider: EmbeddingProvider,
    ) -> None:
        """Initialize the retriever.

        Args:
            vector_store: The vector store to search.
            embedding_provider: The embedding provider.
        """
        self._vector_store = vector_store
        self._embedding_provider = embedding_provider

    async def search(
        self,
        collection: str,
        query: RetrievalQuery,
    ) -> RetrievalResult:
        """Search a single collection.

        Args:
            collection: The collection name.
            query: The retrieval query.

        Returns:
            A RetrievalResult with matched chunks.
        """
        pipeline = RetrievalPipeline(
            config=RetrievalConfig(collection=collection),
            vector_store=self._vector_store,
            embedding_provider=self._embedding_provider,
        )
        result = await pipeline.retrieve(query, collection=collection)
        if result.chunks:
            context_parts = [c.content for c in result.chunks]
            assembled = AssembledContext(
                context="\n\n".join(context_parts),
                chunks=result.chunks,
                chunk_count=len(result.chunks),
                token_estimate=sum(len(c.content.split()) for c in result.chunks),
            )
            result = RetrievalResult(
                query=result.query,
                collection=result.collection,
                chunks=result.chunks,
                context=assembled,
                total_results=result.total_results,
                duration_ms=result.duration_ms,
            )
        return result

    async def search_multi(
        self,
        collections: list[str],
        query: RetrievalQuery,
    ) -> dict[str, RetrievalResult]:
        """Search multiple collections.

        Args:
            collections: The collection names.
            query: The retrieval query.

        Returns:
            A dict mapping collection name to RetrievalResult.
        """
        results: dict[str, RetrievalResult] = {}
        for coll in collections:
            result = await self.search(coll, query)
            results[coll] = result
        return results

    async def retrieve(
        self,
        query: RetrievalQuery,
        collection: str | None = None,
    ) -> RetrievalResult:
        """Retrieve results for a query.

        Args:
            query: The retrieval query.
            collection: Optional collection name.

        Returns:
            A RetrievalResult.
        """
        return await self.search(collection or "default", query)


__all__ = [
    "KnowledgeRetriever",
    "RetrievalPipeline",
    "_result_to_chunk",
]
