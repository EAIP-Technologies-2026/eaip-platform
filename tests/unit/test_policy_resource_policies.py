"""Tests for Resource, Tool, Department, Workflow, and Approval policies."""

from __future__ import annotations

import pytest

from eaip.policy.models import PolicyEffect, PolicyRule
from eaip.policy.resource_policies import (
    ApprovalPolicy,
    DepartmentPolicy,
    PolicyEvaluationReport,
    ResourcePolicy,
    ToolAccessLevel,
    ToolPolicy,
    WorkflowPolicy,
)


class TestResourcePolicy:
    def test_defaults(self) -> None:
        rp = ResourcePolicy(id="rp_1", name="Prod DB Access")
        assert rp.resource_type == ""
        assert rp.resource_pattern == "*"
        assert rp.allowed_actions == ()
        assert rp.enabled is True
        assert rp.priority == 0

    def test_with_rules(self) -> None:
        rule = PolicyRule(
            id="rule_1",
            name="Allow Read",
            effect=PolicyEffect.ALLOW,
            actions=("read",),
        )
        rp = ResourcePolicy(
            id="rp_2",
            name="DB Policy",
            resource_type="database",
            resource_pattern="prod::*",
            allowed_actions=("read", "write"),
            rules=(rule,),
            priority=10,
        )
        assert rp.resource_type == "database"
        assert rp.resource_pattern == "prod::*"
        assert len(rp.rules) == 1
        assert rp.priority == 10

    def test_frozen(self) -> None:
        rp = ResourcePolicy(id="rp_1", name="Test")
        with pytest.raises(ValueError):
            rp.name = "Changed"  # type: ignore[misc]

    def test_extra_forbid(self) -> None:
        with pytest.raises(ValueError):
            ResourcePolicy(id="rp_1", name="Test", unknown_field="x")  # type: ignore[call-arg]


class TestToolPolicy:
    def test_defaults(self) -> None:
        tp = ToolPolicy(id="tp_1", name="Tool Policy")
        assert tp.tool_pattern == "*"
        assert tp.access_level is ToolAccessLevel.ALLOW
        assert tp.max_execution_seconds == 0.0

    def test_restricted_tool(self) -> None:
        tp = ToolPolicy(
            id="tp_2",
            name="Restricted Shell",
            tool_pattern="shell:*",
            access_level=ToolAccessLevel.RESTRICTED,
            allowed_parameters={"command": ["ls", "cat"]},
            max_execution_seconds=30.0,
            rate_limit_per_minute=10,
            roles=("developer",),
        )
        assert tp.access_level is ToolAccessLevel.RESTRICTED
        assert tp.allowed_parameters == {"command": ["ls", "cat"]}
        assert tp.max_execution_seconds == 30.0

    def test_frozen(self) -> None:
        tp = ToolPolicy(id="tp_1", name="Test")
        with pytest.raises(ValueError):
            tp.tool_pattern = "changed"  # type: ignore[misc]


class TestDepartmentPolicy:
    def test_defaults(self) -> None:
        dp = DepartmentPolicy(id="dp_1", name="Engineering", department_id="eng")
        assert dp.department_id == "eng"
        assert dp.resource_policies == ()
        assert dp.max_concurrent_workflows == 0

    def test_with_policies(self) -> None:
        dp = DepartmentPolicy(
            id="dp_2",
            name="Finance",
            department_id="fin",
            resource_policies=("rp_1", "rp_2"),
            tool_policies=("tp_1",),
            max_concurrent_workflows=5,
            max_agent_runs_per_minute=100,
        )
        assert len(dp.resource_policies) == 2
        assert dp.max_concurrent_workflows == 5
        assert dp.max_agent_runs_per_minute == 100

    def test_frozen(self) -> None:
        dp = DepartmentPolicy(id="dp_1", name="Eng", department_id="eng")
        with pytest.raises(ValueError):
            dp.department_id = "changed"  # type: ignore[misc]


class TestWorkflowPolicy:
    def test_defaults(self) -> None:
        wp = WorkflowPolicy(id="wp_1", name="WF Policy")
        assert wp.workflow_pattern == "*"
        assert wp.max_steps == 0
        assert wp.allowed_agent_ids == ()

    def test_with_restrictions(self) -> None:
        wp = WorkflowPolicy(
            id="wp_2",
            name="Prod WF",
            workflow_pattern="production:*",
            max_duration_seconds=3600.0,
            max_steps=20,
            allowed_agent_ids=("agent_a", "agent_b"),
            denied_tool_names=("shell", "network"),
            require_approval_for_steps=("approval_step",),
        )
        assert wp.max_duration_seconds == 3600.0
        assert wp.max_steps == 20
        assert len(wp.allowed_agent_ids) == 2
        assert "shell" in wp.denied_tool_names

    def test_frozen(self) -> None:
        wp = WorkflowPolicy(id="wp_1", name="Test")
        with pytest.raises(ValueError):
            wp.max_steps = 10  # type: ignore[misc]


class TestApprovalPolicy:
    def test_defaults(self) -> None:
        ap = ApprovalPolicy(id="ap_1", name="Approval Policy")
        assert ap.min_approvals_required == 1
        assert ap.timeout_seconds == 86400.0
        assert ap.required_approvers == ()

    def test_with_approvers(self) -> None:
        ap = ApprovalPolicy(
            id="ap_2",
            name="High Value",
            trigger_conditions=({"amount": ">1000"},),
            required_approvers=("manager", "director"),
            min_approvals_required=2,
            timeout_seconds=3600.0,
            escalation_after_seconds=1800.0,
            escalation_approvers=("vp",),
        )
        assert len(ap.trigger_conditions) == 1
        assert ap.min_approvals_required == 2
        assert ap.escalation_after_seconds == 1800.0

    def test_frozen(self) -> None:
        ap = ApprovalPolicy(id="ap_1", name="Test")
        with pytest.raises(ValueError):
            ap.timeout_seconds = 100  # type: ignore[misc]


class TestPolicyEvaluationReport:
    def test_defaults(self) -> None:
        per = PolicyEvaluationReport(
            request_id="req_1",
            subject_id="user_1",
            action="read",
            resource="doc_1",
            effect=PolicyEffect.ALLOW,
        )
        assert per.request_id == "req_1"
        assert per.effect is PolicyEffect.ALLOW
        assert per.evaluation_time_ms == 0.0
        assert per.errors == ()

    def test_with_details(self) -> None:
        per = PolicyEvaluationReport(
            request_id="req_2",
            subject_id="user_2",
            action="write",
            resource="doc_2",
            effect=PolicyEffect.DENY,
            matched_policies=("pol_1",),
            matched_rules=("rule_1",),
            evaluation_time_ms=5.5,
            errors=("no matching policy",),
        )
        assert "pol_1" in per.matched_policies
        assert per.evaluation_time_ms == 5.5
        assert len(per.errors) == 1

    def test_frozen(self) -> None:
        per = PolicyEvaluationReport(
            request_id="r",
            subject_id="s",
            action="a",
            resource="r",
            effect=PolicyEffect.ALLOW,
        )
        with pytest.raises(ValueError):
            per.subject_id = "changed"  # type: ignore[misc]
