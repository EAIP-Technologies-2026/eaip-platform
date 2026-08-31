"""Self-healing manager — automatic recovery actions for known failure modes."""

from __future__ import annotations

from typing import Any

from eaip.diagnostics.events import AutoRecoveryExecuted
from eaip.logging.context import get_logger


class RecoveryAction:
    def __init__(self, action_id: str, target: str, action_fn: Any, description: str = "") -> None:
        self.action_id = action_id
        self.target = target
        self.action_fn = action_fn
        self.description = description


class SelfHealingManager:
    def __init__(self, event_bus: Any = None) -> None:
        self._actions: dict[str, RecoveryAction] = {}
        self._event_bus = event_bus
        self._log = get_logger("eaip.diagnostics.healing")

    def register_action(self, action: RecoveryAction) -> None:
        self._actions[action.action_id] = action

    def get_action(self, action_id: str) -> RecoveryAction | None:
        return self._actions.get(action_id)

    def list_actions(self) -> list[RecoveryAction]:
        return list(self._actions.values())

    async def execute_action(self, action_id: str) -> bool:
        action = self._actions.get(action_id)
        if action is None:
            self._log.warning("healing.action_not_found", action_id=action_id)
            return False
        try:
            if hasattr(action.action_fn, "__call__"):
                result = action.action_fn()
                if hasattr(result, "__await__"):
                    await result
            success = True
            self._log.info("healing.action_executed", action_id=action_id, target=action.target)
        except Exception as exc:
            success = False
            self._log.error("healing.action_failed", action_id=action_id, error=str(exc))

        self._publish_event(
            AutoRecoveryExecuted(
                recovery_id=action_id,
                target=action.target,
                action=action.description,
                success=success,
            )
        )
        return success

    async def execute_all(self) -> dict[str, bool]:
        results: dict[str, bool] = {}
        for action_id in self._actions:
            results[action_id] = await self.execute_action(action_id)
        return results

    def _publish_event(self, event: Any) -> None:
        if self._event_bus is not None:
            import asyncio

            try:
                asyncio.ensure_future(self._event_bus.publish(event))
            except Exception:
                pass


__all__ = ["RecoveryAction", "SelfHealingManager"]
