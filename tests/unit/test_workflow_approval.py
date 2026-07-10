"""Tests for StepApprovalHandler - approve, reject, timeout, pending checks."""

from __future__ import annotations

import pytest

from eaip.events.bus import EventBus
from eaip.workflow.approval import StepApprovalHandler
from eaip.workflow.events import WorkflowStepApproved, WorkflowStepRejected
from eaip.workflow.exceptions import ApprovalTimeoutError
from eaip.workflow.models import WorkflowStepStatus


class TestStepApprovalHandler:
    @pytest.fixture
    def handler(self) -> StepApprovalHandler:
        return StepApprovalHandler()

    async def test_request_approval_returns_token(self, handler: StepApprovalHandler) -> None:
        token = await handler.request_approval("step_1", "run_1", {"step_name": "Check Data"})
        assert isinstance(token, str)
        assert len(token) > 0

    async def test_approve_updates_status(self, handler: StepApprovalHandler) -> None:
        token = await handler.request_approval("step_1", "run_1", {})
        await handler.approve(token, "run_1")
        status = handler.get_status(token)
        assert status is WorkflowStepStatus.APPROVED

    async def test_reject_updates_status(self, handler: StepApprovalHandler) -> None:
        token = await handler.request_approval("step_1", "run_1", {})
        await handler.reject(token, "run_1", "invalid data")
        status = handler.get_status(token)
        assert status is WorkflowStepStatus.REJECTED

    async def test_get_pending_returns_waiting(self, handler: StepApprovalHandler) -> None:
        await handler.request_approval("step_1", "run_1", {"key": "val"})
        pending = handler.get_pending()
        assert len(pending) == 1
        assert pending[0]["step_id"] == "step_1"
        assert pending[0]["status"] is WorkflowStepStatus.WAITING_APPROVAL

    async def test_get_pending_filtered_by_run_id(self, handler: StepApprovalHandler) -> None:
        await handler.request_approval("s1", "run_1", {})
        await handler.request_approval("s2", "run_2", {})
        pending_run1 = handler.get_pending(run_id="run_1")
        assert len(pending_run1) == 1
        assert pending_run1[0]["step_id"] == "s1"

    async def test_get_pending_empty(self, handler: StepApprovalHandler) -> None:
        assert handler.get_pending() == []

    async def test_get_status_nonexistent(self, handler: StepApprovalHandler) -> None:
        assert handler.get_status("bogus_token") is None

    async def test_approve_nonexistent_token(self, handler: StepApprovalHandler) -> None:
        await handler.approve("bogus", "run_1")
        assert handler.get_status("bogus") is None

    async def test_reject_nonexistent_token(self, handler: StepApprovalHandler) -> None:
        await handler.reject("bogus", "run_1", "no reason")
        assert handler.get_status("bogus") is None

    async def test_request_approval_timeout(self) -> None:
        handler = StepApprovalHandler()
        with pytest.raises(ApprovalTimeoutError):
            await handler.request_approval("step_t", "run_t", {}, timeout_seconds=0.01)

    async def test_approval_then_get_pending_removed(self, handler: StepApprovalHandler) -> None:
        token = await handler.request_approval("s1", "run_1", {})
        await handler.approve(token, "run_1")
        pending = handler.get_pending()
        assert all(p["status"] is not WorkflowStepStatus.APPROVED for p in pending)

    async def test_multiple_approvals(self, handler: StepApprovalHandler) -> None:
        t1 = await handler.request_approval("s1", "run_1", {})
        t2 = await handler.request_approval("s2", "run_1", {})
        await handler.approve(t1, "run_1")
        await handler.reject(t2, "run_1", "nope")
        assert handler.get_status(t1) is WorkflowStepStatus.APPROVED
        assert handler.get_status(t2) is WorkflowStepStatus.REJECTED

    async def test_events_published_on_approve(self) -> None:
        events: list = []
        bus = EventBus()
        bus.subscribe(WorkflowStepApproved, events.append)
        handler = StepApprovalHandler(event_bus=bus)
        token = await handler.request_approval("s1", "run_1", {"step_name": "Review"})
        await handler.approve(token, "run_1")
        assert len(events) == 1
        assert events[0].step_id == "s1"

    async def test_events_published_on_reject(self) -> None:
        events: list = []
        bus = EventBus()
        bus.subscribe(WorkflowStepRejected, events.append)
        handler = StepApprovalHandler(event_bus=bus)
        token = await handler.request_approval("s1", "run_1", {"step_name": "Review"})
        await handler.reject(token, "run_1", "bad")
        assert len(events) == 1
        assert events[0].reason == "bad"
