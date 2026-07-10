"""Human-in-the-loop - approval steps, pause/resume, resume tokens, checkpoints."""

from __future__ import annotations

import asyncio
import uuid
from datetime import UTC, datetime
from typing import Any

from eaip.events.bus import EventBus
from eaip.workflow.base import ApprovalHandler
from eaip.workflow.events import (
    WorkflowStepApprovalRequired,
    WorkflowStepApproved,
    WorkflowStepRejected,
)
from eaip.workflow.exceptions import ApprovalTimeoutError
from eaip.workflow.models import WorkflowStepStatus


class StepApprovalHandler(ApprovalHandler):
    """In-memory approval handler with pause/resume semantics.

    Stores pending approvals and allows external approval/rejection via
    resume tokens. Timeout and polling semantics are supported.
    Supports checkpoint-based approvals where the workflow state
    is preserved at the approval point.
    """

    def __init__(self, event_bus: EventBus | None = None) -> None:
        self._pending: dict[str, dict[str, Any]] = {}
        self._resolved: dict[str, str] = {}
        self._checkpoints: dict[str, dict[str, Any]] = {}
        self._event_bus = event_bus

    async def request_approval(
        self,
        step_id: str,
        run_id: str,
        payload: dict[str, Any],
        timeout_seconds: float | None = None,
    ) -> str:
        token = uuid.uuid4().hex[:24]
        self._pending[token] = {
            "step_id": step_id,
            "run_id": run_id,
            "payload": payload,
            "status": WorkflowStepStatus.WAITING_APPROVAL,
            "created_at": datetime.now(UTC).isoformat(),
        }

        if self._event_bus:
            await self._event_bus.publish(
                WorkflowStepApprovalRequired(
                    run_id=run_id,
                    workflow_id="",
                    step_id=step_id,
                    step_name=payload.get("step_name", step_id),
                    payload=payload,
                    resume_token=token,
                    approval_prompt=payload.get("prompt", ""),
                )
            )

        if timeout_seconds and timeout_seconds > 0:
            resolved = await self._poll_for_resolution(token, timeout_seconds)
            if not resolved:
                del self._pending[token]
                raise ApprovalTimeoutError(step_id, timeout_seconds)

        return token

    async def approve(self, token: str, run_id: str) -> None:
        if token not in self._pending:
            return
        entry = self._pending[token]
        entry["status"] = WorkflowStepStatus.APPROVED
        self._resolved[token] = "approved"

        if self._event_bus:
            await self._event_bus.publish(
                WorkflowStepApproved(
                    run_id=run_id,
                    workflow_id="",
                    step_id=entry["step_id"],
                    step_name=entry["payload"].get("step_name", entry["step_id"]),
                    resume_token=token,
                )
            )

    async def reject(self, token: str, run_id: str, reason: str) -> None:
        if token not in self._pending:
            return
        entry = self._pending[token]
        entry["status"] = WorkflowStepStatus.REJECTED
        entry["reason"] = reason
        self._resolved[token] = f"rejected:{reason}"

        if self._event_bus:
            await self._event_bus.publish(
                WorkflowStepRejected(
                    run_id=run_id,
                    workflow_id="",
                    step_id=entry["step_id"],
                    step_name=entry["payload"].get("step_name", entry["step_id"]),
                    reason=reason,
                    resume_token=token,
                )
            )

    # ------------------------------------------------------------------
    # Checkpoint support
    # ------------------------------------------------------------------

    def save_checkpoint(
        self, token: str, checkpoint_data: dict[str, Any],
    ) -> None:
        self._checkpoints[token] = {
            "data": checkpoint_data,
            "saved_at": datetime.now(UTC).isoformat(),
        }

    def get_checkpoint(self, token: str) -> dict[str, Any] | None:
        entry = self._checkpoints.get(token)
        return dict(entry) if entry else None

    # ------------------------------------------------------------------
    # Query methods
    # ------------------------------------------------------------------

    def get_status(self, token: str) -> WorkflowStepStatus | None:
        entry = self._pending.get(token)
        if entry is None:
            return None
        return entry["status"]  # type: ignore[no-any-return]

    def get_pending(self, run_id: str | None = None) -> list[dict[str, Any]]:
        results = []
        for entry in self._pending.values():
            if run_id and entry["run_id"] != run_id:
                continue
            if entry["status"] != WorkflowStepStatus.WAITING_APPROVAL:
                continue
            results.append(dict(entry))
        return results

    def count_pending(self, run_id: str | None = None) -> int:
        return len(self.get_pending(run_id))

    def is_resolved(self, token: str) -> bool:
        return token in self._resolved

    def get_resolution(self, token: str) -> str | None:
        return self._resolved.get(token)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _poll_for_resolution(self, token: str, poll_timeout: float) -> bool:
        elapsed = 0.0
        interval = 0.5
        while elapsed < poll_timeout:
            if token in self._resolved:
                return True
            await asyncio.sleep(interval)
            elapsed += interval
        return False


__all__ = [
    "StepApprovalHandler",
]
