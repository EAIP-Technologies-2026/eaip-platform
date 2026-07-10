from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from eaip.knowledge.federation import KnowledgeFederation
from eaip.knowledge.models import (
    RetrievalResult,
    RetrievedChunk,
    SourceAttribution,
)
from eaip.knowledge.retrieval_engine import RetrievalEngine
from eaip.search.exceptions import ProviderSearchError, SearchQueryError
from eaip.search.models import SearchQuery, SearchResult, SearchResultItem
from eaip.search.providers import (
    CompositeSearchProvider,
    KnowledgeSearchProvider,
    MemorySearchProvider,
    SearchProvider,
)


class TestSearchProviderProtocol:
    def test_protocol_runtime_checkable(self) -> None:
        class FakeProvider:
            name = "fake"

            async def search(self, query: SearchQuery) -> SearchResult:
                return SearchResult()

        assert isinstance(FakeProvider(), SearchProvider)

    def test_protocol_missing_name_fails(self) -> None:
        class BadProvider:
            async def search(self, query: SearchQuery) -> SearchResult:
                return SearchResult()

        assert not isinstance(BadProvider(), SearchProvider)


class TestKnowledgeSearchProvider:
    def test_provider_name(self) -> None:
        p = KnowledgeSearchProvider()
        assert p.name == "knowledge"

    @pytest.fixture
    def mock_engine(self) -> AsyncMock:
        engine = AsyncMock(spec=RetrievalEngine)
        chunk = RetrievedChunk(
            chunk_id="chunk1",
            document_id="doc1",
            collection="default",
            content="hello world",
            score=0.95,
            attribution=SourceAttribution(
                document_id="doc1",
                document_title="Test",
                collection="default",
                chunk_index=0,
                source="test_source",
                score=0.95,
            ),
        )
        engine.search.return_value = RetrievalResult(
            query="test",
            collection="default",
            chunks=(chunk,),
            total_results=1,
        )
        return engine

    @pytest.mark.asyncio
    async def test_search_with_engine(self, mock_engine: AsyncMock) -> None:
        query = SearchQuery(query="test")
        provider = KnowledgeSearchProvider(retrieval_engine=mock_engine)
        result = await provider.search(query)
        assert len(result.items) == 1
        assert result.items[0].id == "chunk1"
        assert result.items[0].content == "hello world"
        assert result.items[0].score == 0.95
        assert result.items[0].title == "Test"

    @pytest.mark.asyncio
    async def test_search_empty_query_raises(self) -> None:
        query = SearchQuery(query="  ")
        provider = KnowledgeSearchProvider()
        with pytest.raises(SearchQueryError):
            await provider.search(query)

    @pytest.mark.asyncio
    async def test_search_no_provider_raises(self) -> None:
        query = SearchQuery(query="test")
        provider = KnowledgeSearchProvider()
        with pytest.raises(ProviderSearchError):
            await provider.search(query)

    @pytest.mark.asyncio
    async def test_search_with_federation(self) -> None:
        federation = AsyncMock(spec=KnowledgeFederation)
        chunk = RetrievedChunk(
            chunk_id="fed1",
            document_id="doc1",
            collection="dept_docs",
            content="federated result",
            score=0.8,
        )
        federation.search_collections.return_value = RetrievalResult(
            query="test",
            collection="dept_docs",
            chunks=(chunk,),
            total_results=1,
        )
        query = SearchQuery(query="test", collections=("dept_docs",))
        provider = KnowledgeSearchProvider(federation=federation)
        result = await provider.search(query)
        assert len(result.items) == 1
        assert result.items[0].id == "fed1"

    @pytest.mark.asyncio
    async def test_search_multi_collections(self, mock_engine: AsyncMock) -> None:
        query = SearchQuery(query="test", collections=("coll1", "coll2"))
        provider = KnowledgeSearchProvider(retrieval_engine=mock_engine)
        result = await provider.search(query)
        assert len(result.items) >= 1


class TestMemorySearchProvider:
    def test_provider_name(self) -> None:
        p = MemorySearchProvider()
        assert p.name == "memory"

    @pytest.mark.asyncio
    async def test_search_no_fn_returns_empty(self) -> None:
        query = SearchQuery(query="test")
        provider = MemorySearchProvider()
        result = await provider.search(query)
        assert result.items == ()
        assert result.total_count == 0

    @pytest.mark.asyncio
    async def test_search_with_mock_fn(self) -> None:
        async def mock_search(_q: str, _k: int) -> list:
            class MockMemory:
                memory_id = "mem1"
                content = "memory content"
                memory_type = type("MT", (), {"value": "episodic"})()
                metadata = {"key": "val"}

            class MockResult:
                memory = MockMemory()
                score = 0.9

            return [MockResult()]

        query = SearchQuery(query="test")
        provider = MemorySearchProvider(memory_search_fn=mock_search)
        result = await provider.search(query)
        assert len(result.items) == 1
        assert result.items[0].id == "mem1"
        assert result.items[0].content == "memory content"
        assert result.items[0].score == 0.9

    @pytest.mark.asyncio
    async def test_search_fn_failure_raises(self) -> None:
        async def failing_fn(_q: str, _k: int) -> list:
            raise RuntimeError("memory error")

        query = SearchQuery(query="test")
        provider = MemorySearchProvider(memory_search_fn=failing_fn)
        with pytest.raises(ProviderSearchError):
            await provider.search(query)


class TestCompositeSearchProvider:
    def test_provider_name(self) -> None:
        p = CompositeSearchProvider()
        assert p.name == "composite"

    @pytest.mark.asyncio
    async def test_empty_providers_returns_empty(self) -> None:
        query = SearchQuery(query="test")
        provider = CompositeSearchProvider()
        result = await provider.search(query)
        assert result.items == ()
        assert result.total_count == 0

    @pytest.mark.asyncio
    async def test_aggregates_from_multiple_providers(self) -> None:
        class ProviderA:
            name = "a"
            async def search(self, q: SearchQuery) -> SearchResult:
                return SearchResult(
                    items=(SearchResultItem(id="a1", collection="a", content="aa", score=0.9),),
                    total_count=1,
                )

        class ProviderB:
            name = "b"
            async def search(self, q: SearchQuery) -> SearchResult:
                return SearchResult(
                    items=(SearchResultItem(id="b1", collection="b", content="bb", score=0.8),),
                    total_count=1,
                )

        provider = CompositeSearchProvider(providers=[ProviderA(), ProviderB()])
        result = await provider.search(SearchQuery(query="test"))
        assert len(result.items) == 2
        assert result.items[0].score >= result.items[1].score

    @pytest.mark.asyncio
    async def test_deduplication(self) -> None:
        class DupProvider:
            name = "dup"
            async def search(self, q: SearchQuery) -> SearchResult:
                item = SearchResultItem(id="same", collection="c", content="content", score=0.9)
                return SearchResult(items=(item,), total_count=1)

        provider = CompositeSearchProvider(providers=[DupProvider(), DupProvider()])
        result = await provider.search(SearchQuery(query="test"))
        assert len(result.items) == 1

    @pytest.mark.asyncio
    async def test_provider_failure_skipped(self) -> None:
        class FailingProvider:
            name = "fail"
            async def search(self, q: SearchQuery) -> SearchResult:
                raise RuntimeError("fail")

        class GoodProvider:
            name = "good"
            async def search(self, q: SearchQuery) -> SearchResult:
                return SearchResult(
                    items=(SearchResultItem(id="g1", collection="c", content="good", score=0.9),),
                    total_count=1,
                )

        provider = CompositeSearchProvider(providers=[FailingProvider(), GoodProvider()])
        result = await provider.search(SearchQuery(query="test"))
        assert len(result.items) == 1
        assert result.items[0].id == "g1"

    def test_add_remove_provider(self) -> None:
        class P:
            name = "p"
            async def search(self, q: SearchQuery) -> SearchResult:
                return SearchResult()

        provider = CompositeSearchProvider()
        assert len(provider.providers) == 0
        provider.add_provider(P())
        assert len(provider.providers) == 1
        provider.remove_provider("p")
        assert len(provider.providers) == 0
