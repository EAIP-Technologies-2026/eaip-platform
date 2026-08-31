"""Tests for ActionExecutor."""

from __future__ import annotations

import pytest

from eaip.automation.executor import ActionExecutor
from eaip.automation.models import ActionType, RuleAction


class TestActionExecutor:
    @pytest.fixture
    def executor(self) -> ActionExecutor:
        return ActionExecutor()

    async def test_execute_notification(self, executor) -> None:
        action = RuleAction(type=ActionType.NOTIFICATION, target="slack")
        result = await executor.execute_action(action, {})
        assert result == "notification:slack"

    async def test_execute_event(self, executor) -> None:
        action = RuleAction(
            type=ActionType.EVENT, target="order.updated", payload={"order_id": "123"}
        )
        result = await executor.execute_action(action, {})
        assert result == "event:order.updated"

    async def test_execute_workflow(self, executor) -> None:
        action = RuleAction(type=ActionType.WORKFLOW, target="wf_order")
        result = await executor.execute_action(action, {})
        assert result == "workflow:wf_order"

    async def test_execute_agent(self, executor) -> None:
        action = RuleAction(type=ActionType.AGENT, target="agent_support")
        result = await executor.execute_action(action, {})
        assert result == "agent:agent_support"

    async def test_dispatch_command_success(self, executor) -> None:
        action = RuleAction(
            type=ActionType.COMMAND,
            target="python -c \"import sys; sys.stdout.write('command_ok')\"",
            timeout_seconds=5.0,
        )
        result = await executor._dispatch(action, {})
        assert "command_ok" in result

    async def test_execute_action_retry_on_failure(self, executor) -> None:
        from eaip.automation.exceptions import ActionExecutionError

        action = RuleAction(type=ActionType.NOTIFICATION, target="slack", retry_on_failure=True)

        original = executor._dispatch

        call_count = 0

        async def failing_dispatch(action, context):
            nonlocal call_count
            call_count += 1
            raise ActionExecutionError("Transient error", context={})

        executor._dispatch = failing_dispatch
        with pytest.raises(ActionExecutionError):
            await executor.execute_action(action, {})
        assert call_count > 1
        executor._dispatch = original

    async def test_execute_webhook_failure(self, executor) -> None:
        from eaip.automation.exceptions import ActionExecutionError

        action = RuleAction(
            type=ActionType.WEBHOOK,
            target="https://nonexistent.example.com/hook",
            timeout_seconds=0.1,
        )
        with pytest.raises(ActionExecutionError):
            await executor.execute_webhook(action, {})

    async def test_execute_command_success(self, executor) -> None:
        action = RuleAction(
            type=ActionType.COMMAND,
            target="python -c \"import sys; sys.stdout.write('hello')\"",
            timeout_seconds=5.0,
        )
        if hasattr(executor, "execute_command"):
            result = await executor.execute_command(action, {})
            assert "hello" in result

    async def test_execute_command_failure(self, executor) -> None:
        from eaip.automation.exceptions import ActionExecutionError

        action = RuleAction(
            type=ActionType.COMMAND,
            target='python -c "import sys; sys.exit(1)"',
            timeout_seconds=5.0,
        )
        with pytest.raises(ActionExecutionError):
            await executor.execute_command(action, {})

    async def test_dispatch_webhook(self, executor) -> None:
        action = RuleAction(
            type=ActionType.WEBHOOK, target="https://example.com", timeout_seconds=0.1
        )
        from eaip.automation.exceptions import ActionExecutionError

        with pytest.raises(ActionExecutionError):
            await executor._dispatch(action, {})

    async def test_dispatch_notification(self, executor) -> None:
        action = RuleAction(type=ActionType.NOTIFICATION, target="email")
        result = await executor._dispatch(action, {})
        assert result == "notification:email"

    async def test_dispatch_all_types(self, executor) -> None:
        for atype in ActionType:
            action = RuleAction(type=atype, target="test", timeout_seconds=0.1)
            if atype == ActionType.WEBHOOK:
                from eaip.automation.exceptions import ActionExecutionError

                with pytest.raises(ActionExecutionError):
                    await executor._dispatch(action, {})
            elif atype == ActionType.COMMAND:
                action = RuleAction(
                    type=atype,
                    target="python -c \"import sys; sys.stdout.write('ok')\"",
                    timeout_seconds=5.0,
                )
                result = await executor._dispatch(action, {})
                assert result is not None
            else:
                result = await executor._dispatch(action, {})
                assert result is not None

    async def test_execute_action_with_context(self, executor) -> None:
        action = RuleAction(type=ActionType.NOTIFICATION, target="slack")
        context = {"id": "exec_1", "rule_id": "r1"}
        result = await executor.execute_action(action, context)
        assert result == "notification:slack"
