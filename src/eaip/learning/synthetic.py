"""M5 Synthetic Data — Apex, Nova, Meridian learning scenarios."""

from __future__ import annotations

import uuid
from typing import Any

from eaip.learning.engine import OrganizationalLearningEngine
from eaip.learning.feedback_loop import FeedbackLoop
from eaip.learning.models import LearningSource


def seed_apex_learning(engine: OrganizationalLearningEngine, feedback: FeedbackLoop, tenant_id: str = "apex") -> dict[str, Any]:
    """Seed Apex: historical decision outcomes, methodology lessons, client engagement learning."""
    records: list[str] = []

    r1 = engine.observe(tenant_id, LearningSource.DECISION, "dec-apex-001", {
        "title": "Pricing strategy shift",
        "outcome": "Revenue increased 12% after dynamic pricing adoption",
        "success": True,
        "improvement": True,
    })
    records.append(r1.id)

    r2 = engine.observe(tenant_id, LearningSource.MISSION, "mission-apex-001", {
        "title": "Q3 client engagement review",
        "outcome": "Client retention improved with proactive outreach",
        "success": True,
    })
    records.append(r2.id)

    r3 = engine.observe(tenant_id, LearningSource.STRATEGY_PERFORMANCE, "strat-apex-001", {
        "title": "Market expansion methodology",
        "outcome": "Regional expansion failed due to insufficient local research",
        "failure": True,
    })
    records.append(r3.id)

    r4 = engine.observe(tenant_id, LearningSource.WORKFLOW, "wf-apex-001", {
        "title": "Contract review automation",
        "outcome": "Automated review reduced cycle time by 40%",
        "success": True,
        "improvement": True,
    })
    records.append(r4.id)

    feedback.record_decision_outcome(tenant_id, "dec-apex-001", {"success": True, "revenue_change": 0.12})
    feedback.record_workflow_outcome(tenant_id, "wf-apex-001", True, {"cycle_time_reduction": 0.4})

    lessons: list[str] = []
    for rec_id in records[:2]:
        rec = engine._store.get_learning_record(tenant_id, rec_id)
        if rec:
            engine.evaluate(tenant_id, rec_id)
            lesson = engine.propose_learning(tenant_id, rec_id, f"Lesson from {rec.source_type.value}", rec.observation.get("title", ""))
            lessons.append(lesson.id)

    return {"tenant": tenant_id, "records": records, "lessons": lessons}


def seed_nova_learning(engine: OrganizationalLearningEngine, feedback: FeedbackLoop, tenant_id: str = "nova") -> dict[str, Any]:
    """Seed Nova: production failure lessons, maintenance decisions, supplier performance learning."""
    records: list[str] = []

    r1 = engine.observe(tenant_id, LearningSource.FAILURE, "fail-nova-001", {
        "title": "Database connection pool exhaustion",
        "outcome": "Service outage for 45 minutes due to connection leak",
        "error": True,
        "failure": True,
    })
    records.append(r1.id)

    r2 = engine.observe(tenant_id, LearningSource.AGENT_PERFORMANCE, "agent-nova-001", {
        "title": "Monitoring agent false positive rate",
        "outcome": "False positive rate reduced from 15% to 3% after threshold tuning",
        "success": True,
        "improvement": True,
    })
    records.append(r2.id)

    r3 = engine.observe(tenant_id, LearningSource.DECISION, "dec-nova-001", {
        "title": "Supplier diversification decision",
        "outcome": "Multi-supplier strategy reduced supply chain risk by 60%",
        "success": True,
    })
    records.append(r3.id)

    r4 = engine.observe(tenant_id, LearningSource.WORKFLOW, "wf-nova-001", {
        "title": "Incident response automation",
        "outcome": "Automated triage reduced MTTR from 2h to 30min",
        "success": True,
        "improvement": True,
    })
    records.append(r4.id)

    feedback.record_prediction_outcome(tenant_id, "pred-nova-001", {"failure_count": 3}, {"failure_count": 5})
    feedback.record_agent_performance(tenant_id, "agent-nova-001", {"success_rate": 0.97, "latency_ms": 200})

    lessons: list[str] = []
    for rec_id in records[:2]:
        rec = engine._store.get_learning_record(tenant_id, rec_id)
        if rec:
            engine.evaluate(tenant_id, rec_id)
            lesson = engine.propose_learning(tenant_id, rec_id, f"Lesson from {rec.source_type.value}", rec.observation.get("title", ""))
            lessons.append(lesson.id)

    return {"tenant": tenant_id, "records": records, "lessons": lessons}


def seed_meridian_learning(engine: OrganizationalLearningEngine, feedback: FeedbackLoop, tenant_id: str = "meridian") -> dict[str, Any]:
    """Seed Meridian: operational lessons, compliance decisions, policy effectiveness learning."""
    records: list[str] = []

    r1 = engine.observe(tenant_id, LearningSource.RECOMMENDATION, "rec-meridian-001", {
        "title": "GDPR compliance automation",
        "outcome": "Automated data subject request handling reduced response time by 80%",
        "success": True,
        "improvement": True,
    })
    records.append(r1.id)

    r2 = engine.observe(tenant_id, LearningSource.DECISION, "dec-meridian-001", {
        "title": "Access control policy tightening",
        "outcome": "Zero security incidents after implementing least-privilege access",
        "success": True,
    })
    records.append(r2.id)

    r3 = engine.observe(tenant_id, LearningSource.WORKFLOW, "wf-meridian-001", {
        "title": "Audit trail generation",
        "outcome": "Full audit trail enabled compliance verification in under 5 minutes",
        "success": True,
    })
    records.append(r3.id)

    r4 = engine.observe(tenant_id, LearningSource.FEEDBACK, "fb-meridian-001", {
        "title": "User satisfaction with self-service portal",
        "outcome": "NPS increased from 35 to 62 after portal redesign",
        "success": True,
        "improvement": True,
    })
    records.append(r4.id)

    feedback.record_decision_outcome(tenant_id, "dec-meridian-001", {"success": True, "incidents": 0})
    feedback.record_workflow_outcome(tenant_id, "wf-meridian-001", True, {"compliance_time_min": 5})

    lessons: list[str] = []
    for rec_id in records[:2]:
        rec = engine._store.get_learning_record(tenant_id, rec_id)
        if rec:
            engine.evaluate(tenant_id, rec_id)
            lesson = engine.propose_learning(tenant_id, rec_id, f"Lesson from {rec.source_type.value}", rec.observation.get("title", ""))
            lessons.append(lesson.id)

    return {"tenant": tenant_id, "records": records, "lessons": lessons}


__all__ = [
    "seed_apex_learning",
    "seed_meridian_learning",
    "seed_nova_learning",
]
