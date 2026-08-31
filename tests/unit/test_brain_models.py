"""Tests for Enterprise Brain models."""

from __future__ import annotations

from eaip.brain.models import BrainQuery, BrainResult, BrainSource, EnterpriseBrainConfig


class TestBrainQuery:
    def test_defaults(self) -> None:
        q = BrainQuery(query="test query")
        assert q.query == "test query"
        assert q.top_k == 10
        assert q.score_threshold == 0.0
        assert q.include_knowledge is True
        assert q.include_memory is True
        assert q.include_context is True
        assert q.filters == {}
        assert q.max_tokens == 4096
        assert q.collection_names == ()

    def test_with_all_fields(self) -> None:
        q = BrainQuery(
            query="specific query",
            top_k=5,
            score_threshold=0.5,
            include_knowledge=False,
            include_memory=True,
            include_context=False,
            filters={"department": "engineering"},
            max_tokens=2048,
            collection_names=("docs", "wiki"),
        )
        assert q.top_k == 5
        assert q.score_threshold == 0.5
        assert q.include_knowledge is False
        assert q.filters["department"] == "engineering"
        assert q.collection_names == ("docs", "wiki")

    def test_frozen(self) -> None:
        q = BrainQuery(query="test")
        try:
            q.query = "changed"
            raise AssertionError("should be frozen")
        except (ValueError, TypeError):
            pass

    def test_extra_forbidden(self) -> None:
        try:
            BrainQuery(query="test", unknown_field="x")
            raise AssertionError("should forbid extra")
        except (ValueError, TypeError):
            pass


class TestBrainSource:
    def test_defaults(self) -> None:
        s = BrainSource(source_type="knowledge", source_id="s1", content_preview="preview")
        assert s.source_type == "knowledge"
        assert s.source_id == "s1"
        assert s.content_preview == "preview"
        assert s.relevance_score == 0.0
        assert s.collection == ""

    def test_with_all_fields(self) -> None:
        s = BrainSource(
            source_type="memory",
            source_id="mem1",
            content_preview="memory content",
            relevance_score=0.95,
            collection="user_scoped",
        )
        assert s.relevance_score == 0.95
        assert s.collection == "user_scoped"

    def test_frozen(self) -> None:
        s = BrainSource(source_type="knowledge", source_id="s1", content_preview="x")
        try:
            s.source_type = "memory"
            raise AssertionError("should be frozen")
        except (ValueError, TypeError):
            pass


class TestBrainResult:
    def test_defaults(self) -> None:
        r = BrainResult(query="test query")
        assert r.query == "test query"
        assert r.answer == ""
        assert r.confidence == 0.0
        assert r.sources == ()
        assert r.duration_ms == 0.0
        assert r.token_count == 0

    def test_with_sources(self) -> None:
        sources = (
            BrainSource(
                source_type="knowledge", source_id="k1", content_preview="c1", relevance_score=0.9
            ),
            BrainSource(
                source_type="memory", source_id="m1", content_preview="c2", relevance_score=0.8
            ),
        )
        r = BrainResult(
            query="q1",
            answer="combined answer",
            confidence=0.85,
            sources=sources,
            duration_ms=150.0,
            token_count=42,
        )
        assert r.answer == "combined answer"
        assert r.confidence == 0.85
        assert len(r.sources) == 2
        assert r.sources[0].source_type == "knowledge"
        assert r.duration_ms == 150.0
        assert r.token_count == 42

    def test_frozen(self) -> None:
        r = BrainResult(query="test")
        try:
            r.query = "changed"
            raise AssertionError("should be frozen")
        except (ValueError, TypeError):
            pass


class TestEnterpriseBrainConfig:
    def test_defaults(self) -> None:
        c = EnterpriseBrainConfig()
        assert c.default_top_k == 10
        assert c.enable_caching is True
        assert c.cache_ttl_seconds == 300
        assert c.max_tokens_per_source == 2000
        assert c.enable_reranking is True

    def test_custom_config(self) -> None:
        c = EnterpriseBrainConfig(
            default_top_k=5,
            enable_caching=False,
            cache_ttl_seconds=600,
            max_tokens_per_source=1000,
            enable_reranking=False,
        )
        assert c.default_top_k == 5
        assert c.enable_caching is False
        assert c.cache_ttl_seconds == 600
        assert c.max_tokens_per_source == 1000
        assert c.enable_reranking is False
