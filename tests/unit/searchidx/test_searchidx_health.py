from __future__ import annotations

import anyio
import pytest

from eaip.searchidx.health import SearchIndexHealthCheck


class TestSearchidxHealth:
    @pytest.mark.asyncio
    async def test_healthy(self) -> None:
        check = SearchIndexHealthCheck(index_count=5, ready_indices=3, cache_available=True)
        report = await check.check()
        assert report.component == "searchidx"
        assert report.status.value == "healthy"
        assert "3/5" in report.message

    @pytest.mark.asyncio
    async def test_degraded_no_indices(self) -> None:
        check = SearchIndexHealthCheck(index_count=0, ready_indices=0, cache_available=True)
        report = await check.check()
        assert report.status.value == "degraded"
        assert "No indices" in report.message

    @pytest.mark.asyncio
    async def test_degraded_cache_unavailable(self) -> None:
        check = SearchIndexHealthCheck(index_count=5, ready_indices=3, cache_available=False)
        report = await check.check()
        assert report.status.value == "degraded"
        assert "unavailable" in report.message

    def test_name(self) -> None:
        check = SearchIndexHealthCheck()
        assert check.name == "searchidx"

    def test_properties(self) -> None:
        check = SearchIndexHealthCheck(index_count=10, ready_indices=8, cache_available=True)
        assert check.index_count == 10
        assert check.ready_indices == 8
        assert check.cache_available is True

    def test_defaults(self) -> None:
        check = SearchIndexHealthCheck()
        assert check.index_count == 0
        assert check.ready_indices == 0
        assert check.cache_available is True

    def test_details_in_report(self) -> None:
        check = SearchIndexHealthCheck(index_count=3, ready_indices=2, cache_available=True)
        report = anyio.run(check.check)
        assert report.details["index_count"] == 3
        assert report.details["ready_indices"] == 2
        assert report.details["cache_available"] is True
