"""Human approval workflow — multi-step approval chains, delegation, deadline enforcement."""

from __future__ import annotations

from datetime import datetime, timedelta
from enum import StrEnum

from eaip.shared.time import utc_now


class ApprovalStepStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    SKIPPED = "skipped"
    ESCALATED = "escalated"


class ApprovalStep:
    def __init__(
        self,
        step_id: str,
        workflow_id: str,
        order: int,
        approver: str,
        description: str = "",
        deadline_minutes: int = 0,
        delegate_to: str | None = None,
    ) -> None:
        self.step_id = step_id
        self.workflow_id = workflow_id
        self.order = order
        self.approver = approver
        self.description = description
        self.deadline_minutes = deadline_minutes
        self.delegate_to = delegate_to
        self.status = ApprovalStepStatus.PENDING
        self.comment: str = ""
        self.decided_at: datetime | None = None
        self.deadline: datetime | None = None
        self.created_at = utc_now()


class ApprovalWorkflow:
    def __init__(
        self,
        workflow_id: str,
        name: str,
        initiator: str,
        steps: list[ApprovalStep] | None = None,
    ) -> None:
        self.workflow_id = workflow_id
        self.name = name
        self.initiator = initiator
        self._steps: dict[str, ApprovalStep] = {}
        self._ordered: list[ApprovalStep] = []
        self.is_completed: bool = False
        self.is_approved: bool = False
        self.created_at = utc_now()
        self.completed_at: datetime | None = None

        if steps:
            for step in steps:
                self.add_step(step)

    def add_step(self, step: ApprovalStep) -> None:
        self._steps[step.step_id] = step
        self._ordered.append(step)
        step.deadline = utc_now() + timedelta(minutes=step.deadline_minutes)

    def get_step(self, step_id: str) -> ApprovalStep | None:
        return self._steps.get(step_id)

    def get_pending_step(self) -> ApprovalStep | None:
        for step in self._ordered:
            if step.status == ApprovalStepStatus.PENDING:
                return step
        return None

    def approve(self, step_id: str, comment: str = "") -> bool:
        step = self._steps.get(step_id)
        if step is None or step.status != ApprovalStepStatus.PENDING:
            return False
        pending = self.get_pending_step()
        if pending is not None and pending.step_id != step_id:
            return False
        step.status = ApprovalStepStatus.APPROVED
        step.comment = comment
        step.decided_at = utc_now()

        if self.get_pending_step() is None:
            self.is_completed = True
            self.is_approved = True
            self.completed_at = utc_now()
        return True

    def reject(self, step_id: str, comment: str = "") -> bool:
        step = self._steps.get(step_id)
        if step is None or step.status != ApprovalStepStatus.PENDING:
            return False
        pending = self.get_pending_step()
        if pending is not None and pending.step_id != step_id:
            return False
        step.status = ApprovalStepStatus.REJECTED
        step.comment = comment
        step.decided_at = utc_now()
        self.is_completed = True
        self.is_approved = False
        self.completed_at = utc_now()
        return True

    def delegate(self, step_id: str, delegate_to: str) -> bool:
        step = self._steps.get(step_id)
        if step is None:
            return False
        step.delegate_to = delegate_to
        return True

    def check_deadlines(self) -> list[ApprovalStep]:
        escalated: list[ApprovalStep] = []
        now = utc_now()
        for step in self._ordered:
            if (
                step.status == ApprovalStepStatus.PENDING
                and step.deadline is not None
                and now >= step.deadline
            ):
                step.status = ApprovalStepStatus.ESCALATED
                escalated.append(step)
        return escalated

    def get_steps(self) -> list[ApprovalStep]:
        return list(self._ordered)

    def current_step_index(self) -> int:
        for i, step in enumerate(self._ordered):
            if step.status == ApprovalStepStatus.PENDING:
                return i
        return len(self._ordered)


__all__ = [
    "ApprovalStep",
    "ApprovalStepStatus",
    "ApprovalWorkflow",
]
