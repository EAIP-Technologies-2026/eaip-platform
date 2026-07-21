"""Tests for agent_governance package."""

from __future__ import annotations

from typing import Any

import pytest

import eaip.agent_governance.events as _events
import eaip.agent_governance.exceptions as _exceptions
import eaip.agent_governance.models as _models
from eaip.agent_governance.events import (
    AgentActivityLogged,
    AgentApprovalRequestApproved,
    AgentApprovalRequestCreated,
    AgentApprovalRequestRejected,
    AgentComplianceCheckCompleted,
    AgentComplianceCheckFailed,
    AgentEscalationTriggered,
    AgentGovernanceConfigUpdated,
    AgentGovernancePolicyCreated,
    AgentGovernancePolicyEnforced,
    AgentGovernancePolicyUpdated,
    AgentGovernancePolicyViolated,
    AgentPermissionChanged,
    AgentRestrictionApplied,
    AgentSopActivated,
    AgentSopCreated,
    AgentSopUpdated,
    AgentUsagePolicyUpdated,
)
from eaip.agent_governance.exceptions import (
    AgentApprovalError,
    AgentComplianceError,
    AgentEscalationError,
    AgentGovernanceError,
    AgentGovernancePolicyError,
    AgentGovernanceViolationError,
    AgentPermissionError,
    AgentRestrictionError,
    AgentSopError,
)
from eaip.agent_governance.health import AgentGovernanceHealthCheck
from eaip.agent_governance.integration import AgentGovernanceRuntimeModule
from eaip.agent_governance.models import (
    AgentAccessScope,
    AgentActivityLog,
    AgentApprovalConfig,
    AgentApprovalRequest,
    AgentApprovalStatus,
    AgentAuditEntry,
    AgentComplianceCheck,
    AgentComplianceResult,
    AgentEscalationRule,
    AgentGovernanceConfig,
    AgentGovernancePolicy,
    AgentGovernanceRule,
    AgentPermission,
    AgentRestriction,
    AgentSop,
    AgentSopStatus,
    AgentUsagePolicy,
)
from eaip.agent_governance.service import AgentGovernanceService

# ── helpers ──────────────────────────────────────────────────────────────


def make_policy(**kwargs: Any) -> AgentGovernancePolicy:
    return AgentGovernancePolicy(
        id=kwargs.get("id", "pol-1"),
        name=kwargs.get("name", "Test Policy"),
        description=kwargs.get("description", ""),
        rules=kwargs.get("rules", ()),
        enabled=kwargs.get("enabled", True),
    )


def make_permission(**kwargs: Any) -> AgentPermission:
    return AgentPermission(
        id=kwargs.get("id", "perm-1"),
        agent_id=kwargs.get("agent_id", "agent-1"),
        scope=kwargs.get("scope", AgentAccessScope.READ),
        resource=kwargs.get("resource", "res-1"),
    )


def make_sop(**kwargs: Any) -> AgentSop:
    return AgentSop(
        id=kwargs.get("id", "sop-1"),
        name=kwargs.get("name", "Test SOP"),
        steps=kwargs.get("steps", ("step1",)),
    )


# ── model tests ──────────────────────────────────────────────────────────


class TestModels:
    def test_agent_access_scope_values(self) -> None:
        assert AgentAccessScope.READ.value == "read"
        assert AgentAccessScope.WRITE.value == "write"
        assert AgentAccessScope.ADMIN.value == "admin"
        assert AgentAccessScope.EXECUTE.value == "execute"
        assert AgentAccessScope.DEPLOY.value == "deploy"

    def test_agent_approval_status_values(self) -> None:
        assert AgentApprovalStatus.PENDING.value == "pending"
        assert AgentApprovalStatus.APPROVED.value == "approved"
        assert AgentApprovalStatus.REJECTED.value == "rejected"
        assert AgentApprovalStatus.CANCELLED.value == "cancelled"

    def test_agent_sop_status_values(self) -> None:
        assert AgentSopStatus.DRAFT.value == "draft"
        assert AgentSopStatus.ACTIVE.value == "active"
        assert AgentSopStatus.ARCHIVED.value == "archived"

    def test_governance_policy_frozen(self) -> None:
        policy = make_policy()
        with pytest.raises(ValueError, match="frozen instance"):
            policy.name = "changed"

    def test_permission_frozen(self) -> None:
        perm = make_permission()
        with pytest.raises(ValueError, match="frozen instance"):
            perm.revoked = True

    def test_governance_config_defaults(self) -> None:
        config = AgentGovernanceConfig(id="cfg-1", name="Default")
        assert config.auditing_enabled is True
        assert config.approvals_enabled is True
        assert config.compliance_enabled is True
        assert config.restrictions_enabled is True
        assert config.sop_enabled is True

    def test_compliance_result_model(self) -> None:
        result = AgentComplianceResult(
            id="cr-1",
            check_id="cc-1",
            agent_id="agent-1",
            passed=True,
        )
        assert result.passed is True
        assert result.details == {}


# ── event tests ──────────────────────────────────────────────────────────


class TestEvents:
    def test_policy_created_event_type(self) -> None:
        event = AgentGovernancePolicyCreated(policy_id="p1", policy_name="P1")
        assert event.event_type == "eaip.agent_governance.policy.created"

    def test_policy_updated_event_type(self) -> None:
        event = AgentGovernancePolicyUpdated(policy_id="p1", policy_name="P1")
        assert event.event_type == "eaip.agent_governance.policy.updated"

    def test_policy_enforced_event_type(self) -> None:
        event = AgentGovernancePolicyEnforced(policy_id="p1", agent_id="a1", action="execute")
        assert event.event_type == "eaip.agent_governance.policy.enforced"

    def test_policy_violated_event_type(self) -> None:
        event = AgentGovernancePolicyViolated(policy_id="p1", agent_id="a1", action="execute")
        assert event.event_type == "eaip.agent_governance.policy.violated"

    def test_permission_changed_event_type(self) -> None:
        event = AgentPermissionChanged(agent_id="a1", permission_id="p1", change="granted")
        assert event.event_type == "eaip.agent_governance.permission.changed"

    def test_activity_logged_event_type(self) -> None:
        event = AgentActivityLogged(log_id="l1", agent_id="a1", action="run")
        assert event.event_type == "eaip.agent_governance.activity.logged"

    def test_approval_request_created_event_type(self) -> None:
        event = AgentApprovalRequestCreated(request_id="r1", agent_id="a1", action="deploy")
        assert event.event_type == "eaip.agent_governance.approval.request.created"

    def test_approval_request_approved_event_type(self) -> None:
        event = AgentApprovalRequestApproved(request_id="r1", agent_id="a1", approved_by="admin")
        assert event.event_type == "eaip.agent_governance.approval.request.approved"

    def test_approval_request_rejected_event_type(self) -> None:
        event = AgentApprovalRequestRejected(
            request_id="r1", agent_id="a1", rejected_by="admin", reason="No"
        )
        assert event.event_type == "eaip.agent_governance.approval.request.rejected"

    def test_restriction_applied_event_type(self) -> None:
        event = AgentRestrictionApplied(
            restriction_id="r1", agent_id="a1", restriction_type="rate_limit"
        )
        assert event.event_type == "eaip.agent_governance.restriction.applied"

    def test_usage_policy_updated_event_type(self) -> None:
        event = AgentUsagePolicyUpdated(policy_id="up1", policy_name="UP1")
        assert event.event_type == "eaip.agent_governance.usage_policy.updated"

    def test_sop_created_event_type(self) -> None:
        event = AgentSopCreated(sop_id="s1", sop_name="S1")
        assert event.event_type == "eaip.agent_governance.sop.created"

    def test_sop_updated_event_type(self) -> None:
        event = AgentSopUpdated(sop_id="s1", sop_name="S1", version=2)
        assert event.event_type == "eaip.agent_governance.sop.updated"

    def test_sop_activated_event_type(self) -> None:
        event = AgentSopActivated(sop_id="s1", sop_name="S1")
        assert event.event_type == "eaip.agent_governance.sop.activated"

    def test_compliance_check_completed_event_type(self) -> None:
        event = AgentComplianceCheckCompleted(check_id="cc1", agent_id="a1", passed=True)
        assert event.event_type == "eaip.agent_governance.compliance.check.completed"

    def test_compliance_check_failed_event_type(self) -> None:
        event = AgentComplianceCheckFailed(check_id="cc1", agent_id="a1", error="timeout")
        assert event.event_type == "eaip.agent_governance.compliance.check.failed"

    def test_escalation_triggered_event_type(self) -> None:
        event = AgentEscalationTriggered(rule_id="er1", agent_id="a1")
        assert event.event_type == "eaip.agent_governance.escalation.triggered"

    def test_config_updated_event_type(self) -> None:
        event = AgentGovernanceConfigUpdated(config_id="cfg1", config_name="Cfg1")
        assert event.event_type == "eaip.agent_governance.config.updated"

    def test_events_are_frozen(self) -> None:
        event = AgentGovernancePolicyCreated(policy_id="p1", policy_name="P1")
        with pytest.raises(ValueError, match="frozen instance"):
            event.policy_id = "p2"


# ── exception tests ──────────────────────────────────────────────────────


class TestExceptions:
    def test_base_exception(self) -> None:
        exc = AgentGovernanceError("something went wrong")
        assert isinstance(exc, AgentGovernanceError)
        assert str(exc) == "something went wrong"

    def test_policy_error(self) -> None:
        exc = AgentGovernancePolicyError("policy not found")
        assert isinstance(exc, AgentGovernanceError)

    def test_violation_error(self) -> None:
        exc = AgentGovernanceViolationError("violation")
        assert isinstance(exc, AgentGovernanceError)

    def test_permission_error(self) -> None:
        exc = AgentPermissionError("permission denied")
        assert isinstance(exc, AgentGovernanceError)

    def test_approval_error(self) -> None:
        exc = AgentApprovalError("approval failed")
        assert isinstance(exc, AgentGovernanceError)

    def test_restriction_error(self) -> None:
        exc = AgentRestrictionError("restriction failed")
        assert isinstance(exc, AgentGovernanceError)

    def test_sop_error(self) -> None:
        exc = AgentSopError("sop not found")
        assert isinstance(exc, AgentGovernanceError)

    def test_compliance_error(self) -> None:
        exc = AgentComplianceError("compliance failed")
        assert isinstance(exc, AgentGovernanceError)

    def test_escalation_error(self) -> None:
        exc = AgentEscalationError("escalation failed")
        assert isinstance(exc, AgentGovernanceError)


# ── service tests ────────────────────────────────────────────────────────


class TestAgentGovernanceService:
    def test_create_and_get_policy(self) -> None:
        svc = AgentGovernanceService()
        policy = make_policy()
        svc.create_policy(policy)
        assert svc.get_policy("pol-1") == policy

    def test_create_duplicate_policy_raises(self) -> None:
        svc = AgentGovernanceService()
        svc.create_policy(make_policy())
        with pytest.raises(AgentGovernancePolicyError, match="already exists"):
            svc.create_policy(make_policy())

    def test_get_missing_policy_raises(self) -> None:
        svc = AgentGovernanceService()
        with pytest.raises(AgentGovernancePolicyError, match="not found"):
            svc.get_policy("nonexistent")

    def test_update_policy(self) -> None:
        svc = AgentGovernanceService()
        svc.create_policy(make_policy())
        updated = svc.update_policy("pol-1", name="Updated Policy")
        assert updated.name == "Updated Policy"

    def test_delete_policy(self) -> None:
        svc = AgentGovernanceService()
        svc.create_policy(make_policy())
        svc.delete_policy("pol-1")
        assert svc.list_policies() == []

    def test_list_policies(self) -> None:
        svc = AgentGovernanceService()
        svc.create_policy(make_policy(id="p1", name="P1"))
        svc.create_policy(make_policy(id="p2", name="P2"))
        assert len(svc.list_policies()) == 2

    def test_enforce_policy_allows(self) -> None:
        rule = AgentGovernanceRule(id="r1", name="Allow read", effect="allow", actions=("read",))
        policy = make_policy(id="p1", rules=(rule,))
        svc = AgentGovernanceService()
        svc.create_policy(policy)
        assert svc.enforce_policy("p1", "agent-1", "read") is True

    def test_enforce_policy_denies(self) -> None:
        rule = AgentGovernanceRule(id="r1", name="Deny delete", effect="deny", actions=("delete",))
        policy = make_policy(id="p1", rules=(rule,))
        svc = AgentGovernanceService()
        svc.create_policy(policy)
        with pytest.raises(AgentGovernanceViolationError, match="denied"):
            svc.enforce_policy("p1", "agent-1", "delete")

    def test_enforce_disabled_policy_skips(self) -> None:
        rule = AgentGovernanceRule(id="r1", name="Deny delete", effect="deny", actions=("delete",))
        policy = make_policy(id="p1", rules=(rule,), enabled=False)
        svc = AgentGovernanceService()
        svc.create_policy(policy)
        assert svc.enforce_policy("p1", "agent-1", "delete") is True

    def test_grant_and_revoke_permission(self) -> None:
        svc = AgentGovernanceService()
        perm = make_permission(id="perm-1", agent_id="agent-1")
        svc.grant_permission(perm)
        assert svc.get_permission("perm-1").revoked is False
        svc.revoke_permission("perm-1")
        assert svc.get_permission("perm-1").revoked is True

    def test_list_permissions_filters_by_agent(self) -> None:
        svc = AgentGovernanceService()
        svc.grant_permission(make_permission(id="p1", agent_id="a1"))
        svc.grant_permission(make_permission(id="p2", agent_id="a2"))
        assert len(svc.list_permissions(agent_id="a1")) == 1
        assert len(svc.list_permissions()) == 2

    def test_log_and_get_activity(self) -> None:
        svc = AgentGovernanceService()
        log = AgentActivityLog(
            id="l1", agent_id="a1", action="run", resource="res1", outcome="success"
        )
        svc.log_activity(log)
        assert svc.get_activity_log("l1") == log

    def test_list_activity_logs_filters_by_agent(self) -> None:
        svc = AgentGovernanceService()
        svc.log_activity(AgentActivityLog(id="l1", agent_id="a1", action="run", resource="res1"))
        svc.log_activity(AgentActivityLog(id="l2", agent_id="a2", action="run", resource="res1"))
        assert len(svc.list_activity_logs(agent_id="a1")) == 1

    def test_create_audit_entry(self) -> None:
        svc = AgentGovernanceService()
        entry = AgentAuditEntry(
            id="ae1",
            agent_id="a1",
            change_type="policy_update",
            previous_state={"enabled": True},
            new_state={"enabled": False},
        )
        svc.create_audit_entry(entry)
        assert len(svc.list_audit_entries()) == 1

    def test_create_approval_config(self) -> None:
        svc = AgentGovernanceService()
        config = AgentApprovalConfig(id="ac1", name="Two-person approval", required_approvals=2)
        svc.create_approval_config(config)
        assert svc.get_approval_config("ac1").required_approvals == 2

    def test_approval_request_lifecycle(self) -> None:
        svc = AgentGovernanceService()
        req = AgentApprovalRequest(
            id="ar1",
            agent_id="a1",
            action="deploy",
            resource="prod",
        )
        svc.create_approval_request(req)
        assert svc.get_approval_request("ar1").status is AgentApprovalStatus.PENDING

        svc.approve_request("ar1", "admin")
        assert svc.get_approval_request("ar1").status is AgentApprovalStatus.APPROVED
        assert svc.get_approval_request("ar1").approved_by == "admin"

    def test_approval_request_rejection(self) -> None:
        svc = AgentGovernanceService()
        req = AgentApprovalRequest(
            id="ar2",
            agent_id="a1",
            action="deploy",
            resource="prod",
        )
        svc.create_approval_request(req)
        svc.reject_request("ar2", "admin", reason="Not authorized")
        result = svc.get_approval_request("ar2")
        assert result.status is AgentApprovalStatus.REJECTED
        assert result.rejection_reason == "Not authorized"

    def test_approve_non_pending_request_raises(self) -> None:
        svc = AgentGovernanceService()
        req = AgentApprovalRequest(id="ar1", agent_id="a1", action="deploy", resource="prod")
        svc.create_approval_request(req)
        svc.approve_request("ar1", "admin")
        with pytest.raises(AgentApprovalError, match="is approved"):
            svc.approve_request("ar1", "admin2")

    def test_apply_and_list_restrictions(self) -> None:
        svc = AgentGovernanceService()
        r = AgentRestriction(id="r1", agent_id="a1", restriction_type="rate_limit", value="10/min")
        svc.apply_restriction(r)
        assert len(svc.list_restrictions()) == 1
        svc.remove_restriction("r1")
        assert len(svc.list_restrictions()) == 0

    def test_restrictions_disabled_raises(self) -> None:
        config = AgentGovernanceConfig(id="cfg", name="No restrictions", restrictions_enabled=False)
        svc = AgentGovernanceService(config=config)
        r = AgentRestriction(id="r1", agent_id="a1", restriction_type="test")
        with pytest.raises(AgentRestrictionError, match="disabled"):
            svc.apply_restriction(r)

    def test_usage_policy_crud(self) -> None:
        svc = AgentGovernanceService()
        up = AgentUsagePolicy(id="up1", name="Basic", max_concurrent_runs=3)
        svc.create_usage_policy(up)
        assert svc.get_usage_policy("up1") == up
        svc.update_usage_policy("up1", max_concurrent_runs=5)
        assert svc.get_usage_policy("up1").max_concurrent_runs == 5

    def test_sop_lifecycle(self) -> None:
        svc = AgentGovernanceService()
        sop = make_sop(id="sop-1")
        svc.create_sop(sop)
        assert svc.get_sop("sop-1").status is AgentSopStatus.DRAFT

        svc.activate_sop("sop-1")
        assert svc.get_sop("sop-1").status is AgentSopStatus.ACTIVE

        svc.archive_sop("sop-1")
        assert svc.get_sop("sop-1").status is AgentSopStatus.ARCHIVED

    def test_sop_update_increments_version(self) -> None:
        svc = AgentGovernanceService()
        sop = make_sop(id="sop-1")
        svc.create_sop(sop)
        updated = svc.update_sop("sop-1", name="Revised")
        assert updated.version == 2

    def test_sops_disabled_raises(self) -> None:
        config = AgentGovernanceConfig(id="cfg", name="No SOPs", sop_enabled=False)
        svc = AgentGovernanceService(config=config)
        with pytest.raises(AgentSopError, match="disabled"):
            svc.create_sop(make_sop())

    def test_compliance_check_lifecycle(self) -> None:
        svc = AgentGovernanceService()
        cc = AgentComplianceCheck(id="cc1", name="Security check", rules=("rule1",))
        svc.create_compliance_check(cc)
        assert svc.get_compliance_check("cc1").name == "Security check"

    def test_run_compliance_check_passes(self) -> None:
        svc = AgentGovernanceService()
        cc = AgentComplianceCheck(id="cc1", name="Check", rules=("rule1",))
        svc.create_compliance_check(cc)
        result = svc.run_compliance_check("cc1", "agent-1")
        assert result.passed is True

    def test_compliance_disabled_raises(self) -> None:
        config = AgentGovernanceConfig(id="cfg", name="No compliance", compliance_enabled=False)
        svc = AgentGovernanceService(config=config)
        cc = AgentComplianceCheck(id="cc1", name="Test")
        with pytest.raises(AgentComplianceError, match="disabled"):
            svc.create_compliance_check(cc)

    def test_escalation_rule_crud(self) -> None:
        svc = AgentGovernanceService()
        rule = AgentEscalationRule(
            id="er1", name="High severity", condition="severity >= 8", target="admin"
        )
        svc.create_escalation_rule(rule)
        assert svc.get_escalation_rule("er1").target == "admin"

    def test_trigger_escalation(self) -> None:
        svc = AgentGovernanceService()
        rule = AgentEscalationRule(id="er1", name="Escalate", condition="true", target="admin")
        svc.create_escalation_rule(rule)
        result = svc.trigger_escalation("er1", "agent-1", reason="Critical failure")
        assert result["rule_id"] == "er1"
        assert result["agent_id"] == "agent-1"

    def test_trigger_disabled_escalation_raises(self) -> None:
        svc = AgentGovernanceService()
        rule = AgentEscalationRule(
            id="er1", name="Disabled", condition="true", target="admin", enabled=False
        )
        svc.create_escalation_rule(rule)
        with pytest.raises(AgentEscalationError, match="disabled"):
            svc.trigger_escalation("er1", "agent-1")

    def test_update_config(self) -> None:
        svc = AgentGovernanceService()
        svc.update_config(auditing_enabled=False)
        assert svc.config.auditing_enabled is False

    def test_event_dispatch(self) -> None:
        svc = AgentGovernanceService()
        received: list[object] = []

        def listener(event: object) -> None:
            received.append(event)

        svc.subscribe(listener)
        svc.create_policy(make_policy())
        assert len(received) == 1
        assert isinstance(received[0], AgentGovernancePolicyCreated)


# ── health check tests ───────────────────────────────────────────────────


class TestAgentGovernanceHealthCheck:
    async def test_healthy_with_no_policies(self) -> None:
        svc = AgentGovernanceService()
        check = AgentGovernanceHealthCheck(svc)
        report = await check.check()
        assert report.status.name == "HEALTHY"

    async def test_healthy_with_all_enabled(self) -> None:
        svc = AgentGovernanceService()
        svc.create_policy(make_policy(id="p1"))
        svc.create_policy(make_policy(id="p2"))
        check = AgentGovernanceHealthCheck(svc)
        report = await check.check()
        assert report.status.name == "HEALTHY"

    async def test_degraded_with_disabled_policies(self) -> None:
        svc = AgentGovernanceService()
        svc.create_policy(make_policy(id="p1"))
        svc.create_policy(make_policy(id="p2", enabled=False))
        check = AgentGovernanceHealthCheck(svc)
        report = await check.check()
        assert report.status.name == "DEGRADED"


# ── integration tests ────────────────────────────────────────────────────


class TestAgentGovernanceRuntimeModule:
    def test_default_name(self) -> None:
        module = AgentGovernanceRuntimeModule()
        assert module.name == "agent_governance"

    def test_initial_service(self) -> None:
        svc = AgentGovernanceService()
        module = AgentGovernanceRuntimeModule(service=svc)
        assert module.service is svc

    def test_startup_duration_starts_zero(self) -> None:
        module = AgentGovernanceRuntimeModule()
        assert module.startup_duration == 0.0


# ── all__ exports ────────────────────────────────────────────────────────


class TestAllExports:
    def test_models_all(self) -> None:
        expected = [
            "AgentAccessScope",
            "AgentActivityLog",
            "AgentApprovalConfig",
            "AgentApprovalRequest",
            "AgentApprovalStatus",
            "AgentAuditEntry",
            "AgentCapability",
            "AgentComplianceCheck",
            "AgentComplianceResult",
            "AgentEscalationRule",
            "AgentGovernanceConfig",
            "AgentGovernancePolicy",
            "AgentGovernanceRule",
            "AgentPermission",
            "AgentRestriction",
            "AgentSop",
            "AgentSopStatus",
            "AgentUsagePolicy",
        ]
        for name in expected:
            assert hasattr(_models, name), f"{name} missing from models.__all__"

    def test_events_all(self) -> None:
        expected = [
            "AgentActivityLogged",
            "AgentApprovalRequestApproved",
            "AgentApprovalRequestCreated",
            "AgentApprovalRequestRejected",
            "AgentComplianceCheckCompleted",
            "AgentComplianceCheckFailed",
            "AgentEscalationTriggered",
            "AgentGovernanceConfigUpdated",
            "AgentGovernancePolicyCreated",
            "AgentGovernancePolicyEnforced",
            "AgentGovernancePolicyUpdated",
            "AgentGovernancePolicyViolated",
            "AgentPermissionChanged",
            "AgentRestrictionApplied",
            "AgentSopActivated",
            "AgentSopCreated",
            "AgentSopUpdated",
            "AgentUsagePolicyUpdated",
        ]
        for name in expected:
            assert hasattr(_events, name), f"{name} missing from events.__all__"

    def test_exceptions_all(self) -> None:
        expected = [
            "AgentApprovalError",
            "AgentComplianceError",
            "AgentEscalationError",
            "AgentGovernanceError",
            "AgentGovernancePolicyError",
            "AgentGovernanceViolationError",
            "AgentPermissionError",
            "AgentRestrictionError",
            "AgentSopError",
        ]
        for name in expected:
            assert hasattr(_exceptions, name), f"{name} missing from exceptions.__all__"
