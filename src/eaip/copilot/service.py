"""ConductorService — orchestrates the governed copilot flow."""

from __future__ import annotations

import json
import uuid
from collections.abc import AsyncIterator
from typing import Any

from eaip.admin.audit import AuditLogger
from eaip.admin.models import AuditEntry, AuditOutcome
from eaip.copilot.approvals import ApprovalService
from eaip.copilot.events import ConductorTurnCompleted
from eaip.copilot.governance import GovernancePolicy, tool_risk
from eaip.copilot.models import ApprovalRequest, CopilotTurn, ToolEvent
from eaip.copilot.planner import ConductorPlanner
from eaip.events.bus import EventBus
from eaip.logging.context import get_logger
from eaip.shared.identifiers import CorrelationId
from eaip.tools.base import Tool
from eaip.tools.registry import ToolRegistry


class ConductorService:
    """Orchestrate a governed Conductor turn: plan, gate, execute, audit.

    The service wires together the planner, the governance policy, the tool
    registry, the approval service, and the audit logger into the vertical
    slice: ask -> inspect -> ground -> approve -> execute -> audit.
    """

    def __init__(
        self,
        *,
        tool_registry: ToolRegistry,
        planner: ConductorPlanner,
        governance: GovernancePolicy,
        approvals: ApprovalService,
        audit: AuditLogger,
        event_bus: EventBus | None = None,
    ) -> None:
        """Initialize the Conductor service.

        Args:
            tool_registry: The platform tool registry.
            planner: The intent planner used to select tools.
            governance: The permission and risk policy.
            approvals: The approval request service.
            audit: The audit logger for immutable audit entries.
            event_bus: Optional event bus for turn events.
        """
        self._tools = tool_registry
        self._planner = planner
        self._governance = governance
        self._approvals = approvals
        self._audit = audit
        self._event_bus = event_bus
        self._log = get_logger("eaip.copilot.service")

    async def converse(self, message: str, user: dict[str, Any]) -> CopilotTurn:
        """Process a single user message into a grounded, governed turn.

        Args:
            message: The raw user message.
            user: The authenticated caller's identity claims.

        Returns:
            A :class:`CopilotTurn` describing the outcome.
        """
        actor = self._actor(user)
        roles = list(user.get("roles") or [])
        correlation = CorrelationId.new()
        plan = self._planner.plan(message)

        events: list[ToolEvent] = []
        pending: ApprovalRequest | None = None
        reply = plan.reply

        if plan.tool_call is not None:
            tool = self._tools.try_get(plan.tool_call.tool_name)
            if tool is None:
                reply = "I tried to use a tool that is not available. Please try again."
                events.append(
                    ToolEvent(tool_name=plan.tool_call.tool_name, status="failed")
                )
                self._audit.log(
                    self._entry(
                        actor,
                        action=f"copilot.tool.{plan.tool_call.tool_name}",
                        resource_type="tool",
                        resource_id=plan.tool_call.tool_name,
                        outcome=AuditOutcome.FAILURE,
                        details={"error": "unknown tool"},
                        correlation=correlation,
                    )
                )
            elif not self._governance.is_permitted(tool, roles):
                reply = "You do not have permission to perform that action."
                events.append(
                    ToolEvent(tool_name=tool.name, status="denied", summary="Permission denied")
                )
                self._audit.log(
                    self._entry(
                        actor,
                        action=f"copilot.tool.{tool.name}",
                        resource_type="tool",
                        resource_id=tool.name,
                        outcome=AuditOutcome.FAILURE,
                        details={"error": "permission denied"},
                        correlation=correlation,
                    )
                )
            elif self._governance.requires_approval(tool):
                risk = tool_risk(tool)
                pending = await self._approvals.create(
                    tool_name=tool.name,
                    arguments=plan.tool_call.arguments,
                    requester_id=actor,
                    risk=risk,
                )
                events.append(
                    ToolEvent(
                        tool_name=tool.name,
                        status="pending_approval",
                        summary="Awaiting your approval",
                        arguments=pending.arguments,
                    )
                )
                self._audit.log(
                    self._entry(
                        actor,
                        action="copilot.approval.request",
                        resource_type="approval",
                        resource_id=pending.id,
                        outcome=AuditOutcome.SUCCESS,
                        details={
                            "tool_name": tool.name,
                            "arguments": pending.arguments,
                            "risk": risk.value,
                        },
                        correlation=correlation,
                    )
                )
            else:
                result, audit_id = await self._execute(
                    actor, tool, plan.tool_call.arguments, correlation, user=user
                )
                events.append(
                    ToolEvent(
                        tool_name=tool.name,
                        status="executed",
                        summary=result,
                        arguments=plan.tool_call.arguments,
                        audit_entry_id=audit_id,
                    )
                )
                reply = result

        turn = CopilotTurn(
            id=f"turn-{uuid.uuid4().hex[:12]}",
            reply=reply,
            tool_events=tuple(events),
            pending_approval=pending,
            correlation_id=str(correlation),
        )
        await self._publish(
            ConductorTurnCompleted(
                turn_id=turn.id,
                actor_id=actor,
                reply=reply,
                tool_events=tuple(event.tool_name for event in events),
                correlation_id=correlation,
            )
        )
        return turn

    async def stream_converse(
        self, message: str, user: dict[str, Any]
    ) -> AsyncIterator[str]:
        """Stream SSE events for a single Conductor turn."""
        turn_id = f"turn-{uuid.uuid4().hex[:12]}"
        start_payload = json.dumps({"turn_id": turn_id, "message": message})
        yield f"event: message_start\ndata: {start_payload}\n\n"

        turn = await self.converse(message, user)

        for event in turn.tool_events:
            call_payload = json.dumps(
                {"tool_name": event.tool_name, "arguments": event.arguments}
            )
            yield f"event: tool_call\ndata: {call_payload}\n\n"
            result_payload = json.dumps(
                {
                    "tool_name": event.tool_name,
                    "status": event.status,
                    "summary": event.summary,
                }
            )
            yield f"event: tool_result\ndata: {result_payload}\n\n"

        if turn.pending_approval:
            approval_payload = json.dumps(
                {
                    "approval_id": turn.pending_approval.id,
                    "tool_name": turn.pending_approval.tool_name,
                }
            )
            yield f"event: approval_required\ndata: {approval_payload}\n\n"

        for word in turn.reply.split():
            delta_payload = json.dumps({"delta": word + " "})
            yield f"event: text_delta\ndata: {delta_payload}\n\n"

        complete_payload = json.dumps(
            {"turn_id": turn_id, "turn": turn.model_dump()}, default=str
        )
        yield f"event: message_complete\ndata: {complete_payload}\n\n"


    async def decide_approval(
        self,
        approval_id: str,
        user: dict[str, Any],
        *,
        approve: bool,
    ) -> tuple[ApprovalRequest, str | None]:
        """Decide a pending approval and, when approved, execute the tool.

        Args:
            approval_id: The approval request id.
            user: The decision-maker's identity claims.
            approve: True to approve and run the tool, False to reject.

        Returns:
            A tuple of the resolved request and (when approved) the tool result.

        Raises:
            ApprovalNotFoundError: If the id is unknown or not pending.
        """
        actor = self._actor(user)
        roles = list(user.get("roles") or [])
        request = await self._approvals.decide(
            approval_id, decided_by=actor, approve=approve
        )
        result: str | None = None
        outcome = AuditOutcome.SUCCESS
        details: dict[str, Any] = {"tool_name": request.tool_name, "result": None}
        if approve:
            tool = self._tools.try_get(request.tool_name)
            if tool is None:
                result = f"Tool {request.tool_name!r} is no longer available."
                details["result"] = result
                details["error"] = "tool unavailable"
                outcome = AuditOutcome.FAILURE
            elif not self._governance.is_permitted(tool, roles):
                result = "You do not have permission to execute this action."
                details["result"] = result
                details["error"] = "permission denied at decision time"
                outcome = AuditOutcome.FAILURE
            else:
                result, _ = await self._execute(
                    actor, tool, request.arguments, CorrelationId.new(), user=user
                )
                details["result"] = result
        self._audit.log(
            self._entry(
                actor,
                action=f"copilot.approval.{'approve' if approve else 'reject'}",
                resource_type="approval",
                resource_id=request.id,
                outcome=outcome,
                details=details,
                correlation=CorrelationId.new(),
            )
        )
        return request, result

    async def list_pending(self, user: dict[str, Any]) -> list[ApprovalRequest]:
        """List the caller's pending approval requests.

        Args:
            user: The authenticated caller's identity claims.

        Returns:
            Pending approval requests for the caller.
        """
        return self._approvals.list_pending(requester_id=self._actor(user))

    async def _execute(
        self,
        actor: str,
        tool: Tool,
        arguments: dict[str, Any],
        correlation: CorrelationId,
        *,
        user: dict[str, Any] | None = None,
    ) -> tuple[str, str]:
        """Execute a tool and write the corresponding audit entry.

        Args:
            actor: The actor triggering the execution.
            tool: The tool to run.
            arguments: The tool arguments.
            correlation: The correlation id for the turn.

        Returns:
            The tool result string and the audit entry id.

        Args:
            user: Authenticated user context passed only to context-aware tools.
        """
        entry = self._entry(
            actor,
            action=f"copilot.tool.{tool.name}",
            resource_type="tool",
            resource_id=tool.name,
            outcome=AuditOutcome.SUCCESS,
            details={"arguments": arguments},
            correlation=correlation,
        )
        try:
            execution_arguments = {**arguments}
            if user is not None:
                execution_arguments["user"] = user
            result = await tool.execute(**execution_arguments)
            entry = entry.model_copy(
                update={"details": {"arguments": arguments, "result": result}}
            )
        except Exception as exc:
            result = f"Tool failed: {exc!r}"
            entry = entry.model_copy(
                update={
                    "outcome": AuditOutcome.FAILURE,
                    "details": {"arguments": arguments, "error": repr(exc)},
                }
            )
        await self._audit.publish(entry)
        return result, entry.id

    @staticmethod
    def _actor(user: dict[str, Any]) -> str:
        """Extract a stable actor id from identity claims."""
        return str(user.get("sub") or user.get("name") or "unknown")

    @staticmethod
    def _entry(
        actor: str,
        *,
        action: str,
        resource_type: str,
        resource_id: str,
        outcome: AuditOutcome,
        details: dict[str, Any],
        correlation: CorrelationId,
    ) -> AuditEntry:
        """Build a new audit entry for a copilot action."""
        return AuditEntry(
            id=f"audit-{uuid.uuid4().hex[:12]}",
            actor_id=actor,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
            outcome=outcome,
            correlation_id=str(correlation),
        )

    async def _publish(self, event: Any) -> None:
        if self._event_bus is not None:
            await self._event_bus.publish(event)


__all__ = ["ConductorService"]
