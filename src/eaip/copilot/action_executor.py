"""Governed Platform Action Execution — planning, gating, execution, and audit.

Implements Stage A1005: Governed execution of platform operations through
existing capabilities with mandatory authorization re-checks, approval gates,
and immutable audit logs.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from eaip.admin.audit import AuditLogger
from eaip.admin.models import AuditEntry, AuditOutcome
from eaip.capabilities.capability import OperationType
from eaip.capabilities.registry import CapabilityRegistry
from eaip.context.permission_context import IdentityScope
from eaip.context.permission_resolver import PermissionContextResolver
from eaip.copilot.approvals import ApprovalService
from eaip.copilot.models import RiskTier
from eaip.logging.context import get_logger
from eaip.policy.authorization import AuthorizationManager
from eaip.policy.context import PolicyEvaluationContext
from eaip.policy.models import PolicyDecision, PolicyEffect
from eaip.shared.identifiers import CorrelationId
from eaip.shared.time import utc_now
from eaip.tools.base import Tool
from eaip.tools.registry import ToolRegistry


class ActionPlan(BaseModel):
    """Structured preview and specification for a governed platform action."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    plan_id: str = Field(description="Unique action plan identifier.")
    intent: str = Field(description="User prompt or intent description.")
    capability_name: str = Field(description="Target capability.")
    operation: OperationType = Field(description="Operation type.")
    tool_name: str = Field(description="Underlying platform tool.")
    target_id: str | None = Field(default=None, description="Specific target entity ID.")
    target_entity_type: str | None = Field(default=None, description="Target entity type.")
    idempotency_key: str | None = Field(default=None, description="Optional idempotency key.")
    arguments: dict[str, Any] = Field(default_factory=dict, description="Execution arguments.")
    risk_tier: RiskTier = Field(default=RiskTier.ACTION, description="Risk classification.")
    requires_approval: bool = Field(
        default=False, description="Whether explicit approval is mandatory."
    )
    preview: str = Field(description="Human-readable preview of what will occur.")
    target_tenant_id: str = Field(description="Target tenant boundary.")
    created_at: datetime = Field(default_factory=utc_now)


class ActionResult(BaseModel):
    """Result of attempting to execute a governed platform action."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    plan_id: str = Field(description="Referenced action plan ID.")
    status: str = Field(
        description="Execution outcome ('executed', 'approval_required', 'denied', 'failed')."
    )
    summary: str = Field(description="User-facing outcome summary.")
    result_data: dict[str, Any] = Field(
        default_factory=dict, description="Raw execution output or error details."
    )
    audit_entry_id: str | None = Field(default=None, description="Immutable audit record ID.")
    approval_id: str | None = Field(default=None, description="Pending approval ID if required.")
    execution_id: str = Field(description="Correlation execution ID.")
    completed_at: datetime = Field(default_factory=utc_now)


class GovernedActionExecutor:
    """Orchestrates governed planning, authorization rechecks, approval gating, and execution."""

    def __init__(
        self,
        *,
        tools: ToolRegistry | dict[str, Tool],
        authz_manager: AuthorizationManager,
        capability_registry: CapabilityRegistry,
        permission_resolver: PermissionContextResolver,
        approvals: ApprovalService,
        audit: AuditLogger,
    ) -> None:
        """Initialize the governed action executor.

        Args:
            tools: Platform tool registry or mapping.
            authz_manager: Platform authorization manager for runtime re-checks.
            capability_registry: Authoritative capability registry.
            permission_resolver: Permission context resolver.
            approvals: Human-in-the-loop approval service.
            audit: Audit logger.
        """
        self._tools = tools
        self._authz = authz_manager
        self._capabilities = capability_registry
        self._resolver = permission_resolver
        self._approvals = approvals
        self._audit = audit
        self._executed_plans: dict[str, ActionResult] = {}
        self._log = get_logger("eaip.copilot.action_executor")

    def _get_tool(self, tool_name: str) -> Tool | None:
        if isinstance(self._tools, ToolRegistry):
            return self._tools.try_get(tool_name)
        return self._tools.get(tool_name)

    async def plan_action(
        self,
        intent: str,
        user: dict[str, Any],
        capability_name: str,
        operation: OperationType = OperationType.EXECUTE,
        tool_name: str | None = None,
        target_id: str | None = None,
        target_entity_type: str | None = None,
        idempotency_key: str | None = None,
        arguments: dict[str, Any] | None = None,
    ) -> ActionPlan:
        """Plan a governed action and produce an execution preview.

        Args:
            intent: User intention prompt.
            user: Authenticated caller claims.
            capability_name: Target capability name.
            operation: Target operation type.
            tool_name: Specific tool name if known.
            target_id: Target entity identifier if known.
            target_entity_type: Target entity type if known.
            idempotency_key: Optional idempotency key.
            arguments: Tool arguments.

        Returns:
            Structured ActionPlan.
        """
        user_id = str(user.get("user_id") or user.get("id") or "anonymous")
        tenant_id = str(user.get("tenant_id") or "default")
        roles = tuple(user.get("roles") or ())

        identity = IdentityScope(
            user_id=user_id,
            tenant_id=tenant_id,
            roles=roles,
            attributes=user.get("attributes") or {},
        )

        perm_ctx = self._resolver.resolve_context(identity)
        cap = self._capabilities.try_get(capability_name)
        cap_title = cap.title if cap else capability_name

        resolved_tool = tool_name
        if resolved_tool is None and hasattr(self._tools, "find_tool"):
            op_tool = self._tools.find_tool(capability_name, operation, target_entity_type)
            if op_tool is not None:
                resolved_tool = op_tool.name
        if resolved_tool is None:
            resolved_tool = "system_health"

        args = arguments or {}

        # Risk classification
        if operation in (OperationType.DELETE, OperationType.CANCEL):
            risk = RiskTier.DESTRUCTIVE
        elif operation in (
            OperationType.CREATE,
            OperationType.UPDATE,
            OperationType.EXECUTE,
            OperationType.PAUSE,
            OperationType.RESUME,
        ):
            risk = RiskTier.ACTION
        else:
            risk = RiskTier.INFORMATIONAL

        # Approval requirement
        requires_approval = (
            risk is RiskTier.DESTRUCTIVE
            or perm_ctx.requires_approval(capability_name)
            or (
                capability_name in ("eaip.operations", "eaip.missions", "eaip.orchestration")
                and operation not in (OperationType.READ, OperationType.QUERY)
            )
        )

        target_desc = f" (Target: `{target_id}`)" if target_id else ""
        preview = (
            f"Action Plan for {cap_title}{target_desc}:\n"
            f"- Operation: {operation.upper()}\n"
            f"- Risk Tier: {risk.upper()}\n"
            f"- Target Tool: `{resolved_tool}`\n"
            f"- Requires Approval: {'YES' if requires_approval else 'NO'}\n"
        )

        return ActionPlan(
            plan_id=f"plan-{uuid.uuid4().hex[:10]}",
            intent=intent,
            capability_name=capability_name,
            operation=operation,
            tool_name=resolved_tool,
            target_id=target_id,
            target_entity_type=target_entity_type,
            idempotency_key=idempotency_key,
            arguments=args,
            risk_tier=risk,
            requires_approval=requires_approval,
            preview=preview,
            target_tenant_id=tenant_id,
        )

    async def execute_action(  # noqa: PLR0911, PLR0912, PLR0915
        self,
        plan: ActionPlan,
        user: dict[str, Any],
        approved: bool = False,
    ) -> ActionResult:
        """Execute a planned action with real-time authorization re-checking.

        Args:
            plan: The ActionPlan to execute.
            user: Current caller claims.
            approved: True if explicit human approval has already been granted.

        Returns:
            ActionResult representing execution status.
        """
        # 0. IDEMPOTENCY / DUPLICATE PREVENTION
        if plan.plan_id in self._executed_plans:
            return self._executed_plans[plan.plan_id]

        user_id = str(user.get("user_id") or user.get("id") or "anonymous")
        tenant_id = str(user.get("tenant_id") or "default")
        roles = tuple(user.get("roles") or ())
        exec_id = f"exec-{uuid.uuid4().hex[:12]}"
        correlation = CorrelationId.new()

        identity = IdentityScope(
            user_id=user_id,
            tenant_id=tenant_id,
            roles=roles,
            attributes=user.get("attributes") or {},
        )
        perm_ctx = self._resolver.resolve_context(identity)

        # 1. MANDATORY REAL-TIME AUTHORIZATION RECHECK
        # We never rely solely on prior assistant context!
        action_name = f"capability:{plan.operation.value}"
        eval_ctx = PolicyEvaluationContext(
            subject_id=user_id,
            subject_roles=roles,
            action=action_name,
            resource=plan.capability_name,
            attributes={"tenant_id": tenant_id, "risk": plan.risk_tier.value},
            correlation_id=correlation,
        )

        decision: PolicyDecision = self._authz.check_permission(eval_ctx)

        # Check tenant isolation
        is_same_tenant = tenant_id == plan.target_tenant_id
        is_admin = bool(set(roles) & {"admin", "system_admin", "super_admin"})

        if not is_same_tenant and not is_admin:
            self._log_audit(
                actor_id=user_id,
                action=f"copilot.action.{plan.operation.value}",
                resource_id=plan.capability_name,
                outcome=AuditOutcome.FAILURE,
                details={"reason": "cross_tenant_violation", "plan_id": plan.plan_id},
                correlation=correlation,
            )
            res = ActionResult(
                plan_id=plan.plan_id,
                status="denied",
                summary="Cross-tenant execution is strictly prohibited.",
                result_data={"error": "tenant_isolation_violation"},
                execution_id=exec_id,
            )
            self._executed_plans[plan.plan_id] = res
            return res

        # Check explicit permission context rights
        if not is_admin:
            if plan.operation in (OperationType.READ, OperationType.QUERY):
                if not perm_ctx.can_see(plan.capability_name):
                    audit_id = self._log_audit(
                        actor_id=user_id,
                        action=f"copilot.action.{plan.operation.value}",
                        resource_id=plan.capability_name,
                        outcome=AuditOutcome.FAILURE,
                        details={"reason": "visibility_denied", "plan_id": plan.plan_id},
                        correlation=correlation,
                    )
                    res = ActionResult(
                        plan_id=plan.plan_id,
                        status="denied",
                        summary="You do not have permission to view this resource.",
                        result_data={"error": "permission_denied"},
                        audit_entry_id=audit_id,
                        execution_id=exec_id,
                    )
                    self._executed_plans[plan.plan_id] = res
                    return res
            elif not perm_ctx.can_act(plan.capability_name):
                audit_id = self._log_audit(
                    actor_id=user_id,
                    action=f"copilot.action.{plan.operation.value}",
                    resource_id=plan.capability_name,
                    outcome=AuditOutcome.FAILURE,
                    details={"reason": "execution_denied", "plan_id": plan.plan_id},
                    correlation=correlation,
                )
                res = ActionResult(
                    plan_id=plan.plan_id,
                    status="denied",
                    summary="You do not have permission to execute this operation.",
                    result_data={"error": "permission_denied"},
                    audit_entry_id=audit_id,
                    execution_id=exec_id,
                )
                self._executed_plans[plan.plan_id] = res
                return res

        # Check explicit policy denial
        has_deny_rule = decision.effect is PolicyEffect.DENY and bool(decision.matched_rules)
        if has_deny_rule and not is_admin:
            audit_id = self._log_audit(
                actor_id=user_id,
                action=f"copilot.action.{plan.operation.value}",
                resource_id=plan.capability_name,
                outcome=AuditOutcome.FAILURE,
                details={"reason": "policy_denial", "matched_rules": list(decision.matched_rules)},
                correlation=correlation,
            )
            res = ActionResult(
                plan_id=plan.plan_id,
                status="denied",
                summary="You do not have permission to execute this operation.",
                result_data={"error": "permission_denied", "rules": list(decision.matched_rules)},
                audit_entry_id=audit_id,
                execution_id=exec_id,
            )
            self._executed_plans[plan.plan_id] = res
            return res

        # 2. APPROVAL GATE ENFORCEMENT
        if plan.requires_approval and not approved:
            approval_req = await self._approvals.create(
                tool_name=plan.tool_name,
                arguments=plan.arguments,
                requester_id=user_id,
                risk=plan.risk_tier,
            )
            audit_id = self._log_audit(
                actor_id=user_id,
                action="copilot.approval.requested",
                resource_id=plan.capability_name,
                outcome=AuditOutcome.SUCCESS,
                details={"approval_id": approval_req.id, "risk": plan.risk_tier.value},
                correlation=correlation,
            )
            return ActionResult(
                plan_id=plan.plan_id,
                status="approval_required",
                summary=(
                    f"Action requires approval due to risk tier `{plan.risk_tier.upper()}`. "
                    f"Approval request `{approval_req.id}` created."
                ),
                result_data={"approval_id": approval_req.id, "status": "pending"},
                approval_id=approval_req.id,
                audit_entry_id=audit_id,
                execution_id=exec_id,
            )

        # 3. GOVERNED EXECUTION
        tool = self._get_tool(plan.tool_name)
        if tool is None:
            audit_id = self._log_audit(
                actor_id=user_id,
                action=f"copilot.action.{plan.operation.value}",
                resource_id=plan.capability_name,
                outcome=AuditOutcome.FAILURE,
                details={"error": "tool_not_found", "tool_name": plan.tool_name},
                correlation=correlation,
            )
            res = ActionResult(
                plan_id=plan.plan_id,
                status="failed",
                summary=f"Underlying execution tool `{plan.tool_name}` is not available.",
                result_data={"error": "tool_not_found"},
                audit_entry_id=audit_id,
                execution_id=exec_id,
            )
            self._executed_plans[plan.plan_id] = res
            return res

        try:
            exec_args = dict(plan.arguments)
            if plan.target_id:
                exec_args["target_id"] = plan.target_id
            exec_args["user"] = user

            raw_output: object = await tool.execute(**exec_args)
            parsed_data = {}
            if isinstance(raw_output, str):
                try:
                    parsed_data = json.loads(raw_output)
                except Exception:
                    parsed_data = {"output": raw_output}
            elif isinstance(raw_output, dict):
                parsed_data = raw_output

            audit_id = self._log_audit(
                actor_id=user_id,
                action=f"copilot.action.{plan.operation.value}",
                resource_id=plan.capability_name,
                outcome=AuditOutcome.SUCCESS,
                details={
                    "tool": plan.tool_name,
                    "target_id": plan.target_id,
                    "execution_id": exec_id,
                },
                correlation=correlation,
            )

            res = ActionResult(
                plan_id=plan.plan_id,
                status="executed",
                summary=(
                    f"Successfully executed {plan.operation.upper()} "
                    f"on {plan.capability_name}."
                ),
                result_data=parsed_data,
                audit_entry_id=audit_id,
                execution_id=exec_id,
            )
            self._executed_plans[plan.plan_id] = res
            return res
        except Exception as exc:
            self._log.error("action.execution_failed", plan_id=plan.plan_id, error=str(exc))
            audit_id = self._log_audit(
                actor_id=user_id,
                action=f"copilot.action.{plan.operation.value}",
                resource_id=plan.capability_name,
                outcome=AuditOutcome.FAILURE,
                details={"error": str(exc)},
                correlation=correlation,
            )
            res = ActionResult(
                plan_id=plan.plan_id,
                status="failed",
                summary=f"Execution error: {exc}",
                result_data={"error": str(exc)},
                audit_entry_id=audit_id,
                execution_id=exec_id,
            )
            self._executed_plans[plan.plan_id] = res
            return res

    def _log_audit(
        self,
        *,
        actor_id: str,
        action: str,
        resource_id: str,
        outcome: AuditOutcome,
        details: dict[str, Any],
        correlation: CorrelationId,
    ) -> str:
        entry = AuditEntry(
            id=f"audit-{uuid.uuid4().hex[:12]}",
            actor_id=actor_id,
            action=action,
            resource_type="capability_action",
            resource_id=resource_id,
            outcome=outcome,
            details=details,
            correlation_id=str(correlation),
        )
        self._audit.log(entry)
        return entry.id


__all__ = ["ActionPlan", "ActionResult", "GovernedActionExecutor"]
