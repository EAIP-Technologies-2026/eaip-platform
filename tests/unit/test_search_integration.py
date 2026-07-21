from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from eaip.search.engine import EnterpriseSearchEngine
from eaip.search.federation import SearchFederation
from eaip.search.health import SearchHealthCheck
from eaip.search.integration import SearchRuntimeModule
from eaip.search.models import SearchQuery, SearchResultItem
from eaip.search.ranking import RankingService


class _MockProvider:
    name = "mock"

    async def search(self, query: SearchQuery) -> SearchResult:
        from eaip.search.models import SearchResult

        return SearchResult(
            items=(SearchResultItem(id="1", collection="c", content="x", score=0.9),),
            total_count=1,
        )


class TestSearchHealthCheck:
    def test_healthy_with_providers(self) -> None:
        check = SearchHealthCheck(provider_count=2)
        assert check.name == "search"
        assert check.provider_count == 2

    @pytest.mark.asyncio
    async def test_check_healthy(self) -> None:
        check = SearchHealthCheck(provider_count=3)
        report = await check.check()
        assert report.component == "search"
        assert report.status.value == "healthy"
        assert "3 provider" in report.message

    @pytest.mark.asyncio
    async def test_check_degraded(self) -> None:
        check = SearchHealthCheck(provider_count=0)
        report = await check.check()
        assert report.status.value == "degraded"
        assert "No search providers" in report.message


class TestSearchRuntimeModule:
    def test_default_initialization(self) -> None:
        mod = SearchRuntimeModule()
        assert mod.name == "search"
        assert isinstance(mod.engine, EnterpriseSearchEngine)
        assert isinstance(mod.federation, SearchFederation)
        assert isinstance(mod.ranking_service, RankingService)

    def test_custom_initialization(self) -> None:
        engine = EnterpriseSearchEngine()
        fed = SearchFederation()
        rank = RankingService(recency_weight=0.5)
        mod = SearchRuntimeModule(engine=engine, federation=fed, ranking_service=rank)
        assert mod.engine is engine
        assert mod.federation is fed
        assert mod.ranking_service is rank

    def test_startup_duration_default(self) -> None:
        mod = SearchRuntimeModule()
        assert mod.startup_duration == 0.0

    @pytest.mark.asyncio
    async def test_start_with_kernel(self) -> None:
        mod = SearchRuntimeModule()
        kernel = MagicMock()
        kernel.platform.health.register = MagicMock()
        kernel.platform.capabilities.register = MagicMock()
        await mod.start(kernel)
        assert mod.startup_duration > 0.0
        kernel.platform.health.register.assert_called_once()
        kernel.platform.capabilities.register.assert_called_once()

    @pytest.mark.asyncio
    async def test_stop(self) -> None:
        mod = SearchRuntimeModule()
        await mod.stop()
        # no exception is the assertion
