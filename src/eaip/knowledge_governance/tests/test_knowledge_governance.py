"""Tests for Knowledge Governance."""

from __future__ import annotations

import uuid

import pytest

from eaip.knowledge_governance.events import (
    KnowledgeAuditTrailEntryCreated,
    KnowledgeClassificationUpdated,
    KnowledgeGovernanceConfigUpdated,
    KnowledgeGovernanceDashboardUpdated,
    KnowledgeGovernanceReportGenerated,
    KnowledgeQualityCheckCompleted,
    KnowledgeQualityCheckFailed,
    KnowledgeQualityCheckStarted,
    KnowledgeQualityScoreComputed,
    KnowledgeRetentionRuleApplied,
    KnowledgeSourceApproved,
    KnowledgeSourceRejected,
    KnowledgeSourceValidated,
    KnowledgeStewardshipAssigned,
    KnowledgeStewardshipUnassigned,
)
from eaip.knowledge_governance.exceptions import (
    KnowledgeClassificationError,
    KnowledgeGovernanceConfigError,
    KnowledgeGovernanceError,
    KnowledgeGovernancePolicyError,
    KnowledgeGovernanceViolationError,
    KnowledgeQualityError,
    KnowledgeRetentionError,
    KnowledgeSourceValidationError,
    KnowledgeStewardshipError,
)
from eaip.knowledge_governance.models import (
    GovernanceScope,
    KnowledgeClassificationLevel,
    KnowledgeGovernancePolicy,
    KnowledgeGovernanceRule,
    KnowledgeQualityMetric,
    KnowledgeRetentionAction,
    KnowledgeSourceStatus,
    KnowledgeStewardshipRole,
)
from eaip.knowledge_governance.service import KnowledgeGovernanceService


@pytest.fixture
def service() -> KnowledgeGovernanceService:
    return KnowledgeGovernanceService()


@pytest.fixture
def sample_rule() -> KnowledgeGovernanceRule:
    return KnowledgeGovernanceRule(
        id=str(uuid.uuid4()),
        name="test-rule",
        actions=("read", "write"),
        effect="allow",
    )


@pytest.mark.asyncio
async def test_create_policy(service: KnowledgeGovernanceService) -> None:
    policy = await service.create_policy("Test Policy", GovernanceScope.COLLECTION)
    assert policy.id is not None
    assert policy.name == "Test Policy"
    assert policy.scope == GovernanceScope.COLLECTION


@pytest.mark.asyncio
async def test_create_policy_empty_name(service: KnowledgeGovernanceService) -> None:
    with pytest.raises(KnowledgeGovernancePolicyError, match="Policy name is required"):
        await service.create_policy("")


@pytest.mark.asyncio
async def test_get_policy(
    service: KnowledgeGovernanceService, sample_rule: KnowledgeGovernanceRule
) -> None:
    created = await service.create_policy("Test", rules=(sample_rule,))
    retrieved = await service.get_policy(created.id)
    assert retrieved.id == created.id
    assert len(retrieved.rules) == 1


@pytest.mark.asyncio
async def test_get_policy_not_found(service: KnowledgeGovernanceService) -> None:
    with pytest.raises(KnowledgeGovernancePolicyError, match="not found"):
        await service.get_policy("nonexistent")


@pytest.mark.asyncio
async def test_list_policies(service: KnowledgeGovernanceService) -> None:
    await service.create_policy("Policy 1")
    await service.create_policy("Policy 2", GovernanceScope.COLLECTION)
    all_policies = await service.list_policies()
    assert len(all_policies) == 2
    coll_policies = await service.list_policies(GovernanceScope.COLLECTION)
    assert len(coll_policies) == 1


@pytest.mark.asyncio
async def test_update_policy(service: KnowledgeGovernanceService) -> None:
    created = await service.create_policy("Original")
    updated = await service.update_policy(created.id, name="Updated")
    assert updated.name == "Updated"
    assert updated.id == created.id


@pytest.mark.asyncio
async def test_enforce_policy(
    service: KnowledgeGovernanceService, sample_rule: KnowledgeGovernanceRule
) -> None:
    created = await service.create_policy("Test", rules=(sample_rule,))
    result = await service.enforce_policy(created.id, "user-1", "read", "resource-1")
    assert result is True


@pytest.mark.asyncio
async def test_enforce_policy_violated(service: KnowledgeGovernanceService) -> None:
    rule = KnowledgeGovernanceRule(
        id=str(uuid.uuid4()),
        name="deny-rule",
        actions=("delete",),
        effect="deny",
    )
    created = await service.create_policy("Strict", rules=(rule,))
    with pytest.raises(KnowledgeGovernanceViolationError):
        await service.enforce_policy(created.id, "user-1", "delete", "resource-1")


@pytest.mark.asyncio
async def test_enforce_policy_disabled(service: KnowledgeGovernanceService) -> None:
    created = await service.create_policy("Disabled")
    await service.update_policy(created.id, enabled=False)
    result = await service.enforce_policy(created.id, "user-1", "read", "resource-1")
    assert result is False


@pytest.mark.asyncio
async def test_start_quality_check(service: KnowledgeGovernanceService) -> None:
    check = await service.start_quality_check("res-1", "document", "Test Check")
    assert check.id is not None
    assert check.resource_id == "res-1"


@pytest.mark.asyncio
async def test_complete_quality_check(service: KnowledgeGovernanceService) -> None:
    check = await service.start_quality_check("res-1", "document")
    metric = KnowledgeQualityMetric(
        id=str(uuid.uuid4()),
        name="accuracy",
        value=0.95,
        threshold=0.8,
        passed=True,
    )
    result = await service.complete_quality_check(
        check_id=check.id,
        metrics=(metric,),
        overall_score=0.95,
        summary="Good quality",
    )
    assert result.check_id == check.id
    assert result.overall_score == 0.95
    assert result.passed is True


@pytest.mark.asyncio
async def test_complete_quality_check_not_found(service: KnowledgeGovernanceService) -> None:
    with pytest.raises(KnowledgeQualityError, match="not found"):
        await service.complete_quality_check("nonexistent")


@pytest.mark.asyncio
async def test_complete_check(service: KnowledgeGovernanceService) -> None:
    check = await service.start_quality_check("res-1", "document")
    metric = KnowledgeQualityMetric(
        id=str(uuid.uuid4()),
        name="completeness",
        value=1.0,
        threshold=0.9,
        passed=True,
    )
    result = await service.complete_check(
        check.id,
        metrics=(metric,),
        overall_score=1.0,
        passed=True,
    )
    assert result.passed is True


@pytest.mark.asyncio
async def test_get_quality_result(service: KnowledgeGovernanceService) -> None:
    check = await service.start_quality_check("res-1", "document")
    metric = KnowledgeQualityMetric(
        id=str(uuid.uuid4()),
        name="accuracy",
        value=0.9,
        threshold=0.8,
        passed=True,
    )
    await service.complete_check(check.id, metrics=(metric,), overall_score=0.9, passed=True)
    result = await service.get_quality_result(check.id)
    assert result is not None
    assert result.overall_score == 0.9


@pytest.mark.asyncio
async def test_quality_result_not_found(service: KnowledgeGovernanceService) -> None:
    with pytest.raises(KnowledgeQualityError, match="not found"):
        await service.get_quality_result("nonexistent")


@pytest.mark.asyncio
async def test_list_quality_results(service: KnowledgeGovernanceService) -> None:
    check1 = await service.start_quality_check("res-1", "document")
    check2 = await service.start_quality_check("res-2", "document")
    await service.complete_check(check1.id, passed=True)
    await service.complete_check(check2.id, passed=True)
    results = await service.list_quality_results()
    assert len(results) == 2


@pytest.mark.asyncio
async def test_create_audit_entry(service: KnowledgeGovernanceService) -> None:
    entry = await service.create_audit_entry("view", actor="user-1", resource_id="res-1")
    assert entry.id is not None
    assert entry.action == "view"
    assert entry.actor == "user-1"


@pytest.mark.asyncio
async def test_list_audit_entries(service: KnowledgeGovernanceService) -> None:
    await service.create_audit_entry("view", actor="user-1")
    await service.create_audit_entry("edit", actor="user-2")
    entries = await service.list_audit_entries()
    assert len(entries) == 2
    user1_entries = await service.list_audit_entries(actor="user-1")
    assert len(user1_entries) == 1


@pytest.mark.asyncio
async def test_generate_report(service: KnowledgeGovernanceService) -> None:
    report = await service.generate_report("quality_summary", name="Q1 Report")
    assert report.id is not None
    assert report.report_type == "quality_summary"
    assert report.name == "Q1 Report"


@pytest.mark.asyncio
async def test_list_reports(service: KnowledgeGovernanceService) -> None:
    await service.generate_report("quality_summary")
    await service.generate_report("compliance")
    reports = await service.list_reports()
    assert len(reports) == 2
    quality = await service.list_reports("quality_summary")
    assert len(quality) == 1


@pytest.mark.asyncio
async def test_create_retention_rule(service: KnowledgeGovernanceService) -> None:
    rule = await service.create_retention_rule(
        "Archive Old",
        "document",
        90,
        KnowledgeRetentionAction.ARCHIVE,
    )
    assert rule.id is not None
    assert rule.max_age_days == 90
    assert rule.action == KnowledgeRetentionAction.ARCHIVE


@pytest.mark.asyncio
async def test_create_retention_rule_empty_name(service: KnowledgeGovernanceService) -> None:
    with pytest.raises(KnowledgeRetentionError, match="Retention rule name is required"):
        await service.create_retention_rule("")


@pytest.mark.asyncio
async def test_apply_retention_rule(service: KnowledgeGovernanceService) -> None:
    rule = await service.create_retention_rule("Cleanup")
    await service.apply_retention_rule(rule.id, ("res-1", "res-2"))
    assert True


@pytest.mark.asyncio
async def test_apply_retention_rule_not_found(service: KnowledgeGovernanceService) -> None:
    with pytest.raises(KnowledgeRetentionError, match="not found"):
        await service.apply_retention_rule("nonexistent")


@pytest.mark.asyncio
async def test_create_classification_policy(service: KnowledgeGovernanceService) -> None:
    policy = await service.create_classification_policy(
        "Internal Only",
        KnowledgeClassificationLevel.CONFIDENTIAL,
    )
    assert policy.id is not None
    assert policy.default_level == KnowledgeClassificationLevel.CONFIDENTIAL


@pytest.mark.asyncio
async def test_create_classification_policy_empty_name(service: KnowledgeGovernanceService) -> None:
    msg = "Classification policy name is required"
    with pytest.raises(KnowledgeClassificationError, match=msg):
        await service.create_classification_policy("")


@pytest.mark.asyncio
async def test_update_classification(service: KnowledgeGovernanceService) -> None:
    await service.update_classification(
        "res-1",
        "document",
        KnowledgeClassificationLevel.RESTRICTED,
        KnowledgeClassificationLevel.INTERNAL,
    )
    assert True


@pytest.mark.asyncio
async def test_validate_source(service: KnowledgeGovernanceService) -> None:
    validation = await service.validate_source("src-1", "api", "auditor-1")
    assert validation.id is not None
    assert validation.status == KnowledgeSourceStatus.VALIDATED


@pytest.mark.asyncio
async def test_approve_source(service: KnowledgeGovernanceService) -> None:
    validation = await service.validate_source("src-1")
    approved = await service.approve_source(validation.id)
    assert approved.status == KnowledgeSourceStatus.APPROVED


@pytest.mark.asyncio
async def test_approve_source_not_found(service: KnowledgeGovernanceService) -> None:
    with pytest.raises(KnowledgeSourceValidationError, match="not found"):
        await service.approve_source("nonexistent")


@pytest.mark.asyncio
async def test_reject_source(service: KnowledgeGovernanceService) -> None:
    validation = await service.validate_source("src-1")
    rejected = await service.reject_source(validation.id, reason="Low quality")
    assert rejected.status == KnowledgeSourceStatus.REJECTED
    assert rejected.validation_notes == "Low quality"


@pytest.mark.asyncio
async def test_assign_steward(service: KnowledgeGovernanceService) -> None:
    assignment = await service.assign_steward("res-1", "user-1", KnowledgeStewardshipRole.OWNER)
    assert assignment.id is not None
    assert assignment.role == KnowledgeStewardshipRole.OWNER


@pytest.mark.asyncio
async def test_unassign_steward(service: KnowledgeGovernanceService) -> None:
    assignment = await service.assign_steward("res-1", "user-1")
    await service.unassign_steward(assignment.id)
    assignments = await service.list_stewardship_assignments()
    assert len(assignments) == 0


@pytest.mark.asyncio
async def test_unassign_steward_not_found(service: KnowledgeGovernanceService) -> None:
    with pytest.raises(KnowledgeStewardshipError, match="not found"):
        await service.unassign_steward("nonexistent")


@pytest.mark.asyncio
async def test_list_stewardship_assignments(service: KnowledgeGovernanceService) -> None:
    await service.assign_steward("res-1", "user-1")
    await service.assign_steward("res-2", "user-2")
    all_assignments = await service.list_stewardship_assignments()
    assert len(all_assignments) == 2
    user1 = await service.list_stewardship_assignments(user_id="user-1")
    assert len(user1) == 1


@pytest.mark.asyncio
async def test_get_dashboard(service: KnowledgeGovernanceService) -> None:
    await service.create_policy("Policy 1")
    await service.create_policy("Policy 2")
    dashboard = await service.get_dashboard()
    assert dashboard.id == "knowledge_governance_dashboard"
    assert dashboard.total_policies == 2


@pytest.mark.asyncio
async def test_update_config(service: KnowledgeGovernanceService) -> None:
    updated = await service.update_config(name="Updated Config", policies_enabled=False)
    assert updated.name == "Updated Config"
    assert updated.policies_enabled is False


@pytest.mark.asyncio
async def test_config_default(service: KnowledgeGovernanceService) -> None:
    config = service.config
    assert config.id == "default"
    assert config.name == "Default Knowledge Governance Config"


@pytest.mark.asyncio
async def test_event_type_policy_created(service: KnowledgeGovernanceService) -> None:
    policy = await service.create_policy("Test")
    assert policy.id is not None


@pytest.mark.asyncio
async def test_event_type_quality_check_events() -> None:
    assert KnowledgeQualityCheckStarted.event_type == (
        "eaip.knowledge_governance.quality_check.started"
    )
    assert KnowledgeQualityCheckCompleted.event_type == (
        "eaip.knowledge_governance.quality_check.completed"
    )
    assert KnowledgeQualityCheckFailed.event_type == (
        "eaip.knowledge_governance.quality_check.failed"
    )
    assert KnowledgeQualityScoreComputed.event_type == (
        "eaip.knowledge_governance.quality_score.computed"
    )


@pytest.mark.asyncio
async def test_event_type_audit_and_report() -> None:
    assert KnowledgeAuditTrailEntryCreated.event_type == (
        "eaip.knowledge_governance.audit_trail.entry_created"
    )
    assert KnowledgeGovernanceReportGenerated.event_type == (
        "eaip.knowledge_governance.report.generated"
    )


@pytest.mark.asyncio
async def test_event_type_retention_and_classification() -> None:
    assert KnowledgeRetentionRuleApplied.event_type == (
        "eaip.knowledge_governance.retention_rule.applied"
    )
    assert KnowledgeClassificationUpdated.event_type == (
        "eaip.knowledge_governance.classification.updated"
    )


@pytest.mark.asyncio
async def test_event_type_source_events() -> None:
    assert KnowledgeSourceValidated.event_type == ("eaip.knowledge_governance.source.validated")
    assert KnowledgeSourceApproved.event_type == ("eaip.knowledge_governance.source.approved")
    assert KnowledgeSourceRejected.event_type == ("eaip.knowledge_governance.source.rejected")


@pytest.mark.asyncio
async def test_event_type_stewardship_events() -> None:
    assert KnowledgeStewardshipAssigned.event_type == (
        "eaip.knowledge_governance.stewardship.assigned"
    )
    assert KnowledgeStewardshipUnassigned.event_type == (
        "eaip.knowledge_governance.stewardship.unassigned"
    )


@pytest.mark.asyncio
async def test_event_type_dashboard_and_config() -> None:
    assert KnowledgeGovernanceDashboardUpdated.event_type == (
        "eaip.knowledge_governance.dashboard.updated"
    )
    assert KnowledgeGovernanceConfigUpdated.event_type == (
        "eaip.knowledge_governance.config.updated"
    )


@pytest.mark.asyncio
async def test_models_frozen() -> None:
    policy = KnowledgeGovernancePolicy(id="p1", name="Test")
    with pytest.raises(ValueError):
        policy.name = "Changed"


@pytest.mark.asyncio
async def test_exception_hierarchy() -> None:
    assert issubclass(KnowledgeGovernanceError, Exception)
    assert issubclass(KnowledgeGovernancePolicyError, KnowledgeGovernanceError)
    assert issubclass(KnowledgeGovernanceViolationError, KnowledgeGovernanceError)
    assert issubclass(KnowledgeQualityError, KnowledgeGovernanceError)
    assert issubclass(KnowledgeClassificationError, KnowledgeGovernanceError)
    assert issubclass(KnowledgeRetentionError, KnowledgeGovernanceError)
    assert issubclass(KnowledgeSourceValidationError, KnowledgeGovernanceError)
    assert issubclass(KnowledgeStewardshipError, KnowledgeGovernanceError)
    assert issubclass(KnowledgeGovernanceConfigError, KnowledgeGovernanceError)


@pytest.mark.asyncio
async def test_str_enum_values() -> None:
    assert GovernanceScope.GLOBAL.value == "global"
    assert GovernanceScope.COLLECTION.value == "collection"
    assert GovernanceScope.DOCUMENT.value == "document"
    assert KnowledgeRetentionAction.ARCHIVE.value == "archive"
    assert KnowledgeRetentionAction.DELETE.value == "delete"
    assert KnowledgeClassificationLevel.PUBLIC.value == "public"
    assert KnowledgeClassificationLevel.CONFIDENTIAL.value == "confidential"
    assert KnowledgeSourceStatus.PENDING.value == "pending"
    assert KnowledgeSourceStatus.APPROVED.value == "approved"
    assert KnowledgeStewardshipRole.OWNER.value == "owner"
    assert KnowledgeStewardshipRole.STEWARD.value == "steward"
