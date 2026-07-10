from __future__ import annotations

import pydantic
import pytest

from eaip.search.engine import EnterpriseSearchEngine
from eaip.search.exceptions import ProviderNotFoundError, SearchQueryError
from eaip.search.models import SearchQuery, SearchResult, SearchResultItem
from eaip.search.providers import SearchProvider


class _MockProvider:
    name: str

    def __init__(self, name: str, items: list[SearchResultItem] | None = None) -> None:
        self.name = name
        self._items = items or []

    async def search(self, query: SearchQuery) -> SearchResult:
        return SearchResult(
            items=tuple(self._items),
            total_count=len(self._items),
            page=query.page,
            page_size=query.page_size,
            total_pages=1,
            query=query.query,
        )


class TestEnterpriseSearchEngine:
    def test_empty_providers(self) -> None:
        engine = EnterpriseSearchEngine()
        assert engine.providers == {}

    def test_register_provider(self) -> None:
        engine = EnterpriseSearchEngine()
        p = _MockProvider(name="test")
        engine.register_provider(p)
        assert "test" in engine.providers

    def test_register_duplicate_raises(self) -> None:
        engine = EnterpriseSearchEngine()
        p = _MockProvider(name="test")
        engine.register_provider(p)
        with pytest.raises(ValueError, match="already registered"):
            engine.register_provider(p)

    def test_unregister_provider(self) -> None:
        engine = EnterpriseSearchEngine()
        p = _MockProvider(name="test")
        engine.register_provider(p)
        engine.unregister_provider("test")
        assert "test" not in engine.providers

    def test_unregister_missing_raises(self) -> None:
        engine = EnterpriseSearchEngine()
        with pytest.raises(ProviderNotFoundError):
            engine.unregister_provider("unknown")

    @pytest.mark.asyncio
    async def test_search_empty_engine(self) -> None:
        engine = EnterpriseSearchEngine()
        result = await engine.search(SearchQuery(query="test"))
        assert result.items == ()
        assert result.total_count == 0

    def test_search_invalid_page_size(self) -> None:
        engine = EnterpriseSearchEngine()
        with pytest.raises(pydantic.ValidationError):
            SearchQuery(query="test", page_size=0)

    @pytest.mark.asyncio
    async def test_search_single_provider(self) -> None:
        engine = EnterpriseSearchEngine()
        items = [SearchResultItem(id="1", collection="c", content="hello", score=0.9)]
        p = _MockProvider(name="p1", items=items)
        engine.register_provider(p)
        result = await engine.search(SearchQuery(query="test"))
        assert len(result.items) == 1
        assert result.items[0].id == "1"

    @pytest.mark.asyncio
    async def test_search_multiple_providers(self) -> None:
        engine = EnterpriseSearchEngine()
        items_a = [SearchResultItem(id="a1", collection="a", content="from a", score=0.9)]
        items_b = [SearchResultItem(id="b1", collection="b", content="from b", score=0.7)]
        engine.register_provider(_MockProvider(name="a", items=items_a))
        engine.register_provider(_MockProvider(name="b", items=items_b))
        result = await engine.search(SearchQuery(query="test"))
        assert len(result.items) == 2

    @pytest.mark.asyncio
    async def test_search_deduplication(self) -> None:
        engine = EnterpriseSearchEngine()
        item = SearchResultItem(id="same", collection="c", content="content", score=0.9)
        engine.register_provider(_MockProvider(name="a", items=[item]))
        engine.register_provider(_MockProvider(name="b", items=[item]))
        result = await engine.search(SearchQuery(query="test"))
        assert len(result.items) == 1

    @pytest.mark.asyncio
    async def test_search_takes_highest_score_on_duplicate(self) -> None:
        engine = EnterpriseSearchEngine()
        low = SearchResultItem(id="dup", collection="c", content="x", score=0.5)
        high = SearchResultItem(id="dup", collection="c", content="x", score=0.9)
        engine.register_provider(_MockProvider(name="a", items=[low]))
        engine.register_provider(_MockProvider(name="b", items=[high]))
        result = await engine.search(SearchQuery(query="test"))
        assert len(result.items) == 1
        assert result.items[0].score == 0.9

    @pytest.mark.asyncio
    async def test_search_pagination(self) -> None:
        engine = EnterpriseSearchEngine()
        items = [
            SearchResultItem(id=str(i), collection="c", content=f"item{i}", score=1.0 - i * 0.1)
            for i in range(5)
        ]
        engine.register_provider(_MockProvider(name="p", items=items))
        query = SearchQuery(query="test", page=1, page_size=2)
        result = await engine.search(query)
        assert len(result.items) == 2
        assert result.total_count == 5
        assert result.total_pages == 3
        assert result.page == 1
        assert result.page_size == 2

    @pytest.mark.asyncio
    async def test_search_provider_specific(self) -> None:
        engine = EnterpriseSearchEngine()
        items = [SearchResultItem(id="1", collection="c", content="x", score=0.9)]
        engine.register_provider(_MockProvider(name="specific", items=items))
        result = await engine.search_provider("specific", SearchQuery(query="test"))
        assert len(result.items) == 1

    @pytest.mark.asyncio
    async def test_search_provider_not_found(self) -> None:
        engine = EnterpriseSearchEngine()
        with pytest.raises(ProviderNotFoundError):
            await engine.search_provider("unknown", SearchQuery(query="test"))

    @pytest.mark.asyncio
    async def test_provider_failure_does_not_block_others(self) -> None:
        class FailingProvider:
            name = "fail"
            async def search(self, query: SearchQuery) -> SearchResult:
                raise RuntimeError("fail")

        engine = EnterpriseSearchEngine()
        engine.register_provider(FailingProvider())
        good_items = [SearchResultItem(id="ok", collection="c", content="ok", score=0.9)]
        engine.register_provider(_MockProvider(name="good", items=good_items))
        result = await engine.search(SearchQuery(query="test"))
        assert len(result.items) == 1
        assert result.items[0].id == "ok"

    def test_get_provider(self) -> None:
        engine = EnterpriseSearchEngine()
        p = _MockProvider(name="findme")
        engine.register_provider(p)
        assert engine.get_provider("findme") is p
        assert engine.get_provider("missing") is None
