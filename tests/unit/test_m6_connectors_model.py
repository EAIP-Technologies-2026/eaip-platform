"""M6 tests — connectors, model fabric, policy, routing, failover, experiments."""

from __future__ import annotations

import pytest

from eaip.connectors.capabilities import (
    CapabilityRegistry,
    ConnectorCapabilityRecord,
    DataClassification,
)
from eaip.connectors.connector_policy import (
    ConnectorInvocationContext,
    ConnectorPolicyEngine,
    ConnectorPolicyRule,
    PolicyDecision,
)
from eaip.connectors.health_tracker import (
    CircuitState,
    ConnectorHealthTracker,
    DegradationLevel,
)
from eaip.connectors.real.base import ConnectionStatus, RealConnectorAdapter
from eaip.connectors.real.registry import RealConnectorRegistry
from eaip.connectors.real.adapters.salesforce import SalesforceConnector
from eaip.connectors.real.adapters.slack import SlackConnector
from eaip.connectors.real.synthetic import (
    create_synthetic_capability_records,
    create_synthetic_health_reports,
    create_synthetic_models,
    get_all_synthetic_data,
)
from eaip.provider_routing.model_evaluation_tracker import (
    ModelEvaluationRecord,
    ModelEvaluationTracker,
)
from eaip.provider_routing.model_experimentation import (
    ExperimentResult,
    ModelExperimentManager,
)
from eaip.provider_routing.model_failover import ModelFailover
from eaip.provider_routing.model_registry import (
    ModelLocality,
    ModelPrivacyLevel,
    ModelRecord,
    ModelRegistry,
    ModelStatus,
)
from eaip.provider_routing.model_router import ModelRouter, TaskRequirements


# ---------------------------------------------------------------------------
# M6-A: Real Connector Framework
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_connector_adapter_registration():
    """Test that adapters can be registered and retrieved."""
    registry = RealConnectorRegistry()
    registry.register_adapter("salesforce", SalesforceConnector)
    registry.register_adapter("slack", SlackConnector)
    assert "salesforce" in registry.list_adapters()
    assert "slack" in registry.list_adapters()
    assert registry.get_adapter("salesforce") is SalesforceConnector
    assert registry.get_adapter("nonexistent") is None


@pytest.mark.asyncio
async def test_connector_discovery():
    """Test connector capability discovery."""
    adapter = SalesforceConnector(connector_id="sf-1", tenant_id="t1")
    await adapter.connect("")
    assert adapter.status == ConnectionStatus.SYNTHETIC
    caps = await adapter.discover()
    assert len(caps) > 0
    assert any(c.name == "soql_query" for c in caps)


@pytest.mark.asyncio
async def test_connector_health_tracking():
    """Test health tracking for connectors."""
    tracker = ConnectorHealthTracker()
    report = await tracker.track_health("conn-1", "tenant-1")
    assert report.connector_id == "conn-1"
    assert report.circuit_state == CircuitState.CLOSED

    for _ in range(5):
        await tracker.update_health("conn-1", "tenant-1", success=False)
    report = await tracker.get_health("conn-1", "tenant-1")
    assert report is not None
    assert report.circuit_state == CircuitState.OPEN
    assert report.degradation_level in (DegradationLevel.MODERATE, DegradationLevel.SEVERE, DegradationLevel.CRITICAL)

    unhealthy = await tracker.get_unhealthy_connectors("tenant-1")
    assert any(u.connector_id == "conn-1" for u in unhealthy)


@pytest.mark.asyncio
async def test_connector_policy_enforcement():
    """Test that policy engine gates connector invocations."""
    engine = ConnectorPolicyEngine()
    engine.add_rule(ConnectorPolicyRule(
        rule_id="r1",
        tenant_id="t1",
        connector_id="conn-1",
        allowed_operations=["read", "list"],
        denied_operations=["delete"],
        max_data_classification="confidential",
        max_autonomy_level="L2",
    ))

    result = engine.check_invocation(ConnectorInvocationContext(
        tenant_id="t1", connector_id="conn-1", operation="read",
    ))
    assert result.decision == PolicyDecision.ALLOW

    result = engine.check_invocation(ConnectorInvocationContext(
        tenant_id="t1", connector_id="conn-1", operation="delete",
    ))
    assert result.decision == PolicyDecision.DENY

    result = engine.check_invocation(ConnectorInvocationContext(
        tenant_id="t1", connector_id="conn-1", operation="read",
        data_classification="restricted",
    ))
    assert result.decision == PolicyDecision.DENY


@pytest.mark.asyncio
async def test_connector_credential_reference_safety():
    """Test that no secrets are persisted — only vault:// references."""
    adapter = SalesforceConnector(connector_id="sf-1", tenant_id="t1")
    assert adapter._validate_credentials_ref("vault://t1/sf-creds") is True
    assert adapter._validate_credentials_ref("") is False
    assert adapter._validate_credentials_ref("api_key=secret123") is False
    assert adapter._validate_credentials_ref("password=abc") is False


@pytest.mark.asyncio
async def test_connector_tenant_isolation():
    """Test that connectors are isolated per tenant."""
    registry = RealConnectorRegistry()
    registry.register_adapter("salesforce", SalesforceConnector)
    inst1 = registry.create_instance("salesforce", "sf-1", "tenant-a")
    inst2 = registry.create_instance("salesforce", "sf-1", "tenant-b")
    assert inst1 is not None
    assert inst2 is not None
    assert registry.get_instance("sf-1", "tenant-a") is inst1
    assert registry.get_instance("sf-1", "tenant-b") is inst2
    assert len(registry.list_instances("tenant-a")) == 1
    assert len(registry.list_instances("tenant-b")) == 1


@pytest.mark.asyncio
async def test_synthetic_adapter_mode():
    """Test that adapters return SYNTHETIC mode when no credentials."""
    adapter = SalesforceConnector(connector_id="sf-synth", tenant_id="t1")
    status = await adapter.connect("")
    assert status == ConnectionStatus.SYNTHETIC
    assert adapter.is_synthetic is True
    result = await adapter.invoke("query", {"soql": "SELECT Id FROM Account"})
    assert result["mode"] == "SYNTHETIC"
    health = await adapter.health()
    assert health.status == ConnectionStatus.SYNTHETIC


# ---------------------------------------------------------------------------
# M6-D: Multi-Model Fabric
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_model_registry_crud():
    """Test model registry create/read/update/delete."""
    registry = ModelRegistry()
    model = ModelRecord(
        id="m1", tenant_id="t1", provider="openai", model_name="gpt-4o",
        capabilities=["chat"], context_limit=128000, quality_score=0.95,
    )
    registry.register_model(model)
    retrieved = registry.get_model("m1", "t1")
    assert retrieved is not None
    assert retrieved.model_name == "gpt-4o"

    models = registry.list_models("t1")
    assert len(models) == 1

    registry.remove_model("m1", "t1")
    assert registry.get_model("m1", "t1") is None


@pytest.mark.asyncio
async def test_model_routing_by_capability():
    """Test that routing selects models matching required capabilities."""
    registry = ModelRegistry()
    registry.register_model(ModelRecord(id="m1", tenant_id="t1", provider="openai", model_name="gpt-4o", capabilities=["chat", "vision"], quality_score=0.95))
    registry.register_model(ModelRecord(id="m2", tenant_id="t1", provider="anthropic", model_name="claude-3", capabilities=["chat"], quality_score=0.90))

    router = ModelRouter(registry)
    decision = await router.route(
        TaskRequirements(required_capabilities=["vision"]),
        tenant_id="t1",
    )
    assert decision.selected_model_id == "m1"


@pytest.mark.asyncio
async def test_model_routing_by_cost():
    """Test that routing considers cost."""
    registry = ModelRegistry()
    registry.register_model(ModelRecord(id="expensive", tenant_id="t1", provider="openai", model_name="gpt-4", capabilities=["chat"], cost_per_1k_tokens=0.03, quality_score=0.90))
    registry.register_model(ModelRecord(id="cheap", tenant_id="t1", provider="openai", model_name="gpt-3.5", capabilities=["chat"], cost_per_1k_tokens=0.002, quality_score=0.80))

    router = ModelRouter(registry)
    decision = await router.route(
        TaskRequirements(max_cost_per_1k=0.01),
        tenant_id="t1",
    )
    assert decision.selected_model_id == "cheap"


@pytest.mark.asyncio
async def test_model_routing_by_privacy():
    """Test that routing respects privacy requirements."""
    registry = ModelRegistry()
    registry.register_model(ModelRecord(id="public", tenant_id="t1", provider="openai", model_name="gpt-4o", capabilities=["chat"], privacy_level=ModelPrivacyLevel.PUBLIC))
    registry.register_model(ModelRecord(id="private", tenant_id="t1", provider="azure", model_name="gpt-4", capabilities=["chat"], privacy_level=ModelPrivacyLevel.PRIVATE))

    router = ModelRouter(registry)
    decision = await router.route(
        TaskRequirements(data_classification="confidential"),
        tenant_id="t1",
    )
    assert decision.selected_model_id == "private"


@pytest.mark.asyncio
async def test_model_failover_policy_check():
    """Test that failover respects policy restrictions."""
    registry = ModelRegistry()
    registry.register_model(ModelRecord(id="primary", tenant_id="t1", provider="openai", model_name="gpt-4o", status=ModelStatus.ACTIVE))
    registry.register_model(ModelRecord(id="fallback", tenant_id="t1", provider="anthropic", model_name="claude-3", status=ModelStatus.ACTIVE))

    failover = ModelFailover(registry)
    failover.set_failover_chain("primary", "t1", ["fallback"])
    assert failover.check_failover_allowed("primary", "fallback", "t1") is True

    failover.forbid_fallback("primary", "fallback")
    assert failover.check_failover_allowed("primary", "fallback", "t1") is False


@pytest.mark.asyncio
async def test_model_failover_never_forbidden():
    """Test that failover never routes to a forbidden model."""
    registry = ModelRegistry()
    registry.register_model(ModelRecord(id="primary", tenant_id="t1", provider="openai", model_name="gpt-4o", status=ModelStatus.ACTIVE))
    registry.register_model(ModelRecord(id="forbidden", tenant_id="t1", provider="bad", model_name="bad-model", status=ModelStatus.ACTIVE))
    registry.register_model(ModelRecord(id="ok", tenant_id="t1", provider="anthropic", model_name="claude-3", status=ModelStatus.ACTIVE))

    failover = ModelFailover(registry)
    failover.set_failover_chain("primary", "t1", ["forbidden", "ok"])
    failover.forbid_fallback("primary", "forbidden")

    result = await failover.failover("primary", "t1", "test error")
    assert result.success is True
    assert result.fallback_model_id == "ok"


@pytest.mark.asyncio
async def test_model_evaluation_tracking():
    """Test model evaluation tracking and aggregation."""
    tracker = ModelEvaluationTracker()
    await tracker.track_evaluation(ModelEvaluationRecord(
        model_id="m1", tenant_id="t1", task_type="summarization",
        quality_score=0.9, latency_ms=500, cost=0.01, success=True,
    ))
    await tracker.track_evaluation(ModelEvaluationRecord(
        model_id="m1", tenant_id="t1", task_type="summarization",
        quality_score=0.8, latency_ms=600, cost=0.012, success=True,
    ))

    perf = await tracker.get_model_performance("m1", "t1")
    assert perf.total_evaluations == 2
    assert perf.avg_quality == pytest.approx(0.85, abs=0.01)
    assert perf.success_rate == 1.0


@pytest.mark.asyncio
async def test_model_experiment_lifecycle():
    """Test experiment creation, recording, and winner promotion."""
    manager = ModelExperimentManager()
    exp = manager.create_experiment(
        experiment_id="exp-1",
        name="Summarization Test",
        tenant_id="t1",
        models=["m1", "m2"],
        task_type="summarization",
    )
    assert exp.status.value == "draft"

    manager.start_experiment("exp-1", "t1")
    manager.record_result(ExperimentResult(
        experiment_id="exp-1", model_id="m1", tenant_id="t1",
        quality=0.9, latency_ms=500, cost=0.01, success=True,
    ))
    manager.record_result(ExperimentResult(
        experiment_id="exp-1", model_id="m2", tenant_id="t1",
        quality=0.8, latency_ms=400, cost=0.008, success=True,
    ))

    summary = manager.get_experiment_results("exp-1", "t1")
    assert summary.recommendation != ""
    assert "m1" in summary.models

    promoted = manager.promote_winner("exp-1", "t1", "m1")
    assert promoted.winner == "m1"
    assert promoted.status.value == "completed"


# ---------------------------------------------------------------------------
# M6-E: Conductor Intents
# ---------------------------------------------------------------------------


def test_conductor_connector_intents():
    """Test that M6 conductor intents are registered."""
    from eaip.copilot.planner import ConductorPlanner

    tools = {"list_integrations": None, "system_health": None, "runtime_diagnostics": None}
    planner = ConductorPlanner(tools=tools)

    result = planner.plan("What connectors are available?")
    assert result.tool_call is not None
    assert result.tool_call.tool_name == "list_integrations"

    result = planner.plan("Is Salesforce healthy?")
    assert result.tool_call is not None

    result = planner.plan("Which model should handle this?")
    assert result.tool_call is not None

    result = planner.plan("Why did EAIP fail over?")
    assert result.tool_call is not None


# ---------------------------------------------------------------------------
# M6-H: Synthetic Data
# ---------------------------------------------------------------------------


def test_synthetic_data_generation():
    """Test that synthetic data generates correctly."""
    data = get_all_synthetic_data()
    assert len(data["connectors"]) >= 8
    assert len(data["capabilities"]) >= 8
    assert len(data["health_reports"]) >= 8
    assert len(data["models"]) >= 6

    apex_conns = [c for c in data["connectors"] if c["tenant_id"] == "apex-advisory-group"]
    assert len(apex_conns) >= 3

    nova_conns = [c for c in data["connectors"] if c["tenant_id"] == "nova-manufacturing-systems"]
    assert len(nova_conns) >= 3

    meridian_conns = [c for c in data["connectors"] if c["tenant_id"] == "meridian-health-services"]
    assert len(meridian_conns) >= 2


def test_capability_registry_operations():
    """Test capability registry CRUD and permission checks."""
    registry = CapabilityRegistry()
    record = ConnectorCapabilityRecord(
        connector_id="conn-1",
        tenant_id="t1",
        connector_type="salesforce",
        capabilities=["query", "crud"],
        operations=["query", "create_record"],
        permissions=["sf:read"],
        data_classes=["account"],
    )
    registry.register_capability(record)

    retrieved = registry.get_capability("conn-1", "t1")
    assert retrieved is not None
    assert retrieved.connector_type == "salesforce"

    assert registry.check_permission("conn-1", "query", "t1") is True
    assert registry.check_permission("conn-1", "delete", "t1") is False
    assert registry.check_permission("nonexistent", "query", "t1") is False

    caps = registry.list_capabilities("t1")
    assert len(caps) == 1

    registry.remove_capability("conn-1", "t1")
    assert registry.get_capability("conn-1", "t1") is None
