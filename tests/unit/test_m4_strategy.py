"""M4 Strategy Foundation tests — PSF, RIL, EGE, KCR, strategy graph, conductor intents."""

from __future__ import annotations

import pytest

from eaip.governance_center.engine import (
    EnterpriseGovernanceEngine,
    GovernanceDecision,
    PolicyCondition,
    PolicyRule,
)
from eaip.intelligence.recursive_loop import IntelligenceCycle, RecursiveIntelligenceEngine
from eaip.strategy.engine import StrategicFrameworkEngine
from eaip.strategy.graph import StrategyExecutionGraph
from eaip.strategy.models import InitiativeStatus, ObjectiveStatus, Priority
from eaip.strategy.persistence import StrategyStore


# ── helpers ──────────────────────────────────────────────────────

def _make_engine(event_bus=None):
    store = StrategyStore()
    return StrategicFrameworkEngine(event_bus=event_bus, store=store), store


# ── PSF: Strategic Objective CRUD ────────────────────────────────

@pytest.mark.asyncio
async def test_strategic_objective_crud():
    engine, _ = _make_engine()

    obj = await engine.create_objective("tenant-a", "Grow revenue", "Increase revenue by 20%", "high", "alice")
    assert obj.id.startswith("obj-")
    assert obj.tenant_id == "tenant-a"
    assert obj.title == "Grow revenue"
    assert obj.priority == Priority.HIGH
    assert obj.status == ObjectiveStatus.DRAFT

    fetched = await engine.get_objective("tenant-a", obj.id)
    assert fetched is not None
    assert fetched.title == "Grow revenue"

    updated = await engine.update_objective("tenant-a", obj.id, {"status": "active", "owner": "bob"})
    assert updated is not None
    assert updated.status == ObjectiveStatus.ACTIVE
    assert updated.owner == "bob"

    objs = await engine.list_objectives("tenant-a")
    assert len(objs) == 1

    active = await engine.list_objectives("tenant-a", status="active")
    assert len(active) == 1

    draft = await engine.list_objectives("tenant-a", status="draft")
    assert len(draft) == 0


# ── PSF: Tenant Isolation ────────────────────────────────────────

@pytest.mark.asyncio
async def test_strategic_objective_tenant_isolation():
    engine, _ = _make_engine()

    obj_apex = await engine.create_objective("apex", "Apex objective", priority="high")
    obj_nova = await engine.create_objective("nova", "Nova objective", priority="medium")

    apex_objs = await engine.list_objectives("apex")
    nova_objs = await engine.list_objectives("nova")

    assert len(apex_objs) == 1
    assert apex_objs[0].id == obj_apex.id
    assert apex_objs[0].tenant_id == "apex"

    assert len(nova_objs) == 1
    assert nova_objs[0].id == obj_nova.id
    assert nova_objs[0].tenant_id == "nova"

    cross = await engine.get_objective("apex", obj_nova.id)
    assert cross is None

    cross2 = await engine.get_objective("nova", obj_apex.id)
    assert cross2 is None


# ── PSF: Initiative Lifecycle ────────────────────────────────────

@pytest.mark.asyncio
async def test_initiative_lifecycle():
    engine, _ = _make_engine()

    obj = await engine.create_objective("t1", "Test objective")
    ini = await engine.create_initiative("t1", obj.id, "Test initiative", "Description", 50000, "owner1")
    assert ini is not None
    assert ini.objective_id == obj.id
    assert ini.status == InitiativeStatus.PLANNED

    updated = await engine.update_initiative_status("t1", ini.id, "in_progress")
    assert updated is not None
    assert updated.status == InitiativeStatus.IN_PROGRESS

    bad = await engine.create_initiative("t1", "obj-nonexistent", "Bad initiative")
    assert bad is None

    inis = await engine.list_initiatives("t1")
    assert len(inis) == 1

    inis_for_obj = await engine.list_initiatives("t1", objective_id=obj.id)
    assert len(inis_for_obj) == 1


# ── PSF: State Supersession ─────────────────────────────────────

@pytest.mark.asyncio
async def test_strategy_state_supersession():
    engine, _ = _make_engine()

    await engine.create_objective("t1", "Obj1")
    state1 = await engine.snapshot_state("t1", "initial baseline")
    assert state1.version == 1
    assert state1.supersedes is None

    await engine.create_objective("t1", "Obj2")
    state2 = await engine.snapshot_state("t1", "added new objective")
    assert state2.version == 2
    assert state2.supersedes == state1.id

    history = await engine.get_state_history("t1")
    assert len(history) == 2

    current = await engine.get_current_state("t1")
    assert current is not None
    assert current.version == 2

    comparison = await engine.compare_states("t1", state1.id, state2.id)
    assert comparison["version_a"] == 1
    assert comparison["version_b"] == 2
    assert len(comparison["added"]) == 1

    obj1 = (await engine.list_objectives("t1", status="draft"))[0]
    new_obj = await engine.supersede_objective("t1", obj1.id, "Obj1 v2", "Updated version")
    assert new_obj is not None
    assert new_obj.supersedes == obj1.id

    old = await engine.get_objective("t1", obj1.id)
    assert old is not None
    assert old.status == ObjectiveStatus.SUPERSEDED


# ── RIL: Intelligence Cycle Lifecycle ────────────────────────────

@pytest.mark.asyncio
async def test_intelligence_cycle_lifecycle():
    ril = RecursiveIntelligenceEngine()

    cycle = await ril.start_cycle("t1", "Improve delivery speed", {"context": "test"})
    assert cycle.id.startswith("ril-")
    assert cycle.status == "started"
    assert cycle.tenant_id == "t1"

    await ril.observe(cycle.id, "t1", [{"signal": "delivery_time", "value": 48}])
    assert cycle.status == "observed"
    assert len(cycle.observations) == 1

    reasoning = await ril.reason(cycle.id, "t1")
    assert "objective" in reasoning or "hypothesis_id" in reasoning
    assert cycle.status == "reasoned"

    plan = await ril.plan(cycle.id, "t1")
    assert "objective" in plan or "plan_id" in plan
    assert cycle.status == "planned"

    exec_result = await ril.execute(cycle.id, "t1")
    assert "status" in exec_result
    assert cycle.status in ("executed", "blocked", "pending_approval")

    measurements = await ril.measure(cycle.id, "t1")
    assert isinstance(measurements, list)
    assert cycle.status == "measured"

    reflection = await ril.reflect(cycle.id, "t1")
    assert "calibration" in reflection
    assert cycle.status == "reflected"

    correction = await ril.correct(cycle.id, "t1")
    assert "adjustments" in correction
    assert cycle.status == "corrected"

    result = await ril.update(cycle.id, "t1")
    assert "corrections_applied" in result
    assert cycle.status == "completed"

    replay = await ril.replay_cycle(cycle.id, "t1")
    assert replay["cycle_id"] == cycle.id
    assert replay["status"] == "completed"
    assert replay["steps"]["observations"] == 1


# ── RIL: Autonomy Bounds ────────────────────────────────────────

@pytest.mark.asyncio
async def test_intelligence_cycle_autonomy_bounds():
    class MockAutonomyEngine:
        def evaluate(self, **kwargs):
            return {"decision": "DENY", "reason": "test deny"}

    ril = RecursiveIntelligenceEngine(autonomy_engine=MockAutonomyEngine())

    cycle = await ril.start_cycle("t1", "Test autonomy")
    exec_result = await ril.execute(cycle.id, "t1")
    assert exec_result.get("error") == "autonomy denied"
    assert cycle.status == "blocked"


# ── EGE: Allow/Deny ─────────────────────────────────────────────

@pytest.mark.asyncio
async def test_governance_engine_allow_deny():
    ege = EnterpriseGovernanceEngine()

    record = ege.evaluate_action("t1", "alice", "read_data", "audit")
    assert record.decision == GovernanceDecision.ALLOW

    deny_policy = PolicyRule(
        id="pol-deny-1", tenant_id="t1", name="Deny risky actions",
        conditions=(PolicyCondition(field="risk", operator="equals", value="high"),),
        effect=GovernanceDecision.DENY, priority=10,
    )
    ege.register_policy(deny_policy)

    record2 = ege.evaluate_action("t1", "bob", "delete_all", "test", risk_level="high")
    assert record2.decision == GovernanceDecision.DENY
    assert "Deny risky actions" in record2.reason

    history = ege.get_decision_history("t1")
    assert len(history) == 2


# ── EGE: Approval Required ──────────────────────────────────────

@pytest.mark.asyncio
async def test_governance_engine_approval_required():
    class MockAutonomy:
        def evaluate(self, **kwargs):
            return {"decision": "REQUIRE_APPROVAL", "reason": "high risk"}

    ege = EnterpriseGovernanceEngine(autonomy_engine=MockAutonomy())

    record = ege.evaluate_action("t1", "alice", "deploy_model", "production", risk_level="high")
    assert record.decision == GovernanceDecision.APPROVAL
    assert "requires approval" in record.reason

    ege.register_policy(PolicyRule(id="pol-esc-1", tenant_id="t1", name="Escalate expensive",
        conditions=(PolicyCondition(field="cost", operator="gt", value=10000),),
        effect=GovernanceDecision.ESCALATE))
    result = ege.check_policy("t1", "pol-esc-1", {"cost": 50000})
    assert result["found"] is True
    assert result["matches"] is True


# ── KCR: Strategic Context Assembly ─────────────────────────────

@pytest.mark.asyncio
async def test_kcr_strategic_context_assembly():
    from eaip.knowledge.kcr import KCRService

    engine, _ = _make_engine()
    await engine.create_objective("t1", "Test Obj", priority="high")
    await engine.create_initiative("t1", (await engine.list_objectives("t1"))[0].id, "Test Ini")

    kcr = KCRService()
    result = await kcr.assemble_strategic_context("t1", "what are our priorities", strategy_engine=engine)

    assert result["tenant_id"] == "t1"
    assert result["context_type"] == "strategic"
    assert result["count"] >= 2

    sources = [p["source"] for p in result["parts"]]
    assert "strategic_objective" in sources
    assert "strategic_initiative" in sources


# ── Strategy Graph: Connections ──────────────────────────────────

@pytest.mark.asyncio
async def test_strategy_graph_connections():
    graph = StrategyExecutionGraph()

    await graph.connect_objective_to_initiative("obj-1", "ini-1")
    await graph.connect_initiative_to_mission("ini-1", "mis-1")
    await graph.connect_mission_to_workflow("mis-1", "wf-1")
    await graph.connect_workflow_to_outcome("wf-1", "out-1")

    chain = await graph.trace_objective_to_outcomes("obj-1")
    assert len(chain) == 4
    assert chain[0]["edge_type"] == "objective_to_initiative"
    assert chain[-1]["edge_type"] == "workflow_to_outcome"
    assert chain[-1]["target"] == "out-1"

    sg = await graph.get_strategy_graph("t1")
    assert sg["node_count"] == 5
    assert sg["edge_count"] == 4

    downstream = await graph.get_downstream("ini-1")
    assert "mis-1" in downstream

    upstream = await graph.get_upstream("mis-1")
    assert "ini-1" in upstream


# ── Conductor: Strategy Intents ──────────────────────────────────

@pytest.mark.asyncio
async def test_conductor_strategy_intents():
    from eaip.copilot.m4_intents import register_m4_intents

    class MockTool:
        pass

    class MockPlanner:
        def __init__(self):
            self._tools = {
                "list_objectives": MockTool(), "list_risks": MockTool(),
                "list_cycles": MockTool(), "replay_cycle": MockTool(),
                "get_decision_history": MockTool(), "get_state_history": MockTool(),
                "trace_objective": MockTool(), "list_kpis": MockTool(),
            }
            self._last_plan = None

        def _route(self, text, message):
            return None

        def plan(self, message):
            text = message.strip().lower()
            for outcome in (self._route(text, message),):
                if outcome is not None:
                    return outcome
            return None

    planner = MockPlanner()
    register_m4_intents(planner)

    plan = planner._route("what are our strategic priorities", "What are our strategic priorities?")
    assert plan is not None
    assert plan.tool_call.tool_name == "list_objectives"

    plan2 = planner._route("what changed in strategy", "What changed in strategy?")
    assert plan2 is not None
    assert plan2.tool_call.tool_name == "get_state_history"

    plan3 = planner._route("which initiatives are at risk", "Which initiatives are at risk?")
    assert plan3 is not None
    assert plan3.tool_call.tool_name == "list_risks"

    plan4 = planner._route("show the reasoning", "Show the reasoning")
    assert plan4 is not None
    assert plan4.tool_call.tool_name == "replay_cycle"

    plan5 = planner._route("show the evidence", "Show the evidence")
    assert plan5 is not None
    assert plan5.tool_call.tool_name == "get_decision_history"


# ── PSF: Constraints ─────────────────────────────────────────────

@pytest.mark.asyncio
async def test_constraints():
    engine, _ = _make_engine()

    from datetime import timedelta
    from eaip.shared.time import utc_now
    now = utc_now()

    con = await engine.create_constraint("t1", "budget", "Budget limit", "high",
        now - timedelta(days=1), now + timedelta(days=30))
    assert con.type == "budget"
    assert con.severity.value == "high"

    violations = await engine.check_constraints("t1", {"budget": "exceeded"})
    assert len(violations) == 1
    assert violations[0]["constraint_id"] == con.id

    violations2 = await engine.check_constraints("t1", {"other": "ok"})
    assert len(violations2) == 0


# ── PSF: Risks and KPIs ─────────────────────────────────────────

@pytest.mark.asyncio
async def test_risks_and_kpis():
    engine, _ = _make_engine()

    obj = await engine.create_objective("t1", "Test obj")
    risk = await engine.create_risk("t1", obj.id, "High risk", "high", "critical", "Mitigation plan")
    assert risk.objective_id == obj.id
    assert risk.likelihood.value == "high"

    kpi = await engine.create_kpi("t1", obj.id, "Revenue", 100000, 75000, "improving")
    assert kpi.name == "Revenue"
    assert kpi.target == 100000

    risks = await engine.list_risks("t1", objective_id=obj.id)
    assert len(risks) == 1

    kpis = await engine.list_kpis("t1", objective_id=obj.id)
    assert len(kpis) == 1


# ── PSF: Themes and Milestones ──────────────────────────────────

@pytest.mark.asyncio
async def test_themes_and_milestones():
    engine, _ = _make_engine()

    theme = await engine.create_theme("t1", "Digital Transformation", "Core theme", 0.9)
    assert theme.name == "Digital Transformation"
    assert theme.weight == 0.9

    themes = await engine.list_themes("t1")
    assert len(themes) == 1

    obj = await engine.create_objective("t1", "Obj1")
    ini = await engine.create_initiative("t1", obj.id, "Ini1")
    ms = await engine.create_milestone("t1", ini.id, "Phase 1 Complete")
    assert ms.initiative_id == ini.id

    milestones = await engine.list_milestones("t1", initiative_id=ini.id)
    assert len(milestones) == 1
