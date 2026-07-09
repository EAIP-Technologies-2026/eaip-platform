"""Runtime registry for knowledge sources and processors."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from eaip.knowledge.base import DocumentParser
from eaip.knowledge.exceptions import (
    ProcessorRegistrationError,
    UnsupportedFormatError,
)
from eaip.knowledge.models import (
    DocumentChunk,
    DocumentFormat,
    KnowledgeCollection,
    KnowledgeDocument,
)
from eaip.logging.context import get_logger


@dataclass
class ProcessorRegistration:
    """Registration record for a document processor.

    Attributes:
        name: The processor name.
        processor: The callable processor.
        formats: The document formats handled.
        priority: Priority (higher = processed first).
    """

    name: str
    processor: Callable[[Any], Any]
    formats: list[DocumentFormat] = field(default_factory=list)
    priority: int = 0


class KnowledgeRegistry:
    """Registry for knowledge components.

    Manages parsers, processors, and format capabilities.
    """

    def __init__(self) -> None:
        """Initialize an empty KnowledgeRegistry."""
        self._parsers: dict[DocumentFormat, DocumentParser] = {}
        self._processors: list[ProcessorRegistration] = []
        self._collections: dict[str, KnowledgeCollection] = {}
        self._documents: dict[tuple[str, str], KnowledgeDocument] = {}
        self._chunks: dict[tuple[str, str], list[DocumentChunk]] = {}
        self._log = get_logger("eaip.knowledge.registry")

    def register_parser(self, doc_format: DocumentFormat, parser: DocumentParser) -> None:
        """Register a document parser.

        Args:
            doc_format: The document format.
            parser: The parser implementation.
        """
        self._parsers[doc_format] = parser
        self._log.debug(
            "registry.register_parser",
            format=doc_format.value,
            parser=type(parser).__name__,
        )

    def get_parser(self, doc_format: DocumentFormat) -> DocumentParser:
        """Get a parser for a given format.

        Args:
            doc_format: The document format.

        Returns:
            A DocumentParser.

        Raises:
            UnsupportedFormatError: If no parser is registered.
        """
        parser = self._parsers.get(doc_format)
        if parser is None:
            raise UnsupportedFormatError(f"No parser registered for {doc_format.value}")
        return parser

    def unregister_parser(self, doc_format: DocumentFormat) -> None:
        """Unregister a parser.

        Args:
            doc_format: The document format to remove.
        """
        self._parsers.pop(doc_format, None)
        self._log.debug("registry.unregister_parser", format=doc_format.value)

    def register_processor(
        self,
        name: str,
        processor: Callable[[Any], Any],
        formats: list[DocumentFormat] | None = None,
        priority: int = 0,
    ) -> None:
        """Register a document processor.

        Args:
            name: Processor name.
            processor: The processor callable.
            formats: Optional formats to associate.
            priority: Processing priority.

        Raises:
            ProcessorRegistrationError: If the processor name is already
                registered.
        """
        if any(p.name == name for p in self._processors):
            raise ProcessorRegistrationError(f"Processor {name!r} is already registered")

        registration = ProcessorRegistration(
            name=name,
            processor=processor,
            formats=formats or [],
            priority=priority,
        )
        self._processors.append(registration)
        self._processors.sort(key=lambda p: p.priority, reverse=True)
        self._log.debug(
            "registry.register_processor",
            name=name,
            formats=[f.value for f in (formats or [])],
            priority=priority,
        )

    def unregister_processor(self, name: str) -> None:
        """Unregister a processor by name.

        Args:
            name: The processor name.
        """
        self._processors[:] = [p for p in self._processors if p.name != name]
        self._log.debug("registry.unregister_processor", name=name)

    def get_processors(
        self, doc_format: DocumentFormat | None = None
    ) -> list[ProcessorRegistration]:
        """Get processors, optionally filtered by format.

        Args:
            doc_format: Optional format filter.

        Returns:
            A list of matching ProcessorRegistration, sorted by priority.
        """
        if doc_format is None:
            return list(self._processors)
        return [p for p in self._processors if not p.formats or doc_format in p.formats]

    def get_supported_formats(self) -> list[DocumentFormat]:
        """Get all formats with a registered parser.

        Returns:
            A list of supported document formats.
        """
        return list(self._parsers.keys())

    def register_collection(
        self, collection: KnowledgeCollection, replace: bool = False
    ) -> None:
        """Register a collection.

        Args:
            collection: The collection to register.
            replace: Whether to replace an existing collection.
        """
        if not replace and collection.name in self._collections:
            return
        self._collections[collection.name] = collection

    def unregister_collection(self, name: str) -> bool:
        """Unregister a collection by name.

        Args:
            name: The collection name.

        Returns:
            True if the collection was removed, False otherwise.
        """
        if name in self._collections:
            del self._collections[name]
            return True
        return False

    def has_collection(self, name: str) -> bool:
        """Check if a collection is registered.

        Args:
            name: The collection name.

        Returns:
            True if registered, False otherwise.
        """
        return name in self._collections

    def get_collection(self, name: str) -> KnowledgeCollection | None:
        """Get a collection by name.

        Args:
            name: The collection name.

        Returns:
            The collection, or None.
        """
        return self._collections.get(name)

    def all_collections(self) -> list[KnowledgeCollection]:
        """Get all registered collections.

        Returns:
            A list of collections.
        """
        return list(self._collections.values())

    def collection_count(self) -> int:
        """Get the number of registered collections.

        Returns:
            The collection count.
        """
        return len(self._collections)

    def register_document(self, document: KnowledgeDocument) -> None:
        """Register a document.

        Args:
            document: The document to register.
        """
        key = (document.document_id, document.collection)
        self._documents[key] = document

    def unregister_document(self, document_id: str, collection: str) -> bool:
        """Unregister a document.

        Args:
            document_id: The document ID.
            collection: The collection name.

        Returns:
            True if the document was removed, False otherwise.
        """
        key = (document_id, collection)
        if key in self._documents:
            del self._documents[key]
            return True
        return False

    def has_document(self, document_id: str, collection: str) -> bool:
        """Check if a document is registered.

        Args:
            document_id: The document ID.
            collection: The collection name.

        Returns:
            True if registered, False otherwise.
        """
        return (document_id, collection) in self._documents

    def get_document(self, document_id: str, collection: str) -> KnowledgeDocument | None:
        """Get a document by ID and collection.

        Args:
            document_id: The document ID.
            collection: The collection name.

        Returns:
            The document, or None.
        """
        return self._documents.get((document_id, collection))

    def all_documents(self, collection: str | None = None) -> list[KnowledgeDocument]:
        """Get all registered documents, optionally filtered by collection.

        Args:
            collection: Optional collection filter.

        Returns:
            A list of documents.
        """
        if collection is None:
            return list(self._documents.values())
        return [
            doc
            for (doc_id, col), doc in self._documents.items()
            if col == collection
        ]

    def document_count(self, collection: str | None = None) -> int:
        """Get the number of registered documents.

        Args:
            collection: Optional collection filter.

        Returns:
            The document count.
        """
        if collection is None:
            return len(self._documents)
        return sum(1 for (_, col) in self._documents if col == collection)

    def register_chunks(self, chunks: list[DocumentChunk]) -> None:
        """Register document chunks.

        Args:
            chunks: The chunks to register.
        """
        for chunk in chunks:
            key = (chunk.document_id, chunk.collection)
            if key not in self._chunks:
                self._chunks[key] = []
            self._chunks[key].append(chunk)

    def get_document_chunks(
        self, document_id: str, collection: str
    ) -> list[DocumentChunk]:
        """Get chunks for a document.

        Args:
            document_id: The document ID.
            collection: The collection name.

        Returns:
            A list of chunks.
        """
        return self._chunks.get((document_id, collection)) or []

    def clear(self) -> None:
        """Clear all registrations."""
        self._parsers.clear()
        self._processors.clear()
        self._collections.clear()
        self._documents.clear()
        self._chunks.clear()
        self._log.debug("registry.cleared")

    async def health(self) -> dict[str, object]:
        """Return health status for this registry.

        Returns:
            A dict with health information.
        """
        return {
            "status": "healthy",
            "collections": self.collection_count(),
            "documents": self.document_count(),
        }


__all__ = [
    "KnowledgeRegistry",
    "ProcessorRegistration",
]
