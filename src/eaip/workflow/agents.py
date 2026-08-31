"""Multi-agent orchestration - agent delegation, handoff, messaging, shared context memory."""

from __future__ import annotations

import time
import uuid
from collections import defaultdict
from contextlib import suppress
from typing import Any

from eaip.agents.models import AgentSpec, Goal
from eaip.workflow.exceptions import AgentDelegationError
from eaip.workflow.models import WorkflowContext


class AgentOrchestrator:
    """Coordinates multi-agent workflows: delegation, handoff, messaging.

    Delegates to AgentRuntime for per-agent execution.
    Integrates with Memory Engine for shared context persistence.
    """

    def __init__(
        self,
        agent_runtime: Any = None,
        memory_engine: Any = None,
        event_bus: Any = None,
    ) -> None:
        self._runtime = agent_runtime
        self._memory = memory_engine
        self._event_bus = event_bus
        self._handoffs: dict[str, list[dict[str, Any]]] = defaultdict(list)
        self._agent_messages: dict[str, list[dict[str, Any]]] = defaultdict(list)

    # ------------------------------------------------------------------
    # Agent delegation
    # ------------------------------------------------------------------

    async def delegate(
        self,
        agent_id: str,
        prompt: str,
        _parent_run_id: str | None = None,
        _workflow_context: WorkflowContext | None = None,
        _timeout_seconds: float | None = None,
        memory_keys: list[str] | None = None,
    ) -> str:
        spec = AgentSpec(id=agent_id, name=agent_id)
        goal = Goal(text=prompt)

        if memory_keys and self._memory:
            context_str = await self._load_memory_context(memory_keys)
            goal = Goal(text=f"{prompt}\n\nContext from memory:\n{context_str}")

        run = await self._runtime.create_run(spec, goal)
        result = await self._runtime.start_run(run.id)
        if result.status.value != "completed":
            msg = f"run ended with status {result.status}: {result.error or 'unknown'}"
            raise AgentDelegationError(agent_id, msg)

        if memory_keys and self._memory and result.result:
            await self._save_memory_output(agent_id, result.result, memory_keys)

        return result.result or ""

    async def delegate_async(
        self,
        agent_id: str,
        prompt: str,
        _parent_run_id: str | None = None,
        _workflow_context: WorkflowContext | None = None,
    ) -> str:
        spec = AgentSpec(id=agent_id, name=agent_id)
        goal = Goal(text=prompt)
        run = await self._runtime.create_run(spec, goal)
        return str(run.id)

    async def wait_for_agent(self, run_id: str, _timeout_seconds: float | None = None) -> str:
        result = await self._runtime.start_run(run_id)
        if result.status.value != "completed":
            msg = f"run ended with status {result.status}: {result.error or 'unknown'}"
            raise AgentDelegationError(run_id, msg)
        return result.result or ""

    # ------------------------------------------------------------------
    # Agent handoff
    # ------------------------------------------------------------------

    async def handoff(
        self,
        from_agent_id: str,
        to_agent_id: str,
        context: str,
        parent_run_id: str | None = None,
        memory_keys: list[str] | None = None,
    ) -> str:
        handoff_id = uuid.uuid4().hex[:12]
        self._handoffs[from_agent_id].append(
            {
                "handoff_id": handoff_id,
                "to_agent_id": to_agent_id,
                "context": context,
                "timestamp": time.time(),
            }
        )

        enriched_context = context
        if memory_keys and self._memory:
            mem = await self._load_memory_context(memory_keys)
            enriched_context = f"{context}\n\nShared Memory:\n{mem}"

        return await self.delegate(
            agent_id=to_agent_id,
            prompt=enriched_context,
            _parent_run_id=parent_run_id,
        )

    def get_handoffs(self, agent_id: str) -> list[dict[str, Any]]:
        return list(self._handoffs.get(agent_id, []))

    # ------------------------------------------------------------------
    # Agent messaging
    # ------------------------------------------------------------------

    async def send_message(self, to_agent_id: str, message: dict[str, Any]) -> None:
        inbox = self._agent_messages.setdefault(to_agent_id, [])
        inbox.append({"message": message, "timestamp": time.time(), "read": False})

    async def broadcast_message(self, agent_ids: list[str], message: dict[str, Any]) -> None:
        for agent_id in agent_ids:
            await self.send_message(agent_id, message)

    async def read_messages(self, agent_id: str) -> list[dict[str, Any]]:
        inbox = self._agent_messages.get(agent_id, [])
        for msg in inbox:
            msg["read"] = True
        return list(inbox)

    def count_unread(self, agent_id: str) -> int:
        inbox = self._agent_messages.get(agent_id, [])
        return sum(1 for m in inbox if not m.get("read"))

    # ------------------------------------------------------------------
    # Shared memory integration
    # ------------------------------------------------------------------

    async def _load_memory_context(self, memory_keys: list[str]) -> str:
        if not self._memory or not memory_keys:
            return ""
        parts = []
        for key in memory_keys:
            try:
                mem = await self._memory.get_memory(key)
                if mem:
                    parts.append(f"{key}: {mem.content[:500]}")
            except Exception:
                parts.append(f"{key}: <unavailable>")
        return "\n".join(parts)

    async def _save_memory_output(
        self,
        agent_id: str,
        output: str,
        memory_keys: list[str],
    ) -> None:
        if not self._memory:
            return
        for key in memory_keys:
            with suppress(Exception):
                await self._memory.create_memory(
                    scope=f"agent:{agent_id}",
                    content=output[:2000],
                    tags=("agent_output", agent_id, key),
                )

    def _serialize_context(self, ctx: WorkflowContext | None) -> dict[str, Any] | None:
        if ctx is None:
            return None
        return {
            "variables": ctx.variables,
            "agent_outputs": ctx.agent_outputs,
            "tool_outputs": ctx.tool_outputs,
            "shared_memory_keys": list(ctx.shared_memory_keys),
            "metadata": ctx.metadata,
        }


__all__ = [
    "AgentOrchestrator",
]
