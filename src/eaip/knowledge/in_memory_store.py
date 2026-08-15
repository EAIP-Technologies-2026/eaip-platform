"""In-memory vector store for development, testing, and standalone runtime."""

from __future__ import annotations

import math
from typing import Any

from eaip.knowledge.models import DocumentChunk, RetrievalQuery
from eaip.logging.context import get_logger


class InMemoryVectorStore:
    """VectorStore implementation backed by in-process memory.

    Stores document chunks with their embeddings and performs
    cosine similarity search.  Suitable for development, testing,
    and standalone runtime without an external vector database.
    """

    def __init__(self) -> None:
        """Initialize an empty in-memory vector store."""
        self._collections: dict[str, int] = {}
        self._points: dict[str, list[DocumentChunk]] = {}
        self._log = get_logger("eaip.knowledge.in_memory_store")

    async def create_collection(self, name: str, dimensions: int, **_kwargs: str) -> None:
        """Create a new collection.

        Args:
            name: The collection name.
            dimensions: The embedding dimension.
            **kwargs: Ignored; accepted for protocol conformance.
        """
        self._collections[name] = dimensions
        if name not in self._points:
            self._points[name] = []

    async def upsert_points(self, collection: str, chunks: list[DocumentChunk]) -> None:
        """Insert or update points in a collection.

        Args:
            collection: The collection name.
            chunks: The document chunks to upsert.
        """
        if not chunks:
            return
        if collection not in self._points:
            self._points[collection] = []
        existing_ids = {c.chunk_id for c in self._points[collection]}
        for chunk in chunks:
            if chunk.chunk_id in existing_ids:
                self._points[collection] = [
                    c for c in self._points[collection] if c.chunk_id != chunk.chunk_id
                ]
            self._points[collection].append(chunk)

    async def delete_points(self, collection: str, point_ids: list[str]) -> None:
        """Delete points from a collection.

        Args:
            collection: The collection name.
            point_ids: The point identifiers to delete.
        """
        if not point_ids:
            return
        if collection in self._points:
            id_set = set(point_ids)
            self._points[collection] = [
                c for c in self._points[collection] if c.chunk_id not in id_set
            ]

    async def search(self, collection: str, query: RetrievalQuery) -> list[dict[str, object]]:
        """Search a collection using cosine similarity.

        Args:
            collection: The collection name.
            query: The retrieval query.

        Returns:
            A list of search results with id, score, and payload.
        """
        chunks = self._points.get(collection, [])
        if not chunks:
            return []

        query_vec = list(query.vector) if query.vector else [0.0] * 384
        scored: list[tuple[float, DocumentChunk]] = []
        for chunk in chunks:
            chunk_vec = list(chunk.embedding) if chunk.embedding else [0.0] * len(query_vec)
            score = _cosine_similarity(query_vec, chunk_vec)
            if score >= query.score_threshold:
                scored.append((score, chunk))
        scored.sort(key=lambda x: x[0], reverse=True)
        top = scored[: query.top_k]

        results: list[dict[str, object]] = []
        for score, chunk in top:
            payload: dict[str, Any] = {
                "document_id": chunk.document_id,
                "collection": chunk.collection,
                "content": chunk.content,
                "content_hash": chunk.content_hash,
                "chunk_index": chunk.chunk_index,
            }
            payload.update(chunk.metadata)
            results.append(
                {
                    "id": chunk.chunk_id,
                    "score": score,
                    "payload": payload,
                    "version": 0,
                }
            )
        return results

    async def delete_collection(self, name: str) -> None:
        """Delete a collection entirely.

        Args:
            name: The collection name.
        """
        self._collections.pop(name, None)
        self._points.pop(name, None)

    async def list_collections(self) -> list[str]:
        """List all collection names.

        Returns:
            A list of collection names.
        """
        return list(self._collections.keys())

    async def collection_info(self, name: str) -> dict[str, object]:
        """Get information about a collection.

        Args:
            name: The collection name.

        Returns:
            A dictionary with collection info.
        """
        return {
            "name": name,
            "status": "green",
            "vectors_count": len(self._points.get(name, [])),
        }


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    """Compute cosine similarity between two vectors."""
    if len(a) != len(b):
        min_len = min(len(a), len(b))
        a, b = a[:min_len], b[:min_len]
    dot = sum(x * y for x, y in zip(a, b, strict=False))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot / (norm_a * norm_b)


__all__ = ["InMemoryVectorStore"]
