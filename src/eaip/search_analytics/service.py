"""SearchAnalyticsService — query logging, metrics collection, reports, trends, alerts, funnels."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta
from itertools import count as _id_counter
from typing import Any

from eaip.logging.context import get_logger
from eaip.search_analytics.exceptions import (
    SearchAnalyticsConfigError,
    SearchAnalyticsReportError,
)
from eaip.search_analytics.models import (
    SearchAbandonmentAnalysis,
    SearchAnalyticsAlert,
    SearchAnalyticsConfig,
    SearchAnalyticsDashboard,
    SearchAnalyticsReport,
    SearchClickThrough,
    SearchFunnel,
    SearchFunnelAnalysis,
    SearchFunnelStep,
    SearchMetrics,
    SearchMetricsPeriod,
    SearchPerformanceReport,
    SearchPopularQuery,
    SearchQueryLog,
    SearchSession,
    SearchSessionStatus,
    SearchTrend,
    SearchTrendPeriod,
    SearchZeroResultQuery,
)
from eaip.shared.time import utc_now


class SearchAnalyticsService:
    """Central service for search analytics operations."""

    def __init__(self, config: SearchAnalyticsConfig | None = None) -> None:
        self._config = config or SearchAnalyticsConfig()
        self._query_logs: list[SearchQueryLog] = []
        self._click_throughs: list[SearchClickThrough] = []
        self._sessions: dict[str, SearchSession] = {}
        self._alerts: dict[str, SearchAnalyticsAlert] = {}
        self._dashboards: dict[str, SearchAnalyticsDashboard] = {}
        self._funnels: dict[str, SearchFunnel] = {}
        self._id_counter = _id_counter()
        self._log = get_logger("eaip.search_analytics.service")

    @property
    def config(self) -> SearchAnalyticsConfig:
        return self._config

    async def update_config(self, config: SearchAnalyticsConfig) -> SearchAnalyticsConfig:
        self._config = config
        self._log.info("search_analytics.config.updated")
        return self._config

    async def log_query(
        self,
        query: str,
        user_id: str = "",
        session_id: str = "",
        result_count: int = 0,
        duration_ms: float = 0.0,
        source: str = "",
        filters: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> SearchQueryLog:
        if not self._config.logging_enabled:
            raise SearchAnalyticsConfigError("Query logging is disabled")

        log_entry = SearchQueryLog(
            id=f"q_{next(self._id_counter)}",
            query=query,
            user_id=user_id,
            session_id=session_id,
            result_count=result_count,
            duration_ms=duration_ms,
            source=source,
            filters=filters or {},
            metadata=metadata or {},
        )
        self._query_logs.append(log_entry)
        self._trim_old_logs()
        return log_entry

    async def collect_metrics(
        self, period: SearchMetricsPeriod = SearchMetricsPeriod.LAST_24H
    ) -> SearchMetrics:
        now = utc_now()
        cutoff = self._period_cutoff(now, period)
        logs = [ql for ql in self._query_logs if ql.timestamp >= cutoff]

        if not logs:
            return SearchMetrics(period=period)

        durations = [ql.duration_ms for ql in logs if ql.duration_ms > 0]
        durations_sorted = sorted(durations)
        d_len = len(durations_sorted)

        unique_users = len({ql.user_id for ql in logs if ql.user_id})
        zero_result = len([ql for ql in logs if ql.result_count == 0])
        total_clicks = len(self._click_throughs)

        avg_duration = sum(durations) / d_len if d_len else 0.0
        p50 = durations_sorted[d_len // 2] if d_len else 0.0
        p95 = durations_sorted[int(d_len * 0.95)] if d_len else 0.0
        p99 = durations_sorted[int(d_len * 0.99)] if d_len else 0.0

        ctr = total_clicks / len(logs) if logs else 0.0

        abandoned_count = len(
            [
                s
                for s in self._sessions.values()
                if s.status == SearchSessionStatus.ABANDONED and s.started_at >= cutoff
            ]
        )
        total_sessions = len([s for s in self._sessions.values() if s.started_at >= cutoff])
        abandonment_rate = abandoned_count / total_sessions if total_sessions else 0.0

        return SearchMetrics(
            total_queries=len(logs),
            unique_users=unique_users,
            avg_duration_ms=round(avg_duration, 6),
            p50_duration_ms=round(p50, 6),
            p95_duration_ms=round(p95, 6),
            p99_duration_ms=round(p99, 6),
            total_results_retrieved=sum(ql.result_count for ql in logs),
            zero_result_queries=zero_result,
            click_through_rate=round(ctr, 6),
            abandonment_rate=round(abandonment_rate, 6),
            period=period,
        )

    async def generate_performance_report(
        self, period: SearchMetricsPeriod = SearchMetricsPeriod.LAST_24H
    ) -> SearchPerformanceReport:
        metrics = await self.collect_metrics(period)
        now = utc_now()
        cutoff = self._period_cutoff(now, period)
        logs = [ql for ql in self._query_logs if ql.timestamp >= cutoff]

        durations = [ql.duration_ms for ql in logs if ql.duration_ms > 0]
        error_count = len([ql for ql in logs if ql.result_count == 0])

        throughput = 0.0
        if period != SearchMetricsPeriod.CUSTOM:
            hours = period_duration_hours(period) * 60
            throughput = round(len(logs) / hours, 6) if hours else 0.0

        report = SearchPerformanceReport(
            id=f"perf_{next(self._id_counter)}",
            period=period,
            metrics=metrics,
            avg_response_time_ms=metrics.avg_duration_ms,
            max_response_time_ms=max(durations) if durations else 0.0,
            min_response_time_ms=min(durations) if durations else 0.0,
            throughput_per_minute=throughput,
            error_rate=round(error_count / len(logs), 6) if logs else 0.0,
            cache_hit_rate=0.0,
        )
        self._log.info("search_analytics.performance_report.generated", report_id=report.id)
        return report

    async def compute_trend(
        self,
        metric_name: str,
        period: SearchTrendPeriod = SearchTrendPeriod.DAILY,
    ) -> SearchTrend:
        now = utc_now()
        cutoff = now - timedelta(days=30)
        logs = [ql for ql in self._query_logs if ql.timestamp >= cutoff]

        if not logs:
            return SearchTrend(metric_name=metric_name, period=period)

        mid = len(logs) // 2
        first_half = logs[:mid]
        second_half = logs[mid:]

        def avg_dur(entries: list[SearchQueryLog]) -> float:
            vals = [e.duration_ms for e in entries if e.duration_ms > 0]
            return sum(vals) / len(vals) if vals else 0.0

        baseline = avg_dur(first_half)
        current = avg_dur(second_half)
        change_pct = ((current - baseline) / baseline * 100) if baseline else 0.0

        trend_threshold = 5.0
        direction = "stable"
        if change_pct > trend_threshold:
            direction = "up"
        elif change_pct < -trend_threshold:
            direction = "down"

        return SearchTrend(
            metric_name=metric_name,
            period=period,
            direction=direction,
            change_percent=round(change_pct, 6),
            confidence=round(min(abs(change_pct) / 100, 1.0), 6),
            baseline_avg=round(baseline, 6),
            current_avg=round(current, 6),
            data_points=len(logs),
        )

    async def generate_report(
        self,
        name: str = "",
        period: SearchMetricsPeriod = SearchMetricsPeriod.LAST_24H,
    ) -> SearchAnalyticsReport:
        metrics = await self.collect_metrics(period)
        performance = await self.generate_performance_report(period)
        trends = [
            await self.compute_trend("avg_duration_ms", SearchTrendPeriod.DAILY),
            await self.compute_trend("query_volume", SearchTrendPeriod.DAILY),
        ]
        popular = await self.identify_popular_queries(period)
        zero_result = await self.identify_zero_result_queries(period)

        report = SearchAnalyticsReport(
            id=f"report_{next(self._id_counter)}",
            name=name or f"Search Analytics Report ({period.value})",
            period=period,
            metrics=metrics,
            performance=performance,
            trends=tuple(trends),
            popular_queries=tuple(popular),
            zero_result_queries=tuple(zero_result),
        )
        self._log.info("search_analytics.report.generated", report_id=report.id)
        return report

    async def create_dashboard(self, name: str, description: str = "") -> SearchAnalyticsDashboard:
        dashboard = SearchAnalyticsDashboard(
            id=f"dash_{next(self._id_counter)}",
            name=name,
            description=description,
        )
        self._dashboards[dashboard.id] = dashboard
        self._log.info("search_analytics.dashboard.created", dashboard_id=dashboard.id)
        return dashboard

    async def update_dashboard(
        self, dashboard_id: str, name: str | None = None, description: str | None = None
    ) -> SearchAnalyticsDashboard:
        dashboard = self._dashboards.get(dashboard_id)
        if dashboard is None:
            raise SearchAnalyticsReportError(f"Dashboard not found: {dashboard_id!r}")

        updated = dashboard
        if name is not None:
            updated = dashboard.model_copy(update={"name": name, "updated_at": utc_now()})
        if description is not None:
            updated = updated.model_copy(
                update={"description": description, "updated_at": utc_now()}
            )

        self._dashboards[dashboard_id] = updated
        return updated

    async def identify_popular_queries(
        self, period: SearchMetricsPeriod = SearchMetricsPeriod.LAST_24H
    ) -> list[SearchPopularQuery]:
        now = utc_now()
        cutoff = self._period_cutoff(now, period)
        logs = [ql for ql in self._query_logs if ql.timestamp >= cutoff]

        query_counts: defaultdict[str, list[float]] = defaultdict(list)
        for ql in logs:
            query_counts[ql.query].append(ql.duration_ms)

        result = []
        threshold = self._config.popular_query_threshold
        for query, durations in query_counts.items():
            if len(durations) >= threshold:
                clicks_for_query = len([ct for ct in self._click_throughs if ct.query == query])
                ctr = clicks_for_query / len(durations)
                result.append(
                    SearchPopularQuery(
                        query=query,
                        count=len(durations),
                        avg_duration_ms=round(sum(durations) / len(durations), 6),
                        click_through_rate=round(ctr, 6),
                    )
                )

        result.sort(key=lambda x: x.count, reverse=True)
        return result

    async def identify_zero_result_queries(
        self, period: SearchMetricsPeriod = SearchMetricsPeriod.LAST_24H
    ) -> list[SearchZeroResultQuery]:
        now = utc_now()
        cutoff = self._period_cutoff(now, period)
        logs = [ql for ql in self._query_logs if ql.timestamp >= cutoff and ql.result_count == 0]

        query_data: defaultdict[str, list[str]] = defaultdict(list)
        for ql in logs:
            query_data[ql.query].append(ql.user_id)

        return [
            SearchZeroResultQuery(
                query=query,
                count=len(user_ids),
                last_occurrence=now,
                user_ids=tuple(set(user_ids)),
            )
            for query, user_ids in query_data.items()
        ]

    async def log_click_through(
        self,
        query: str,
        result_id: str,
        result_position: int = 0,
        user_id: str = "",
        session_id: str = "",
        dwell_time_ms: float = 0.0,
    ) -> SearchClickThrough:
        ct = SearchClickThrough(
            query=query,
            result_id=result_id,
            result_position=result_position,
            user_id=user_id,
            session_id=session_id,
            dwell_time_ms=dwell_time_ms,
        )
        self._click_throughs.append(ct)
        return ct

    async def start_session(self, session_id: str, user_id: str = "") -> SearchSession:
        session = SearchSession(id=session_id, user_id=user_id)
        self._sessions[session_id] = session
        return session

    async def complete_session(self, session_id: str) -> SearchSession:
        session = self._sessions.get(session_id)
        if session is None:
            raise SearchAnalyticsReportError(f"Session not found: {session_id!r}")

        updated = session.model_copy(
            update={
                "status": SearchSessionStatus.COMPLETED,
                "completed_at": utc_now(),
            }
        )
        self._sessions[session_id] = updated
        return updated

    async def abandon_session(self, session_id: str) -> SearchSession:
        session = self._sessions.get(session_id)
        if session is None:
            raise SearchAnalyticsReportError(f"Session not found: {session_id!r}")

        now = utc_now()
        duration = (now - session.started_at).total_seconds() * 1000
        updated = session.model_copy(
            update={
                "status": SearchSessionStatus.ABANDONED,
                "completed_at": now,
                "total_duration_ms": duration,
            }
        )
        self._sessions[session_id] = updated
        return updated

    async def create_alert(
        self,
        metric_name: str,
        threshold_value: float,
        operator: str = "gt",
        severity: str = "warning",
        message: str = "",
    ) -> SearchAnalyticsAlert:
        alert = SearchAnalyticsAlert(
            id=f"alert_{next(self._id_counter)}",
            metric_name=metric_name,
            threshold_value=threshold_value,
            operator=operator,
            severity=severity,
            message=message or f"Alert on {metric_name}",
        )
        self._alerts[alert.id] = alert
        return alert

    async def check_alerts(self, metrics: SearchMetrics) -> list[SearchAnalyticsAlert]:
        triggered: list[SearchAnalyticsAlert] = []
        for alert in list(self._alerts.values()):
            if alert.acknowledged:
                continue

            current = self._get_metric_value(metrics, alert.metric_name)
            if current is None:
                continue

            triggered_flag = self._check_alert_condition(
                alert.operator, current, alert.threshold_value
            )

            if triggered_flag:
                triggered_alert = alert.model_copy(
                    update={"current_value": current, "triggered_at": utc_now()}
                )
                self._alerts[alert.id] = triggered_alert
                triggered.append(triggered_alert)

        return triggered

    async def create_funnel(
        self, name: str, steps: list[SearchFunnelStep], description: str = ""
    ) -> SearchFunnel:
        funnel = SearchFunnel(
            id=f"funnel_{next(self._id_counter)}",
            name=name,
            description=description,
            steps=tuple(steps),
        )
        self._funnels[funnel.id] = funnel
        return funnel

    async def analyze_funnel(
        self, funnel_id: str, period: SearchMetricsPeriod = SearchMetricsPeriod.LAST_24H
    ) -> SearchFunnelAnalysis:
        funnel = self._funnels.get(funnel_id)
        if funnel is None:
            raise SearchAnalyticsReportError(f"Funnel not found: {funnel_id!r}")

        now = utc_now()
        cutoff = self._period_cutoff(now, period)
        logs = [ql for ql in self._query_logs if ql.timestamp >= cutoff]

        total_entries = len(logs)
        step_counts: list[int] = []

        for _i, step in enumerate(funnel.steps):
            filtered = len([ql for ql in logs if self._matches_event_filter(ql, step.event_filter)])
            step_counts.append(filtered)

        conversion_rates: list[float] = []
        for count in step_counts:
            rate = count / total_entries if total_entries else 0.0
            conversion_rates.append(round(rate, 6))

        overall = conversion_rates[-1] if conversion_rates else 0.0

        drop_offs = [
            funnel.steps[i].name
            for i in range(1, len(step_counts))
            if step_counts[i] < step_counts[i - 1]
        ]

        return SearchFunnelAnalysis(
            funnel_id=funnel_id,
            period=period,
            total_entries=total_entries,
            step_counts=tuple(step_counts),
            conversion_rates=tuple(conversion_rates),
            overall_conversion_rate=overall,
            drop_off_points=tuple(drop_offs),
        )

    async def analyze_abandonment(
        self, period: SearchMetricsPeriod = SearchMetricsPeriod.LAST_24H
    ) -> SearchAbandonmentAnalysis:
        now = utc_now()
        cutoff = self._period_cutoff(now, period)
        sessions = [s for s in self._sessions.values() if s.started_at >= cutoff]

        total = len(sessions)
        abandoned = [s for s in sessions if s.status == SearchSessionStatus.ABANDONED]
        abandoned_count = len(abandoned)
        abandonment_rate = abandoned_count / total if total else 0.0

        query_counts = [s.query_count for s in abandoned]
        avg_queries = sum(query_counts) / len(query_counts) if query_counts else 0.0

        durations = [s.total_duration_ms for s in abandoned if s.total_duration_ms > 0]
        avg_duration = sum(durations) / len(durations) if durations else 0.0

        exit_queries: defaultdict[str, int] = defaultdict(int)
        for s in abandoned:
            if s.queries:
                exit_queries[s.queries[-1]] += 1

        top_exits = sorted(exit_queries, key=lambda q: exit_queries[q], reverse=True)[:5]

        return SearchAbandonmentAnalysis(
            period=period,
            total_sessions=total,
            abandoned_sessions=abandoned_count,
            abandonment_rate=round(abandonment_rate, 6),
            avg_queries_before_abandonment=round(avg_queries, 6),
            avg_session_duration_before_abandonment_ms=round(avg_duration, 6),
            top_exit_queries=tuple(top_exits),
        )

    async def get_dashboard(self, dashboard_id: str) -> SearchAnalyticsDashboard:
        dashboard = self._dashboards.get(dashboard_id)
        if dashboard is None:
            raise SearchAnalyticsReportError(f"Dashboard not found: {dashboard_id!r}")
        return dashboard

    async def list_dashboards(self) -> list[SearchAnalyticsDashboard]:
        return list(self._dashboards.values())

    @staticmethod
    def _get_metric_value(metrics: SearchMetrics, metric_name: str) -> float | None:
        mapping: dict[str, float | int] = {
            "total_queries": metrics.total_queries,
            "unique_users": metrics.unique_users,
            "avg_duration_ms": metrics.avg_duration_ms,
            "p50_duration_ms": metrics.p50_duration_ms,
            "p95_duration_ms": metrics.p95_duration_ms,
            "p99_duration_ms": metrics.p99_duration_ms,
            "zero_result_queries": metrics.zero_result_queries,
            "click_through_rate": metrics.click_through_rate,
            "abandonment_rate": metrics.abandonment_rate,
        }
        return mapping.get(metric_name)

    @staticmethod
    def _check_alert_condition(operator: str, current: float, threshold: float) -> bool:
        if operator == "gt":
            return current > threshold
        if operator == "lt":
            return current < threshold
        if operator == "gte":
            return current >= threshold
        if operator == "lte":
            return current <= threshold
        if operator == "eq":
            return current == threshold
        return False

    @staticmethod
    def _period_cutoff(now: datetime, period: SearchMetricsPeriod) -> datetime:
        if period == SearchMetricsPeriod.LAST_HOUR:
            return now - timedelta(hours=1)
        if period == SearchMetricsPeriod.LAST_24H:
            return now - timedelta(hours=24)
        if period == SearchMetricsPeriod.LAST_7D:
            return now - timedelta(days=7)
        if period == SearchMetricsPeriod.LAST_30D:
            return now - timedelta(days=30)
        return now - timedelta(hours=24)

    @staticmethod
    def _matches_event_filter(ql: SearchQueryLog, event_filter: str) -> bool:
        if not event_filter:
            return True
        expected_parts = 2
        parts = event_filter.split("=", 1)
        if len(parts) == expected_parts:
            key, value = parts
            if key == "source":
                return ql.source == value
        return True

    def _trim_old_logs(self) -> None:
        cutoff = utc_now() - timedelta(days=self._config.retention_days)
        self._query_logs = [ql for ql in self._query_logs if ql.timestamp >= cutoff]


def period_duration_hours(period: SearchMetricsPeriod) -> float:
    mapping = {
        SearchMetricsPeriod.LAST_HOUR: 1.0,
        SearchMetricsPeriod.LAST_24H: 24.0,
        SearchMetricsPeriod.LAST_7D: 168.0,
        SearchMetricsPeriod.LAST_30D: 720.0,
        SearchMetricsPeriod.CUSTOM: 24.0,
    }
    return mapping.get(period, 24.0)


__all__ = ["SearchAnalyticsService", "period_duration_hours"]
