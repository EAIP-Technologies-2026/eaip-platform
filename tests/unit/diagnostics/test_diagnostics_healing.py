from __future__ import annotations

import pytest

from eaip.diagnostics.healing import RecoveryAction, SelfHealingManager


class TestSelfHealingManager:
    @pytest.fixture
    def manager(self) -> SelfHealingManager:
        return SelfHealingManager()

    def test_register_action(self, manager: SelfHealingManager) -> None:
        action = RecoveryAction(
            action_id="a1", target="memory", action_fn=lambda: None, description="clear cache"
        )
        manager.register_action(action)
        assert manager.get_action("a1") is not None

    def test_list_actions(self, manager: SelfHealingManager) -> None:
        manager.register_action(
            RecoveryAction(action_id="a1", target="mem", action_fn=lambda: None)
        )
        manager.register_action(
            RecoveryAction(action_id="a2", target="cpu", action_fn=lambda: None)
        )
        assert len(manager.list_actions()) == 2

    @pytest.mark.asyncio
    async def test_execute_action_success(self, manager: SelfHealingManager) -> None:
        called = False

        def action() -> None:
            nonlocal called
            called = True

        manager.register_action(RecoveryAction(action_id="a1", target="test", action_fn=action))
        result = await manager.execute_action("a1")
        assert result is True
        assert called

    @pytest.mark.asyncio
    async def test_execute_action_not_found(self, manager: SelfHealingManager) -> None:
        result = await manager.execute_action("nonexistent")
        assert result is False

    @pytest.mark.asyncio
    async def test_execute_all(self, manager: SelfHealingManager) -> None:
        manager.register_action(RecoveryAction(action_id="a1", target="t1", action_fn=lambda: None))
        manager.register_action(RecoveryAction(action_id="a2", target="t2", action_fn=lambda: None))
        results = await manager.execute_all()
        assert len(results) == 2
        assert all(results.values())
