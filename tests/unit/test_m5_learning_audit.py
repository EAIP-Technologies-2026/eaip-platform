"""M5 Tests — Learning, Audit, Governance."""

from __future__ import annotations

import pytest

from eaip.audit_chain.chain import AuditChain
from eaip.audit_chain.proof import ProofEngine
from eaip.audit_chain.replay import ReplayEngine
from eaip.audit_chain.verification import VerificationEngine
from eaip.governance_center.approval_workflows import ApprovalWorkflowEngine
from eaip.governance_center.service import GovernanceCenterService
from eaip.learning.adaptation import AdaptationEngine
from eaip.learning.engine import OrganizationalLearningEngine
from eaip.learning.feedback_loop import FeedbackLoop
from eaip.learning.models import LearningSource, LearningStatus
from eaip.learning.persistence import LearningStore


# ── Helpers ──────────────────────────────────────────────────

def _make_engine():
    store = LearningStore()
    events: list[object] = []
    engine = OrganizationalLearningEngine(store=store, event_publisher=events.append)
    feedback = FeedbackLoop(store=store, event_publisher=events.append, learning_engine=engine)
    adaptation = AdaptationEngine(store=store, event_publisher=events.append)
    return engine, feedback, adaptation, store, events


def _make_proof_engine():
    chain = AuditChain()
    proof = ProofEngine(audit_chain=chain)
    verification = VerificationEngine(proof_engine=proof)
    replay = ReplayEngine(proof_engine=proof)
    return proof, verification, replay, chain


# ── Learning Tests ──────────────────────────────────────────

def test_learning_record_lifecycle():
    engine, _, _, store, events = _make_engine()
    record = engine.observe("t1", LearningSource.DECISION, "dec-1", {"title": "test"})
    assert record.status == LearningStatus.PROPOSED
    assert record.tenant_id == "t1"

    evaluated = engine.evaluate("t1", record.id)
    assert evaluated.status == LearningStatus.VALIDATING

    lesson = engine.propose_learning("t1", record.id, "Test lesson", "Description")
    assert lesson.status == LearningStatus.PROPOSED

    validated = engine.validate("t1", lesson.id)
    assert validated.status == LearningStatus.VALIDATING

    approved = engine.approve("t1", lesson.id, "appr-1")
    assert approved.status == LearningStatus.APPROVED

    activated = engine.activate("t1", lesson.id)
    assert activated.status == LearningStatus.ACTIVATED
    assert activated.effective_date is not None


def test_learning_tenant_isolation():
    engine, _, _, _, _ = _make_engine()
    engine.observe("t1", LearningSource.DECISION, "dec-1", {"title": "t1 obs"})
    engine.observe("t2", LearningSource.DECISION, "dec-2", {"title": "t2 obs"})

    t1_records = engine.get_learning_history("t1")
    t2_records = engine.get_learning_history("t2")
    assert len(t1_records) == 1
    assert len(t2_records) == 1
    assert t1_records[0].tenant_id == "t1"
    assert t2_records[0].tenant_id == "t2"


def test_lesson_proposal_and_approval():
    engine, _, _, _, _ = _make_engine()
    record = engine.observe("t1", LearningSource.FAILURE, "fail-1", {"error": True, "failure": True})
    engine.evaluate("t1", record.id)
    lesson = engine.propose_learning("t1", record.id, "Learn from failure")
    assert lesson.confidence > 0

    rejected = engine.reject("t1", lesson.id, "Not applicable")
    assert rejected.status == LearningStatus.REJECTED


def test_lesson_supersede():
    engine, _, _, _, _ = _make_engine()
    r1 = engine.observe("t1", LearningSource.SUCCESS, "s-1", {"success": True})
    r2 = engine.observe("t1", LearningSource.SUCCESS, "s-2", {"success": True, "improvement": True})
    engine.evaluate("t1", r1.id)
    engine.evaluate("t1", r2.id)
    l1 = engine.propose_learning("t1", r1.id, "Old lesson")
    l2 = engine.propose_learning("t1", r2.id, "New lesson")
    engine.approve("t1", l1.id)
    engine.activate("t1", l1.id)
    superseded = engine.supersede("t1", l1.id, l2.id)
    assert superseded.status == LearningStatus.SUPERSEDED


# ── Feedback Loop Tests ─────────────────────────────────────

def test_feedback_loop_prediction_outcome():
    _, feedback, _, store, events = _make_engine()
    fb = feedback.record_prediction_outcome(
        "t1", "pred-1", {"value": 100}, {"value": 80}
    )
    assert fb.error > 0
    assert fb.quality_score < 1.0

    summary = feedback.get_feedback_summary("t1")
    assert summary["total"] == 1
    assert "prediction" in summary["by_source"]


def test_feedback_loop_decision_outcome():
    _, feedback, _, _, _ = _make_engine()
    fb = feedback.record_decision_outcome("t1", "dec-1", {"success": True})
    assert fb.quality_score == 0.8


def test_feedback_loop_workflow_outcome():
    _, feedback, _, _, _ = _make_engine()
    fb = feedback.record_workflow_outcome("t1", "wf-1", True, {"duration_ms": 500})
    assert fb.quality_score == 1.0


def test_feedback_loop_agent_performance():
    _, feedback, _, _, _ = _make_engine()
    fb = feedback.record_agent_performance("t1", "agent-1", {"success_rate": 0.95, "latency_ms": 300})
    assert fb.quality_score > 0.5


# ── Adaptation Tests ────────────────────────────────────────

def test_adaptation_proposal_governance():
    engine, _, adaptation, _, _ = _make_engine()
    record = engine.observe("t1", LearningSource.WORKFLOW, "wf-1", {"title": "optimize"})
    engine.evaluate("t1", record.id)
    lesson = engine.propose_learning("t1", record.id, "Workflow lesson")

    proposal = adaptation.propose_workflow_improvement("t1", lesson.id, "wf-main")
    assert proposal.risk_level.value == "medium"
    assert proposal.status == LearningStatus.PROPOSED

    proposal2 = adaptation.propose_policy_recommendation("t1", lesson.id)
    assert proposal2.risk_level.value == "high"


# ── Execution Proof Tests ───────────────────────────────────

def test_execution_proof_generation():
    proof_engine, _, _, _ = _make_proof_engine()
    proof = proof_engine.generate_proof(
        tenant_id="t1",
        execution_id="exec-1",
        intent={"action": "deploy"},
        context={"env": "prod"},
        policy={"allow": True},
        inputs={"data": "test"},
        outputs={"result": "ok"},
    )
    assert proof.tenant_id == "t1"
    assert proof.execution_id == "exec-1"
    assert proof.current_hash != ""
    assert proof.intent_hash != ""
    assert proof.chain_index == 0


def test_proof_verification():
    proof_engine, _, _, _ = _make_proof_engine()
    proof = proof_engine.generate_proof("t1", "exec-1", intent={"action": "test"})
    result = proof_engine.verify_proof("t1", proof.proof_id)
    assert result.valid is True


def test_chain_verification():
    proof_engine, _, _, _ = _make_proof_engine()
    proof_engine.generate_proof("t1", "exec-1", intent={"a": 1})
    proof_engine.generate_proof("t1", "exec-2", intent={"a": 2})
    proof_engine.generate_proof("t1", "exec-3", intent={"a": 3})
    result = proof_engine.verify_chain("t1")
    assert result["valid"] is True
    assert result["count"] == 3


def test_tamper_detection():
    proof_engine, verification, _, _ = _make_proof_engine()
    proof_engine.generate_proof("t1", "exec-1")
    proof_engine.generate_proof("t1", "exec-2")
    tampered = verification.detect_tampering("t1")
    assert len(tampered) == 0


def test_secret_exclusion_from_proofs():
    proof_engine, _, _, _ = _make_proof_engine()
    proof = proof_engine.generate_proof(
        "t1", "exec-1",
        inputs={"data": "test", "secret_token": "s3cret", "password": "p@ss", "api_key": "key123"},
    )
    assert proof.input_hash != ""
    report = proof_engine.inspect_execution("t1", "exec-1")
    assert "secret_token" not in str(report)
    assert "password" not in str(report)
    assert "api_key" not in str(report)


def test_inspect_execution():
    proof_engine, _, _, _ = _make_proof_engine()
    proof_engine.generate_proof("t1", "exec-1", intent={"deploy": True})
    report = proof_engine.inspect_execution("t1", "exec-1")
    assert report["count"] == 1
    assert report["proofs"][0]["intent_hash"] != ""


# ── Replay Tests ────────────────────────────────────────────

def test_replay_execution():
    proof_engine, _, replay, _ = _make_proof_engine()
    proof_engine.generate_proof("t1", "exec-1", intent={"action": "test"})
    result = replay.replay_execution("t1", "exec-1")
    assert result.success is True
    assert result.mode == "simulated"
    assert len(result.steps) >= 2


def test_replay_idempotency():
    proof_engine, _, replay, _ = _make_proof_engine()
    proof_engine.generate_proof("t1", "exec-1")
    r1 = replay.replay_execution("t1", "exec-1")
    r2 = replay.replay_execution("t1", "exec-1")
    assert r1.replay_id == r2.replay_id


# ── Governance Tests ────────────────────────────────────────

def test_governance_policy_evaluation():
    svc = GovernanceCenterService()
    policy = svc.register_policy("t1", "test-policy", conditions={"env": "prod"}, effect="allow")
    result = svc.evaluate_policy("t1", policy.id, {"env": "prod"})
    assert result["allowed"] is True

    result2 = svc.evaluate_policy("t1", policy.id, {"env": "dev"})
    assert result2["allowed"] is False


def test_governance_tenant_isolation():
    svc = GovernanceCenterService()
    svc.register_policy("t1", "p1")
    svc.register_policy("t2", "p2")
    assert len(svc.list_policies("t1")) == 1
    assert len(svc.list_policies("t2")) == 1


def test_governance_decisions_exceptions_violations():
    svc = GovernanceCenterService()
    d = svc.record_decision("t1", "admin", "deploy", "approved", reason="all checks passed")
    assert d.decision == "approved"

    e = svc.record_exception("t1", "gp-1", "emergency fix", "cto")
    assert e.approver == "cto"

    v = svc.record_violation("t1", "gp-1", "unauthorized access", severity="high")
    assert v.severity == "high"

    metrics = svc.get_governance_metrics("t1")
    assert metrics.total_decisions == 1
    assert metrics.total_exceptions == 1
    assert metrics.total_violations == 1


# ── Approval Workflow Tests ─────────────────────────────────

def test_approval_workflow_lifecycle():
    engine = ApprovalWorkflowEngine()
    req = engine.create_approval_request("t1", "user-1", "deployment", target_id="deploy-1")
    assert req.status == "pending"

    approved = engine.approve("t1", req.id, "manager-1", reason="LGTM")
    assert approved.status == "approved"
    assert approved.approver == "manager-1"


def test_approval_reject_and_defer():
    engine = ApprovalWorkflowEngine()
    req1 = engine.create_approval_request("t1", "user-1", "policy_change")
    rejected = engine.reject("t1", req1.id, "manager-1", reason="too risky")
    assert rejected.status == "rejected"

    req2 = engine.create_approval_request("t1", "user-1", "budget")
    deferred = engine.defer("t1", req2.id, "manager-1", reason="need more info")
    assert deferred.status == "deferred"


def test_approval_expiry():
    engine = ApprovalWorkflowEngine()
    req = engine.create_approval_request("t1", "user-1", "temp_access", expires_at="2020-01-01T00:00:00")
    expired = engine.expire_approvals("t1")
    assert len(expired) == 1
    assert expired[0].status == "expired"


def test_pending_approvals():
    engine = ApprovalWorkflowEngine()
    engine.create_approval_request("t1", "u1", "type_a")
    engine.create_approval_request("t1", "u2", "type_b")
    req3 = engine.create_approval_request("t1", "u3", "type_c")
    engine.approve("t1", req3.id, "mgr")
    pending = engine.get_pending_approvals("t1")
    assert len(pending) == 2


# ── Conductor Intent Tests ──────────────────────────────────

def test_conductor_learning_intents():
    from eaip.copilot.m5_intents import M5IntentRouter
    router = M5IntentRouter({})

    result = router.route("what did eaip learn recently", "")
    assert result is not None
    assert result.tool_call.tool_name == "get_learning_history"

    result2 = router.route("show recent lessons", "")
    assert result2 is not None
    assert result2.tool_call.tool_name == "list_lessons"

    result3 = router.route("pending adaptations", "")
    assert result3 is not None
    assert result3.tool_call.tool_name == "list_adaptations"

    result4 = router.route("can i verify this execution", "")
    assert result4 is not None
    assert result4.tool_call.tool_name == "verify_chain"

    result5 = router.route("show me the execution proof for exec-1", "")
    assert result5 is not None
    assert result5.tool_call.tool_name == "get_execution_proof"
