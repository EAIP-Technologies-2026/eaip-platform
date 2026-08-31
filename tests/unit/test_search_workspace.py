"""Tests for Search & Investigation (WS-006) — mapping, capabilities, suggestions."""

from __future__ import annotations

from typing import Any

from eaip.http.routers.search_router import (
    build_capabilities,
    item_to_dict,
    suggestions_from_recent,
)
from eaip.search.engine import EnterpriseSearchEngine
from eaip.search.models import SearchQuery, SearchResult, SearchResultItem


def _item(
    item_id: str = "chunk-1",
    collection: str = "default",
    content: str = "Relevant document content about AI governance.",
    score: float = 0.85,
    title: str = "AI Governance Policy",
    source: str = "governance.md",
    metadata: dict[str, Any] | None = None,
) -> SearchResultItem:
    return SearchResultItem(
        id=item_id,
        collection=collection,
        content=content,
        score=score,
        title=title,
        source=source,
        metadata=(
            {"updated_at": "2025-01-01T00:00:00Z"}
            if metadata is None
            else metadata
        ),
    )


class TestSearchResultMapping:
    """Mapping SearchResultItem into the search API contract."""

    def test_maps_core_fields(self) -> None:
        out = item_to_dict(_item(), query="governance")
        assert out["id"] == "chunk-1"
        assert out["title"] == "AI Governance Policy"
        assert out["category"] == "default"
        assert out["source"] == "governance.md"
        assert out["score"] == 0.85
        assert out["query"] == "governance"

    def test_excerpt_comes_from_content(self) -> None:
        out = item_to_dict(_item(), query="q")
        assert out["excerpt"].startswith("Relevant document content")
        assert out["description"] == out["excerpt"]

    def test_timestamp_from_metadata(self) -> None:
        out = item_to_dict(_item(), query="q")
        assert out["timestamp"] == "2025-01-01T00:00:00Z"

    def test_empty_metadata_has_no_timestamp(self) -> None:
        out = item_to_dict(_item(metadata={}), query="q")
        assert out["timestamp"] == ""

    def test_title_falls_back_to_content(self) -> None:
        item = _item(title="")
        out = item_to_dict(item, query="q")
        assert out["title"] == item.content[:120]

    def test_category_falls_back_to_knowledge(self) -> None:
        item = _item(collection="")
        out = item_to_dict(item, query="q")
        assert out["category"] == "knowledge"

    def test_score_rounding(self) -> None:
        item = _item(score=0.85123)
        out = item_to_dict(item, query="q")
        assert out["score"] == 0.8512


class TestSearchCapabilities:
    """Capability reporting must only advertise genuinely available sources."""

    def test_engine_absent_reports_unavailable(self) -> None:
        caps = build_capabilities(
            None,
            knowledge_available=False,
            events_available=False,
            notifications_available=False,
        )
        assert caps["engineAvailable"] is False
        for source in caps["sources"]:
            assert source["available"] is False

    def test_knowledge_available_when_engine_has_provider(self) -> None:
        engine = EnterpriseSearchEngine()
        provider = _FakeProvider("knowledge")
        engine.register_provider(provider)
        caps = build_capabilities(
            engine,
            knowledge_available=False,
            events_available=True,
            notifications_available=False,
        )
        by_id = {s["id"]: s for s in caps["sources"]}
        assert by_id["knowledge"]["available"] is True
        assert by_id["events"]["available"] is True
        assert by_id["notifications"]["available"] is False

    def test_knowledge_available_when_engine_resolvable(self) -> None:
        caps = build_capabilities(
            None,
            knowledge_available=True,
            events_available=False,
            notifications_available=False,
        )
        by_id = {s["id"]: s for s in caps["sources"]}
        assert by_id["knowledge"]["available"] is True

    def test_source_metadata_is_static(self) -> None:
        caps = build_capabilities(None, knowledge_available=False, events_available=False, notifications_available=False)
        for source in caps["sources"]:
            assert source["label"]
            assert source["description"]


class TestSearchSuggestions:
    """Suggestions must be derived from real recent searches."""

    def test_empty_recent_yields_no_suggestions(self) -> None:
        assert suggestions_from_recent([]) == []

    def test_dedupes_repeat_queries(self) -> None:
        recent = [
            {"query": "governance", "category": "knowledge"},
            {"query": "governance", "category": "knowledge"},
            {"query": "cost", "category": "cost"},
        ]
        suggestions = suggestions_from_recent(recent)
        assert len(suggestions) == 2

    def test_ignores_blank_queries(self) -> None:
        recent = [{"query": "  ", "category": ""}, {"query": "", "category": ""}]
        assert suggestions_from_recent(recent) == []

    def test_preserves_category(self) -> None:
        suggestions = suggestions_from_recent(
            [{"query": "agent health", "category": "monitoring"}]
        )
        assert suggestions[0]["category"] == "monitoring"

    def test_does_not_fabricate_entries(self) -> None:
        assert suggestions_from_recent([{"query": "cost by model"}]) == [
            {"text": "cost by model", "category": ""}
        ]


class TestSearchQueryConstruction:
    """SearchQuery construction used by the global search endpoint."""

    def test_page_size_field_limit(self) -> None:
        from pydantic import ValidationError

        try:
            SearchQuery(query="q", page=1, page_size=0)
        except ValidationError:
            pass
        else:
            raise AssertionError("page_size=0 should be rejected")
        query = SearchQuery(query="q", page=1, page_size=150)
        assert query.page_size == 150

    def test_collection_filter_is_applied(self) -> None:
        query = SearchQuery(query="q", page=1, page_size=20)
        filtered = query.model_copy(update={"collections": ("default",)})
        assert filtered.collections == ("default",)
        assert query.collections == ()

    def test_min_score_default(self) -> None:
        query = SearchQuery(query="q", page=1, page_size=20)
        assert query.min_score == 0.0

    def test_frozen_model_supports_copy(self) -> None:
        query = SearchQuery(query="q", page=1, page_size=20)
        updated = query.model_copy(update={"page": 3})
        assert updated.page == 3


class _FakeProvider:
    name: str

    def __init__(self, name: str) -> None:
        self.name = name

    async def search(self, query: Any) -> SearchResult:  # pragma: no cover
        return SearchResult(items=(), total_count=0, page=1, page_size=20)
