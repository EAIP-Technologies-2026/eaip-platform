"""Unit tests for Stage A1007 — Operational Intelligence."""

from __future__ import annotations

import pytest

from eaip.admin.audit import AuditLogger
from eaip.agents.registry import AgentRegistry
from eaip.context.permission_context import IdentityScope
from eaip.copilot.operational_intelligence import (
    OperationalIntelligenceService,
)
from eaip.workflow.registry import WorkflowRegistry


@pytest.fixture
def op_service() -> OperationalIntelligenceService:
    audit = AuditLogger()
    agents = AgentRegistry()
    workflows = WorkflowRegistry()
    return OperationalIntelligenceService(
        audit_logger=audit,
        agent_registry=agents,
        workflow_registry=workflows,
    )


def test_distinguish_live_from_static_query(op_service: OperationalIntelligenceService) -> None:
    """Verify live state queries are clearly distinguished from static platform knowledge."""
    # Live operational questions
    assert op_service.is_operational_query("Is the system healthy?") is True
    assert op_service.is_operational_query("How many agents are running right now?") is True
    assert op_service.is_operational_query("What is our AI cost?") is True

    # Static capability knowledge questions
    assert op_service.is_operational_query("What is Operations?") is False
    assert op_service.is_operational_query("Tell me about Second Brains") is False
    assert op_service.is_operational_query("What does the Knowledge capability do?") is False


@pytest.mark.asyncio
async def test_live_snapshot_capture(op_service: OperationalIntelligenceService) -> None:
    """Verify live snapshot aggregates telemetry with freshness metadata."""
    identity = IdentityScope(user_id="sre-1", tenant_id="tenant-prod", roles=("operator",))
    snapshot = await op_service.get_live_snapshot(identity)

    assert snapshot.system_health_status in ("healthy", "ok", "degraded")
    assert snapshot.tenant_id == "tenant-prod"
    assert "uptime_pct" in snapshot.metrics
    assert "p99_latency_ms" in snapshot.metrics
    assert snapshot.data_freshness_seconds < 1.0


@pytest.mark.asyncio
async def test_answer_operational_query(op_service: OperationalIntelligenceService) -> None:
    """Verify operational query generates grounded response with freshness citations."""
    identity = IdentityScope(user_id="admin-1", tenant_id="tenant-prod", roles=("admin",))
    resp = await op_service.answer_operational_query(
        query="Check system health",
        identity=identity,
        current_route="/dashboard",
    )

    assert "Live Operational Telemetry" in resp.reply
    assert "System Health Status" in resp.reply
    assert "Live data captured at" in resp.reply
    assert resp.tenant_id == "tenant-prod"
    assert resp.grounded_capability == "eaip.monitoring"
