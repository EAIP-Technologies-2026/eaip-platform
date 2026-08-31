"""Knowledge Engine protocols — abstract interfaces for providers, parsers, chunkers, stores."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from eaip.knowledge.models import (
    DocumentChunk,
    IngestionResult,
    RetrievalQuery,
)


@runtime_checkable
class DocumentParser(Protocol):
    """Protocol for parsing documents into raw text."""

    async def parse(self, content: bytes, **kwargs: str) -> str:
        """Parse document content into plain text.

        Args:
            content: Raw document bytes.
            **kwargs: Optional metadata hints.

        Returns:
            Extracted plain text.
        """
        ...


@runtime_checkable
class Chunker(Protocol):
    """Protocol for splitting text into chunks."""

    async def chunk(
        self, text: str, document_id: str, collection: str, **kwargs: str
    ) -> list[DocumentChunk]:
        """Split text into chunks.

        Args:
            text: The text to chunk.
            document_id: The source document identifier.
            collection: The knowledge collection name.
            **kwargs: Optional chunking parameters.

        Returns:
            A list of document chunks.
        """
        ...


@runtime_checkable
class EmbeddingProvider(Protocol):
    """Protocol for generating embeddings through the Provider Framework."""

    async def embed(self, texts: list[str], **kwargs: str) -> list[tuple[float, ...]]:
        """Generate embeddings for the given texts.

        Args:
            texts: The texts to embed.
            **kwargs: Optional embedding parameters.

        Returns:
            A list of embedding vectors.
        """
        ...

    @property
    def dimensions(self) -> int:
        """Return the embedding dimension."""
        ...


@runtime_checkable
class VectorStore(Protocol):
    """Protocol for storing and retrieving vector embeddings."""

    async def create_collection(self, name: str, dimensions: int, **kwargs: str) -> None:
        """Create a new collection.

        Args:
            name: The collection name.
            dimensions: The embedding dimension.
            **kwargs: Optional collection parameters.
        """
        ...

    async def upsert_points(self, collection: str, chunks: list[DocumentChunk]) -> None:
        """Insert or update points in a collection.

        Args:
            collection: The collection name.
            chunks: The document chunks to upsert.
        """
        ...

    async def delete_points(self, collection: str, point_ids: list[str]) -> None:
        """Delete points from a collection.

        Args:
            collection: The collection name.
            point_ids: The point identifiers to delete.
        """
        ...

    async def search(self, collection: str, query: RetrievalQuery) -> list[dict[str, object]]:
        """Search a collection.

        Args:
            collection: The collection name.
            query: The retrieval query.

        Returns:
            A list of search results.
        """
        ...

    async def delete_collection(self, name: str) -> None:
        """Delete a collection entirely.

        Args:
            name: The collection name.
        """
        ...

    async def list_collections(self) -> list[str]:
        """List all collection names.

        Returns:
            A list of collection names.
        """
        ...

    async def collection_info(self, name: str) -> dict[str, object]:
        """Get information about a collection.

        Args:
            name: The collection name.

        Returns:
            A dictionary with collection info.
        """
        ...


@runtime_checkable
class KnowledgeProvider(Protocol):
    """Combined protocol for a full knowledge storage backend.

    A KnowledgeProvider must satisfy both the VectorStore and
    EmbeddingProvider protocols.
    """

    name: str

    async def create_collection(self, name: str, dimensions: int, **kwargs: str) -> None:
        """Create a new collection."""

    async def upsert_points(self, collection: str, chunks: list[DocumentChunk]) -> None:
        """Upsert points into a collection."""

    async def delete_points(self, collection: str, point_ids: list[str]) -> None:
        """Delete points from a collection."""

    async def search(self, collection: str, query: RetrievalQuery) -> list[dict[str, object]]:
        """Search a collection."""

    async def delete_collection(self, name: str) -> None:
        """Delete a collection."""

    async def list_collections(self) -> list[str]:
        """List all collections."""

    async def collection_info(self, name: str) -> dict[str, object]:
        """Get collection info."""

    async def embed(self, texts: list[str], **kwargs: str) -> list[tuple[float, ...]]:
        """Embed a list of texts."""

    @property
    def dimensions(self) -> int:
        """Return the embedding dimension."""
        ...


@runtime_checkable
class KnowledgeEventHandler(Protocol):
    """Protocol for handling knowledge events."""

    async def on_document_ingested(self, result: IngestionResult) -> None:
        """Handle a document ingested event.

        Args:
            result: The ingestion result.
        """
        ...

    async def on_document_deleted(self, document_id: str, collection: str) -> None:
        """Handle a document deleted event.

        Args:
            document_id: The document identifier.
            collection: The collection name.
        """
        ...


__all__ = [
    "Chunker",
    "DocumentParser",
    "EmbeddingProvider",
    "KnowledgeEventHandler",
    "KnowledgeProvider",
    "VectorStore",
]
