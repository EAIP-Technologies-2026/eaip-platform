"""KnowledgeEngine — high-level API for knowledge management."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Any, cast

from eaip.knowledge.base import (
    Chunker,
    EmbeddingProvider,
    VectorStore,
)
from eaip.knowledge.events import (
    DocumentDeleted,
    KnowledgeEngineEvent,
)
from eaip.knowledge.exceptions import (
    CollectionNotFoundError,
    DocumentNotFoundError,
    KnowledgeEngineError,
    KnowledgeError,
)
from eaip.knowledge.ingestion import IngestionPipeline
from eaip.knowledge.models import (
    ChunkingConfig,
    DocumentFormat,
    EmbeddingConfig,
    IngestionConfig,
    IngestionResult,
    KnowledgeCollection,
    KnowledgeDocument,
    RetrievalConfig,
    RetrievalQuery,
    RetrievalResult,
)
from eaip.knowledge.registry import KnowledgeRegistry
from eaip.knowledge.retrieval import KnowledgeRetriever
from eaip.logging.context import get_logger


class KnowledgeEngine:
    """High-level API for knowledge management.

    Wraps ingestion, retrieval, and collection lifecycle into a
    single entry point. Designed to be used by capabilities and
    other knowledge consumers.
    """

    def __init__(
        self,
        registry_or_store: KnowledgeRegistry | VectorStore,
        vector_store_or_embedding: VectorStore | EmbeddingProvider,
        embedding_or_chunker: EmbeddingProvider | Chunker | None = None,
        *,
        default_collection: str = "default",
        chunker: Chunker | None = None,
        event_handlers: dict[type[KnowledgeEngineEvent], list[Any]] | None = None,
        authorize_fn: Callable[[str, str], None] | None = None,
        event_publisher: Callable[[object], None] | None = None,
        **kwargs: object,
    ) -> None:
        """Initialize the KnowledgeEngine.

        Supports two construction patterns:
        1. Engine(registry, vector_store, embedding_provider)  -- test/legacy
        2. Engine(vector_store, embedding_provider, chunker)   -- current
        """
        self._authorize_fn = authorize_fn
        self._event_publisher = event_publisher
        self._event_handlers: dict[type[KnowledgeEngineEvent], list[Any]] = event_handlers or {}
        self._default_collection = default_collection
        self._log = get_logger("eaip.knowledge.engine")

        if embedding_or_chunker is None and not isinstance(registry_or_store, KnowledgeRegistry):
            self._registry = KnowledgeRegistry()
            self._vector_store = registry_or_store
            self._embedding_provider = cast("EmbeddingProvider", vector_store_or_embedding)
            self._chunker = chunker or self._default_chunker()
        elif isinstance(registry_or_store, KnowledgeRegistry):
            self._registry = registry_or_store
            self._vector_store = cast("VectorStore", vector_store_or_embedding)
            self._embedding_provider = cast("EmbeddingProvider", embedding_or_chunker)
            self._chunker = chunker or self._default_chunker()
        else:
            self._registry = KnowledgeRegistry()
            self._vector_store = registry_or_store
            self._embedding_provider = cast("EmbeddingProvider", vector_store_or_embedding)
            self._chunker = (
                cast("Chunker", embedding_or_chunker)
                if embedding_or_chunker
                else self._default_chunker()
            )

        default_chunking: ChunkingConfig | None = kwargs.get("default_chunking")  # type: ignore[assignment]
        default_embedding: EmbeddingConfig | None = kwargs.get("default_embedding")  # type: ignore[assignment]

        _chunking_cfg = cast("ChunkingConfig | None", getattr(self._chunker, "config", None))
        self._ingestion_config = IngestionConfig(
            collection=default_collection,
            chunking=default_chunking or _chunking_cfg or ChunkingConfig(),
            embedding=default_embedding
            or EmbeddingConfig(
                provider="default",
                model="default",
                dimensions=384,
            ),
        )

        self._retrieval_config = RetrievalConfig(
            collection=default_collection,
            top_k=10,
            score_threshold=0.0,
        )

        pub = event_publisher or self._publish_event
        self._ingestion_pipeline = IngestionPipeline(
            config=self._ingestion_config,
            vector_store=self._vector_store,
            embedding_provider=self._embedding_provider,
            event_publisher=pub,
        )

        self._retriever = KnowledgeRetriever(
            vector_store=self._vector_store,
            embedding_provider=self._embedding_provider,
        )

    @staticmethod
    def _default_chunker() -> Chunker:
        from eaip.knowledge.chunker import FixedSizeChunker  # noqa: PLC0415

        return FixedSizeChunker(ChunkingConfig())

    async def ingest(
        self,
        document_id: str,
        content: bytes,
        doc_format: DocumentFormat | str,
        *,
        title: str = "",
        source: str = "",
        metadata: dict[str, Any] | None = None,
        collection: str | None = None,
    ) -> IngestionResult:
        """Ingest a knowledge document."""
        coll = collection or self._default_collection
        await self._ensure_collection_exists(coll)

        if self._authorize_fn:
            self._authorize_fn("ingest", coll)

        _cfg = IngestionConfig(
            collection=coll,
            chunking=self._ingestion_config.chunking,
            embedding=self._ingestion_config.embedding,
        )
        _pipeline = IngestionPipeline(
            config=_cfg,
            vector_store=self._vector_store,
            embedding_provider=self._embedding_provider,
            event_publisher=self._event_publisher or self._publish_event,
        )
        result = await _pipeline.ingest(
            document_id=document_id,
            content=content,
            doc_format=doc_format,
            title=title,
            source=source,
            metadata=metadata,
        )

        doc = KnowledgeDocument(
            document_id=result.document.document_id,
            collection=result.document.collection,
            format=result.document.format,
            title=result.document.title,
            source=result.document.source,
            metadata=result.document.metadata,
            indexing_status=result.document.indexing_status,
            content_hash=result.document.content_hash,
            chunk_count=result.document.chunk_count,
        )
        self._registry.register_document(doc)
        return result

    async def search(
        self,
        query_str: str,
        *,
        top_k: int = 10,
        score_threshold: float = 0.0,
        filter_metadata: dict[str, Any] | None = None,
        collection: str | None = None,
    ) -> RetrievalResult:
        """Search knowledge documents."""
        if self._authorize_fn:
            self._authorize_fn("search", collection or self._default_collection)
        query = RetrievalQuery(
            query=query_str,
            top_k=top_k,
            score_threshold=score_threshold,
            filter_metadata=filter_metadata or {},
        )
        return await self._retriever.search(collection or self._default_collection, query)

    async def search_all(
        self,
        query_str: str,
        *,
        collections: Sequence[str] | None = None,
        top_k: int = 10,
    ) -> list[RetrievalResult]:
        """Search across multiple collections."""
        query = RetrievalQuery(query=query_str, top_k=top_k)
        colls = collections if collections is not None else [self._default_collection]
        results: list[RetrievalResult] = []
        for coll in colls:
            result = await self._retriever.search(coll, query)
            results.append(result)
        return results

    async def query(
        self,
        query_str: str,
        *,
        collection: str = "default",
        **_kwargs: object,
    ) -> RetrievalResult:
        """Query a collection by name.

        Args:
            query_str: The query text.
            collection: The collection name.

        Returns:
            A RetrievalResult.

        Raises:
            CollectionNotFoundError: If the collection does not exist.
        """
        if not self._registry.has_collection(collection):
            raise CollectionNotFoundError(f"Collection {collection!r} not found")
        if self._authorize_fn:
            self._authorize_fn("query", collection)
        return await self._retriever.search(collection, RetrievalQuery(query=query_str))

    async def search_multi(
        self,
        query_str: str,
        collections: list[str],
    ) -> dict[str, RetrievalResult]:
        """Search across multiple collections.

        Args:
            query_str: The query text.
            collections: The collection names.

        Returns:
            A dict mapping collection name to RetrievalResult.
        """
        results: dict[str, RetrievalResult] = {}
        for coll in collections:
            result = await self._retriever.search(coll, RetrievalQuery(query=query_str))
            results[coll] = result
        return results

    async def delete_document(
        self,
        document_id: str,
        collection: str | None = None,
    ) -> bool:
        """Delete a document from the knowledge store.

        Args:
            document_id: The document identifier to delete.
            collection: The collection name.

        Returns:
            True if the document was deleted, False otherwise.

        Raises:
            DocumentNotFoundError: If the document does not exist.
        """
        coll = collection or self._default_collection
        self._log.info(
            "engine.delete_document",
            document_id=document_id,
            collection=coll,
        )
        if not self._registry.has_document(document_id, coll):
            return False

        try:
            if hasattr(self._vector_store, "delete_points"):
                await self._vector_store.delete_points(coll, [document_id])
            self._registry.unregister_document(document_id, coll)
            self._publish_event(
                DocumentDeleted(
                    document_id=document_id,
                    collection=coll,
                )
            )
            return True
        except DocumentNotFoundError:
            raise
        except Exception as exc:
            raise KnowledgeEngineError(f"Failed to delete document {document_id}: {exc}") from exc

    async def create_collection(
        self, name: str, dimensions: int = 384, **kwargs: object
    ) -> KnowledgeCollection:
        """Create a new collection.

        Args:
            name: The collection name.
            dimensions: The embedding dimension.
            **kwargs: Ignored, for backward compatibility.

        Returns:
            The created KnowledgeCollection.
        """
        if self._registry.has_collection(name):
            raise KnowledgeError(f"Collection {name!r} already exists")

        embedding_config: EmbeddingConfig | None = kwargs.get("embedding_config")  # type: ignore[assignment]
        if embedding_config is not None:
            dimensions = embedding_config.dimensions

        self._log.info("engine.create_collection", name=name, dimensions=dimensions)
        try:
            await self._vector_store.create_collection(name, dimensions)
        except Exception as exc:
            raise KnowledgeEngineError(f"Failed to create collection {name}: {exc}") from exc

        col = KnowledgeCollection(
            collection_id=f"col:{name}",
            name=name,
            embedding_config=embedding_config
            or EmbeddingConfig(
                provider="default",
                model="default",
                dimensions=dimensions,
            ),
        )
        self._registry.register_collection(col)
        return col

    async def delete_collection(self, name: str) -> bool:
        """Delete a collection.

        Args:
            name: The collection name.

        Returns:
            True if the collection was deleted, False if not found.
        """
        self._log.info("engine.delete_collection", name=name)
        if not self._registry.has_collection(name):
            return False
        try:
            await self._vector_store.delete_collection(name)
        except Exception as exc:
            raise KnowledgeEngineError(f"Failed to delete collection {name}: {exc}") from exc
        self._registry.unregister_collection(name)
        return True

    async def list_collections(self) -> list[str]:
        """List all collections.

        Returns:
            A list of collection names.
        """
        return [c.name for c in self._registry.all_collections()]

    async def get_collection(self, name: str) -> KnowledgeCollection:
        """Get a collection by name.

        Args:
            name: The collection name.

        Returns:
            The KnowledgeCollection.

        Raises:
            CollectionNotFoundError: If the collection does not exist.
        """
        col = self._registry.get_collection(name)
        if col is None:
            raise CollectionNotFoundError(f"Collection {name!r} not found")
        return col

    async def health(self) -> dict[str, object]:
        """Check the health of the engine and its dependencies.

        Returns:
            A health status dictionary.
        """
        try:
            colls = await self.list_collections()
            return {
                "status": "healthy",
                "collections": len(colls),
                "collection_names": colls,
                "default_collection": self._default_collection,
            }
        except Exception as exc:
            return {
                "status": "degraded",
                "error": str(exc),
                "default_collection": self._default_collection,
            }

    def on(self, event_type: type[KnowledgeEngineEvent], handler: Any) -> None:
        """Register an event handler.

        Args:
            event_type: The event type to handle.
            handler: The handler callable.
        """
        if event_type not in self._event_handlers:
            self._event_handlers[event_type] = []
        self._event_handlers[event_type].append(handler)

    def _publish_event(self, event: object) -> None:
        """Publish a domain event to all registered handlers."""
        if self._event_publisher:
            self._event_publisher(event)
            return
        evt_type: type[KnowledgeEngineEvent] = type(event)  # type: ignore[assignment]
        handlers = self._event_handlers.get(evt_type, [])
        for handler in handlers:
            try:
                handler(event)
            except Exception as exc:
                self._log.warning(
                    "engine.event_handler.failed",
                    event_type=type(event).__name__,
                    error=str(exc),
                )

    async def _ensure_collection_exists(self, name: str) -> None:
        if self._registry.has_collection(name):
            return
        col = KnowledgeCollection(
            collection_id=f"col:{name}",
            name=name,
        )
        self._registry.register_collection(col)
        if hasattr(self._vector_store, "create_collection"):
            try:
                await self._vector_store.create_collection(name, 384)
            except Exception:
                self._log.warning("create_collection failed for %s", name)


__all__ = ["KnowledgeEngine"]
