"""Enterprise Analytics & Insights — KPI engine, analytics service, reporting, trends, and telemetry."""

from eaip.analytics.aggregation import AggregationEngine
from eaip.analytics.dashboard import DashboardService
from eaip.analytics.events import (
    AnomalyDetected,
    DashboardCreated,
    DashboardUpdated,
    KpiEvaluated,
    MetricRecorded,
    ReportGenerated,
    TrendComputed,
)
from eaip.analytics.exceptions import (
    AnalyticsError,
    AnalyticsQueryError,
    DashboardNotFoundError,
    MetricNotFoundError,
    ReportError,
)
from eaip.analytics.health import AnalyticsHealthCheck
from eaip.analytics.integration import AnalyticsRuntimeModule
from eaip.analytics.kpi_engine import KpiEngine
from eaip.analytics.models import (
    AnalyticsConfig,
    AnalyticsReport,
    DashboardDefinition,
    DashboardWidget,
    MetricDefinition,
    MetricPoint,
    TimeSeriesPoint,
    TimeSeriesResult,
    TrendAnalysis,
)
from eaip.analytics.service import AnalyticsService
from eaip.analytics.telemetry import TelemetryCollector
from eaip.analytics.trends import TrendAnalyzer

__all__ = [
    "AggregationEngine",
    "AnalyticsConfig",
    "AnalyticsError",
    "AnalyticsHealthCheck",
    "AnalyticsQueryError",
    "AnalyticsReport",
    "AnalyticsRuntimeModule",
    "AnalyticsService",
    "AnomalyDetected",
    "DashboardCreated",
    "DashboardDefinition",
    "DashboardNotFoundError",
    "DashboardService",
    "DashboardUpdated",
    "DashboardWidget",
    "KpiEngine",
    "KpiEvaluated",
    "MetricDefinition",
    "MetricNotFoundError",
    "MetricPoint",
    "MetricRecorded",
    "ReportError",
    "ReportGenerated",
    "TelemetryCollector",
    "TimeSeriesPoint",
    "TimeSeriesResult",
    "TrendAnalysis",
    "TrendAnalyzer",
    "TrendComputed",
]
