"""Agent Performance Analyzer — record, analyze, and compare agent execution performance."""

from __future__ import annotations

from eaip.agentperf.analyzer import AgentPerfAnalyzer
from eaip.agentperf.events import (
    AgentComparisonCompleted,
    BottleneckDetected,
    ExecutionRecorded,
)
from eaip.agentperf.exceptions import (
    AgentNotFoundError,
    AnalyzerError,
)
from eaip.agentperf.health import AgentPerfHealthCheck
from eaip.agentperf.integration import AgentPerfRuntimeModule
from eaip.agentperf.models import (
    AnalyzerConfig,
    BottleneckReport,
    ExecutionRecord,
    PerformanceMetrics,
)

__all__ = [
    "AgentComparisonCompleted",
    "AgentNotFoundError",
    "AgentPerfAnalyzer",
    "AgentPerfHealthCheck",
    "AgentPerfRuntimeModule",
    "AnalyzerConfig",
    "AnalyzerError",
    "BottleneckDetected",
    "BottleneckReport",
    "ExecutionRecord",
    "ExecutionRecorded",
    "PerformanceMetrics",
]
