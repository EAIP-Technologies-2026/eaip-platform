"""Tests for Enterprise Reporting — report catalog, row generation, and export."""

from __future__ import annotations

from typing import Any

from eaip.export.engine import ExportEngine

from eaip.http.routers.reports import (
    REPORTS,
    SUPPORTED_FORMATS,
    _columns_for,
    _ensure_reports_registered,
    _rows_from_cost,
    _rows_from_events,
    _rows_from_health,
    _rows_from_knowledge,
    _rows_from_operations,
)


class TestReportCatalog:
    def test_catalog_has_expected_reports(self) -> None:
        ids = [r["id"] for r in REPORTS]
        assert ids == ["operations", "health", "cost", "knowledge", "events"]

    def test_reports_have_formats_and_source_type(self) -> None:
        for r in REPORTS:
            assert r["name"]
            assert r["description"]
            assert r["sourceType"]
            assert all(f in SUPPORTED_FORMATS for f in r["formats"])

    def test_duplicate_report_ids(self) -> None:
        ids = [r["id"] for r in REPORTS]
        assert len(ids) == len(set(ids))


class TestRowsFromOperations:
    def test_builds_summary_and_section_rows(self) -> None:
        data = {
            "overview": {
                "totalOperations": 10,
                "successfulOperations": 8,
                "failedOperations": 2,
                "successRate": 80.0,
                "activeOperations": 3,
                "uptime": "1h 2m 3s",
                "overallStatus": "healthy",
            },
            "agents": {
                "total": 2,
                "running": 1,
                "idle": 1,
                "error": 0,
                "paused": 0,
                "totalExecutions": 6,
                "successRate": 66.67,
                "avgLatencyMs": 120.0,
            },
            "workflows": {
                "total": 1,
                "active": 1,
                "paused": 0,
                "draft": 0,
                "totalExecutions": 4,
                "successRate": 100.0,
                "avgDurationMs": 500.0,
            },
            "health": {"overall": "healthy", "totalServices": 3, "healthy": 3, "degraded": 0, "down": 0},
            "events": {
                "total": 1,
                "recent": [{"id": "e1", "type": "agent", "title": "Agent started", "description": "", "timestamp": "2025-01-01T00:00:00Z"}],
            },
        }
        rows = _rows_from_operations(data)
        resources = [r["resource"] for r in rows]
        assert resources[:4] == ["Overview", "Agents", "Workflows", "Health"]
        assert resources[-1] == "Event"
        assert rows[0]["totalOperations"] == 10
        assert rows[1]["running"] == 1
        assert rows[2]["successRate"] == 100.0
        assert rows[3]["down"] == 0
        assert rows[4]["eventId"] == "e1"

    def test_empty_operations_data(self) -> None:
        rows = _rows_from_operations({})
        assert rows[0]["totalOperations"] == 0
        assert len(rows) == 4

    def test_missing_events_section(self) -> None:
        rows = _rows_from_operations({"overview": {}})
        assert len(rows) == 4


class TestRowsFromHealth:
    def test_service_rows(self) -> None:
        data = {
            "overall": "degraded",
            "services": [
                {"name": "AgentRuntime", "status": "healthy", "message": ""},
                {"name": "KnowledgeEngine", "status": "degraded", "message": "slow"},
            ],
        }
        rows = _rows_from_health(data)
        assert len(rows) == 2
        assert rows[0]["service"] == "AgentRuntime"
        assert rows[1]["status"] == "degraded"

    def test_empty_health(self) -> None:
        assert _rows_from_health({}) == []


class TestRowsFromCost:
    def test_overview_model_and_tenant_rows(self) -> None:
        data = {
            "overview": {"totalCost": 12.5, "totalRequests": 3, "totalTokens": 500, "modelCount": 1, "currency": "USD"},
            "byModel": {"gpt-4o": {"cost": 12.5, "tokens": 500}},
            "byTenant": {"acme": 8.0},
        }
        rows = _rows_from_cost(data)
        assert rows[0]["resource"] == "Overview"
        assert rows[0]["totalCost"] == 12.5
        assert rows[1]["resource"] == "Model"
        assert rows[1]["model"] == "gpt-4o"
        assert rows[2]["resource"] == "Tenant"
        assert rows[2]["tenant"] == "acme"

    def test_empty_cost(self) -> None:
        rows = _rows_from_cost({})
        assert len(rows) == 1
        assert rows[0]["totalCost"] == 0.0


class TestRowsFromKnowledge:
    def test_summary_and_collection_rows(self) -> None:
        stats = {"totalDocuments": 20, "totalCollections": 2, "indexedCount": 18, "pendingCount": 2, "failedCount": 0}
        collections = [
            {"name": "Governance", "description": "Policies", "documentCount": 12},
            {"name": "Onboarding", "description": "Guides", "documentCount": 8},
        ]
        rows = _rows_from_knowledge(stats, collections)
        assert rows[0]["resource"] == "Summary"
        assert rows[0]["totalDocuments"] == 20
        assert rows[1]["name"] == "Governance"
        assert len(rows) == 3

    def test_collection_cap_at_50(self) -> None:
        collections = [{"name": f"c{i}", "documentCount": 0} for i in range(60)]
        rows = _rows_from_knowledge({}, collections)
        assert len(rows) == 51


class TestRowsFromEvents:
    def test_activity_rows(self) -> None:
        activity = [
            {"id": "a1", "type": "agent", "action": "Agent Started", "message": "ok", "timestamp": "2025-01-01T00:00:00Z", "status": "success"}
        ]
        rows = _rows_from_events(activity)
        assert len(rows) == 1
        assert rows[0]["action"] == "Agent Started"

    def test_empty_activity(self) -> None:
        assert _rows_from_events([]) == []


class TestReportHelpers:
    def test_columns_union_in_order(self) -> None:
        rows: list[dict[str, Any]] = [{"a": 1, "b": 2}, {"b": 3, "c": 4}]
        assert _columns_for(rows) == ["a", "b", "c"]

    def test_columns_empty(self) -> None:
        assert _columns_for([]) == []

    def test_ensure_registers_definitions_once(self) -> None:
        engine = ExportEngine()
        _ensure_reports_registered(engine)
        assert len(engine.list_reports()) == len(REPORTS)
        _ensure_reports_registered(engine)
        assert len(engine.list_reports()) == len(REPORTS)
        for r in engine.list_reports():
            assert r.id in {item["id"] for item in REPORTS}

    def test_ensure_none_is_noop(self) -> None:
        _ensure_reports_registered(None)


__all__: list[str] = []
