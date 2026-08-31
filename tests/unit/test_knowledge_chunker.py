"""Tests for knowledge chunking strategies."""

from __future__ import annotations

import pytest

from eaip.knowledge.chunker import (
    FixedSizeChunker,
    RecursiveChunker,
    SemanticChunker,
    create_chunker,
)
from eaip.knowledge.models import ChunkingConfig, ChunkingStrategy


class TestFixedSizeChunker:
    @pytest.mark.asyncio
    async def test_chunk_basic(self) -> None:
        cfg = ChunkingConfig(strategy=ChunkingStrategy.FIXED_SIZE, chunk_size=10, chunk_overlap=2)
        chunker = FixedSizeChunker(cfg)
        text = "Hello world, this is a test document for chunking."
        chunks = await chunker.chunk(text, "doc1", "test")
        assert len(chunks) >= 1
        for c in chunks:
            assert c.document_id == "doc1"
            assert c.collection == "test"
            assert len(c.chunk_id) == 16
            assert c.content_hash

    @pytest.mark.asyncio
    async def test_chunk_small_text(self) -> None:
        cfg = ChunkingConfig(strategy=ChunkingStrategy.FIXED_SIZE, chunk_size=100)
        chunker = FixedSizeChunker(cfg)
        chunks = await chunker.chunk("Hello", "doc1", "test")
        assert len(chunks) == 1
        assert chunks[0].content == "Hello"

    @pytest.mark.asyncio
    async def test_chunk_empty_text(self) -> None:
        cfg = ChunkingConfig(strategy=ChunkingStrategy.FIXED_SIZE, chunk_size=10)
        chunker = FixedSizeChunker(cfg)
        chunks = await chunker.chunk("", "doc1", "test")
        assert len(chunks) == 0

    @pytest.mark.asyncio
    async def test_chunk_with_overlap(self) -> None:
        cfg = ChunkingConfig(strategy=ChunkingStrategy.FIXED_SIZE, chunk_size=10, chunk_overlap=3)
        chunker = FixedSizeChunker(cfg)
        text = "This is a longer document text for overlap testing."
        chunks = await chunker.chunk(text, "doc1", "test")
        assert len(chunks) >= 2

    @pytest.mark.asyncio
    async def test_max_chunks(self) -> None:
        cfg = ChunkingConfig(strategy=ChunkingStrategy.FIXED_SIZE, chunk_size=5, max_chunks=2)
        chunker = FixedSizeChunker(cfg)
        text = "A" * 100
        chunks = await chunker.chunk(text, "doc1", "test")
        assert len(chunks) <= 2


class TestSemanticChunker:
    @pytest.mark.asyncio
    async def test_chunk_by_paragraph(self) -> None:
        cfg = ChunkingConfig(
            strategy=ChunkingStrategy.SEMANTIC,
            chunk_size=20,
            separators=("\n\n", "\n", "."),
        )
        chunker = SemanticChunker(cfg)
        text = "First paragraph.\n\nSecond paragraph.\n\nThird paragraph."
        chunks = await chunker.chunk(text, "doc1", "test")
        assert len(chunks) >= 2

    @pytest.mark.asyncio
    async def test_chunk_single_paragraph(self) -> None:
        cfg = ChunkingConfig(strategy=ChunkingStrategy.SEMANTIC, chunk_size=500)
        chunker = SemanticChunker(cfg)
        text = "This is a single paragraph without any line breaks. It should be one chunk."
        chunks = await chunker.chunk(text, "doc1", "test")
        assert len(chunks) == 1

    @pytest.mark.asyncio
    async def test_chunk_large_paragraph(self) -> None:
        cfg = ChunkingConfig(strategy=ChunkingStrategy.SEMANTIC, chunk_size=20)
        chunker = SemanticChunker(cfg)
        text = "This is a long paragraph that should be split into multiple semantic chunks. " * 5
        chunks = await chunker.chunk(text, "doc1", "test")
        assert len(chunks) >= 2


class TestRecursiveChunker:
    @pytest.mark.asyncio
    async def test_chunk_recursive(self) -> None:
        cfg = ChunkingConfig(
            strategy=ChunkingStrategy.RECURSIVE,
            chunk_size=20,
            separators=("\n\n", "\n", ".", " "),
        )
        chunker = RecursiveChunker(cfg)
        text = "First sentence. Second sentence. Third sentence. Fourth sentence."
        chunks = await chunker.chunk(text, "doc1", "test")
        assert len(chunks) >= 2

    @pytest.mark.asyncio
    async def test_chunk_small(self) -> None:
        cfg = ChunkingConfig(strategy=ChunkingStrategy.RECURSIVE, chunk_size=500)
        chunker = RecursiveChunker(cfg)
        text = "Short text."
        chunks = await chunker.chunk(text, "doc1", "test")
        assert len(chunks) == 1


class TestCreateChunker:
    def test_create_fixed_size(self) -> None:
        cfg = ChunkingConfig(strategy=ChunkingStrategy.FIXED_SIZE)
        chunker = create_chunker(cfg)
        assert isinstance(chunker, FixedSizeChunker)

    def test_create_semantic(self) -> None:
        cfg = ChunkingConfig(strategy=ChunkingStrategy.SEMANTIC)
        chunker = create_chunker(cfg)
        assert isinstance(chunker, SemanticChunker)

    def test_create_recursive(self) -> None:
        cfg = ChunkingConfig(strategy=ChunkingStrategy.RECURSIVE)
        chunker = create_chunker(cfg)
        assert isinstance(chunker, RecursiveChunker)

    def test_create_fixed_size_default(self) -> None:
        cfg = ChunkingConfig()
        chunker = create_chunker(cfg)
        assert isinstance(chunker, FixedSizeChunker)

    @staticmethod
    def _set_strategy(self, value: str) -> None: ...
