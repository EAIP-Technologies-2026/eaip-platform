from __future__ import annotations

import pydantic
import pytest

from eaip.searchidx.models import (
    CachePolicy,
    IndexField,
    IndexJob,
    SearchCacheConfig,
    SearchIndex,
)


class TestIndexField:
    def test_defaults(self) -> None:
        f = IndexField(name="title", type="text")
        assert f.name == "title"
        assert f.type == "text"
        assert f.searchable is True
        assert f.filterable is False
        assert f.sortable is False
        assert f.boost == 1.0
        assert f.analyzer == "standard"

    def test_frozen(self) -> None:
        f = IndexField(name="x", type="text")
        with pytest.raises(pydantic.ValidationError):
            f.name = "y"  # type: ignore[misc]

    def test_extra_forbidden(self) -> None:
        with pytest.raises(pydantic.ValidationError):
            IndexField(name="x", type="text", unknown="x")  # type: ignore[call-arg]

    def test_invalid_type(self) -> None:
        with pytest.raises(pydantic.ValidationError):
            IndexField(name="x", type="json")

    def test_all_types(self) -> None:
        for t in ("text", "keyword", "integer", "float", "date", "boolean"):
            f = IndexField(name="x", type=t)
            assert f.type == t

    def test_boost_range(self) -> None:
        f = IndexField(name="x", type="text", boost=2.5)
        assert f.boost == 2.5
        with pytest.raises(pydantic.ValidationError):
            IndexField(name="x", type="text", boost=-1.0)

    def test_custom_analyzer(self) -> None:
        f = IndexField(name="x", type="text", analyzer="english")
        assert f.analyzer == "english"


class TestSearchIndex:
    def test_defaults(self) -> None:
        idx = SearchIndex(id="idx1", name="articles", source_type="documents")
        assert idx.id == "idx1"
        assert idx.status == "building"
        assert idx.document_count == 0
        assert idx.fields == ()
        assert idx.last_built_at is None
        assert idx.metadata == {}

    def test_frozen(self) -> None:
        idx = SearchIndex(id="idx1", name="articles", source_type="docs")
        with pytest.raises(pydantic.ValidationError):
            idx.status = "ready"  # type: ignore[misc]

    def test_extra_forbidden(self) -> None:
        with pytest.raises(pydantic.ValidationError):
            SearchIndex(id="idx1", name="articles", source_type="docs", unknown="x")  # type: ignore[call-arg]

    def test_invalid_status(self) -> None:
        with pytest.raises(pydantic.ValidationError):
            SearchIndex(id="idx1", name="x", source_type="x", status="unknown")

    def test_with_fields(self) -> None:
        fields = (IndexField(name="title", type="text"), IndexField(name="age", type="integer"))
        idx = SearchIndex(
            id="idx1",
            name="users",
            source_type="db",
            fields=fields,
            status="ready",
            document_count=100,
        )
        assert len(idx.fields) == 2
        assert idx.status == "ready"
        assert idx.document_count == 100


class TestIndexJob:
    def test_defaults(self) -> None:
        job = IndexJob(id="j1", index_id="idx1", type="full")
        assert job.id == "j1"
        assert job.status == "pending"
        assert job.documents_processed == 0
        assert job.started_at is None
        assert job.completed_at is None
        assert job.error is None

    def test_frozen(self) -> None:
        job = IndexJob(id="j1", index_id="idx1", type="full")
        with pytest.raises(pydantic.ValidationError):
            job.status = "running"  # type: ignore[misc]

    def test_extra_forbidden(self) -> None:
        with pytest.raises(pydantic.ValidationError):
            IndexJob(id="j1", index_id="idx1", type="full", unknown="x")  # type: ignore[call-arg]

    def test_invalid_status(self) -> None:
        with pytest.raises(pydantic.ValidationError):
            IndexJob(id="j1", index_id="idx1", type="full", status="unknown")

    def test_invalid_type(self) -> None:
        with pytest.raises(pydantic.ValidationError):
            IndexJob(id="j1", index_id="idx1", type="hybrid")

    def test_failed_job(self) -> None:
        job = IndexJob(id="j1", index_id="idx1", type="full", status="failed", error="timeout")
        assert job.error == "timeout"


class TestCachePolicy:
    def test_defaults(self) -> None:
        p = CachePolicy(id="cp1", name="default", key_pattern="*")
        assert p.ttl_seconds == 300
        assert p.warm_on_start is False
        assert p.invalidation_events == ()
        assert p.metadata == {}

    def test_frozen(self) -> None:
        p = CachePolicy(id="cp1", name="default", key_pattern="*")
        with pytest.raises(pydantic.ValidationError):
            p.ttl_seconds = 600  # type: ignore[misc]

    def test_extra_forbidden(self) -> None:
        with pytest.raises(pydantic.ValidationError):
            CachePolicy(id="cp1", name="default", key_pattern="*", unknown="x")  # type: ignore[call-arg]

    def test_range_validation(self) -> None:
        with pytest.raises(pydantic.ValidationError):
            CachePolicy(id="cp1", name="default", key_pattern="*", ttl_seconds=0)

    def test_with_events(self) -> None:
        p = CachePolicy(
            id="cp1", name="default", key_pattern="idx:*", invalidation_events=("index.updated",)
        )
        assert p.invalidation_events == ("index.updated",)


class TestSearchCacheConfig:
    def test_defaults(self) -> None:
        cfg = SearchCacheConfig()
        assert cfg.enable_cache is True
        assert cfg.default_ttl_seconds == 300
        assert cfg.max_cache_size == 10000
        assert cfg.enable_warming is True
        assert cfg.warming_interval_seconds == 60

    def test_frozen(self) -> None:
        cfg = SearchCacheConfig()
        with pytest.raises(pydantic.ValidationError):
            cfg.enable_cache = False  # type: ignore[misc]

    def test_extra_forbidden(self) -> None:
        with pytest.raises(pydantic.ValidationError):
            SearchCacheConfig(unknown="x")  # type: ignore[call-arg]

    def test_range_validation(self) -> None:
        with pytest.raises(pydantic.ValidationError):
            SearchCacheConfig(default_ttl_seconds=0)
