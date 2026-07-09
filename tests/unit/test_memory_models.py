"""Tests for Memory Engine domain models."""

from __future__ import annotations

from datetime import datetime, timezone

from eaip.memory.models import (
    ConsolidationConfig,
    ConsolidationReport,
    IndexingConfig,
    MemoryConfig,
    MemoryItem,
    MemoryQuery,
    MemoryRelation,
    MemoryResult,
    MemoryScope,
    MemorySearchResult,
    MemoryStatus,
    MemoryType,
    RetentionConfig,
    ScopedMemoryId,
)


def _scope(tenant: str = "t1", user: str | None = "u1") -> MemoryScope:
    return MemoryScope(tenant_id=tenant, user_id=user)


class TestMemoryType:
    def test_values(self) -> None:
        assert MemoryType.WORKING.value == "working"
        assert MemoryType.SESSION.value == "session"
        assert MemoryType.LONG_TERM.value == "long_term"
        assert MemoryType.EPISODIC.value == "episodic"
        assert MemoryType.SEMANTIC.value == "semantic"

    def test_str_enum(self) -> None:
        assert str(MemoryType.WORKING) == "working"


class TestMemoryStatus:
    def test_values(self) -> None:
        assert MemoryStatus.ACTIVE.value == "active"
        assert MemoryStatus.ARCHIVED.value == "archived"
        assert MemoryStatus.EXPIRED.value == "expired"
        assert MemoryStatus.CONSOLIDATED.value == "consolidated"


class TestMemoryScope:
    def test_defaults(self) -> None:
        scope = MemoryScope(tenant_id="t1")
        assert scope.tenant_id == "t1"
        assert scope.user_id is None
        assert scope.session_id is None
        assert scope.application_id is None

    def test_scope_key_tenant_only(self) -> None:
        scope = MemoryScope(tenant_id="t1")
        assert scope.scope_key() == "t1"

    def test_scope_key_with_user(self) -> None:
        scope = MemoryScope(tenant_id="t1", user_id="u1")
        assert scope.scope_key() == "t1:u1"

    def test_scope_key_full(self) -> None:
        scope = MemoryScope(tenant_id="t1", user_id="u1", session_id="s1", application_id="a1")
        assert scope.scope_key() == "t1:u1:s1:a1"

    def test_frozen(self) -> None:
        scope = MemoryScope(tenant_id="t1")
        try:
            scope.tenant_id = "t2"
            assert False, "should be frozen"
        except (TypeError, AttributeError, ValueError):
            pass

    def test_extra_forbidden(self) -> None:
        try:
            MemoryScope(tenant_id="t1", unknown="x")
            assert False, "should reject extra fields"
        except (ValueError, TypeError):
            pass


class TestScopedMemoryId:
    def test_fully_qualified(self) -> None:
        scope = MemoryScope(tenant_id="t1", user_id="u1")
        smid = ScopedMemoryId(memory_id="m1", scope=scope)
        assert smid.fully_qualified() == "t1:u1:m1"

    def test_fully_qualified_tenant_only(self) -> None:
        scope = MemoryScope(tenant_id="t1")
        smid = ScopedMemoryId(memory_id="m1", scope=scope)
        assert smid.fully_qualified() == "t1:m1"


class TestMemoryItem:
    def test_defaults(self) -> None:
        scope = MemoryScope(tenant_id="t1")
        item = MemoryItem(memory_id="m1", memory_type=MemoryType.WORKING, scope=scope, content="hello")
        assert item.memory_id == "m1"
        assert item.memory_type is MemoryType.WORKING
        assert item.content == "hello"
        assert item.importance == 0.5
        assert item.status is MemoryStatus.ACTIVE
        assert item.version == 1
        assert item.access_count == 0
        assert item.embedding == ()
        assert isinstance(item.created_at, datetime)

    def test_default_importance(self) -> None:
        scope = MemoryScope(tenant_id="t1")
        item = MemoryItem(memory_id="m1", memory_type=MemoryType.SESSION, scope=scope, content="x")
        assert item.importance == 0.5

    def test_importance_range_rejected(self) -> None:
        scope = MemoryScope(tenant_id="t1")
        try:
            MemoryItem(memory_id="m1", memory_type=MemoryType.SESSION, scope=scope, content="x", importance=1.5)
            assert False, "should raise"
        except (ValueError, TypeError):
            pass

    def test_content_summary_default(self) -> None:
        scope = MemoryScope(tenant_id="t1")
        item = MemoryItem(memory_id="m1", memory_type=MemoryType.LONG_TERM, scope=scope, content="long content")
        assert item.content_summary == ""

    def test_expires_at(self) -> None:
        scope = MemoryScope(tenant_id="t1")
        dt = datetime(2026, 12, 31, tzinfo=timezone.utc)
        item = MemoryItem(
            memory_id="m1", memory_type=MemoryType.EPISODIC, scope=scope,
            content="episodic", expires_at=dt,
        )
        assert item.expires_at == dt

    def test_frozen(self) -> None:
        scope = MemoryScope(tenant_id="t1")
        item = MemoryItem(memory_id="m1", memory_type=MemoryType.WORKING, scope=scope, content="x")
        try:
            item.content = "y"
            assert False, "should be frozen"
        except (TypeError, AttributeError, ValueError):
            pass


class TestMemoryRelation:
    def test_defaults(self) -> None:
        rel = MemoryRelation(source_id="m1", target_id="m2", relation_type="references")
        assert rel.source_id == "m1"
        assert rel.target_id == "m2"
        assert rel.relation_type == "references"
        assert rel.weight == 1.0
        assert rel.metadata == {}

    def test_with_weight(self) -> None:
        rel = MemoryRelation(source_id="m1", target_id="m2", relation_type="derives", weight=0.8)
        assert rel.weight == 0.8


class TestMemoryQuery:
    def test_defaults(self) -> None:
        q = MemoryQuery(query="test")
        assert q.query == "test"
        assert q.top_k == 10
        assert q.score_threshold == 0.0
        assert q.offset == 0
        assert q.limit == 100
        assert not q.include_embeddings

    def test_with_filters(self) -> None:
        q = MemoryQuery(
            query="search", memory_types=(MemoryType.WORKING,),
            tags=("important",), top_k=5,
        )
        assert q.memory_types == (MemoryType.WORKING,)
        assert q.tags == ("important",)
        assert q.top_k == 5


class TestMemorySearchResult:
    def test_defaults(self) -> None:
        scope = MemoryScope(tenant_id="t1")
        item = MemoryItem(memory_id="m1", memory_type=MemoryType.WORKING, scope=scope, content="x")
        sr = MemorySearchResult(memory=item)
        assert sr.score == 0.0
        assert sr.relations == ()

    def test_with_score_and_relations(self) -> None:
        scope = MemoryScope(tenant_id="t1")
        item = MemoryItem(memory_id="m1", memory_type=MemoryType.WORKING, scope=scope, content="x")
        rel = MemoryRelation(source_id="m1", target_id="m2", relation_type="ref")
        sr = MemorySearchResult(memory=item, score=0.95, relations=(rel,))
        assert sr.score == 0.95
        assert len(sr.relations) == 1


class TestMemoryResult:
    def test_defaults(self) -> None:
        mr = MemoryResult(query="test")
        assert mr.query == "test"
        assert mr.results == ()
        assert mr.total_count == 0
        assert mr.duration_ms == 0.0

    def test_with_results(self) -> None:
        scope = MemoryScope(tenant_id="t1")
        item = MemoryItem(memory_id="m1", memory_type=MemoryType.WORKING, scope=scope, content="x")
        sr = MemorySearchResult(memory=item, score=0.9)
        mr = MemoryResult(query="q", results=(sr,), total_count=1, duration_ms=1.5)
        assert mr.total_count == 1
        assert mr.duration_ms == 1.5
        assert len(mr.results) == 1


class TestMemoryConfig:
    def test_defaults(self) -> None:
        cfg = MemoryConfig()
        assert cfg.default_importance == 0.5
        assert cfg.max_working_memories == 50
        assert cfg.enable_expiration is True
        assert cfg.enable_versioning is True

    def test_custom(self) -> None:
        cfg = MemoryConfig(default_importance=0.8, enable_expiration=False)
        assert cfg.default_importance == 0.8
        assert cfg.enable_expiration is False


class TestIndexingConfig:
    def test_defaults(self) -> None:
        cfg = IndexingConfig()
        assert cfg.index_content is True
        assert cfg.embedding_dimensions == 384
        assert cfg.batch_size == 32


class TestRetentionConfig:
    def test_defaults(self) -> None:
        cfg = RetentionConfig()
        assert cfg.working_ttl_seconds == 3600
        assert cfg.session_ttl_seconds == 86400
        assert cfg.semantic_ttl_seconds == 0
        assert cfg.archive_on_expire is True


class TestConsolidationConfig:
    def test_defaults(self) -> None:
        cfg = ConsolidationConfig()
        assert cfg.min_memories_for_consolidation == 5
        assert cfg.consolidation_interval_seconds == 86400
        assert cfg.enable_deduplication is True


class TestConsolidationReport:
    def test_defaults(self) -> None:
        r = ConsolidationReport()
        assert r.source_count == 0
        assert r.consolidated_count == 0
        assert r.removed_count == 0
        assert r.details == {}

    def test_with_values(self) -> None:
        r = ConsolidationReport(source_count=10, consolidated_count=3, duration_ms=5.0)
        assert r.source_count == 10
        assert r.consolidated_count == 3
        assert r.duration_ms == 5.0
