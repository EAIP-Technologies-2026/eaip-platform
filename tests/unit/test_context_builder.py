"""Tests for ContextBuilder."""

from __future__ import annotations

import asyncio

from eaip.context.builder import ContextBuilder
from eaip.context.models import AssembledContext, ContextBuilderConfig, ContextDocument


class _MockMemoryEngine:
    def __init__(self) -> None:
        self.queries: list[str] = []

    async def search(self, query: str) -> object:
        self.queries.append(query)
        return _MockMemoryResult()


class _MockMemoryResult:
    items: list = []


class _MockKnowledgeEngine:
    def __init__(self) -> None:
        self.queries: list[str] = []

    async def search(self, query: str, **kwargs: object) -> object:
        self.queries.append(query)
        return _MockKnowledgeResult()


class _MockKnowledgeResult:
    chunks: list = []


class TestContextBuilder:
    async def test_empty_assemble(self) -> None:
        builder = ContextBuilder()
        result = await builder.assemble()
        assert result.document_count == 0
        assert result.total_tokens == 0

    async def test_assemble_with_extra_documents(self) -> None:
        builder = ContextBuilder()
        docs = [
            ContextDocument(content="doc1", relevance_score=0.9),
            ContextDocument(content="doc2", relevance_score=0.5),
        ]
        result = await builder.assemble(extra_documents=docs)
        assert result.document_count == 2
        assert result.total_tokens > 0

    async def test_filter_by_relevance(self) -> None:
        config = ContextBuilderConfig(relevance_threshold=0.8)
        builder = ContextBuilder(config)
        docs = [
            ContextDocument(content="high", relevance_score=0.95),
            ContextDocument(content="low", relevance_score=0.3),
            ContextDocument(content="medium", relevance_score=0.8),
        ]
        result = await builder.assemble(extra_documents=docs)
        assert result.document_count == 2
        assert result.documents[0].content == "high"
        assert result.documents[1].content == "medium"

    async def test_truncate_to_max_tokens(self) -> None:
        config = ContextBuilderConfig(max_tokens=5)
        builder = ContextBuilder(config)
        docs = [
            ContextDocument(content="a" * 100, relevance_score=0.9),
            ContextDocument(content="b" * 100, relevance_score=0.8),
        ]
        result = await builder.assemble(extra_documents=docs)
        assert result.total_tokens <= 5
        assert result.document_count >= 1

    async def test_max_documents(self) -> None:
        config = ContextBuilderConfig(max_documents=2)
        builder = ContextBuilder(config)
        docs = [
            ContextDocument(content=f"doc{i}", relevance_score=1.0 - i * 0.1)
            for i in range(5)
        ]
        result = await builder.assemble(extra_documents=docs)
        assert result.document_count <= 2

    def test_merge_deduplicates(self) -> None:
        builder = ContextBuilder()
        ctx1 = AssembledContext(
            documents=(
                ContextDocument(content="unique1", source="src/a"),
                ContextDocument(content="duplicate", source="src/x"),
            ),
            total_tokens=10,
            document_count=2,
        )
        ctx2 = AssembledContext(
            documents=(
                ContextDocument(content="unique2", source="src/b"),
                ContextDocument(content="duplicate", source="src/x"),
            ),
            total_tokens=10,
            document_count=2,
        )
        merged = builder.merge([ctx1, ctx2])
        assert merged.document_count == 3

    def test_merge_no_dedup(self) -> None:
        config = ContextBuilderConfig(deduplicate=False)
        builder = ContextBuilder(config)
        ctx1 = AssembledContext(
            documents=(ContextDocument(content="dup", source="src/x"),),
            total_tokens=2,
            document_count=1,
        )
        ctx2 = AssembledContext(
            documents=(ContextDocument(content="dup", source="src/x"),),
            total_tokens=2,
            document_count=1,
        )
        merged = builder.merge([ctx1, ctx2])
        assert merged.document_count == 2

    async def test_integration_with_memory(self) -> None:
        mem = _MockMemoryEngine()
        builder = ContextBuilder(memory_engine=mem)
        result = await builder.assemble(memory_queries=["test query"])
        assert result.document_count == 0
        assert "test query" in mem.queries

    async def test_integration_with_knowledge(self) -> None:
        kn = _MockKnowledgeEngine()
        builder = ContextBuilder(knowledge_engine=kn)
        result = await builder.assemble(knowledge_queries=["test knowledge"])
        assert result.document_count == 0
        assert "test knowledge" in kn.queries

    async def test_event_publisher_called(self) -> None:
        events: list[object] = []

        def publisher(event: object) -> None:
            events.append(event)

        builder = ContextBuilder(event_publisher=publisher)
        docs = [ContextDocument(content="hello", relevance_score=0.9)]
        await builder.assemble(extra_documents=docs)
        assert len(events) == 1
        assert events[0].document_count == 1

    def test_config_property(self) -> None:
        cfg = ContextBuilderConfig(max_tokens=512)
        builder = ContextBuilder(cfg)
        assert builder.config.max_tokens == 512

    async def test_assemble_with_query_fallback(self) -> None:
        mem = _MockMemoryEngine()
        builder = ContextBuilder(memory_engine=mem)
        result = await builder.assemble(query="fallback query")
        assert result.document_count == 0
        assert "fallback query" in mem.queries
