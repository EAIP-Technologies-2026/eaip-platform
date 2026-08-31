"""AgentPerfAnalyzer — record, analyze, and compare agent execution performance."""

from __future__ import annotations

import statistics
import uuid
from datetime import timedelta

from eaip.agentperf.events import (
    AgentComparisonCompleted,
    BottleneckDetected,
    ExecutionRecorded,
)
from eaip.agentperf.exceptions import (
    AgentNotFoundError,
)
from eaip.agentperf.models import (
    AnalyzerConfig,
    BottleneckReport,
    ExecutionRecord,
    PerformanceMetrics,
)
from eaip.logging.context import get_logger
from eaip.shared.time import utc_now


class AgentPerfAnalyzer:
    """Central service for recording and analyzing agent execution performance."""

    def __init__(self, config: AnalyzerConfig | None = None) -> None:
        self._config = config or AnalyzerConfig()
        self._records: dict[str, ExecutionRecord] = {}
        self._bottlenecks: dict[str, BottleneckReport] = {}
        self._log = get_logger("eaip.agentperf.analyzer")

    @property
    def config(self) -> AnalyzerConfig:
        return self._config

    async def record_execution(self, record: ExecutionRecord) -> ExecutionRecord:
        """Record an agent execution."""
        self._records[record.id] = record
        event = ExecutionRecorded(
            execution_id=record.id,
            agent_id=record.agent_id,
            task_type=record.task_type,
            duration_ms=record.duration_ms,
            success=record.success,
        )
        await self._check_thresholds(record)
        self._log.info(
            "agentperf.execution.recorded", execution_id=record.id, agent_id=record.agent_id
        )
        return record

    async def get_execution(self, execution_id: str) -> ExecutionRecord:
        """Retrieve an execution record by ID."""
        record = self._records.get(execution_id)
        if record is None:
            raise AgentNotFoundError(f"Execution '{execution_id}' not found")
        return record

    async def list_executions(self, agent_id: str | None = None) -> list[ExecutionRecord]:
        """List execution records, optionally filtered by agent."""
        records = list(self._records.values())
        if agent_id is not None:
            records = [r for r in records if r.agent_id == agent_id]
        return sorted(records, key=lambda r: r.timestamp, reverse=True)

    async def get_agent_metrics(self, agent_id: str) -> PerformanceMetrics:
        """Get aggregated performance metrics for an agent."""
        agent_records = [r for r in self._records.values() if r.agent_id == agent_id]
        if not agent_records:
            raise AgentNotFoundError(f"No executions found for agent '{agent_id}'")

        total = len(agent_records)
        successful = sum(1 for r in agent_records if r.success)
        failed = total - successful
        durations = [r.duration_ms for r in agent_records]
        tokens = [r.tokens_used for r in agent_records]
        sorted_durations = sorted(durations)
        p95_index = max(0, int(len(sorted_durations) * 0.95) - 1)
        p95_duration = sorted_durations[p95_index] if sorted_durations else 0.0

        now = utc_now()
        return PerformanceMetrics(
            agent_id=agent_id,
            total_executions=total,
            successful_executions=successful,
            failed_executions=failed,
            avg_duration_ms=statistics.mean(durations) if durations else 0.0,
            p95_duration_ms=p95_duration,
            total_tokens_used=sum(tokens),
            avg_tokens_per_execution=statistics.mean(tokens) if tokens else 0.0,
            success_rate=successful / total if total > 0 else 1.0,
            period_start=now - timedelta(days=30),
            period_end=now,
        )

    async def get_bottlenecks(self, agent_id: str | None = None) -> list[BottleneckReport]:
        """Get bottleneck reports, optionally filtered by agent."""
        bottlenecks = list(self._bottlenecks.values())
        if agent_id is not None:
            bottlenecks = [b for b in bottlenecks if b.agent_id == agent_id]
        return sorted(bottlenecks, key=lambda b: b.detected_at, reverse=True)

    async def get_recommendations(self, agent_id: str) -> list[str]:
        """Get performance recommendations for an agent."""
        recs: list[str] = []
        agent_records = [r for r in self._records.values() if r.agent_id == agent_id]
        if not agent_records:
            return recs

        durations = [r.duration_ms for r in agent_records]
        avg_dur = statistics.mean(durations) if durations else 0.0
        tokens = [r.tokens_used for r in agent_records]
        avg_tok = statistics.mean(tokens) if tokens else 0.0

        if avg_dur > self._config.duration_threshold_ms:
            recs.append(
                f"Average duration {avg_dur:.0f}ms exceeds threshold {self._config.duration_threshold_ms:.0f}ms"
            )
        if avg_tok > self._config.token_threshold:
            recs.append(
                f"Average token usage {avg_tok:.0f} exceeds threshold {self._config.token_threshold}"
            )
        failed = sum(1 for r in agent_records if not r.success)
        if failed > 0:
            recs.append(f"Agent has {failed} failed execution(s) — investigate failures")

        task_types = set(r.task_type for r in agent_records)
        if len(task_types) > 5:
            recs.append(
                f"Agent handles {len(task_types)} different task types — consider specialization"
            )

        return recs

    async def compare_agents(self, agent_ids: list[str]) -> dict[str, PerformanceMetrics]:
        """Compare performance metrics across multiple agents."""
        result: dict[str, PerformanceMetrics] = {}
        for agent_id in agent_ids:
            metrics = await self.get_agent_metrics(agent_id)
            result[agent_id] = metrics
        event = AgentComparisonCompleted(
            comparison_id=str(uuid.uuid4()),
            agent_ids=tuple(agent_ids),
            metric="duration_ms",
        )
        self._log.info("agentperf.comparison.completed", agents=agent_ids)
        return result

    async def get_trend(
        self, agent_id: str, metric: str = "duration_ms"
    ) -> list[dict[str, object]]:
        agent_records = [r for r in self._records.values() if r.agent_id == agent_id]
        if not agent_records:
            raise AgentNotFoundError(f"No executions found for agent '{agent_id}'")

        sorted_records = sorted(agent_records, key=lambda r: r.timestamp)
        trend: list[dict[str, object]] = []
        for record in sorted_records:
            point = {
                "timestamp": record.timestamp,
                "execution_id": record.id,
                "task_type": record.task_type,
            }
            if metric == "duration_ms":
                point["value"] = record.duration_ms
            elif metric == "tokens_used":
                point["value"] = record.tokens_used
            elif metric == "success":
                point["value"] = 1.0 if record.success else 0.0
            else:
                point["value"] = record.duration_ms
            trend.append(point)
        return trend

    async def _check_thresholds(self, record: ExecutionRecord) -> None:
        """Check if an execution record exceeds configured thresholds."""
        alerts: list[str] = []
        if record.duration_ms > self._config.duration_threshold_ms:
            alerts.append("duration")
        if record.tokens_used > self._config.token_threshold:
            alerts.append("tokens")

        for alert in alerts:
            report_id = str(uuid.uuid4())
            threshold = (
                self._config.duration_threshold_ms
                if alert == "duration"
                else float(self._config.token_threshold)
            )
            actual = record.duration_ms if alert == "duration" else float(record.tokens_used)
            recommendation = (
                f"Reduce execution duration below {threshold:.0f}ms"
                if alert == "duration"
                else f"Reduce token usage below {int(threshold)}"
            )
            report = BottleneckReport(
                id=report_id,
                agent_id=record.agent_id,
                metric=alert,
                threshold=threshold,
                actual_value=actual,
                recommendation=recommendation,
            )
            self._bottlenecks[report_id] = report
            event = BottleneckDetected(
                report_id=report_id,
                agent_id=record.agent_id,
                metric=alert,
                actual_value=actual,
                threshold=threshold,
            )
            self._log.warning(
                "agentperf.bottleneck.detected", agent_id=record.agent_id, metric=alert
            )


__all__ = ["AgentPerfAnalyzer"]
