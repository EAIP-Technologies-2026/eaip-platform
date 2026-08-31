"""Configurable chunking strategies for knowledge documents."""

from __future__ import annotations

import asyncio
import hashlib
from collections.abc import AsyncIterator, Sequence

from eaip.knowledge.base import Chunker
from eaip.knowledge.exceptions import ChunkingError
from eaip.knowledge.models import ChunkingConfig, ChunkingStrategy, DocumentChunk
from eaip.logging.context import get_logger


def _make_chunk_id(document_id: str, index: int) -> str:
    raw = f"{document_id}:{index}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def _hash_content(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


class FixedSizeChunker:
    """Chunks text by a fixed character count with optional overlap."""

    def __init__(self, config: ChunkingConfig) -> None:
        """Initialize FixedSizeChunker.

        Args:
            config: The chunking configuration.
        """
        self._config = config
        self._log = get_logger("eaip.knowledge.chunker.fixed")

    async def chunk(
        self, text: str, document_id: str, collection: str, **_kwargs: str
    ) -> list[DocumentChunk]:
        """Split text by fixed character count.

        Args:
            text: The text to chunk.
            document_id: The source document identifier.
            collection: The collection name.

        Returns:
            A list of document chunks.
        """
        chunk_size = self._config.chunk_size
        overlap = self._config.chunk_overlap
        max_chunks = self._config.max_chunks

        if chunk_size < 1:
            raise ChunkingError("chunk_size must be >= 1")

        chunks: list[DocumentChunk] = []
        start = 0
        index = 0

        while start < len(text):
            end = min(start + chunk_size, len(text))
            content = text[start:end]
            chunk = DocumentChunk(
                chunk_id=_make_chunk_id(document_id, index),
                document_id=document_id,
                collection=collection,
                content=content,
                content_hash=_hash_content(content),
                chunk_index=index,
            )
            chunks.append(chunk)
            index += 1

            if end >= len(text):
                break

            if max_chunks > 0 and index >= max_chunks:
                break

            next_start = end - overlap if overlap > 0 else end
            if next_start <= start:
                next_start = end
            start = next_start

        self._log.debug("chunker.fixed.complete", chunk_count=len(chunks))
        return chunks


class SemanticChunker:
    """Chunks text by natural semantic boundaries (paragraphs, sections)."""

    def __init__(self, config: ChunkingConfig) -> None:
        """Initialize SemanticChunker.

        Args:
            config: The chunking configuration.
        """
        self._config = config
        self._log = get_logger("eaip.knowledge.chunker.semantic")

    async def chunk(
        self, text: str, document_id: str, collection: str, **_kwargs: str
    ) -> list[DocumentChunk]:
        """Split text by semantic boundaries.

        Args:
            text: The text to chunk.
            document_id: The source document identifier.
            collection: The collection name.

        Returns:
            A list of document chunks.
        """
        separators = self._config.separators
        max_chunk_size = self._config.chunk_size
        max_chunks = self._config.max_chunks

        chunks: list[DocumentChunk] = []
        index = 0
        current = ""

        async for paragraph in self._iter_paragraphs(text, separators):
            if len(current) + len(paragraph) <= max_chunk_size or not current:
                current += paragraph
            else:
                if current:
                    chunk = DocumentChunk(
                        chunk_id=_make_chunk_id(document_id, index),
                        document_id=document_id,
                        collection=collection,
                        content=current.strip(),
                        content_hash=_hash_content(current),
                        chunk_index=index,
                    )
                    chunks.append(chunk)
                    index += 1
                    if max_chunks > 0 and index >= max_chunks:
                        break
                current = paragraph

        if current and (max_chunks == 0 or index < max_chunks):
            chunk = DocumentChunk(
                chunk_id=_make_chunk_id(document_id, index),
                document_id=document_id,
                collection=collection,
                content=current.strip(),
                content_hash=_hash_content(current),
                chunk_index=index,
            )
            chunks.append(chunk)

        self._log.debug("chunker.semantic.complete", chunk_count=len(chunks))
        return chunks

    @staticmethod
    async def _iter_paragraphs(text: str, separators: Sequence[str]) -> AsyncIterator[str]:
        """Split text by separators, yielding non-empty paragraphs."""
        paragraphs: list[str] = [text]
        for sep in separators:
            if sep == "":
                break
            expanded: list[str] = []
            for p in paragraphs:
                expanded.extend(p.split(sep))
            paragraphs = [p for p in expanded if p.strip()]

        for p in paragraphs:
            yield p.strip() + (separators[0] if separators else "")
            await asyncio.sleep(0)


class RecursiveChunker:
    """Chunks text by recursively trying smaller separators."""

    def __init__(self, config: ChunkingConfig) -> None:
        """Initialize RecursiveChunker.

        Args:
            config: The chunking configuration.
        """
        self._config = config
        self._log = get_logger("eaip.knowledge.chunker.recursive")

    async def chunk(
        self, text: str, document_id: str, collection: str, **_kwargs: str
    ) -> list[DocumentChunk]:
        """Split text recursively with smaller separators.

        Args:
            text: The text to chunk.
            document_id: The source document identifier.
            collection: The collection name.

        Returns:
            A list of document chunks.
        """
        separators = self._config.separators
        chunk_size = self._config.chunk_size
        max_chunks = self._config.max_chunks

        chunks: list[DocumentChunk] = []
        parts = self._recursive_split(text, list(separators), chunk_size)

        for index, part in enumerate(parts):
            if max_chunks > 0 and index >= max_chunks:
                break
            chunk = DocumentChunk(
                chunk_id=_make_chunk_id(document_id, index),
                document_id=document_id,
                collection=collection,
                content=part.strip(),
                content_hash=_hash_content(part),
                chunk_index=index,
            )
            chunks.append(chunk)

        self._log.debug("chunker.recursive.complete", chunk_count=len(chunks))
        return chunks

    @staticmethod
    def _recursive_split(text: str, separators: list[str], chunk_size: int) -> list[str]:
        if len(text) <= chunk_size:
            return [text] if text.strip() else []

        if not separators:
            return [
                text[i : i + chunk_size]
                for i in range(0, len(text), chunk_size)
                if text[i : i + chunk_size].strip()
            ]

        separator = separators[0]
        remaining = separators[1:] if len(separators) > 1 else []

        parts = text.split(separator)
        merged: list[str] = []
        current = ""

        for part in parts:
            if not current:
                current = part
            elif len(current) + len(separator) + len(part) <= chunk_size:
                current += separator + part
            else:
                if current.strip():
                    merged.append(current)
                current = part

        if current.strip():
            merged.append(current)

        result: list[str] = []
        for m in merged:
            if len(m) > chunk_size:
                result.extend(RecursiveChunker._recursive_split(m, remaining, chunk_size))
            elif m.strip():
                result.append(m)

        return result


def create_chunker(config: ChunkingConfig) -> Chunker:
    """Factory function returning the appropriate chunker for a config.

    Args:
        config: The chunking configuration.

    Returns:
        A Chunker implementation.

    Raises:
        ChunkingError: If the strategy is unknown.
    """
    if config.strategy is ChunkingStrategy.FIXED_SIZE:
        return FixedSizeChunker(config)
    if config.strategy is ChunkingStrategy.SEMANTIC:
        return SemanticChunker(config)
    assert config.strategy is ChunkingStrategy.RECURSIVE
    return RecursiveChunker(config)


__all__ = [
    "FixedSizeChunker",
    "RecursiveChunker",
    "SemanticChunker",
    "create_chunker",
]
