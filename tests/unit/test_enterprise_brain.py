"""Tests for EnterpriseBrain."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from eaip.brain.enterprise_brain import EnterpriseBrain
from eaip.brain.exceptions import BrainQueryError
from eaip.brain.models import BrainQuery, BrainResult, EnterpriseBrainConfig


class TestEnterpriseBrainInit:
    def test_default_config(self) -> None:
        brain = EnterpriseBrain()
        assert brain.config.default_top_k == 10
        assert brain.config.enable_caching is True

    def test_custom_config(self) -> None:
        config = EnterpriseBrainConfig(default_top_k=5, enable_caching=False)
        brain = EnterpriseBrain(config=config)
        assert brain.config.default_top_k == 5
        assert brain.config.enable_caching is False


class TestEnterpriseBrainQuery:
    @pytest.mark.asyncio
    async def test_query_without_sources_returns_empty(self) -> None:
        brain = EnterpriseBrain()
        result = await brain.query(BrainQuery(query="test"))
        assert isinstance(result, BrainResult)
        assert result.query == "test"
        assert result.answer == ""
        assert result.confidence == 0.0
        assert result.sources == ()

    @pytest.mark.asyncio
    async def test_query_knowledge_only(self) -> None:
        mock_engine = AsyncMock()
        chunk = MagicMock()
        chunk.chunk_id = "chunk1"
        chunk.content = "relevant knowledge content"
        chunk.score = 0.95
        mock_result = MagicMock()
        mock_result.chunks = [chunk]
        mock_engine.search = AsyncMock(return_value=mock_result)

        brain = EnterpriseBrain(knowledge_engine=mock_engine)
        result = await brain.query(
            BrainQuery(query="test", include_memory=False, include_context=False)
        )
        assert len(result.sources) == 1
        assert result.sources[0].source_type == "knowledge"
        assert result.sources[0].source_id == "chunk1"
        assert result.confidence > 0.0

    @pytest.mark.asyncio
    async def test_query_memory_only(self) -> None:
        mock_engine = AsyncMock()
        memory_item = MagicMock()
        memory_item.memory_id = "mem1"
        memory_item.content = "relevant memory content"
        search_result_item = MagicMock()
        search_result_item.memory = memory_item
        search_result_item.score = 0.85
        mock_result = MagicMock()
        mock_result.results = [search_result_item]
        mock_engine.search_memories = AsyncMock(return_value=mock_result)

        brain = EnterpriseBrain(memory_engine=mock_engine)
        result = await brain.query(
            BrainQuery(query="test", include_knowledge=False, include_context=False)
        )
        assert len(result.sources) == 1
        assert result.sources[0].source_type == "memory"
        assert result.sources[0].source_id == "mem1"

    @pytest.mark.asyncio
    async def test_query_context_only(self) -> None:
        mock_builder = AsyncMock()
        context_doc = MagicMock()
        context_doc.source = "ctx:test"
        context_doc.content = "context content"
        context_doc.relevance_score = 0.75
        mock_context = MagicMock()
        mock_context.documents = [context_doc]
        mock_context.document_count = 1
        mock_context.total_tokens = 50
        mock_builder.assemble = AsyncMock(return_value=mock_context)

        brain = EnterpriseBrain(context_builder=mock_builder)
        result = await brain.query(
            BrainQuery(query="test", include_knowledge=False, include_memory=False)
        )
        assert len(result.sources) == 1
        assert result.sources[0].source_type == "context"
        assert result.sources[0].source_id == "ctx:test"

    @pytest.mark.asyncio
    async def test_query_all_sources_merged(self) -> None:
        chunk = MagicMock()
        chunk.chunk_id = "k1"
        chunk.content = "knowledge"
        chunk.score = 0.9
        mock_knowledge = AsyncMock()
        mock_knowledge.search = AsyncMock(return_value=MagicMock(chunks=[chunk]))

        memory_item = MagicMock()
        memory_item.memory_id = "m1"
        memory_item.content = "memory"
        search_item = MagicMock()
        search_item.memory = memory_item
        search_item.score = 0.8
        mock_memory = AsyncMock()
        mock_memory.search_memories = AsyncMock(return_value=MagicMock(results=[search_item]))

        context_doc = MagicMock()
        context_doc.source = "c1"
        context_doc.content = "context"
        context_doc.relevance_score = 0.7
        mock_context = MagicMock()
        mock_context.documents = [context_doc]
        mock_context.document_count = 1
        mock_context.total_tokens = 30
        mock_builder = AsyncMock()
        mock_builder.assemble = AsyncMock(return_value=mock_context)

        brain = EnterpriseBrain(
            knowledge_engine=mock_knowledge,
            memory_engine=mock_memory,
            context_builder=mock_builder,
        )
        result = await brain.query(BrainQuery(query="test"))
        assert len(result.sources) == 3
        types = {s.source_type for s in result.sources}
        assert types == {"knowledge", "memory", "context"}

    @pytest.mark.asyncio
    async def test_query_deduplication(self) -> None:
        chunk = MagicMock()
        chunk.chunk_id = "dup1"
        chunk.content = "duplicate knowledge"
        chunk.score = 0.9
        mock_knowledge = AsyncMock()
        mock_knowledge.search = AsyncMock(return_value=MagicMock(chunks=[chunk, chunk]))

        brain = EnterpriseBrain(
            knowledge_engine=mock_knowledge, memory_engine=None, context_builder=None
        )
        result = await brain.query(
            BrainQuery(query="test", include_memory=False, include_context=False)
        )
        assert len(result.sources) == 1

    @pytest.mark.asyncio
    async def test_query_score_threshold(self) -> None:
        chunk_high = MagicMock()
        chunk_high.chunk_id = "high"
        chunk_high.content = "high score"
        chunk_high.score = 0.9
        chunk_low = MagicMock()
        chunk_low.chunk_id = "low"
        chunk_low.content = "low score"
        chunk_low.score = 0.1
        mock_knowledge = AsyncMock()
        mock_knowledge.search = AsyncMock(return_value=MagicMock(chunks=[chunk_high, chunk_low]))

        brain = EnterpriseBrain(
            knowledge_engine=mock_knowledge, memory_engine=None, context_builder=None
        )
        result = await brain.query(
            BrainQuery(
                query="test", score_threshold=0.5, include_memory=False, include_context=False
            )
        )
        assert len(result.sources) == 1
        assert result.sources[0].source_id == "high"

    @pytest.mark.asyncio
    async def test_query_top_k(self) -> None:
        chunks = []
        for i in range(10):
            c = MagicMock()
            c.chunk_id = f"chunk{i}"
            c.content = f"content {i}"
            c.score = 1.0 - (i * 0.1)
            chunks.append(c)
        mock_knowledge = AsyncMock()
        mock_knowledge.search = AsyncMock(return_value=MagicMock(chunks=chunks))

        brain = EnterpriseBrain(
            knowledge_engine=mock_knowledge,
            memory_engine=None,
            context_builder=None,
            config=EnterpriseBrainConfig(enable_reranking=False),
        )
        result = await brain.query(
            BrainQuery(query="test", top_k=3, include_memory=False, include_context=False)
        )
        assert len(result.sources) == 3

    @pytest.mark.asyncio
    async def test_health_status(self) -> None:
        brain = EnterpriseBrain()
        health = await brain.health()
        assert health["status"] == "healthy"
        assert health["knowledge_configured"] is False
        assert health["memory_configured"] is False
        assert health["context_configured"] is False
        assert health["agents_configured"] is False


class TestEnterpriseBrainErrors:
    @pytest.mark.asyncio
    async def test_brain_query_error(self) -> None:
        mock_engine = AsyncMock()
        mock_engine.search.side_effect = RuntimeError("connection failed")

        brain = EnterpriseBrain(knowledge_engine=mock_engine)
        with pytest.raises(BrainQueryError):
            await brain.query(BrainQuery(query="test", include_memory=False, include_context=False))

    @pytest.mark.asyncio
    async def test_brain_source_unavailable(self) -> None:
        mock_engine = AsyncMock()
        mock_engine.search.side_effect = RuntimeError("unavailable")

        brain = EnterpriseBrain(knowledge_engine=mock_engine)
        with pytest.raises(BrainQueryError):
            await brain.query(BrainQuery(query="test", include_memory=False, include_context=False))


class TestEnterpriseBrainConvenienceMethods:
    @pytest.mark.asyncio
    async def test_query_knowledge_convenience(self) -> None:
        chunk = MagicMock()
        chunk.chunk_id = "k1"
        chunk.content = "knowledge content"
        chunk.score = 0.9
        mock_engine = AsyncMock()
        mock_engine.search = AsyncMock(return_value=MagicMock(chunks=[chunk]))

        brain = EnterpriseBrain(
            knowledge_engine=mock_engine, memory_engine=None, context_builder=None
        )
        sources = await brain.query_knowledge("test query")
        assert len(sources) == 1
        assert sources[0].source_type == "knowledge"

    @pytest.mark.asyncio
    async def test_query_memory_convenience(self) -> None:
        memory_item = MagicMock()
        memory_item.memory_id = "m1"
        memory_item.content = "memory content"
        search_item = MagicMock()
        search_item.memory = memory_item
        search_item.score = 0.8
        mock_engine = AsyncMock()
        mock_engine.search_memories = AsyncMock(return_value=MagicMock(results=[search_item]))

        brain = EnterpriseBrain(
            memory_engine=mock_engine, knowledge_engine=None, context_builder=None
        )
        sources = await brain.query_memory("test query")
        assert len(sources) == 1
        assert sources[0].source_type == "memory"

    @pytest.mark.asyncio
    async def test_query_context_convenience(self) -> None:
        context_doc = MagicMock()
        context_doc.source = "ctx:test"
        context_doc.content = "context content"
        context_doc.relevance_score = 0.7
        mock_context = MagicMock()
        mock_context.documents = [context_doc]
        mock_context.document_count = 1
        mock_context.total_tokens = 40
        mock_builder = AsyncMock()
        mock_builder.assemble = AsyncMock(return_value=mock_context)

        brain = EnterpriseBrain(context_builder=mock_builder)
        sources = await brain.query_context("test query")
        assert len(sources) == 1
        assert sources[0].source_type == "context"
