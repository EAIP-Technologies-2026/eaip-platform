from __future__ import annotations

import anyio
import pytest

from eaip.searchidx.exceptions import IndexBuildError, IndexNotFoundError
from eaip.searchidx.index_manager import IndexManager
from eaip.searchidx.models import IndexField, SearchIndex


class _Fixture:
    def __init__(self) -> None:
        self.mgr = IndexManager()
        self.idx = SearchIndex(
            id="idx1",
            name="articles",
            source_type="documents",
            fields=(
                IndexField(name="title", type="text"),
                IndexField(name="body", type="text"),
            ),
        )
        self.mgr.create(self.idx)


@pytest.fixture
def fixture() -> _Fixture:
    return _Fixture()


class TestIndexManager:
    def test_create(self, fixture: _Fixture) -> None:
        assert fixture.mgr.get("idx1") is fixture.idx

    def test_get_returns_none(self, fixture: _Fixture) -> None:
        assert fixture.mgr.get("unknown") is None

    def test_get_index(self, fixture: _Fixture) -> None:
        assert fixture.mgr.get_index("idx1") is fixture.idx

    def test_get_index_not_found(self, fixture: _Fixture) -> None:
        with pytest.raises(IndexNotFoundError):
            fixture.mgr.get_index("unknown")

    def test_update(self, fixture: _Fixture) -> None:
        updated = fixture.mgr.update("idx1", name="updated", document_count=50)
        assert updated.name == "updated"
        assert updated.document_count == 50

    def test_update_not_found(self, fixture: _Fixture) -> None:
        with pytest.raises(IndexNotFoundError):
            fixture.mgr.update("unknown", name="x")

    def test_delete(self, fixture: _Fixture) -> None:
        result = fixture.mgr.delete("idx1")
        assert result.id == "idx1"
        assert fixture.mgr.get("idx1") is None

    def test_delete_not_found(self, fixture: _Fixture) -> None:
        with pytest.raises(IndexNotFoundError):
            fixture.mgr.delete("unknown")

    def test_list_indices_empty(self) -> None:
        mgr = IndexManager()
        assert mgr.list_indices() == []

    def test_list_indices(self, fixture: _Fixture) -> None:
        assert len(fixture.mgr.list_indices()) == 1

    @pytest.mark.asyncio
    async def test_build_index(self, fixture: _Fixture) -> None:
        job = await fixture.mgr.build_index("idx1")
        assert job.status == "completed"
        assert job.type == "full"
        idx = fixture.mgr.get_index("idx1")
        assert idx.status == "ready"

    @pytest.mark.asyncio
    async def test_build_index_not_found(self, fixture: _Fixture) -> None:
        with pytest.raises(IndexNotFoundError):
            await fixture.mgr.build_index("unknown")

    @pytest.mark.asyncio
    async def test_incremental_index(self, fixture: _Fixture) -> None:
        await fixture.mgr.build_index("idx1")
        job = await fixture.mgr.incremental_index("idx1")
        assert job.status == "completed"
        assert job.type == "incremental"

    @pytest.mark.asyncio
    async def test_incremental_index_not_ready(self, fixture: _Fixture) -> None:
        with pytest.raises(IndexBuildError):
            await fixture.mgr.incremental_index("idx1")

    @pytest.mark.asyncio
    async def test_incremental_index_not_found(self, fixture: _Fixture) -> None:
        with pytest.raises(IndexNotFoundError):
            await fixture.mgr.incremental_index("unknown")

    @pytest.mark.asyncio
    async def test_get_index_status(self, fixture: _Fixture) -> None:
        status = await fixture.mgr.get_index_status("idx1")
        assert status["id"] == "idx1"
        assert status["name"] == "articles"
        assert "total_jobs" in status

    @pytest.mark.asyncio
    async def test_get_index_status_not_found(self, fixture: _Fixture) -> None:
        with pytest.raises(IndexNotFoundError):
            await fixture.mgr.get_index_status("unknown")

    @pytest.mark.asyncio
    async def test_search_index(self, fixture: _Fixture) -> None:
        await fixture.mgr.build_index("idx1")
        results = await fixture.mgr.search_index("idx1", "test query")
        assert len(results) >= 1

    @pytest.mark.asyncio
    async def test_search_index_not_ready(self, fixture: _Fixture) -> None:
        idx2 = SearchIndex(id="idx2", name="pending", source_type="docs")
        fixture.mgr.create(idx2)
        with pytest.raises(IndexBuildError):
            await fixture.mgr.search_index("idx2", "test")

    @pytest.mark.asyncio
    async def test_search_index_not_found(self, fixture: _Fixture) -> None:
        with pytest.raises(IndexNotFoundError):
            await fixture.mgr.search_index("unknown", "test")

    @pytest.mark.asyncio
    async def test_suggest(self, fixture: _Fixture) -> None:
        await fixture.mgr.build_index("idx1")
        suggestions = await fixture.mgr.suggest("idx1", "ti")
        assert "title" in suggestions

    @pytest.mark.asyncio
    async def test_suggest_not_ready(self, fixture: _Fixture) -> None:
        idx2 = SearchIndex(id="idx2", name="pending", source_type="docs")
        fixture.mgr.create(idx2)
        with pytest.raises(IndexBuildError):
            await fixture.mgr.suggest("idx2", "ti")

    @pytest.mark.asyncio
    async def test_suggest_not_found(self, fixture: _Fixture) -> None:
        with pytest.raises(IndexNotFoundError):
            await fixture.mgr.suggest("unknown", "ti")

    def test_delete_removes_jobs(self, fixture: _Fixture) -> None:
        anyio.run(fixture.mgr.build_index, "idx1")
        fixture.mgr.delete("idx1")
        assert fixture.mgr.get("idx1") is None
