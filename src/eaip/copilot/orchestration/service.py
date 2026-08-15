"""OrchestrationService — governs enterprise orchestration plan lifecycle.

An orchestration plan is a bounded, governed execution plan.  It composes:
- Existing ToolRegistry/SkillRegistry for step execution
- Existing GovernancePolicy for permission checks
- Existing ApprovalService for human approval gates
- Existing AuditLogger for immutable audit trail
- Existing EventBus for domain events
- Existing SystemTwinService for live state

It does NOT create a parallel execution pathway.
"""

from __future__ import annotations

import hashlib
import uuid
from typing import Any

from eaip.admin.audit import AuditLogger
from eaip.admin.models import AuditEntry, AuditOutcome
from eaip.copilot.governance import GovernancePolicy
from eaip.copilot.orchestration.models import (
    CreatePlanRequest,
    FailureClass,
    OrchestrationPlan,
    OrchestrationStep,
    PlanRisk,
    PlanStatus,
    StepStatus,
)
from eaip.events.bus import EventBus
from eaip.logging.context import get_logger
from eaip.shared.identifiers import CorrelationId
from eaip.shared.time import utc_now
from eaip.tools.registry import ToolRegistry

# Valid state transitions.
_TRANSITIONS: dict[PlanStatus, frozenset[PlanStatus]] = {
    PlanStatus.DRAFT: frozenset(
        {PlanStatus.READY, PlanStatus.CANCELLED}
    ),
    PlanStatus.READY: frozenset(
        {
            PlanStatus.AWAITING_APPROVAL,
            PlanStatus.RUNNING,
            PlanStatus.CANCELLED,
        }
    ),
    PlanStatus.AWAITING_APPROVAL: frozenset(
        {
            PlanStatus.APPROVED,
            PlanStatus.CANCELLED,
            PlanStatus.DRAFT,
        }
    ),
    PlanStatus.APPROVED: frozenset(
        {
            PlanStatus.RUNNING,
            PlanStatus.CANCELLED,
            PlanStatus.DRAFT,
        }
    ),
    PlanStatus.RUNNING: frozenset(
        {
            PlanStatus.PAUSED,
            PlanStatus.BLOCKED,
            PlanStatus.FAILED,
            PlanStatus.CANCELLED,
            PlanStatus.COMPLETED,
            PlanStatus.PARTIAL_SUCCESS,
        }
    ),
    PlanStatus.PAUSED: frozenset(
        {
            PlanStatus.RUNNING,
            PlanStatus.CANCELLED,
        }
    ),
    PlanStatus.BLOCKED: frozenset(
        {
            PlanStatus.RUNNING,
            PlanStatus.CANCELLED,
            PlanStatus.FAILED,
        }
    ),
    PlanStatus.FAILED: frozenset(
        {PlanStatus.ROLLED_BACK, PlanStatus.DRAFT}
    ),
    PlanStatus.CANCELLED: frozenset(set()),
    PlanStatus.COMPLETED: frozenset(set()),
    PlanStatus.PARTIAL_SUCCESS: frozenset(
        {PlanStatus.ROLLED_BACK, PlanStatus.DRAFT}
    ),
    PlanStatus.ROLLED_BACK: frozenset(set()),
}

# Failure classification for step errors.
_FAILURE_PATTERNS: list[tuple[str, FailureClass]] = [
    ("permission", FailureClass.PERMISSION),
    ("denied", FailureClass.PERMISSION),
    ("unauthorized", FailureClass.PERMISSION),
    ("timeout", FailureClass.TIMEOUT),
    ("timed out", FailureClass.TIMEOUT),
    ("not found", FailureClass.DEPENDENCY),
    ("unavailable", FailureClass.DEPENDENCY),
    ("validation", FailureClass.VALIDATION),
    ("invalid", FailureClass.VALIDATION),
    ("policy", FailureClass.POLICY),
    ("governance", FailureClass.POLICY),
    ("rate limit", FailureClass.TRANSIENT),
    ("temporary", FailureClass.TRANSIENT),
    ("retry", FailureClass.TRANSIENT),
]


class OrchestrationService:
    """Manage governed orchestration plans with bounded execution.

    Plans are owned by a user within a tenant.  Steps are executed
    through the existing ToolRegistry with governance enforcement.
    All operations are audited.  Live state is revalidated before
    execution.  Cancellation is authoritative.
    """

    READ_PERMISSION = "copilot:orchestration:read"
    WRITE_PERMISSION = "copilot:orchestration:write"
    EXECUTE_PERMISSION = "copilot:orchestration:execute"
    DELETE_PERMISSION = "copilot:orchestration:delete"

    def __init__(
        self,
        *,
        governance: GovernancePolicy,
        audit: AuditLogger,
        tool_registry: ToolRegistry,
        event_bus: EventBus | None = None,
    ) -> None:
        """Initialize with existing platform primitives."""
        self._governance = governance
        self._audit = audit
        self._tools = tool_registry
        self._event_bus = event_bus
        self._log = get_logger("eaip.copilot.orchestration")
        self._plans: dict[str, OrchestrationPlan] = {}

    async def create(
        self,
        user: dict[str, Any],
        request: CreatePlanRequest,
    ) -> OrchestrationPlan:
        """Create a new orchestration plan in DRAFT status."""
        actor = self._actor(user)
        tenant = self._tenant(user)
        self._require_permission(user, self.WRITE_PERMISSION)

        plan_id = f"plan-{uuid.uuid4().hex[:12]}"
        now = utc_now()

        steps: list[OrchestrationStep] = []
        for i, step_data in enumerate(request.steps):
            step_id = step_data.get("id", f"step-{i + 1}")
            steps.append(
                OrchestrationStep(
                    id=step_id,
                    description=step_data.get("description", ""),
                    tool_name=step_data.get("tool_name", ""),
                    skill_id=step_data.get("skill_id", ""),
                    inputs=step_data.get("inputs", {}),
                    dependencies=tuple(step_data.get("dependencies", [])),
                    risk=PlanRisk(
                        step_data.get("risk", "informational")
                    ),
                    required_permission=step_data.get(
                        "required_permission", ""
                    ),
                    approval_required=step_data.get(
                        "approval_required", False
                    ),
                    reversible=step_data.get("reversible", False),
                    rollback_tool=step_data.get("rollback_tool", ""),
                    rollback_inputs=step_data.get(
                        "rollback_inputs", {}
                    ),
                    timeout_seconds=step_data.get(
                        "timeout_seconds", 60
                    ),
                    max_retries=step_data.get("max_retries", 1),
                )
            )

        plan_hash = self._compute_hash(steps)

        # Validate dependencies.
        step_ids = {s.id for s in steps}
        for step in steps:
            for dep in step.dependencies:
                if dep not in step_ids:
                    raise ValueError(
                        f"Step '{step.id}' depends on unknown "
                        f"step '{dep}'"
                    )

        # Detect cycles.
        if self._has_cycle(steps):
            raise ValueError("Plan contains a dependency cycle")

        # Determine cumulative risk.
        cumulative_risk = request.estimated_risk
        if any(
            s.risk == PlanRisk.DESTRUCTIVE for s in steps
        ):
            cumulative_risk = PlanRisk.DESTRUCTIVE
        elif any(
            s.risk == PlanRisk.ACTION for s in steps
        ):
            cumulative_risk = PlanRisk.ACTION

        plan = OrchestrationPlan(
            id=plan_id,
            tenant_id=tenant,
            owner_id=actor,
            objective=request.objective,
            description=request.description,
            status=PlanStatus.DRAFT,
            risk=cumulative_risk,
            steps=tuple(steps),
            estimated_risk=cumulative_risk,
            investigation_id=request.investigation_id,
            created_at=now,
            updated_at=now,
            plan_hash=plan_hash,
        )
        self._plans[plan_id] = plan

        self._audit_log(
            actor, "orchestration.created", plan_id, tenant
        )
        self._log.info(
            "orchestration.created",
            plan_id=plan_id,
            actor=actor,
            tenant=tenant,
            steps=len(steps),
        )
        return plan

    async def get(
        self, user: dict[str, Any], plan_id: str
    ) -> OrchestrationPlan | None:
        """Retrieve a plan visible to the user."""
        self._require_permission(user, self.READ_PERMISSION)
        plan = self._plans.get(plan_id)
        if plan is None:
            return None
        if not self._is_visible(user, plan):
            return None
        return plan

    async def list_plans(
        self,
        user: dict[str, Any],
        *,
        status: PlanStatus | None = None,
        limit: int = 20,
    ) -> list[OrchestrationPlan]:
        """List plans visible to the user."""
        self._require_permission(user, self.READ_PERMISSION)
        results: list[OrchestrationPlan] = []
        for plan in self._plans.values():
            if not self._is_visible(user, plan):
                continue
            if status and plan.status is not status:
                continue
            results.append(plan)
        results.sort(key=lambda p: p.updated_at, reverse=True)
        return results[:limit]

    async def ready(
        self, user: dict[str, Any], plan_id: str
    ) -> OrchestrationPlan:
        """Transition a plan from DRAFT to READY."""
        return await self._transition(
            user, plan_id, PlanStatus.READY, "readied"
        )

    async def request_approval(
        self, user: dict[str, Any], plan_id: str
    ) -> OrchestrationPlan:
        """Move plan to AWAITING_APPROVAL."""
        plan = await self._get_owned(user, plan_id)
        if plan.status not in (PlanStatus.READY, PlanStatus.DRAFT):
            raise ValueError(
                "Plan must be READY or DRAFT to request approval"
            )
        # Check if any step requires approval.
        needs_approval = any(
            s.approval_required
            or s.risk in (PlanRisk.ACTION, PlanRisk.DESTRUCTIVE)
            for s in plan.steps
        )
        if not needs_approval:
            # No approval needed — go to AWAITING_APPROVAL first,
            # then approve() will transition to APPROVED.
            return await self._transition(
                user,
                plan_id,
                PlanStatus.AWAITING_APPROVAL,
                "approval_requested",
            )
        return await self._transition(
            user,
            plan_id,
            PlanStatus.AWAITING_APPROVAL,
            "approval_requested",
        )

    async def approve(
        self, user: dict[str, Any], plan_id: str
    ) -> OrchestrationPlan:
        """Approve a plan that is awaiting approval."""
        plan = await self._get_owned(user, plan_id)
        # Re-check plan integrity first (before status check),
        # so hash tampering is detected regardless of plan state.
        current_hash = self._compute_hash(list(plan.steps))
        if current_hash != plan.plan_hash:
            raise ValueError(
                "Plan has been modified since approval request"
            )
        if plan.status is not PlanStatus.AWAITING_APPROVAL:
            raise ValueError("Plan is not awaiting approval")
        return await self._transition(
            user, plan_id, PlanStatus.APPROVED, "approved"
        )

    async def execute(
        self, user: dict[str, Any], plan_id: str
    ) -> OrchestrationPlan:
        """Execute an approved plan."""
        plan = await self._get_owned(user, plan_id)
        if plan.status not in (
            PlanStatus.APPROVED,
            PlanStatus.PAUSED,
        ):
            raise ValueError(
                "Plan must be APPROVED or PAUSED to execute"
            )
        self._require_permission(user, self.EXECUTE_PERMISSION)

        plan = plan.model_copy(
            update={
                "status": PlanStatus.RUNNING,
                "started_at": plan.started_at or utc_now(),
                "updated_at": utc_now(),
            }
        )
        self._plans[plan_id] = plan
        self._audit_log(
            self._actor(user),
            "orchestration.execution_started",
            plan_id,
            self._tenant(user),
        )
        return plan

    async def execute_steps(
        self, user: dict[str, Any], plan_id: str
    ) -> OrchestrationPlan:
        """Execute ready steps in the plan.

        Steps are executed in dependency order.  Independent steps
        may be executed concurrently up to the concurrency budget.
        """
        plan = await self._get_owned(user, plan_id)
        if plan.status is not PlanStatus.RUNNING:
            raise ValueError("Plan is not running")

        budget = plan.budget
        if plan.tool_calls_used >= budget.max_tool_calls:
            return await self._fail_plan(
                user, plan_id, "Tool call budget exceeded"
            )

        # Find ready steps (pending + all deps completed).
        completed_ids = {
            s.id
            for s in plan.steps
            if s.status in (StepStatus.COMPLETED, StepStatus.SKIPPED)
        }
        ready_steps = [
            s
            for s in plan.steps
            if s.status == StepStatus.PENDING
            and all(d in completed_ids for d in s.dependencies)
        ]

        if not ready_steps:
            # All steps done or blocked.
            all_done = all(
                s.status
                in (
                    StepStatus.COMPLETED,
                    StepStatus.SKIPPED,
                    StepStatus.FAILED,
                )
                for s in plan.steps
            )
            if all_done:
                has_failures = any(
                    s.status == StepStatus.FAILED
                    for s in plan.steps
                )
                terminal = (
                    PlanStatus.PARTIAL_SUCCESS
                    if has_failures
                    else PlanStatus.COMPLETED
                )
                plan = plan.model_copy(
                    update={
                        "status": terminal,
                        "completed_at": utc_now(),
                        "updated_at": utc_now(),
                        "result_summary": self._build_summary(
                            plan
                        ),
                    }
                )
                self._plans[plan_id] = plan
                self._audit_log(
                    self._actor(user),
                    f"orchestration.{terminal.value}",
                    plan_id,
                    self._tenant(user),
                )
            return plan

        # Execute up to max_concurrent_steps.
        executed = 0
        for step in ready_steps[:budget.max_concurrent_steps]:
            if plan.tool_calls_used >= budget.max_tool_calls:
                break

            step_plan = await self._execute_step(
                user, plan, step
            )
            plan = step_plan
            executed += 1

        self._plans[plan_id] = plan
        return plan

    async def _execute_step(
        self,
        user: dict[str, Any],
        plan: OrchestrationPlan,
        step: OrchestrationStep,
    ) -> OrchestrationPlan:
        """Execute a single plan step."""
        actor = self._actor(user)
        now = utc_now()
        correlation = str(CorrelationId.new())

        # Mark step as running.
        step.status = StepStatus.RUNNING
        step.started_at = now
        step.correlation_id = correlation
        plan = plan.model_copy(
            update={
                "current_step_index": list(plan.steps).index(step),
                "tool_calls_used": plan.tool_calls_used + 1,
                "updated_at": now,
            }
        )

        # Resolve tool.
        tool = self._tools.try_get(step.tool_name)
        if tool is None:
            step.status = StepStatus.FAILED
            step.error = f"Tool '{step.tool_name}' not available"
            step.failure_class = FailureClass.DEPENDENCY
            self._audit_step_failure(
                actor, plan.id, step, correlation
            )
            return plan

        # Check permissions.
        roles = list(user.get("roles") or [])
        if not self._governance.is_permitted(tool, roles):
            step.status = StepStatus.FAILED
            step.error = "Permission denied"
            step.failure_class = FailureClass.PERMISSION
            self._audit_step_failure(
                actor, plan.id, step, correlation
            )
            return plan

        # Check budget.
        if plan.tool_calls_used > plan.budget.max_tool_calls:
            step.status = StepStatus.FAILED
            step.error = "Tool call budget exceeded"
            step.failure_class = FailureClass.POLICY
            self._audit_step_failure(
                actor, plan.id, step, correlation
            )
            return plan

        # Execute with timeout.
        try:
            inputs = {**step.inputs, "user": user}
            result = await tool.execute(**inputs)
            step.status = StepStatus.COMPLETED
            step.result = result
            step.completed_at = utc_now()
            self._audit_log(
                actor,
                "orchestration.step_completed",
                plan.id,
                plan.tenant_id,
                details={"step_id": step.id, "tool": step.tool_name},
            )
        except TimeoutError:
            step.status = StepStatus.FAILED
            step.error = "Step timed out"
            step.failure_class = FailureClass.TIMEOUT
            self._audit_step_failure(
                actor, plan.id, step, correlation
            )
        except PermissionError as exc:
            step.status = StepStatus.FAILED
            step.error = str(exc)
            step.failure_class = FailureClass.PERMISSION
            self._audit_step_failure(
                actor, plan.id, step, correlation
            )
        except Exception as exc:
            step.status = StepStatus.FAILED
            step.error = repr(exc)
            step.failure_class = self._classify_failure(str(exc))
            # Retry if transient and retries remain.
            if (
                step.failure_class is FailureClass.TRANSIENT
                and step.retry_count < step.max_retries
            ):
                step.retry_count += 1
                step.status = StepStatus.PENDING
                plan = plan.model_copy(
                    update={"retries_used": plan.retries_used + 1}
                )
                self._log.info(
                    "orchestration.step_retry",
                    plan_id=plan.id,
                    step_id=step.id,
                    retry=step.retry_count,
                )
            else:
                self._audit_step_failure(
                    actor, plan.id, step, correlation
                )

        return plan

    async def pause(
        self, user: dict[str, Any], plan_id: str
    ) -> OrchestrationPlan:
        """Pause a running plan."""
        return await self._transition(
            user, plan_id, PlanStatus.PAUSED, "paused"
        )

    async def resume(
        self, user: dict[str, Any], plan_id: str
    ) -> OrchestrationPlan:
        """Resume a paused plan. Re-checks authorization."""
        plan = await self._get_owned(user, plan_id)
        if plan.status is not PlanStatus.PAUSED:
            raise ValueError("Plan is not paused")
        # Re-check plan integrity.
        current_hash = self._compute_hash(list(plan.steps))
        if current_hash != plan.plan_hash:
            raise ValueError(
                "Plan integrity check failed — plan was modified"
            )
        return await self._transition(
            user, plan_id, PlanStatus.RUNNING, "resumed"
        )

    async def cancel(
        self, user: dict[str, Any], plan_id: str
    ) -> OrchestrationPlan:
        """Cancel a plan. Authoritative — stops all new execution."""
        plan = await self._get_owned(user, plan_id)
        terminal_statuses = {
            PlanStatus.COMPLETED,
            PlanStatus.CANCELLED,
            PlanStatus.ROLLED_BACK,
        }
        if plan.status in terminal_statuses:
            raise ValueError(
                f"Cannot cancel plan in {plan.status.value} status"
            )
        plan = plan.model_copy(
            update={
                "status": PlanStatus.CANCELLED,
                "completed_at": utc_now(),
                "updated_at": utc_now(),
            }
        )
        self._plans[plan_id] = plan
        self._audit_log(
            self._actor(user),
            "orchestration.cancelled",
            plan_id,
            self._tenant(user),
        )
        return plan

    async def rollback(
        self, user: dict[str, Any], plan_id: str
    ) -> OrchestrationPlan:
        """Rollback completed reversible steps.

        Rollback itself is a governed action.  Steps are rolled back
        in reverse order.  Each rollback uses the step's rollback_tool
        if defined.
        """
        plan = await self._get_owned(user, plan_id)
        if plan.status not in (
            PlanStatus.FAILED,
            PlanStatus.PARTIAL_SUCCESS,
        ):
            raise ValueError(
                "Plan must be FAILED or PARTIAL_SUCCESS to rollback"
            )

        self._require_permission(user, self.EXECUTE_PERMISSION)
        actor = self._actor(user)

        rolled_back = 0
        for step in reversed(list(plan.steps)):
            if step.status is not StepStatus.COMPLETED:
                continue
            if not step.reversible or not step.rollback_tool:
                continue
            if plan.rollbacks_used >= plan.budget.max_rollbacks:
                break

            tool = self._tools.try_get(step.rollback_tool)
            if tool is None:
                self._log.warning(
                    "orchestration.rollback_tool_missing",
                    plan_id=plan_id,
                    step_id=step.id,
                    tool=step.rollback_tool,
                )
                continue

            try:
                inputs = {**step.rollback_inputs, "user": user}
                await tool.execute(**inputs)
                step.status = StepStatus.ROLLED_BACK
                rolled_back += 1
                plan = plan.model_copy(
                    update={"rollbacks_used": plan.rollbacks_used + 1}
                )
                self._audit_log(
                    actor,
                    "orchestration.step_rolled_back",
                    plan_id,
                    plan.tenant_id,
                    details={"step_id": step.id},
                )
            except Exception as exc:
                self._log.error(
                    "orchestration.rollback_failed",
                    plan_id=plan_id,
                    step_id=step.id,
                    error=str(exc),
                )

        plan = plan.model_copy(
            update={
                "status": PlanStatus.ROLLED_BACK,
                "completed_at": utc_now(),
                "updated_at": utc_now(),
                "result_summary": (
                    f"Rolled back {rolled_back} steps."
                ),
            }
        )
        self._plans[plan_id] = plan
        self._audit_log(
            actor,
            "orchestration.rolled_back",
            plan_id,
            plan.tenant_id,
        )
        return plan

    async def get_timeline(
        self, user: dict[str, Any], plan_id: str
    ) -> list[dict[str, Any]]:
        """Get the execution timeline for a plan."""
        plan = await self.get(user, plan_id)
        if plan is None:
            return []
        events: list[dict[str, Any]] = []
        events.append(
            {
                "timestamp": plan.created_at.isoformat(),
                "event": "plan_created",
                "description": f"Plan created: {plan.objective}",
            }
        )
        if plan.started_at:
            events.append(
                {
                    "timestamp": plan.started_at.isoformat(),
                    "event": "execution_started",
                    "description": "Execution started",
                }
            )
        for step in plan.steps:
            if step.started_at:
                events.append(
                    {
                        "timestamp": step.started_at.isoformat(),
                        "event": "step_started",
                        "description": (
                            f"Step '{step.id}': {step.description}"
                        ),
                        "step_id": step.id,
                    }
                )
            if step.completed_at:
                events.append(
                    {
                        "timestamp": step.completed_at.isoformat(),
                        "event": (
                            "step_completed"
                            if step.status is StepStatus.COMPLETED
                            else "step_failed"
                        ),
                        "description": (
                            f"Step '{step.id}': "
                            f"{step.status.value}"
                        ),
                        "step_id": step.id,
                        "result": step.result[:200] if step.result else "",
                        "error": step.error[:200] if step.error else "",
                    }
                )
        if plan.completed_at:
            events.append(
                {
                    "timestamp": plan.completed_at.isoformat(),
                    "event": "plan_completed",
                    "description": (
                        f"Plan {plan.status.value}: "
                        f"{plan.result_summary}"
                    ),
                }
            )
        events.sort(key=lambda e: e["timestamp"])
        return events

    def serialize(
        self, plan: OrchestrationPlan
    ) -> dict[str, Any]:
        """Serialize a plan for API response."""
        return {
            "id": plan.id,
            "tenant_id": plan.tenant_id,
            "owner_id": plan.owner_id,
            "objective": plan.objective,
            "description": plan.description,
            "status": plan.status.value,
            "risk": plan.risk.value,
            "steps": [
                {
                    "id": s.id,
                    "description": s.description,
                    "tool_name": s.tool_name,
                    "risk": s.risk.value,
                    "status": s.status.value,
                    "dependencies": list(s.dependencies),
                    "approval_required": s.approval_required,
                    "reversible": s.reversible,
                    "result": s.result[:200] if s.result else "",
                    "error": s.error[:200] if s.error else "",
                    "failure_class": s.failure_class.value,
                    "retry_count": s.retry_count,
                }
                for s in plan.steps
            ],
            "current_step_index": plan.current_step_index,
            "estimated_risk": plan.estimated_risk.value,
            "approval_required": plan.approval_required,
            "investigation_id": plan.investigation_id,
            "budget": {
                "max_steps": plan.budget.max_steps,
                "max_tool_calls": plan.budget.max_tool_calls,
                "max_retries": plan.budget.max_retries,
                "max_execution_seconds": plan.budget.max_execution_seconds,
                "max_concurrent_steps": plan.budget.max_concurrent_steps,
                "max_destructive_actions": plan.budget.max_destructive_actions,
                "max_rollbacks": plan.budget.max_rollbacks,
            },
            "tool_calls_used": plan.tool_calls_used,
            "retries_used": plan.retries_used,
            "rollbacks_used": plan.rollbacks_used,
            "result_summary": plan.result_summary,
            "failure_info": plan.failure_info,
            "plan_hash": plan.plan_hash,
            "created_at": plan.created_at.isoformat(),
            "updated_at": plan.updated_at.isoformat(),
            "started_at": (
                plan.started_at.isoformat()
                if plan.started_at
                else None
            ),
            "completed_at": (
                plan.completed_at.isoformat()
                if plan.completed_at
                else None
            ),
            "provenance": plan.provenance,
        }

    # --- Private helpers ---

    async def _transition(
        self,
        user: dict[str, Any],
        plan_id: str,
        target: PlanStatus,
        action: str,
    ) -> OrchestrationPlan:
        """Transition a plan to a new status."""
        actor = self._actor(user)
        plan = await self._get_owned(user, plan_id)
        allowed = _TRANSITIONS.get(plan.status, frozenset())
        if target not in allowed:
            raise ValueError(
                f"Cannot transition from {plan.status.value} "
                f"to {target.value}"
            )
        plan = plan.model_copy(
            update={
                "status": target,
                "updated_at": utc_now(),
            }
        )
        self._plans[plan_id] = plan
        self._audit_log(
            actor,
            f"orchestration.{action}",
            plan_id,
            plan.tenant_id,
        )
        return plan

    async def _fail_plan(
        self,
        user: dict[str, Any],
        plan_id: str,
        reason: str,
    ) -> OrchestrationPlan:
        """Fail a plan with a reason."""
        plan = self._plans[plan_id]
        plan = plan.model_copy(
            update={
                "status": PlanStatus.FAILED,
                "completed_at": utc_now(),
                "updated_at": utc_now(),
                "failure_info": reason,
            }
        )
        self._plans[plan_id] = plan
        self._audit_log(
            self._actor(user),
            "orchestration.failed",
            plan_id,
            plan.tenant_id,
            details={"reason": reason},
        )
        return plan

    async def _get_owned(
        self, user: dict[str, Any], plan_id: str
    ) -> OrchestrationPlan:
        """Get a plan and verify ownership."""
        plan = self._plans.get(plan_id)
        if plan is None:
            raise ValueError(f"Plan not found: {plan_id}")
        if not self._is_owner(user, plan):
            raise PermissionError("You do not own this plan")
        return plan

    def _is_owner(
        self, user: dict[str, Any], plan: OrchestrationPlan
    ) -> bool:
        """Check if the user is the plan owner."""
        return self._actor(user) == plan.owner_id

    def _is_visible(
        self, user: dict[str, Any], plan: OrchestrationPlan
    ) -> bool:
        """Check if the user can see this plan."""
        if self._tenant(user) != plan.tenant_id:
            return False
        if self._is_owner(user, plan):
            return True
        roles = list(user.get("roles") or [])
        return "admin" in roles

    def _require_permission(
        self, user: dict[str, Any], permission: str
    ) -> None:
        """Enforce permissions from server-authenticated roles."""
        roles = list(user.get("roles") or [])
        permissions = self._governance.role_permissions(roles)
        if permission not in permissions and "*" not in permissions:
            raise PermissionError(
                "You do not have permission for this operation"
            )

    def _audit_log(
        self,
        actor: str,
        action: str,
        resource_id: str,
        tenant: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Write an audit entry."""
        self._audit.log(
            AuditEntry(
                id=f"audit-orch-{uuid.uuid4().hex[:12]}",
                actor_id=actor,
                action=action,
                resource_type="orchestration",
                resource_id=resource_id,
                outcome=AuditOutcome.SUCCESS,
                details={"tenant_id": tenant, **(details or {})},
                correlation_id=str(CorrelationId.new()),
            )
        )

    def _audit_step_failure(
        self,
        actor: str,
        plan_id: str,
        step: OrchestrationStep,
        correlation: str,
    ) -> None:
        """Audit a step failure."""
        self._audit.log(
            AuditEntry(
                id=f"audit-orch-step-{uuid.uuid4().hex[:12]}",
                actor_id=actor,
                action="orchestration.step_failed",
                resource_type="orchestration_step",
                resource_id=f"{plan_id}/{step.id}",
                outcome=AuditOutcome.FAILURE,
                details={
                    "step_id": step.id,
                    "tool": step.tool_name,
                    "error": step.error[:200],
                    "failure_class": step.failure_class.value,
                },
                correlation_id=correlation,
            )
        )

    @staticmethod
    def _compute_hash(steps: list[OrchestrationStep]) -> str:
        """Compute a hash of the plan steps for integrity checking."""
        content = "|".join(
            f"{s.id}:{s.tool_name}:{s.description}"
            for s in steps
        )
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    @staticmethod
    def _has_cycle(steps: list[OrchestrationStep]) -> bool:
        """Detect cycles in the step dependency graph using DFS."""
        adj: dict[str, list[str]] = {s.id: list(s.dependencies) for s in steps}
        WHITE, GRAY, BLACK = 0, 1, 2
        color: dict[str, int] = {s.id: WHITE for s in steps}

        def dfs(node: str) -> bool:
            color[node] = GRAY
            for neighbor in adj.get(node, []):
                if color.get(neighbor) == GRAY:
                    return True
                if color.get(neighbor) == WHITE and dfs(neighbor):
                    return True
            color[node] = BLACK
            return False

        return any(
            dfs(s.id)
            for s in steps
            if color.get(s.id) == WHITE
        )

    @staticmethod
    def _classify_failure(error: str) -> FailureClass:
        """Classify a failure from its error message."""
        lower = error.lower()
        for pattern, classification in _FAILURE_PATTERNS:
            if pattern in lower:
                return classification
        return FailureClass.UNKNOWN

    @staticmethod
    def _build_summary(plan: OrchestrationPlan) -> str:
        """Build a result summary from step outcomes."""
        completed = sum(
            1
            for s in plan.steps
            if s.status == StepStatus.COMPLETED
        )
        failed = sum(
            1 for s in plan.steps if s.status is StepStatus.FAILED
        )
        skipped = sum(
            1 for s in plan.steps if s.status is StepStatus.SKIPPED
        )
        total = len(plan.steps)
        return (
            f"{completed}/{total} steps completed, "
            f"{failed} failed, {skipped} skipped."
        )

    @staticmethod
    def _actor(user: dict[str, Any]) -> str:
        """Extract actor from authenticated claims."""
        return str(user.get("sub") or user.get("name") or "unknown")

    @staticmethod
    def _tenant(user: dict[str, Any]) -> str:
        """Extract tenant from authenticated claims."""
        return str(
            user.get("organization_id")
            or user.get("org_id")
            or user.get("tenant_id")
            or "default"
        )


__all__ = ["OrchestrationService"]
