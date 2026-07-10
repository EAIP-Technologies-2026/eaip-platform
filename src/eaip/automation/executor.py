"""Action executor - webhook, workflow, agent, command, event, and notification actions."""

from __future__ import annotations

import asyncio
import time
from typing import Any

from eaip.automation.events import ActionExecuted, ActionFailed
from eaip.automation.exceptions import ActionExecutionError
from eaip.automation.models import ActionType, RuleAction
from eaip.events.bus import EventBus
from eaip.logging.context import get_logger


class ActionExecutor:
    def __init__(self, event_bus: EventBus | None = None) -> None:
        self._event_bus = event_bus or EventBus()
        self._log = get_logger("eaip.automation.executor")

    async def execute_action(self, action: RuleAction, context: dict[str, Any]) -> str:
        max_retries = 3 if action.retry_on_failure else 1
        last_error: Exception | None = None

        for attempt in range(1, max_retries + 1):
            try:
                start = time.monotonic()
                result = await self._dispatch(action, context)
                duration_ms = (time.monotonic() - start) * 1000
                await self._event_bus.publish(
                    ActionExecuted(
                        execution_id=context.get("id", ""),
                        action=action,
                        result=result,
                        duration_ms=duration_ms,
                    ),
                )
                return result
            except ActionExecutionError as exc:
                last_error = exc
                await self._event_bus.publish(
                    ActionFailed(
                        execution_id=context.get("id", ""),
                        action=action,
                        error=str(exc),
                        attempt=attempt,
                    ),
                )
                if attempt < max_retries:
                    delay = 2.0 ** attempt
                    await asyncio.sleep(delay)

        raise ActionExecutionError(
            f"Action failed after {max_retries} attempts",
            context={"action_type": action.type, "target": action.target, "attempts": max_retries},
            cause=last_error,
        )

    async def _dispatch(self, action: RuleAction, context: dict[str, Any]) -> str:
        if action.type == ActionType.WEBHOOK:
            return await self.execute_webhook(action, context)
        elif action.type == ActionType.WORKFLOW:
            return await self.execute_workflow(action, context)
        elif action.type == ActionType.AGENT:
            return await self.execute_agent(action, context)
        elif action.type == ActionType.COMMAND:
            return await self.execute_command(action, context)
        elif action.type == ActionType.EVENT:
            return await self.execute_event(action, context)
        elif action.type == ActionType.NOTIFICATION:
            return await self.execute_notification(action, context)
        else:
            raise ActionExecutionError(
                f"Unknown action type: {action.type}",
                context={"action_type": action.type},
            )

    async def execute_webhook(self, action: RuleAction, context: dict[str, Any]) -> str:
        try:
            import httpx
            async with httpx.AsyncClient(timeout=action.timeout_seconds) as client:
                response = await client.post(
                    action.target,
                    json=action.payload or context,
                    headers=action.headers,
                )
                response.raise_for_status()
                return response.text
        except Exception as exc:
            raise ActionExecutionError(
                f"Webhook failed for {action.target}: {exc}",
                context={"target": action.target},
                cause=exc,
            )

    async def execute_workflow(self, action: RuleAction, context: dict[str, Any]) -> str:
        return f"workflow:{action.target}"

    async def execute_agent(self, action: RuleAction, context: dict[str, Any]) -> str:
        return f"agent:{action.target}"

    async def execute_command(self, action: RuleAction, context: dict[str, Any]) -> str:
        import asyncio.subprocess as subprocess
        try:
            proc = await asyncio.create_subprocess_shell(
                action.target,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(), timeout=action.timeout_seconds,
            )
            if proc.returncode != 0:
                raise ActionExecutionError(
                    f"Command failed with exit code {proc.returncode}: {stderr.decode()}",
                    context={"target": action.target, "returncode": proc.returncode},
                )
            return stdout.decode()
        except ActionExecutionError:
            raise
        except Exception as exc:
            raise ActionExecutionError(
                f"Command execution failed: {exc}",
                context={"target": action.target},
                cause=exc,
            )

    async def execute_event(self, action: RuleAction, context: dict[str, Any]) -> str:
        from eaip.automation.events import RuleTriggered
        await self._event_bus.publish(
            RuleTriggered(
                rule_id="",
                rule_name="",
                trigger_type=ActionType.EVENT,
                trigger_event=action.payload or context,
            ),
        )
        return f"event:{action.target}"

    async def execute_notification(self, action: RuleAction, context: dict[str, Any]) -> str:
        return f"notification:{action.target}"


__all__ = ["ActionExecutor"]
