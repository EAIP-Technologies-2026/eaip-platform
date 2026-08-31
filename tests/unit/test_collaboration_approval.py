"""Tests for CollaborationApprovalService."""

from __future__ import annotations

import pytest

from eaip.collaboration.approval import (
    ApprovalStatus,
    CollaborationApprovalService,
)
from eaip.collaboration.exceptions import ApprovalError


class TestCollaborationApprovalService:
    @pytest.fixture
    def service(self) -> CollaborationApprovalService:
        return CollaborationApprovalService()

    async def test_request_approval(
        self,
        service: CollaborationApprovalService,
    ) -> None:
        approval_id = await service.request_approval(
            step_id="step1",
            session_id="s1",
            payload={"input": "data"},
            approvers=["admin", "manager"],
        )
        assert approval_id is not None
        assert "step1" in approval_id

    async def test_request_approval_no_approvers(
        self,
        service: CollaborationApprovalService,
    ) -> None:
        with pytest.raises(ApprovalError):
            await service.request_approval(
                step_id="step1",
                session_id="s1",
                payload={},
                approvers=[],
            )

    async def test_approve(
        self,
        service: CollaborationApprovalService,
    ) -> None:
        approval_id = await service.request_approval(
            step_id="step1",
            session_id="s1",
            payload={},
            approvers=["admin", "manager"],
        )
        await service.approve(approval_id, "admin")
        status = await service.get_approval_status(approval_id)
        assert status is not None
        assert status["status"] is ApprovalStatus.PENDING
        assert status["responses"]["admin"] is True

    async def test_approve_all(
        self,
        service: CollaborationApprovalService,
    ) -> None:
        approval_id = await service.request_approval(
            step_id="step1",
            session_id="s1",
            payload={},
            approvers=["admin", "manager"],
        )
        await service.approve(approval_id, "admin")
        await service.approve(approval_id, "manager")
        status = await service.get_approval_status(approval_id)
        assert status is not None
        assert status["status"] is ApprovalStatus.APPROVED

    async def test_approve_not_found(
        self,
        service: CollaborationApprovalService,
    ) -> None:
        with pytest.raises(ApprovalError):
            await service.approve("nonexistent", "admin")

    async def test_approve_unauthorized(
        self,
        service: CollaborationApprovalService,
    ) -> None:
        approval_id = await service.request_approval(
            step_id="step1",
            session_id="s1",
            payload={},
            approvers=["admin"],
        )
        with pytest.raises(ApprovalError):
            await service.approve(approval_id, "hacker")

    async def test_reject(
        self,
        service: CollaborationApprovalService,
    ) -> None:
        approval_id = await service.request_approval(
            step_id="step1",
            session_id="s1",
            payload={},
            approvers=["admin"],
        )
        await service.reject(approval_id, "admin", "not ready")
        status = await service.get_approval_status(approval_id)
        assert status is not None
        assert status["status"] is ApprovalStatus.REJECTED
        assert status["errors"]["admin"] == "not ready"

    async def test_reject_not_found(
        self,
        service: CollaborationApprovalService,
    ) -> None:
        with pytest.raises(ApprovalError):
            await service.reject("nonexistent", "admin", "no")

    async def test_reject_unauthorized(
        self,
        service: CollaborationApprovalService,
    ) -> None:
        approval_id = await service.request_approval(
            step_id="step1",
            session_id="s1",
            payload={},
            approvers=["admin"],
        )
        with pytest.raises(ApprovalError):
            await service.reject(approval_id, "hacker", "no")

    async def test_get_approval_status_not_found(
        self,
        service: CollaborationApprovalService,
    ) -> None:
        status = await service.get_approval_status("nonexistent")
        assert status is None

    async def test_list_pending_approvals(
        self,
        service: CollaborationApprovalService,
    ) -> None:
        await service.request_approval("step1", "s1", {}, ["admin", "manager"])
        await service.request_approval("step2", "s1", {}, ["admin"])
        pending = await service.list_pending_approvals("admin")
        assert len(pending) == 2

    async def test_list_pending_approvals_after_approve(
        self,
        service: CollaborationApprovalService,
    ) -> None:
        aid = await service.request_approval("step1", "s1", {}, ["admin", "manager"])
        await service.approve(aid, "admin")
        pending = await service.list_pending_approvals("admin")
        assert len(pending) == 1  # still pending for manager
        no_pending = await service.list_pending_approvals("other")
        assert len(no_pending) == 0

    async def test_approve_already_approved(
        self,
        service: CollaborationApprovalService,
    ) -> None:
        aid = await service.request_approval("step1", "s1", {}, ["admin"])
        await service.approve(aid, "admin")
        await service.approve(aid, "admin")
        status = await service.get_approval_status(aid)
        assert status is not None
        assert status["status"] is ApprovalStatus.APPROVED
