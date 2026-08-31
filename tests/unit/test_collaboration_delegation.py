"""Tests for TaskDelegationService."""

from __future__ import annotations

import pytest

from eaip.collaboration.delegation import TaskDelegationService
from eaip.collaboration.exceptions import DelegationError
from eaip.collaboration.models import DelegationRequest, DelegationStatus


class TestTaskDelegationService:
    @pytest.fixture
    def service(self) -> TaskDelegationService:
        return TaskDelegationService()

    @pytest.fixture
    def delegation_request(self) -> DelegationRequest:
        return DelegationRequest(
            id="d1",
            from_agent_id="agent_a",
            to_agent_id="agent_b",
            task_description="Analyze results",
            context={"data": "metrics"},
            priority=5,
        )

    async def test_delegate_task(
        self,
        service: TaskDelegationService,
        delegation_request: DelegationRequest,
    ) -> None:
        result = await service.delegate_task(delegation_request)
        assert result.id == "d1"
        assert result.from_agent_id == "agent_a"
        assert result.to_agent_id == "agent_b"
        assert result.status is DelegationStatus.PENDING

    async def test_accept_task(
        self,
        service: TaskDelegationService,
        delegation_request: DelegationRequest,
    ) -> None:
        await service.delegate_task(delegation_request)
        accepted = await service.accept_task("d1")
        assert accepted.status is DelegationStatus.ACCEPTED

    async def test_accept_not_found(self, service: TaskDelegationService) -> None:
        with pytest.raises(DelegationError):
            await service.accept_task("nonexistent")

    async def test_accept_twice_raises(
        self,
        service: TaskDelegationService,
        delegation_request: DelegationRequest,
    ) -> None:
        await service.delegate_task(delegation_request)
        await service.accept_task("d1")
        with pytest.raises(DelegationError):
            await service.accept_task("d1")

    async def test_reject_task(
        self,
        service: TaskDelegationService,
        delegation_request: DelegationRequest,
    ) -> None:
        await service.delegate_task(delegation_request)
        rejected = await service.reject_task("d1", "too busy")
        assert rejected.status is DelegationStatus.REJECTED
        assert rejected.response == "too busy"

    async def test_reject_not_found(self, service: TaskDelegationService) -> None:
        with pytest.raises(DelegationError):
            await service.reject_task("nonexistent", "no")

    async def test_reject_non_pending(
        self,
        service: TaskDelegationService,
        delegation_request: DelegationRequest,
    ) -> None:
        await service.delegate_task(delegation_request)
        await service.accept_task("d1")
        with pytest.raises(DelegationError):
            await service.reject_task("d1", "too late")

    async def test_complete_task(
        self,
        service: TaskDelegationService,
        delegation_request: DelegationRequest,
    ) -> None:
        await service.delegate_task(delegation_request)
        await service.accept_task("d1")
        completed = await service.complete_task("d1", "analysis done")
        assert completed.status is DelegationStatus.COMPLETED
        assert completed.response == "analysis done"

    async def test_complete_not_found(self, service: TaskDelegationService) -> None:
        with pytest.raises(DelegationError):
            await service.complete_task("nonexistent", "result")

    async def test_complete_not_accepted(
        self,
        service: TaskDelegationService,
        delegation_request: DelegationRequest,
    ) -> None:
        await service.delegate_task(delegation_request)
        with pytest.raises(DelegationError):
            await service.complete_task("d1", "result")

    async def test_get_delegation(
        self,
        service: TaskDelegationService,
        delegation_request: DelegationRequest,
    ) -> None:
        await service.delegate_task(delegation_request)
        result = await service.get_delegation("d1")
        assert result is not None
        assert result.id == "d1"

    async def test_get_delegation_not_found(self, service: TaskDelegationService) -> None:
        result = await service.get_delegation("nonexistent")
        assert result is None

    async def test_list_delegations(
        self,
        service: TaskDelegationService,
        delegation_request: DelegationRequest,
    ) -> None:
        await service.delegate_task(delegation_request)
        d2 = DelegationRequest(
            id="d2",
            from_agent_id="agent_b",
            to_agent_id="agent_c",
            task_description="Task 2",
        )
        await service.delegate_task(d2)
        all_dels = await service.list_delegations()
        assert len(all_dels) == 2

    async def test_list_delegations_by_agent(
        self,
        service: TaskDelegationService,
        delegation_request: DelegationRequest,
    ) -> None:
        await service.delegate_task(delegation_request)
        matches = await service.list_delegations(agent_id="agent_a")
        assert len(matches) == 1
        matches_to = await service.list_delegations(agent_id="agent_b")
        assert len(matches_to) == 1

    async def test_list_delegations_by_status(
        self,
        service: TaskDelegationService,
        delegation_request: DelegationRequest,
    ) -> None:
        await service.delegate_task(delegation_request)
        pending = await service.list_delegations(status=DelegationStatus.PENDING)
        assert len(pending) == 1
        accepted = await service.list_delegations(status=DelegationStatus.ACCEPTED)
        assert len(accepted) == 0

    async def test_query_available_agents(self, service: TaskDelegationService) -> None:
        agents = {
            "agent_a": ["analysis", "reporting"],
            "agent_b": ["analysis"],
            "agent_c": ["reporting"],
        }
        result = await service.query_available_agents("analysis", agents)
        assert "agent_a" in result
        assert "agent_b" in result
        assert "agent_c" not in result

    async def test_query_available_agents_no_match(self, service: TaskDelegationService) -> None:
        result = await service.query_available_agents("unknown", {"a1": ["analysis"]})
        assert result == []

    async def test_query_available_agents_empty(self, service: TaskDelegationService) -> None:
        result = await service.query_available_agents("analysis")
        assert result == []
