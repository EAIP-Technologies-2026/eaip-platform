"""Capacity Analyzer — analyze resource usage, predict capacity needs, detect threshold breaches."""

from __future__ import annotations

from eaip.capacity.analyzer import CapacityAnalyzer
from eaip.capacity.events import (
    CapacityReportGenerated,
    MetricRecorded,
    ThresholdBreached,
)
from eaip.capacity.exceptions import (
    CapacityError,
    ResourceNotFoundError,
)
from eaip.capacity.health import CapacityAnalyzerHealthCheck
from eaip.capacity.integration import CapacityRuntimeModule
from eaip.capacity.models import (
    CapacityConfig,
    CapacityReport,
    ResourceMetric,
)

__all__ = [
    "CapacityAnalyzer",
    "CapacityAnalyzerHealthCheck",
    "CapacityConfig",
    "CapacityError",
    "CapacityReport",
    "CapacityReportGenerated",
    "CapacityRuntimeModule",
    "MetricRecorded",
    "ResourceMetric",
    "ResourceNotFoundError",
    "ThresholdBreached",
]
