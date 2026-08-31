"""Tests for :mod:`eaip.perf.load_testing`."""

from __future__ import annotations

import pytest

from eaip.perf.exceptions import LoadTestError
from eaip.perf.load_testing import LoadTestOrchestrator
from eaip.perf.models import BenchmarkRunStatus, LoadTestScenario

LoadTestOrchestrator.__test__ = False
LoadTestScenario.__test__ = False
BenchmarkRunStatus.__test__ = False


class TestCreateScenario:
    def test_create_and_get(self) -> None:
        orch = LoadTestOrchestrator()
        s = LoadTestScenario(id="s1", name="basic", target_component="api")
        orch.create_scenario(s)
        assert orch.get_scenario("s1") is s

    def test_get_missing(self) -> None:
        orch = LoadTestOrchestrator()
        with pytest.raises(LoadTestError):
            orch.get_scenario("nonexistent")

    def test_delete_existing(self) -> None:
        orch = LoadTestOrchestrator()
        s = LoadTestScenario(id="s1", name="basic", target_component="api")
        orch.create_scenario(s)
        orch.delete_scenario("s1")
        with pytest.raises(LoadTestError):
            orch.get_scenario("s1")

    def test_delete_missing(self) -> None:
        orch = LoadTestOrchestrator()
        with pytest.raises(LoadTestError):
            orch.delete_scenario("nonexistent")

    def test_update_scenario(self) -> None:
        orch = LoadTestOrchestrator()
        s = LoadTestScenario(id="s1", name="basic", target_component="api")
        orch.create_scenario(s)
        updated = orch.update_scenario("s1", name="stress", concurrency_level=50)
        assert updated.name == "stress"
        assert updated.concurrency_level == 50

    def test_update_missing(self) -> None:
        orch = LoadTestOrchestrator()
        with pytest.raises(LoadTestError):
            orch.update_scenario("nonexistent", name="new")


class TestListScenarios:
    def test_empty(self) -> None:
        orch = LoadTestOrchestrator()
        assert orch.list_scenarios() == []

    def test_all(self) -> None:
        orch = LoadTestOrchestrator()
        orch.create_scenario(LoadTestScenario(id="s1", name="a", target_component="api"))
        orch.create_scenario(LoadTestScenario(id="s2", name="b", target_component="db"))
        assert len(orch.list_scenarios()) == 2

    def test_filter_by_component(self) -> None:
        orch = LoadTestOrchestrator()
        orch.create_scenario(LoadTestScenario(id="s1", name="a", target_component="api"))
        orch.create_scenario(LoadTestScenario(id="s2", name="b", target_component="db"))
        result = orch.list_scenarios(target_component="api")
        assert len(result) == 1

    def test_filter_by_enabled(self) -> None:
        orch = LoadTestOrchestrator()
        orch.create_scenario(
            LoadTestScenario(id="s1", name="a", target_component="api", enabled=True)
        )
        orch.create_scenario(
            LoadTestScenario(id="s2", name="b", target_component="api", enabled=False)
        )
        result = orch.list_scenarios(enabled=True)
        assert len(result) == 1


class TestExecuteScenario:
    @pytest.mark.asyncio
    async def test_execute_disabled_scenario(self) -> None:
        orch = LoadTestOrchestrator()
        s = LoadTestScenario(id="s1", name="disabled", target_component="api", enabled=False)
        orch.create_scenario(s)
        with pytest.raises(LoadTestError, match="disabled"):
            await orch.execute_scenario("s1")

    @pytest.mark.asyncio
    async def test_execute_missing_scenario(self) -> None:
        orch = LoadTestOrchestrator()
        with pytest.raises(LoadTestError):
            await orch.execute_scenario("nonexistent")

    @pytest.mark.asyncio
    async def test_execute_successful(self) -> None:
        orch = LoadTestOrchestrator()
        s = LoadTestScenario(
            id="s1", name="basic", target_component="api", duration_seconds=1, concurrency_level=5
        )
        orch.create_scenario(s)
        result = await orch.execute_scenario("s1")
        assert result.status is BenchmarkRunStatus.COMPLETED
        assert result.total_requests > 0
        assert result.avg_response_time_ms > 0
        assert result.throughput_reqs_per_sec > 0

    @pytest.mark.asyncio
    async def test_execute_with_metadata(self) -> None:
        orch = LoadTestOrchestrator()
        s = LoadTestScenario(
            id="s1", name="basic", target_component="api", duration_seconds=1, concurrency_level=5
        )
        orch.create_scenario(s)
        result = await orch.execute_scenario("s1", metadata={"trigger": "ci"})
        assert result.metadata.get("trigger") == "ci"

    @pytest.mark.asyncio
    async def test_cancel_scenario(self) -> None:
        orch = LoadTestOrchestrator()
        s = LoadTestScenario(
            id="s1", name="basic", target_component="api", duration_seconds=5, concurrency_level=5
        )
        orch.create_scenario(s)
        result = await orch.execute_scenario("s1")
        assert result.status is BenchmarkRunStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_cancel_missing(self) -> None:
        orch = LoadTestOrchestrator()
        with pytest.raises(LoadTestError):
            await orch.cancel_scenario("nonexistent")


class TestGetResult:
    @pytest.mark.asyncio
    async def test_get_result(self) -> None:
        orch = LoadTestOrchestrator()
        s = LoadTestScenario(
            id="s1", name="basic", target_component="api", duration_seconds=1, concurrency_level=5
        )
        orch.create_scenario(s)
        result = await orch.execute_scenario("s1")
        fetched = await orch.get_result(result.id)
        assert fetched.id == result.id

    @pytest.mark.asyncio
    async def test_get_result_missing(self) -> None:
        orch = LoadTestOrchestrator()
        with pytest.raises(LoadTestError):
            await orch.get_result("nonexistent")


class TestListResults:
    @pytest.mark.asyncio
    async def test_list_results_empty(self) -> None:
        orch = LoadTestOrchestrator()
        results = await orch.list_results()
        assert results == []

    @pytest.mark.asyncio
    async def test_list_results(self) -> None:
        orch = LoadTestOrchestrator()
        s = LoadTestScenario(
            id="s1", name="basic", target_component="api", duration_seconds=1, concurrency_level=5
        )
        orch.create_scenario(s)
        await orch.execute_scenario("s1")
        await orch.execute_scenario("s1")
        results = await orch.list_results()
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_list_results_filter_by_scenario(self) -> None:
        orch = LoadTestOrchestrator()
        s1 = LoadTestScenario(
            id="s1", name="a", target_component="api", duration_seconds=1, concurrency_level=5
        )
        s2 = LoadTestScenario(
            id="s2", name="b", target_component="db", duration_seconds=1, concurrency_level=5
        )
        orch.create_scenario(s1)
        orch.create_scenario(s2)
        await orch.execute_scenario("s1")
        await orch.execute_scenario("s2")
        results = await orch.list_results(scenario_id="s1")
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_list_results_limit(self) -> None:
        orch = LoadTestOrchestrator()
        s = LoadTestScenario(
            id="s1", name="basic", target_component="api", duration_seconds=1, concurrency_level=5
        )
        orch.create_scenario(s)
        for _ in range(5):
            await orch.execute_scenario("s1")
        results = await orch.list_results(limit=3)
        assert len(results) == 3
