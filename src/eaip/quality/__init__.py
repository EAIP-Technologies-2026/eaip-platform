"""Quality & Testing Framework — test management, execution, gates, coverage, regression."""

from __future__ import annotations

from eaip.quality.coverage import CoverageAnalyzer
from eaip.quality.engine import TestEngine
from eaip.quality.events import (
    CoverageReported,
    QualityGateEvaluated,
    QualityGateFailed,
    QualityGatePassed,
    RegressionCleared,
    RegressionDetected,
    SuiteRegistered,
    TestCaseRegistered,
    TestCaseUnregistered,
    TestExecutionCompleted,
    TestExecutionFailed,
    TestExecutionStarted,
)
from eaip.quality.exceptions import (
    CoverageError,
    QualityError,
    QualityGateError,
    RegressionDetectionError,
    SuiteNotFoundError,
    TestCaseNotFoundError,
    TestExecutionError,
)
from eaip.quality.gates import QualityGateService
from eaip.quality.health import QualityHealthCheck
from eaip.quality.integration import QualityRuntimeModule
from eaip.quality.models import (
    CoverageReport,
    PerformanceBenchmark,
    QualityCondition,
    QualityConfig,
    QualityGate,
    QualityGateStatus,
    RegressionChange,
    RegressionResult,
    TestCase,
    TestCaseStatus,
    TestCaseType,
    TestExecution,
    TestExecutionStatus,
    TestSuite,
)

__all__ = [
    "CoverageAnalyzer",
    "CoverageError",
    "CoverageReport",
    "CoverageReported",
    "PerformanceBenchmark",
    "QualityCondition",
    "QualityConfig",
    "QualityError",
    "QualityGate",
    "QualityGateError",
    "QualityGateEvaluated",
    "QualityGateFailed",
    "QualityGatePassed",
    "QualityGateService",
    "QualityGateStatus",
    "QualityHealthCheck",
    "QualityRuntimeModule",
    "RegressionChange",
    "RegressionCleared",
    "RegressionDetected",
    "RegressionDetectionError",
    "RegressionResult",
    "SuiteNotFoundError",
    "SuiteRegistered",
    "TestCase",
    "TestCaseNotFoundError",
    "TestCaseRegistered",
    "TestCaseStatus",
    "TestCaseType",
    "TestCaseUnregistered",
    "TestEngine",
    "TestExecution",
    "TestExecutionCompleted",
    "TestExecutionError",
    "TestExecutionFailed",
    "TestExecutionStarted",
    "TestExecutionStatus",
    "TestSuite",
]
