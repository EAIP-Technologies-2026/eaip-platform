"""Tests for :mod:`eaip.agentperf.analyzer`."""

from __future__ import annotations

import pytest

from eaip.agentperf.analyzer import AgentPerfAnalyzer
from eaip.agentperf.exceptions import AgentNotFoundError
from eaip.agentperf.models import AnalyzerConfig, ExecutionRecord


class TestAgentPerfAnalyzer:
    @pytest.fixture
    def analyzer(self) -> AgentPerfAnalyzer:
        return AgentPerfAnalyzer()

    @pytest.fixture
    def sample_record(self) -> ExecutionRecord:
        return ExecutionRecord(
            id="exec1",
            agent_id="agent1",
            task_type="reasoning",
            duration_ms=1500.0,
            tokens_used=1024,
            success=True,
        )

    class TestRecordExecution:
        async def test_record(
            self, analyzer: AgentPerfAnalyzer, sample_record: ExecutionRecord
        ) -> None:
            result = await analyzer.record_execution(sample_record)
            assert result.id == "exec1"
            assert result.agent_id == "agent1"

        async def test_list_executions(
            self, analyzer: AgentPerfAnalyzer, sample_record: ExecutionRecord
        ) -> None:
            await analyzer.record_execution(sample_record)
            records = await analyzer.list_executions()
            assert len(records) == 1

        async def test_list_executions_filtered_by_agent(
            self, analyzer: AgentPerfAnalyzer, sample_record: ExecutionRecord
        ) -> None:
            await analyzer.record_execution(sample_record)
            records = await analyzer.list_executions(agent_id="agent1")
            assert len(records) == 1
            records = await analyzer.list_executions(agent_id="nonexistent")
            assert len(records) == 0

    class TestGetExecution:
        async def test_get(
            self, analyzer: AgentPerfAnalyzer, sample_record: ExecutionRecord
        ) -> None:
            await analyzer.record_execution(sample_record)
            record = await analyzer.get_execution("exec1")
            assert record.task_type == "reasoning"

        async def test_not_found(self, analyzer: AgentPerfAnalyzer) -> None:
            with pytest.raises(AgentNotFoundError):
                await analyzer.get_execution("nonexistent")

    class TestGetAgentMetrics:
        async def test_metrics(
            self, analyzer: AgentPerfAnalyzer, sample_record: ExecutionRecord
        ) -> None:
            await analyzer.record_execution(sample_record)
            metrics = await analyzer.get_agent_metrics("agent1")
            assert metrics.agent_id == "agent1"
            assert metrics.total_executions == 1
            assert metrics.successful_executions == 1
            assert metrics.avg_duration_ms == 1500.0

        async def test_metrics_not_found(self, analyzer: AgentPerfAnalyzer) -> None:
            with pytest.raises(AgentNotFoundError):
                await analyzer.get_agent_metrics("nonexistent")

    class TestBottlenecks:
        async def test_bottleneck_detected(self, analyzer: AgentPerfAnalyzer) -> None:
            record = ExecutionRecord(
                id="exec1",
                agent_id="agent1",
                task_type="reasoning",
                duration_ms=10000.0,
                tokens_used=9000,
                success=True,
            )
            await analyzer.record_execution(record)
            bottlenecks = await analyzer.get_bottlenecks("agent1")
            assert len(bottlenecks) >= 1

        async def test_no_bottlenecks(
            self, analyzer: AgentPerfAnalyzer, sample_record: ExecutionRecord
        ) -> None:
            await analyzer.record_execution(sample_record)
            bottlenecks = await analyzer.get_bottlenecks("agent1")
            assert len(bottlenecks) == 0

    class TestRecommendations:
        async def test_recommendations(self, analyzer: AgentPerfAnalyzer) -> None:
            record = ExecutionRecord(
                id="exec1",
                agent_id="agent1",
                task_type="reasoning",
                duration_ms=10000.0,
                tokens_used=9000,
                success=False,
            )
            await analyzer.record_execution(record)
            recs = await analyzer.get_recommendations("agent1")
            assert len(recs) > 0

        async def test_no_recommendations(
            self, analyzer: AgentPerfAnalyzer, sample_record: ExecutionRecord
        ) -> None:
            await analyzer.record_execution(sample_record)
            recs = await analyzer.get_recommendations("agent1")
            assert len(recs) == 0

    class TestCompareAgents:
        async def test_compare(self, analyzer: AgentPerfAnalyzer) -> None:
            r1 = ExecutionRecord(
                id="e1", agent_id="agent1", task_type="t1", duration_ms=100.0, tokens_used=10
            )
            r2 = ExecutionRecord(
                id="e2", agent_id="agent2", task_type="t1", duration_ms=200.0, tokens_used=20
            )
            await analyzer.record_execution(r1)
            await analyzer.record_execution(r2)
            result = await analyzer.compare_agents(["agent1", "agent2"])
            assert len(result) == 2
            assert result["agent1"].avg_duration_ms == 100.0

    class TestTrend:
        async def test_trend(
            self, analyzer: AgentPerfAnalyzer, sample_record: ExecutionRecord
        ) -> None:
            await analyzer.record_execution(sample_record)
            trend = await analyzer.get_trend("agent1")
            assert len(trend) == 1
            assert trend[0]["value"] == 1500.0

        async def test_trend_not_found(self, analyzer: AgentPerfAnalyzer) -> None:
            with pytest.raises(AgentNotFoundError):
                await analyzer.get_trend("nonexistent")

    class TestConfig:
        def test_default_config(self) -> None:
            a = AgentPerfAnalyzer()
            assert a.config.duration_threshold_ms == 5000.0
            assert a.config.token_threshold == 4096

        def test_custom_config(self) -> None:
            config = AnalyzerConfig(duration_threshold_ms=3000.0, token_threshold=2048)
            a = AgentPerfAnalyzer(config=config)
            assert a.config.duration_threshold_ms == 3000.0
            assert a.config.token_threshold == 2048
