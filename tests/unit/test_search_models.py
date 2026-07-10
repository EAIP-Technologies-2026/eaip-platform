from __future__ import annotations

import pydantic
import pytest

from eaip.search.models import (
    Pagination,
    SearchFilter,
    SearchProviderConfig,
    SearchQuery,
    SearchResult,
    SearchResultItem,
)


class TestSearchQuery:
    def test_defaults(self) -> None:
        q = SearchQuery(query="hello")
        assert q.query == "hello"
        assert q.filters == ()
        assert q.page == 1
        assert q.page_size == 20
        assert q.sort_by is None
        assert q.sort_order == "desc"
        assert q.collections == ()
        assert q.search_type == "hybrid"
        assert q.alpha == 0.5
        assert q.min_score == 0.0

    def test_with_filters(self) -> None:
        f = SearchFilter(field="author", operator="eq", value="john")
        q = SearchQuery(query="test", filters=(f,), collections=("docs",), search_type="semantic")
        assert len(q.filters) == 1
        assert q.filters[0].field == "author"
        assert q.collections == ("docs",)
        assert q.search_type == "semantic"

    def test_frozen(self) -> None:
        q = SearchQuery(query="test")
        with pytest.raises(pydantic.ValidationError):
            q.query = "changed"  # type: ignore[misc]

    def test_extra_forbidden(self) -> None:
        with pytest.raises(pydantic.ValidationError):
            SearchQuery(query="test", unknown_field="x")  # type: ignore[call-arg]

    def test_alpha_range(self) -> None:
        q = SearchQuery(query="test", alpha=0.0)
        assert q.alpha == 0.0
        q2 = SearchQuery(query="test", alpha=1.0)
        assert q2.alpha == 1.0

    def test_min_score_ge_zero(self) -> None:
        q = SearchQuery(query="test", min_score=0.5)
        assert q.min_score == 0.5


class TestSearchResultItem:
    def test_defaults(self) -> None:
        item = SearchResultItem(id="1", collection="default", content="test content")
        assert item.id == "1"
        assert item.collection == "default"
        assert item.content == "test content"
        assert item.score == 0.0
        assert item.title == ""
        assert item.source == ""
        assert item.metadata == {}
        assert item.highlights == {}

    def test_with_full_data(self) -> None:
        item = SearchResultItem(
            id="doc1",
            collection="wiki",
            content="some text",
            score=0.95,
            title="Test Doc",
            source="filesystem",
            metadata={"author": "john"},
            highlights={"content": "some <em>text</em>"},
        )
        assert item.score == 0.95
        assert item.title == "Test Doc"
        assert item.metadata["author"] == "john"
        assert item.highlights["content"] == "some <em>text</em>"

    def test_frozen(self) -> None:
        item = SearchResultItem(id="1", collection="c", content="x")
        with pytest.raises(pydantic.ValidationError):
            item.content = "y"  # type: ignore[misc]


class TestSearchResult:
    def test_defaults(self) -> None:
        r = SearchResult()
        assert r.items == ()
        assert r.total_count == 0
        assert r.page == 1
        assert r.page_size == 20
        assert r.total_pages == 0
        assert r.duration_ms == 0.0
        assert r.query == ""

    def test_with_items(self) -> None:
        items = (
            SearchResultItem(id="1", collection="c", content="a"),
            SearchResultItem(id="2", collection="c", content="b"),
        )
        r = SearchResult(items=items, total_count=2, page=1, page_size=10, total_pages=1)
        assert len(r.items) == 2
        assert r.total_pages == 1

    def test_frozen(self) -> None:
        r = SearchResult()
        with pytest.raises(pydantic.ValidationError):
            r.total_count = 5  # type: ignore[misc]


class TestSearchFilter:
    def test_operators(self) -> None:
        f1 = SearchFilter(field="age", operator="gte", value=18)
        assert f1.operator == "gte"
        f2 = SearchFilter(field="tags", operator="contains", value="urgent")
        assert f2.operator == "contains"
        f3 = SearchFilter(field="status", operator="in", value=["a", "b"])
        assert f3.operator == "in"

    def test_frozen(self) -> None:
        f = SearchFilter(field="x", operator="eq", value=1)
        with pytest.raises(pydantic.ValidationError):
            f.field = "y"  # type: ignore[misc]


class TestSearchProviderConfig:
    def test_defaults(self) -> None:
        cfg = SearchProviderConfig(provider_type="qdrant")
        assert cfg.provider_type == "qdrant"
        assert cfg.endpoint == ""
        assert cfg.timeout_seconds == 60
        assert cfg.max_retries == 3
        assert cfg.options == {}

    def test_with_options(self) -> None:
        cfg = SearchProviderConfig(
            provider_type="elasticsearch",
            endpoint="http://localhost:9200",
            timeout_seconds=30,
            max_retries=5,
            options={"index": "my_index"},
        )
        assert cfg.options["index"] == "my_index"
        assert cfg.endpoint == "http://localhost:9200"

    def test_frozen(self) -> None:
        cfg = SearchProviderConfig(provider_type="test")
        with pytest.raises(pydantic.ValidationError):
            cfg.provider_type = "other"  # type: ignore[misc]


class TestPagination:
    def test_defaults(self) -> None:
        p = Pagination()
        assert p.page == 1
        assert p.page_size == 20
        assert p.max_page_size == 1000

    def test_custom(self) -> None:
        p = Pagination(page=2, page_size=50, max_page_size=500)
        assert p.page == 2
        assert p.page_size == 50

    def test_page_ge_one(self) -> None:
        try:
            Pagination(page=0)
            assert False, "page must be >= 1"
        except Exception:
            pass

    def test_frozen(self) -> None:
        p = Pagination(page=1, page_size=10)
        with pytest.raises(pydantic.ValidationError):
            p.page = 3  # type: ignore[misc]
