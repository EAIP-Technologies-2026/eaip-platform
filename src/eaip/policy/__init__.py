"""Policy Engine & Authorization subsystem.

Provides the policy model, evaluation engine with RBAC and ABAC support,
an observable policy registry, an authorization manager, health checks,
domain events, and a runtime module for kernel lifecycle integration.
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

__all__ = [
    "AuthorizationManager",
    "ConditionOp",
    "Policy",
    "PolicyCondition",
    "PolicyDecision",
    "PolicyEffect",
    "PolicyEngine",
    "PolicyError",
    "PolicyEvaluationContext",
    "PolicyHealthCheck",
    "PolicyRegistry",
    "PolicyRule",
    "PolicyRuleMatched",
    "PolicyRuntimeModule",
    "PolicyViolation",
    "PolicyViolationError",
]
