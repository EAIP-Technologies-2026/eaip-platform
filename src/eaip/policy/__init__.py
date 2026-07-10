"""Policy Engine & Authorization subsystem.

Provides the policy model, evaluation engine with RBAC and ABAC support,
an observable policy registry, an authorization manager, health checks,
domain events, and a runtime module for kernel lifecycle integration.
Includes resource, tool, department, workflow, and approval policies.
"""

from __future__ import annotations

from eaip.policy.authorization import AuthorizationManager
from eaip.policy.context import PolicyEvaluationContext
from eaip.policy.engine import PolicyEngine
from eaip.policy.events import PolicyEvaluated, PolicyRuleMatched, PolicyViolation
from eaip.policy.exceptions import PolicyError, PolicyViolationError
from eaip.policy.health import PolicyHealthCheck
from eaip.policy.integration import PolicyRuntimeModule
from eaip.policy.models import (
    ConditionOp,
    Policy,
    PolicyCondition,
    PolicyDecision,
    PolicyEffect,
    PolicyRule,
)
from eaip.policy.registry import PolicyRegistry
from eaip.policy.resource_policies import (
    ApprovalPolicy,
    DepartmentPolicy,
    PolicyEvaluationReport,
    ResourcePolicy,
    ToolAccessLevel,
    ToolPolicy,
    WorkflowPolicy,
)

__all__ = [
    "ApprovalPolicy",
    "AuthorizationManager",
    "ConditionOp",
    "DepartmentPolicy",
    "Policy",
    "PolicyCondition",
    "PolicyDecision",
    "PolicyEffect",
    "PolicyEngine",
    "PolicyError",
    "PolicyEvaluationContext",
    "PolicyEvaluationReport",
    "PolicyHealthCheck",
    "PolicyRegistry",
    "PolicyRule",
    "PolicyRuleMatched",
    "PolicyRuntimeModule",
    "PolicyViolation",
    "PolicyViolationError",
    "ResourcePolicy",
    "ToolAccessLevel",
    "ToolPolicy",
    "WorkflowPolicy",
]
