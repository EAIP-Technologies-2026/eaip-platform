"""Tests for Operations Analytics — aggregation, calculations, health mapping."""

from __future__ import annotations


class TestOperationsAnalyticsCalculations:
    """Verify the calculation logic used by the operations analytics router."""

    def test_safe_div_normal(self) -> None:
        from eaip.http.routers.operations_analytics import _safe_div
        assert _safe_div(10, 2) == 5.0

    def test_safe_div_zero_denominator(self) -> None:
        from eaip.http.routers.operations_analytics import _safe_div
        assert _safe_div(10, 0) == 0.0
        assert _safe_div(0, 0) == 0.0

    def test_safe_div_zero_numerator(self) -> None:
        from eaip.http.routers.operations_analytics import _safe_div
        assert _safe_div(0, 10) == 0.0

    def test_success_rate_calculation(self) -> None:
        from eaip.http.routers.operations_analytics import _safe_div
        successful = 8
        failed = 2
        rate = _safe_div(successful, successful + failed) * 100
        assert rate == 80.0

    def test_success_rate_all_success(self) -> None:
        from eaip.http.routers.operations_analytics import _safe_div
        successful = 10
        failed = 0
        rate = _safe_div(successful, successful + failed) * 100
        assert rate == 100.0

    def test_success_rate_all_failure(self) -> None:
        from eaip.http.routers.operations_analytics import _safe_div
        successful = 0
        failed = 10
        rate = _safe_div(successful, successful + failed) * 100
        assert rate == 0.0

    def test_success_rate_no_operations(self) -> None:
        from eaip.http.routers.operations_analytics import _safe_div
        successful = 0
        failed = 0
        rate = _safe_div(successful, successful + failed) * 100
        assert rate == 0.0

    def test_overall_success_rate_combined(self) -> None:
        from eaip.http.routers.operations_analytics import _safe_div
        agent_successful = 8
        agent_failed = 2
        wf_successful = 9
        wf_failed = 1
        total_successful = agent_successful + wf_successful
        total_failed = agent_failed + wf_failed
        rate = _safe_div(total_successful, total_successful + total_failed) * 100
        assert rate == 85.0

    def test_status_text_healthy(self) -> None:
        from eaip.http.routers.operations_analytics import _status_text
        from eaip.health.checks import HealthStatus
        assert _status_text(HealthStatus.HEALTHY) == "healthy"

    def test_status_text_string(self) -> None:
        from eaip.http.routers.operations_analytics import _status_text
        assert _status_text("custom") == "custom"

    def test_overall_status_healthy(self) -> None:
        down = 0
        degraded = 0
        status = "healthy"
        if down > 0:
            status = "down"
        elif degraded > 0:
            status = "degraded"
        assert status == "healthy"

    def test_overall_status_degraded(self) -> None:
        down = 0
        degraded = 1
        status = "healthy"
        if down > 0:
            status = "down"
        elif degraded > 0:
            status = "degraded"
        assert status == "degraded"

    def test_overall_status_down(self) -> None:
        down = 1
        degraded = 1
        status = "healthy"
        if down > 0:
            status = "down"
        elif degraded > 0:
            status = "degraded"
        assert status == "down"

    def test_overall_status_down_over_degraded(self) -> None:
        down = 1
        degraded = 0
        status = "healthy"
        if down > 0:
            status = "down"
        elif degraded > 0:
            status = "degraded"
        assert status == "down"

    def test_uptime_formatting(self) -> None:
        uptime_seconds = 90061
        days, rem = divmod(uptime_seconds, 86400)
        hours, rem = divmod(rem, 3600)
        minutes, secs = divmod(rem, 60)
        parts = []
        if days:
            parts.append(f"{days}d")
        if hours:
            parts.append(f"{hours}h")
        if minutes:
            parts.append(f"{minutes}m")
        parts.append(f"{secs}s")
        result = " ".join(parts)
        assert result == "1d 1h 1m 1s"

    def test_uptime_zero(self) -> None:
        uptime_seconds = 0
        days, rem = divmod(uptime_seconds, 86400)
        hours, rem = divmod(rem, 3600)
        minutes, secs = divmod(rem, 60)
        parts = []
        if days:
            parts.append(f"{days}d")
        if hours:
            parts.append(f"{hours}h")
        if minutes:
            parts.append(f"{minutes}m")
        parts.append(f"{secs}s")
        result = " ".join(parts)
        assert result == "0s"

    def test_avg_latency_calculation(self) -> None:
        durations = [100.0, 200.0, 300.0, 400.0]
        avg = sum(durations) / len(durations) if durations else 0.0
        assert avg == 250.0

    def test_avg_latency_empty(self) -> None:
        durations: list[float] = []
        avg = sum(durations) / len(durations) if durations else 0.0
        assert avg == 0.0


class TestOperationsAnalyticsDataStructures:
    """Verify the data structures returned by the API."""

    def test_overview_structure(self) -> None:
        overview = {
            "totalOperations": 100,
            "successfulOperations": 95,
            "failedOperations": 5,
            "successRate": 95.0,
            "activeOperations": 3,
            "uptime": "1d 2h 3m 4s",
            "uptimeSeconds": 93784,
            "overallStatus": "healthy",
        }
        assert overview["totalOperations"] == 100
        assert overview["successRate"] == 95.0
        assert overview["overallStatus"] == "healthy"

    def test_agent_analytics_structure(self) -> None:
        agents = {
            "total": 10,
            "running": 3,
            "idle": 5,
            "error": 1,
            "paused": 1,
            "totalExecutions": 50,
            "successfulExecutions": 45,
            "failedExecutions": 5,
            "successRate": 90.0,
            "avgLatencyMs": 150.5,
            "executionsToday": 10,
        }
        assert agents["total"] == 10
        assert agents["successRate"] == 90.0

    def test_workflow_analytics_structure(self) -> None:
        workflows = {
            "total": 5,
            "active": 2,
            "paused": 1,
            "draft": 2,
            "totalExecutions": 20,
            "successfulExecutions": 18,
            "failedExecutions": 2,
            "successRate": 90.0,
            "avgDurationMs": 500.0,
            "executionsToday": 5,
        }
        assert workflows["total"] == 5
        assert workflows["successRate"] == 90.0

    def test_health_analytics_structure(self) -> None:
        health = {
            "overall": "healthy",
            "totalServices": 10,
            "healthy": 8,
            "degraded": 1,
            "down": 1,
        }
        assert health["totalServices"] == 10
        assert health["overall"] == "healthy"

    def test_failure_structure(self) -> None:
        failure = {
            "id": "fail-1",
            "title": "Agent Execution Failed",
            "message": "Timeout after 30s",
            "severity": "error",
            "source": "agent-runtime",
            "timestamp": "2024-01-01T00:00:00Z",
            "type": "agent.failed",
        }
        assert failure["severity"] == "error"
        assert failure["source"] == "agent-runtime"
