"""Tests for AI Governance & Compliance subsystem."""

from __future__ import annotations

import pytest

from eaip.ai_governance.events import (
    AiAuditTrailEntryCreated,
    AiBiasCheckCompleted,
    AiComplianceCheckCompleted,
    AiComplianceCheckFailed,
    AiComplianceCheckStarted,
    AiComplianceReportGenerated,
    AiFairnessMetricComputed,
    AiGovernanceDashboardUpdated,
    AiGovernancePolicyCreated,
    AiGovernancePolicyEnforced,
    AiGovernancePolicyViolated,
    AiGovernanceReviewApproved,
    AiGovernanceReviewRejected,
    AiGovernanceReviewStarted,
    AiModelRiskAssessed,
)
from eaip.ai_governance.exceptions import (
    AiBiasDetectionError,
    AiComplianceCheckError,
    AiComplianceError,
    AiComplianceRequirementError,
    AiExplainabilityError,
    AiFairnessError,
    AiGovernanceError,
    AiGovernancePolicyError,
    AiGovernanceViolationError,
    AiReviewError,
    AiRiskAssessmentError,
)
from eaip.ai_governance.health import AiGovernanceHealthCheck
from eaip.ai_governance.integration import AiGovernanceRuntimeModule
from eaip.ai_governance.models import (
    AiAuditTrail,
    AiBiasCheckResult,
    AiComplianceCheck,
    AiComplianceReport,
    AiComplianceResult,
    AiExplainabilityRecord,
    AiFairnessMetric,
    AiGovernanceConfig,
    AiGovernanceDashboard,
    AiGovernancePolicy,
    AiGovernanceReview,
    AiGovernanceRule,
    AiModelRiskAssessment,
    ComplianceStandard,
    ComplianceStatus,
    PolicyType,
    ReviewStatus,
    RiskLevel,
)
from eaip.ai_governance.service import AiGovernanceService
from eaip.health.checks import HealthStatus


class TestModels:
    def test_ai_governance_policy_defaults(self) -> None:
        policy = AiGovernancePolicy(id="p1", name="Test Policy", policy_type=PolicyType.SAFETY)
        assert policy.id == "p1"
        assert policy.name == "Test Policy"
        assert policy.policy_type == PolicyType.SAFETY
        assert policy.enabled is True
        assert policy.version == "1.0.0"

    def test_ai_governance_rule_frozen(self) -> None:
        rule = AiGovernanceRule(id="r1", name="Rule 1", policy_type=PolicyType.USAGE)
        with pytest.raises(AttributeError):
            rule.name = "Changed"

    def test_ai_governance_config_defaults(self) -> None:
        config = AiGovernanceConfig()
        assert config.enabled is True
        assert config.auto_enforce is False
        assert config.compliance_check_interval_hours == 24

    def test_compliance_status_enum(self) -> None:
        assert ComplianceStatus.COMPLIANT.value == "compliant"
        assert ComplianceStatus.NON_COMPLIANT.value == "non_compliant"

    def test_risk_level_enum(self) -> None:
        assert RiskLevel.LOW.value == "low"
        assert RiskLevel.CRITICAL.value == "critical"

    def test_review_status_enum(self) -> None:
        assert ReviewStatus.PENDING.value == "pending"
        assert ReviewStatus.APPROVED.value == "approved"

    def test_policy_type_enum(self) -> None:
        assert PolicyType.USAGE.value == "usage"
        assert PolicyType.COMPLIANCE.value == "compliance"

    def test_compliance_standard_enum(self) -> None:
        assert ComplianceStandard.ISO_42001.value == "iso_42001"
        assert ComplianceStandard.EU_AI_ACT.value == "eu_ai_act"

    def test_ai_audit_trail_defaults(self) -> None:
        entry = AiAuditTrail(id="a1", action="test_action")
        assert entry.actor == ""
        assert entry.resource_id == ""

    def test_ai_bias_check_result_defaults(self) -> None:
        result = AiBiasCheckResult(id="b1")
        assert result.bias_score == 0.0
        assert result.biased is False

    def test_ai_fairness_metric(self) -> None:
        metric = AiFairnessMetric(
            id="f1", model_id="m1", metric_name="demographic_parity", value=0.05
        )
        assert metric.metric_name == "demographic_parity"
        assert metric.passed is False

    def test_ai_model_risk_assessment_defaults(self) -> None:
        assessment = AiModelRiskAssessment(id="ra1", model_id="m1")
        assert assessment.risk_level == RiskLevel.LOW
        assert assessment.risk_score == 0.0

    def test_ai_explainability_record(self) -> None:
        record = AiExplainabilityRecord(id="e1", model_id="m1", prediction_id="p1", method="shap")
        assert record.method == "shap"

    def test_ai_compliance_check_defaults(self) -> None:
        check = AiComplianceCheck(id="c1", requirement_id="r1", name="Check 1")
        assert check.status == ComplianceStatus.PENDING

    def test_ai_compliance_report(self) -> None:
        report = AiComplianceReport(id="r1", name="Report", standard=ComplianceStandard.ISO_42001)
        assert report.overall_status == ComplianceStatus.PENDING
        assert report.score == 0.0

    def test_ai_governance_review(self) -> None:
        review = AiGovernanceReview(id="rv1", resource_id="res1", resource_type="model")
        assert review.status == ReviewStatus.PENDING
        assert review.completed_at is None

    def test_ai_governance_dashboard_defaults(self) -> None:
        dash = AiGovernanceDashboard(id="d1")
        assert dash.total_policies == 0
        assert dash.overall_compliance_score == 0.0

    def test_ai_compliance_result(self) -> None:
        result = AiComplianceResult(
            check_id="c1",
            requirement_id="r1",
            status=ComplianceStatus.COMPLIANT,
            score=95.0,
        )
        assert result.score == 95.0
        assert result.status == ComplianceStatus.COMPLIANT


class TestEvents:
    def test_policy_created_event_type(self) -> None:
        event = AiGovernancePolicyCreated(policy_id="p1", policy_name="Test", policy_type="safety")
        assert event.event_type == "eaip.ai_governance.policy.created"
        assert event.policy_id == "p1"

    def test_policy_enforced_event(self) -> None:
        event = AiGovernancePolicyEnforced(
            policy_id="p1",
            policy_name="Test",
            subject_id="user1",
            action="infer",
            resource="model:x",
        )
        assert event.subject_id == "user1"

    def test_policy_violated_event(self) -> None:
        event = AiGovernancePolicyViolated(
            policy_id="p1",
            policy_name="Test",
            subject_id="user1",
            action="infer",
            resource="model:x",
            explanation="Blocked",
        )
        assert event.explanation == "Blocked"

    def test_compliance_check_started(self) -> None:
        event = AiComplianceCheckStarted(check_id="c1", requirement_id="r1", standard="iso_42001")
        assert event.event_type == "eaip.ai_governance.compliance.check_started"

    def test_compliance_check_completed(self) -> None:
        event = AiComplianceCheckCompleted(
            check_id="c1", requirement_id="r1", status="compliant", score=100.0
        )
        assert event.score == 100.0

    def test_compliance_check_failed(self) -> None:
        event = AiComplianceCheckFailed(check_id="c1", requirement_id="r1", error="timeout")
        assert event.error == "timeout"

    def test_report_generated_event(self) -> None:
        event = AiComplianceReportGenerated(
            report_id="r1", standard="iso_42001", overall_status="compliant", score=95.0
        )
        assert event.score == 95.0

    def test_audit_trail_entry_created(self) -> None:
        event = AiAuditTrailEntryCreated(entry_id="e1", action="policy.created", actor="admin")
        assert event.actor == "admin"

    def test_review_started_event(self) -> None:
        event = AiGovernanceReviewStarted(
            review_id="rv1", resource_id="res1", resource_type="model", reviewer="admin"
        )
        assert event.reviewer == "admin"

    def test_review_approved_event(self) -> None:
        event = AiGovernanceReviewApproved(
            review_id="rv1", resource_id="res1", reviewer="admin", comments="Looks good"
        )
        assert event.event_type == "eaip.ai_governance.review.approved"

    def test_review_rejected_event(self) -> None:
        event = AiGovernanceReviewRejected(
            review_id="rv1", resource_id="res1", reviewer="admin", comments="Needs work"
        )
        assert event.comments == "Needs work"

    def test_bias_check_completed_event(self) -> None:
        event = AiBiasCheckCompleted(check_id="b1", model_id="m1", bias_score=0.05, biased=False)
        assert event.biased is False

    def test_fairness_metric_computed_event(self) -> None:
        event = AiFairnessMetricComputed(
            metric_id="f1", model_id="m1", metric_name="parity", value=0.1, passed=True
        )
        assert event.passed is True

    def test_model_risk_assessed_event(self) -> None:
        event = AiModelRiskAssessed(
            assessment_id="a1",
            model_id="m1",
            model_name="gpt-4",
            risk_level="low",
            risk_score=0.1,
        )
        assert event.risk_score == 0.1

    def test_dashboard_updated_event(self) -> None:
        event = AiGovernanceDashboardUpdated(
            dashboard_id="d1", overall_compliance_score=85.0, total_policies=5
        )
        assert event.total_policies == 5


class TestExceptions:
    def test_ai_governance_error(self) -> None:
        err = AiGovernanceError("test error")
        assert "test error" in str(err)

    def test_ai_governance_policy_error(self) -> None:
        err = AiGovernancePolicyError("policy error")
        assert isinstance(err, AiGovernanceError)

    def test_ai_governance_violation_error(self) -> None:
        err = AiGovernanceViolationError("violation")
        assert isinstance(err, AiGovernanceError)

    def test_ai_compliance_error(self) -> None:
        err = AiComplianceError("compliance error")
        assert isinstance(err, AiGovernanceError)

    def test_ai_compliance_requirement_error(self) -> None:
        err = AiComplianceRequirementError("req error")
        assert isinstance(err, AiComplianceError)

    def test_ai_compliance_check_error(self) -> None:
        err = AiComplianceCheckError("check error")
        assert isinstance(err, AiComplianceError)

    def test_ai_bias_detection_error(self) -> None:
        err = AiBiasDetectionError("bias error")
        assert isinstance(err, AiGovernanceError)

    def test_ai_fairness_error(self) -> None:
        err = AiFairnessError("fairness error")
        assert isinstance(err, AiGovernanceError)

    def test_ai_explainability_error(self) -> None:
        err = AiExplainabilityError("explain error")
        assert isinstance(err, AiGovernanceError)

    def test_ai_review_error(self) -> None:
        err = AiReviewError("review error")
        assert isinstance(err, AiGovernanceError)

    def test_ai_risk_assessment_error(self) -> None:
        err = AiRiskAssessmentError("risk error")
        assert isinstance(err, AiGovernanceError)


class TestHealthCheck:
    async def test_healthy(self) -> None:
        check = AiGovernanceHealthCheck(policy_count=3, requirement_count=5)
        report = await check.check()
        assert report.status == HealthStatus.HEALTHY
        assert report.details["policy_count"] == 3

    async def test_degraded_no_policies(self) -> None:
        check = AiGovernanceHealthCheck(policy_count=0)
        report = await check.check()
        assert report.status == HealthStatus.DEGRADED

    async def test_degraded_check_failed(self) -> None:
        check = AiGovernanceHealthCheck(
            policy_count=2, requirement_count=0, last_check_passed=False
        )
        report = await check.check()
        assert report.status == HealthStatus.DEGRADED


class TestIntegration:
    async def test_runtime_module_defaults(self) -> None:
        module = AiGovernanceRuntimeModule()
        assert module.name == "ai_governance"
        assert module.startup_duration == 0.0
        assert module.service is not None

    async def test_start_stop(self) -> None:
        module = AiGovernanceRuntimeModule()
        await module.start()
        assert module.startup_duration >= 0.0
        await module.stop()


class TestService:
    async def test_create_policy(self) -> None:
        svc = AiGovernanceService()
        policy = await svc.create_policy(
            name="Safety Policy",
            policy_type=PolicyType.SAFETY,
            description="Ensures AI safety",
        )
        assert policy.name == "Safety Policy"
        assert policy.policy_type == PolicyType.SAFETY
        assert policy.id in svc._policies

    async def test_create_policy_empty_name_raises(self) -> None:
        svc = AiGovernanceService()
        with pytest.raises(AiGovernancePolicyError):
            await svc.create_policy(name="", policy_type=PolicyType.USAGE)

    async def test_get_policy_not_found(self) -> None:
        svc = AiGovernanceService()
        with pytest.raises(AiGovernancePolicyError):
            await svc.get_policy("nonexistent")

    async def test_list_policies(self) -> None:
        svc = AiGovernanceService()
        await svc.create_policy(name="P1", policy_type=PolicyType.USAGE)
        await svc.create_policy(name="P2", policy_type=PolicyType.SAFETY)
        policies = await svc.list_policies()
        assert len(policies) == 2

    async def test_list_policies_filtered(self) -> None:
        svc = AiGovernanceService()
        await svc.create_policy(name="P1", policy_type=PolicyType.USAGE)
        await svc.create_policy(name="P2", policy_type=PolicyType.SAFETY)
        policies = await svc.list_policies(policy_type=PolicyType.SAFETY)
        assert len(policies) == 1
        assert policies[0].name == "P2"

    async def test_update_policy(self) -> None:
        svc = AiGovernanceService()
        policy = await svc.create_policy(name="Old", policy_type=PolicyType.ETHICS)
        updated = await svc.update_policy(policy.id, name="New", enabled=False)
        assert updated.name == "New"
        assert updated.enabled is False

    async def test_enforce_policy_no_rules(self) -> None:
        svc = AiGovernanceService()
        policy = await svc.create_policy(name="Test", policy_type=PolicyType.ACCESS)
        with pytest.raises(AiGovernanceViolationError):
            await svc.enforce_policy(
                policy_id=policy.id,
                subject_id="user1",
                action="infer",
                resource="model:x",
            )

    async def test_enforce_policy_with_matching_rule(self) -> None:
        svc = AiGovernanceService()
        rule = AiGovernanceRule(
            id="r1", name="Allow Infer", policy_type=PolicyType.ACCESS, actions=("infer",)
        )
        policy = await svc.create_policy(
            name="Access Policy",
            policy_type=PolicyType.ACCESS,
            rules=(rule,),
        )
        result = await svc.enforce_policy(
            policy_id=policy.id,
            subject_id="user1",
            action="infer",
            resource="model:x",
        )
        assert result is True

    async def test_create_requirement(self) -> None:
        svc = AiGovernanceService()
        req = await svc.create_requirement(
            name="GDPR Compliance",
            standard=ComplianceStandard.GDPR,
        )
        assert req.name == "GDPR Compliance"
        assert req.standard == ComplianceStandard.GDPR

    async def test_create_requirement_empty_name_raises(self) -> None:
        svc = AiGovernanceService()
        with pytest.raises(AiComplianceRequirementError):
            await svc.create_requirement(name="", standard=ComplianceStandard.GDPR)

    async def test_get_requirement_not_found(self) -> None:
        svc = AiGovernanceService()
        with pytest.raises(AiComplianceRequirementError):
            await svc.get_requirement("nonexistent")

    async def test_list_requirements(self) -> None:
        svc = AiGovernanceService()
        await svc.create_requirement(name="R1", standard=ComplianceStandard.GDPR)
        await svc.create_requirement(name="R2", standard=ComplianceStandard.ISO_42001)
        reqs = await svc.list_requirements()
        assert len(reqs) == 2

    async def test_run_and_complete_compliance_check(self) -> None:
        svc = AiGovernanceService()
        req = await svc.create_requirement(name="Test Req", standard=ComplianceStandard.CUSTOM)
        check = await svc.run_compliance_check(req.id)
        assert check.requirement_id == req.id

        result = await svc.complete_compliance_check(
            check.id,
            status=ComplianceStatus.COMPLIANT,
            score=100.0,
            summary="All checks passed",
        )
        assert result.score == 100.0
        assert result.status == ComplianceStatus.COMPLIANT

    async def test_complete_compliance_check_not_found(self) -> None:
        svc = AiGovernanceService()
        with pytest.raises(AiComplianceCheckError):
            await svc.complete_compliance_check("nonexistent", status=ComplianceStatus.COMPLIANT)

    async def test_generate_compliance_report(self) -> None:
        svc = AiGovernanceService()
        req = await svc.create_requirement(name="R1", standard=ComplianceStandard.ISO_42001)
        check = await svc.run_compliance_check(req.id)
        await svc.complete_compliance_check(
            check.id, status=ComplianceStatus.COMPLIANT, score=100.0
        )
        report = await svc.generate_compliance_report(ComplianceStandard.ISO_42001)
        assert report.score == 100.0
        assert report.total_checks == 1
        assert report.passed_checks == 1

    async def test_create_audit_entry(self) -> None:
        svc = AiGovernanceService()
        entry = await svc.create_audit_entry(
            action="policy.created",
            actor="admin",
            resource_id="p1",
            resource_type="policy",
        )
        assert entry.action == "policy.created"

    async def test_list_audit_entries(self) -> None:
        svc = AiGovernanceService()
        await svc.create_audit_entry(action="create", actor="admin")
        await svc.create_audit_entry(action="update", actor="user1")
        entries = await svc.list_audit_entries()
        assert len(entries) == 2
        entries = await svc.list_audit_entries(actor="admin")
        assert len(entries) == 1

    async def test_start_review(self) -> None:
        svc = AiGovernanceService()
        review = await svc.start_review(
            resource_id="model:1",
            resource_type="model",
            reviewer="admin",
        )
        assert review.resource_id == "model:1"
        assert review.status == ReviewStatus.PENDING

    async def test_approve_review(self) -> None:
        svc = AiGovernanceService()
        review = await svc.start_review(
            resource_id="model:1", resource_type="model", reviewer="admin"
        )
        approved = await svc.approve_review(review.id, comments="Approved")
        assert approved.status == ReviewStatus.APPROVED
        assert approved.decision == "approved"

    async def test_reject_review(self) -> None:
        svc = AiGovernanceService()
        review = await svc.start_review(
            resource_id="model:1", resource_type="model", reviewer="admin"
        )
        rejected = await svc.reject_review(review.id, comments="Rejected")
        assert rejected.status == ReviewStatus.REJECTED
        assert rejected.decision == "rejected"

    async def test_review_not_found(self) -> None:
        svc = AiGovernanceService()
        with pytest.raises(AiReviewError):
            await svc.approve_review("nonexistent")

    async def test_assess_model_risk_low(self) -> None:
        svc = AiGovernanceService()
        assessment = await svc.assess_model_risk(
            model_id="m1",
            model_name="test-model",
            dimensions={"bias": 0.1, "toxicity": 0.05},
        )
        assert assessment.risk_level == RiskLevel.LOW
        assert assessment.model_id == "m1"

    async def test_assess_model_risk_critical(self) -> None:
        svc = AiGovernanceService()
        assessment = await svc.assess_model_risk(
            model_id="m1",
            dimensions={"bias": 0.9, "toxicity": 0.85},
        )
        assert assessment.risk_level == RiskLevel.CRITICAL

    async def test_get_risk_assessment_not_found(self) -> None:
        svc = AiGovernanceService()
        with pytest.raises(AiRiskAssessmentError):
            await svc.get_risk_assessment("nonexistent")

    async def test_list_risk_assessments(self) -> None:
        svc = AiGovernanceService()
        await svc.assess_model_risk(model_id="m1", dimensions={"bias": 0.1})
        await svc.assess_model_risk(model_id="m2", dimensions={"bias": 0.9})
        assessments = await svc.list_risk_assessments()
        assert len(assessments) == 2
        high = await svc.list_risk_assessments(risk_level=RiskLevel.LOW)
        assert len(high) >= 1

    async def test_run_bias_check(self) -> None:
        svc = AiGovernanceService()
        result = await svc.run_bias_check(
            model_id="m1",
            dataset_id="ds1",
            dimensions={"gender": 0.02, "race": 0.01},
        )
        assert result.biased is False
        assert result.model_id == "m1"

    async def test_run_bias_check_detected(self) -> None:
        svc = AiGovernanceService()
        result = await svc.run_bias_check(
            model_id="m1",
            dimensions={"gender": 0.5, "race": 0.6},
            threshold=0.1,
        )
        assert result.biased is True
        assert len(result.recommendations) > 0

    async def test_get_bias_check(self) -> None:
        svc = AiGovernanceService()
        result = await svc.run_bias_check(model_id="m1")
        fetched = await svc.get_bias_check(result.id)
        assert fetched.id == result.id

    async def test_compute_fairness_metric(self) -> None:
        svc = AiGovernanceService()
        metric = await svc.compute_fairness_metric(
            model_id="m1",
            metric_name="demographic_parity",
            value=0.05,
            threshold=0.1,
        )
        assert metric.passed is True
        assert metric.metric_name == "demographic_parity"

    async def test_compute_fairness_metric_failed(self) -> None:
        svc = AiGovernanceService()
        metric = await svc.compute_fairness_metric(
            model_id="m1",
            metric_name="equal_opportunity",
            value=0.15,
            threshold=0.1,
        )
        assert metric.passed is False

    async def test_get_fairness_metric(self) -> None:
        svc = AiGovernanceService()
        metric = await svc.compute_fairness_metric(model_id="m1", metric_name="test", value=0.0)
        fetched = await svc.get_fairness_metric(metric.id)
        assert fetched.id == metric.id

    async def test_get_dashboard(self) -> None:
        svc = AiGovernanceService()
        await svc.create_policy(name="P1", policy_type=PolicyType.SAFETY)
        await svc.create_policy(name="P2", policy_type=PolicyType.USAGE)
        dash = await svc.get_dashboard()
        assert dash.total_policies == 2
        assert dash.active_policies == 2
        assert dash.overall_compliance_score == 0.0
