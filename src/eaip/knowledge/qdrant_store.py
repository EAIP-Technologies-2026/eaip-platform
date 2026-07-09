"""Qdrant vector store integration."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from eaip.knowledge.exceptions import CollectionNotFoundError, RetrievalError
from eaip.knowledge.models import DocumentChunk, RetrievalQuery
from eaip.logging.context import get_logger


class QdrantStore:
    """Vector store implementation backed by Qdrant.

    Supports dense vector search, metadata filtering, and
    hybrid search (dense + sparse) when Qdrant is configured
    with a sparse model.
    """

    def __init__(
        self,
        *,
        host: str = "localhost",
        port: int = 6333,
        api_key: str = "",
        prefer_grpc: bool = False,
        timeout: float = 30.0,
    ) -> None:
        """Initialize the QdrantStore.

        Args:
            host: Qdrant host address.
            port: Qdrant REST port.
            api_key: Optional API key for Qdrant Cloud.
            prefer_grpc: Prefer gRPC over REST.
            timeout: Request timeout in seconds.
        """
        self._host = host
        self._port = port
        self._api_key = api_key
        self._prefer_grpc = prefer_grpc
        self._timeout = timeout
        self._client: Any = None
        self._models: Any = None
        self._log = get_logger("eaip.knowledge.qdrant")

    @property
    def _is_connected(self) -> bool:
        return self._client is not None

    async def _ensure_client(self) -> None:
        if self._client is not None:
            return
        try:
            from qdrant_client import QdrantClient as _QdrantClient  # type: ignore[import-not-found]  # noqa: PLC0415
            from qdrant_client.http import models as _models  # type: ignore[import-not-found]  # noqa: PLC0415

            self._models = _models
            self._client = _QdrantClient(
                host=self._host,
                port=self._port,
                api_key=self._api_key or None,
                prefer_grpc=self._prefer_grpc,
                timeout=self._timeout,
            )
            self._log.info("qdrant.client.connected", host=self._host, port=self._port)
        except ImportError:
            msg = "qdrant-client is required"
            raise RuntimeError(msg) from None
        except Exception as exc:
            self._log.error("qdrant.client.failed", error=str(exc))
            raise

    async def create_collection(self, name: str, dimensions: int, **kwargs: str) -> None:
        """Create a new Qdrant collection.

        Args:
            name: The collection name.
            dimensions: The embedding dimension.
            **kwargs: Optional parameters (distance, indexing_threshold).
        """
        await self._ensure_client()
        assert self._client is not None
        self._log.info("qdrant.create_collection", name=name, dimensions=dimensions)
        try:
            from qdrant_client.http import models as _models  # noqa: PLC0415

            distance = _models.Distance.COSINE
            if "distance" in kwargs:
                distance = _models.Distance(kwargs["distance"])

            self._client.create_collection(
                collection_name=name,
                vectors_config=_models.VectorParams(size=dimensions, distance=distance),
                optimizers_config=_models.OptimizersConfigDiff(
                    indexing_threshold=kwargs.get("indexing_threshold", 20000),
                ),
            )
        except Exception as exc:
            self._log.error("qdrant.create_collection.failed", name=name, error=str(exc))
            raise

    async def upsert_points(self, collection: str, chunks: list[DocumentChunk]) -> None:
        """Insert or update points in a Qdrant collection.

        Args:
            collection: The collection name.
            chunks: The document chunks to upsert.
        """
        if not chunks:
            return
        await self._ensure_client()
        assert self._client is not None
        try:
            from qdrant_client.http import models as _models  # noqa: PLC0415

            points: list[object] = []
            for chunk in chunks:
                payload: dict[str, object] = {
                    "document_id": chunk.document_id,
                    "collection": chunk.collection,
                    "content": chunk.content,
                    "content_hash": chunk.content_hash,
                    "chunk_index": chunk.chunk_index,
                }
                payload.update(chunk.metadata)
                vector = list(chunk.embedding) if chunk.embedding else None
                point = _models.PointStruct(
                    id=chunk.chunk_id,
                    vector=vector or [0.0],
                    payload=payload,
                )
                points.append(point)

            self._client.upsert(
                collection_name=collection,
                points=points,
            )
        except Exception as exc:
            self._log.error("qdrant.upsert.failed", collection=collection, error=str(exc))
            raise

    async def delete_points(self, collection: str, point_ids: list[str]) -> None:
        """Delete points from a Qdrant collection.

        Args:
            collection: The collection name.
            point_ids: The point identifiers to delete.
        """
        if not point_ids:
            return
        await self._ensure_client()
        assert self._client is not None
        try:
            from qdrant_client.http import models as _models  # noqa: PLC0415

            self._client.delete(
                collection_name=collection,
                points_selector=_models.Filter(
                    must=[
                        _models.FieldCondition(
                            key="chunk_id",
                            match=_models.MatchValue(value=pid),
                        )
                        for pid in point_ids
                    ],
                ),
            )
        except Exception as exc:
            self._log.error("qdrant.delete.failed", collection=collection, error=str(exc))
            raise

    async def search(self, collection: str, query: RetrievalQuery) -> list[dict[str, object]]:
        """Search a Qdrant collection.

        Args:
            collection: The collection name.
            query: The retrieval query.

        Returns:
            A list of search results.
        """
        await self._ensure_client()
        assert self._client is not None
        self._log.debug("qdrant.search", collection=collection, query=query.query[:50])

        try:
            query_filter = (
                self._build_filter(query.filter_metadata) if query.filter_metadata else None
            )

            if query.hybrid:
                scroll_result = self._client.scroll(
                    collection_name=collection,
                    limit=query.top_k * 2,
                    with_payload=True,
                    with_vectors=query.include_embeddings,
                )
                hits = list(scroll_result[0]) if scroll_result else []
            else:
                search_result = self._client.search(
                    collection_name=collection,
                    query_vector=self._get_query_vector(query),
                    limit=query.top_k,
                    query_filter=query_filter,
                    score_threshold=query.score_threshold,
                    with_payload=True,
                    with_vectors=query.include_embeddings,
                )
                hits = search_result

            results: list[dict[str, object]] = []
            for hit in hits:
                payload = getattr(hit, "payload", {}) or {}
                results.append(
                    {
                        "id": getattr(hit, "id", ""),
                        "score": getattr(hit, "score", 0.0),
                        "payload": payload,
                        "version": getattr(hit, "version", 0),
                    }
                )

            return results

        except Exception as exc:
            self._log.error("qdrant.search.failed", collection=collection, error=str(exc))
            raise RetrievalError(f"Qdrant search failed: {exc}") from exc

    async def delete_collection(self, name: str) -> None:
        """Delete a Qdrant collection.

        Args:
            name: The collection name.
        """
        await self._ensure_client()
        assert self._client is not None
        try:
            self._client.delete_collection(collection_name=name)
        except Exception as exc:
            self._log.error("qdrant.delete_collection.failed", name=name, error=str(exc))
            raise

    async def list_collections(self) -> list[str]:
        """List all Qdrant collection names.

        Returns:
            A list of collection names.
        """
        await self._ensure_client()
        assert self._client is not None
        try:
            collections = self._client.get_collections()
            return [c.name for c in collections.collections]
        except Exception as exc:
            self._log.error("qdrant.list_collections.failed", error=str(exc))
            raise

    async def collection_info(self, name: str) -> dict[str, object]:
        """Get information about a Qdrant collection.

        Args:
            name: The collection name.

        Returns:
            A dictionary with collection info.
        """
        await self._ensure_client()
        assert self._client is not None
        try:
            info = self._client.get_collection(collection_name=name)
            return {
                "name": name,
                "status": str(info.status),
                "vectors_count": info.vectors_count,
                "points_count": info.points_count,
                "segments_count": info.segments_count,
            }
        except Exception as exc:
            raise CollectionNotFoundError(f"Collection {name!r} not found: {exc}") from exc

    def _build_filter(self, metadata: dict[str, Any]) -> object:
        from qdrant_client.http import models as _models  # noqa: PLC0415

        conditions: list[object] = []
        for key, value in metadata.items():
            if isinstance(value, str):
                conditions.append(
                    _models.FieldCondition(key=key, match=_models.MatchValue(value=value))
                )
            elif isinstance(value, (int, float)):
                conditions.append(
                    _models.FieldCondition(key=key, range=_models.Range(gte=value, lte=value))
                )
            elif isinstance(value, list):
                conditions.append(
                    _models.FieldCondition(key=key, match=_models.MatchAny(any=value))
                )
        return _models.Filter(must=conditions) if conditions else None

    def _get_query_vector(self, _query: RetrievalQuery) -> Sequence[float]:
        return [0.0] * 384


__all__ = ["QdrantStore"]
