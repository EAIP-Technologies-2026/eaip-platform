"""Search analytics domain events."""

from __future__ import annotations

from typing import Any, ClassVar

from eaip.events.event import DomainEvent


class SearchAnalyticsConfigUpdated(DomainEvent):
    event_type: ClassVar[str] = "eaip.search_analytics.config.updated"
    config: dict[str, Any] = {}


class SearchQueryLogged(DomainEvent):
    event_type: ClassVar[str] = "eaip.search_analytics.query.logged"
    query_id: str = ""
    query: str = ""
    user_id: str = ""
    session_id: str = ""
    result_count: int = 0
    duration_ms: float = 0.0


class SearchMetricsCollected(DomainEvent):
    event_type: ClassVar[str] = "eaip.search_analytics.metrics.collected"
    period: str = ""
    total_queries: int = 0
    unique_users: int = 0
    avg_duration_ms: float = 0.0
    zero_result_queries: int = 0


class SearchPerformanceReportGenerated(DomainEvent):
    event_type: ClassVar[str] = "eaip.search_analytics.performance_report.generated"
    report_id: str = ""
    period: str = ""
    avg_response_time_ms: float = 0.0
    throughput_per_minute: float = 0.0


class SearchTrendComputed(DomainEvent):
    event_type: ClassVar[str] = "eaip.search_analytics.trend.computed"
    metric_name: str = ""
    period: str = ""
    direction: str = ""
    change_percent: float = 0.0
    confidence: float = 0.0


class SearchAnalyticsReportGenerated(DomainEvent):
    event_type: ClassVar[str] = "eaip.search_analytics.report.generated"
    report_id: str = ""
    name: str = ""
    period: str = ""
    metric_count: int = 0


class SearchAnalyticsDashboardCreated(DomainEvent):
    event_type: ClassVar[str] = "eaip.search_analytics.dashboard.created"
    dashboard_id: str = ""
    name: str = ""


class SearchAnalyticsDashboardUpdated(DomainEvent):
    event_type: ClassVar[str] = "eaip.search_analytics.dashboard.updated"
    dashboard_id: str = ""
    changes: dict[str, Any] = {}


class SearchPopularQueryIdentified(DomainEvent):
    event_type: ClassVar[str] = "eaip.search_analytics.popular_query.identified"
    query: str = ""
    count: int = 0
    click_through_rate: float = 0.0


class SearchZeroResultQueryIdentified(DomainEvent):
    event_type: ClassVar[str] = "eaip.search_analytics.zero_result_query.identified"
    query: str = ""
    count: int = 0


class SearchClickThroughLogged(DomainEvent):
    event_type: ClassVar[str] = "eaip.search_analytics.click_through.logged"
    query: str = ""
    result_id: str = ""
    result_position: int = 0
    user_id: str = ""
    dwell_time_ms: float = 0.0


class SearchSessionStarted(DomainEvent):
    event_type: ClassVar[str] = "eaip.search_analytics.session.started"
    session_id: str = ""
    user_id: str = ""


class SearchSessionCompleted(DomainEvent):
    event_type: ClassVar[str] = "eaip.search_analytics.session.completed"
    session_id: str = ""
    query_count: int = 0
    click_count: int = 0


class SearchSessionAbandoned(DomainEvent):
    event_type: ClassVar[str] = "eaip.search_analytics.session.abandoned"
    session_id: str = ""
    query_count: int = 0
    duration_ms: float = 0.0


class SearchAnalyticsAlertTriggered(DomainEvent):
    event_type: ClassVar[str] = "eaip.search_analytics.alert.triggered"
    alert_id: str = ""
    metric_name: str = ""
    current_value: float = 0.0
    threshold_value: float = 0.0
    severity: str = ""


class SearchFunnelAnalysisCompleted(DomainEvent):
    event_type: ClassVar[str] = "eaip.search_analytics.funnel_analysis.completed"
    funnel_id: str = ""
    overall_conversion_rate: float = 0.0
    total_entries: int = 0


class SearchAbandonmentAnalysisCompleted(DomainEvent):
    event_type: ClassVar[str] = "eaip.search_analytics.abandonment_analysis.completed"
    period: str = ""
    abandonment_rate: float = 0.0
    total_sessions: int = 0


SearchAnalyticsEvent = (
    SearchAnalyticsConfigUpdated
    | SearchQueryLogged
    | SearchMetricsCollected
    | SearchPerformanceReportGenerated
    | SearchTrendComputed
    | SearchAnalyticsReportGenerated
    | SearchAnalyticsDashboardCreated
    | SearchAnalyticsDashboardUpdated
    | SearchPopularQueryIdentified
    | SearchZeroResultQueryIdentified
    | SearchClickThroughLogged
    | SearchSessionStarted
    | SearchSessionCompleted
    | SearchSessionAbandoned
    | SearchAnalyticsAlertTriggered
    | SearchFunnelAnalysisCompleted
    | SearchAbandonmentAnalysisCompleted
)

__all__ = [
    "SearchAbandonmentAnalysisCompleted",
    "SearchAnalyticsAlertTriggered",
    "SearchAnalyticsConfigUpdated",
    "SearchAnalyticsDashboardCreated",
    "SearchAnalyticsDashboardUpdated",
    "SearchAnalyticsEvent",
    "SearchAnalyticsReportGenerated",
    "SearchClickThroughLogged",
    "SearchFunnelAnalysisCompleted",
    "SearchMetricsCollected",
    "SearchPerformanceReportGenerated",
    "SearchPopularQueryIdentified",
    "SearchQueryLogged",
    "SearchSessionAbandoned",
    "SearchSessionCompleted",
    "SearchSessionStarted",
    "SearchTrendComputed",
    "SearchZeroResultQueryIdentified",
]
