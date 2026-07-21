"""Tests for SharedStateManager."""

from __future__ import annotations

import pytest

from eaip.collaboration.exceptions import CollaborationError
from eaip.collaboration.state import SharedStateManager


class TestSharedStateManager:
    @pytest.fixture
    def manager(self) -> SharedStateManager:
        return SharedStateManager()

    async def test_create_state(self, manager: SharedStateManager) -> None:
        state = await manager.create_state("s1")
        assert state.session_id == "s1"
        assert state.variables == {}
        assert state.agent_contributions == {}
        assert state.version == 1

    async def test_set_variable(self, manager: SharedStateManager) -> None:
        await manager.create_state("s1")
        updated = await manager.set_variable("s1", "status", "running", agent_id="a1")
        assert updated.variables["status"] == "running"
        assert updated.version == 2

    async def test_set_variable_no_state(self, manager: SharedStateManager) -> None:
        with pytest.raises(CollaborationError):
            await manager.set_variable("nonexistent", "key", "value")

    async def test_get_variable(self, manager: SharedStateManager) -> None:
        await manager.create_state("s1")
        await manager.set_variable("s1", "key1", "value1")
        val = await manager.get_variable("s1", "key1")
        assert val == "value1"

    async def test_get_variable_not_found(self, manager: SharedStateManager) -> None:
        await manager.create_state("s1")
        val = await manager.get_variable("s1", "nonexistent")
        assert val is None

    async def test_get_variable_no_state(self, manager: SharedStateManager) -> None:
        val = await manager.get_variable("nonexistent", "key")
        assert val is None

    async def test_get_all_variables(self, manager: SharedStateManager) -> None:
        await manager.create_state("s1")
        await manager.set_variable("s1", "a", "1")
        await manager.set_variable("s1", "b", "2")
        all_vars = await manager.get_all_variables("s1")
        assert all_vars == {"a": "1", "b": "2"}

    async def test_get_all_variables_no_state(self, manager: SharedStateManager) -> None:
        all_vars = await manager.get_all_variables("nonexistent")
        assert all_vars == {}

    async def test_record_contribution(self, manager: SharedStateManager) -> None:
        await manager.create_state("s1")
        updated = await manager.record_contribution("s1", "agent_a", "analysis complete")
        assert updated.agent_contributions["agent_a"] == "analysis complete"
        assert updated.version == 2

    async def test_record_contribution_no_state(self, manager: SharedStateManager) -> None:
        with pytest.raises(CollaborationError):
            await manager.record_contribution("nonexistent", "a1", "summary")

    async def test_get_shared_state(self, manager: SharedStateManager) -> None:
        await manager.create_state("s1")
        state = await manager.get_shared_state("s1")
        assert state is not None
        assert state.session_id == "s1"

    async def test_get_shared_state_not_found(self, manager: SharedStateManager) -> None:
        state = await manager.get_shared_state("nonexistent")
        assert state is None

    async def test_merge_states(self, manager: SharedStateManager) -> None:
        await manager.create_state("s1")
        await manager.create_state("s2")
        await manager.set_variable("s1", "key1", "from_target")
        await manager.set_variable("s2", "key2", "from_source")
        merged = await manager.merge_states("s1", "s2")
        assert merged.variables["key1"] == "from_target"
        assert merged.variables["key2"] == "from_source"

    async def test_merge_states_no_target(self, manager: SharedStateManager) -> None:
        await manager.create_state("s2")
        with pytest.raises(CollaborationError):
            await manager.merge_states("nonexistent", "s2")

    async def test_merge_states_no_source(self, manager: SharedStateManager) -> None:
        await manager.create_state("s1")
        with pytest.raises(CollaborationError):
            await manager.merge_states("s1", "nonexistent")
