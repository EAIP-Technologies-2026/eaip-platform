"""Tests for CollaborationRuntimeModule."""

from __future__ import annotations

import pytest

from eaip.collaboration.coordinator import CoordinationEngine
from eaip.collaboration.delegation import TaskDelegationService
from eaip.collaboration.approval import CollaborationApprovalService
from eaip.collaboration.state import SharedStateManager
from eaip.collaboration.tracking import ExecutionTracker
from eaip.collaboration.health import CollaborationHealthCheck
from eaip.collaboration.integration import CollaborationRuntimeModule


class TestCollaborationRuntimeModule:
    @pytest.fixture
    def module(self) -> CollaborationRuntimeModule:
        return CollaborationRuntimeModule()

    def test_name(self, module: CollaborationRuntimeModule) -> None:
        assert module.name == "collaboration"

    def test_coordinator_property(self, module: CollaborationRuntimeModule) -> None:
        assert isinstance(module.coordinator, CoordinationEngine)

    def test_delegation_property(self, module: CollaborationRuntimeModule) -> None:
        assert isinstance(module.delegation, TaskDelegationService)

    def test_approval_property(self, module: CollaborationRuntimeModule) -> None:
        assert isinstance(module.approval, CollaborationApprovalService)

    def test_state_manager_property(self, module: CollaborationRuntimeModule) -> None:
        assert isinstance(module.state_manager, SharedStateManager)

    def test_tracker_property(self, module: CollaborationRuntimeModule) -> None:
        assert isinstance(module.tracker, ExecutionTracker)

    def test_health_check(self) -> None:
        check = CollaborationHealthCheck()
        assert check.name == "eaip.collaboration"
