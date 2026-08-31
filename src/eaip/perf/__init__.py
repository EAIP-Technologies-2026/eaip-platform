"""Performance Management — benchmark definitions, load test orchestration, regression detection."""

from __future__ import annotations

from eaip.perf.benchmarks import BenchmarkEngine
from eaip.perf.events import (
    BenchmarkCreated,
    BenchmarkRunCompleted,
    BenchmarkRunFailed,
    FalsePositiveMarked,
    LoadTestCompleted,
    LoadTestStarted,
    RegressionDetected,
    RegressionResolved,
)
from eaip.perf.exceptions import (
    BenchmarkNotFoundError,
    BenchmarkRunError,
    LoadTestError,
    PerfConfigError,
    PerfError,
    RegressionNotFoundError,
)
from eaip.perf.health import PerfHealthCheck
from eaip.perf.integration import PerfRuntimeModule
from eaip.perf.load_testing import LoadTestOrchestrator
from eaip.perf.models import (
    BenchmarkDefinition,
    BenchmarkRun,
    BenchmarkRunStatus,
    LoadTestResult,
    LoadTestScenario,
    MetricType,
    PerfConfig,
    PerformanceRegression,
    RegressionDirection,
    RegressionSeverity,
    RegressionStatus,
)
from eaip.perf.regression import RegressionDetector

__all__ = [
    "BenchmarkCreated",
    "BenchmarkDefinition",
    "BenchmarkEngine",
    "BenchmarkNotFoundError",
    "BenchmarkRun",
    "BenchmarkRunCompleted",
    "BenchmarkRunError",
    "BenchmarkRunFailed",
    "BenchmarkRunStatus",
    "FalsePositiveMarked",
    "LoadTestCompleted",
    "LoadTestError",
    "LoadTestOrchestrator",
    "LoadTestResult",
    "LoadTestScenario",
    "LoadTestStarted",
    "MetricType",
    "PerfConfig",
    "PerfConfigError",
    "PerfError",
    "PerfHealthCheck",
    "PerfRuntimeModule",
    "PerformanceRegression",
    "RegressionDetected",
    "RegressionDetector",
    "RegressionDirection",
    "RegressionNotFoundError",
    "RegressionResolved",
    "RegressionSeverity",
    "RegressionStatus",
]
