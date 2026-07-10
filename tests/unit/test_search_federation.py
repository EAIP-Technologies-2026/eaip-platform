from __future__ import annotations

import pytest

from eaip.search.federation import SearchFederation
from eaip.search.models import SearchQuery, SearchResult, SearchResultItem
from eaip.search.providers import SearchProvider


class _MockSource:
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


class TestSearchFederation:
    def test_register_source(self) -> None:
        fed = SearchFederation()
        fed.register_source("enterprise", _MockSource("enterprise"))
        assert "enterprise" in fed._sources

    def test_unregister_source(self) -> None:
        fed = SearchFederation()
        fed.register_source("dept", _MockSource("dept"))
        fed.unregister_source("dept")
        assert "dept" not in fed._sources

    def test_unregister_nonexistent(self) -> None:
        fed = SearchFederation()
        fed.unregister_source("missing")

    @pytest.mark.asyncio
    async def test_federated_search_empty(self) -> None:
        fed = SearchFederation()
        result = await fed.federated_search(SearchQuery(query="test"))
        assert result.items == ()
        assert result.total_count == 0

    @pytest.mark.asyncio
    async def test_federated_search_all_sources(self) -> None:
        fed = SearchFederation()
        fed.register_source(
            "source_a",
            _MockSource("a", items=[SearchResultItem(id="a1", collection="a", content="aa", score=0.9)]),
        )
        fed.register_source(
            "source_b",
            _MockSource("b", items=[SearchResultItem(id="b1", collection="b", content="bb", score=0.8)]),
        )
        result = await fed.federated_search(SearchQuery(query="test"))
        assert len(result.items) == 2

    @pytest.mark.asyncio
    async def test_federated_search_filtered_sources(self) -> None:
        fed = SearchFederation()
        fed.register_source("alpha", _MockSource("alpha", items=[SearchResultItem(id="a1", collection="a", content="aa")]))
        fed.register_source("beta", _MockSource("beta", items=[SearchResultItem(id="b1", collection="b", content="bb")]))
        result = await fed.federated_search(SearchQuery(query="test"), sources=("alpha",))
        assert len(result.items) == 1
        assert result.items[0].id == "a1"

    @pytest.mark.asyncio
    async def test_enterprise_search_all(self) -> None:
        fed = SearchFederation()
        fed.register_source("brain", _MockSource("brain", items=[SearchResultItem(id="e1", collection="e", content="ent")]))
        result = await fed.enterprise_search(SearchQuery(query="test"))
        assert len(result.items) >= 1

    @pytest.mark.asyncio
    async def test_department_search(self) -> None:
        fed = SearchFederation()
        fed.register_source(
            "dept_engineering",
            _MockSource("dept_engineering", items=[SearchResultItem(id="d1", collection="dept", content="data")]),
        )
        fed.register_source(
            "enterprise_brain",
            _MockSource("enterprise_brain", items=[SearchResultItem(id="e1", collection="ent", content="global")]),
        )
        result = await fed.department_search(SearchQuery(query="test"), department_id="engineering")
        assert len(result.items) == 1
        assert result.items[0].id == "d1"

    @pytest.mark.asyncio
    async def test_department_search_no_match(self) -> None:
        fed = SearchFederation()
        fed.register_source("hr_data", _MockSource("hr_data"))
        result = await fed.department_search(SearchQuery(query="test"), department_id="engineering")
        assert result.items == ()

    @pytest.mark.asyncio
    async def test_source_failure_skipped(self) -> None:
        class FailingSource:
            name = "fail"
            async def search(self, query: SearchQuery) -> SearchResult:
                raise RuntimeError("fail")

        fed = SearchFederation()
        fed.register_source("failing", FailingSource())
        fed.register_source(
            "good",
            _MockSource("good", items=[SearchResultItem(id="ok", collection="c", content="ok", score=0.9)]),
        )
        result = await fed.federated_search(SearchQuery(query="test"))
        assert len(result.items) == 1
        assert result.items[0].id == "ok"

    @pytest.mark.asyncio
    async def test_deduplication(self) -> None:
        fed = SearchFederation()
        item = SearchResultItem(id="dup", collection="c", content="content", score=0.9)
        fed.register_source("a", _MockSource("a", items=[item]))
        fed.register_source("b", _MockSource("b", items=[item]))
        result = await fed.federated_search(SearchQuery(query="test"))
        assert len(result.items) == 1

    async def test_health(self) -> None:
        fed = SearchFederation()
        fed.register_source("s1", _MockSource("s1"))
        fed.register_source("s2", _MockSource("s2"))
        status = await fed.health()
        assert status == {"s1": "registered", "s2": "registered"}
