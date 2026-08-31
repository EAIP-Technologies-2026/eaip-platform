from __future__ import annotations

import asyncio
import time
import uuid
from typing import Any

from eaip.intelligence.models import IntelligenceContext, KernelExecution
from eaip.intelligence.registry import CapabilityRegistry
from eaip.logging.context import get_logger
from eaip.shared.time import utc_now

log = get_logger("eaip.intelligence.kernel")


class IntelligenceKernel:
    def __init__(self, registry: CapabilityRegistry, agent_runtime: Any | None = None, event_bus: Any | None = None) -> None:
        self._registry = registry
        self._runtime = agent_runtime
        self._event_bus = event_bus
        self._executions: dict[str, KernelExecution] = {}

    async def execute(self, capability_id: str, context: IntelligenceContext, inputs: dict[str, Any] | None = None) -> KernelExecution:
        tenant_id = context.tenant_id
        cap = self._registry.get(capability_id, tenant_id)
        if not cap:
            raise ValueError(f"capability {capability_id!r} not found for tenant {tenant_id!r}")
        required = set(cap.required_permissions)
        if required and not required.intersection(set(context.permissions)):
            raise PermissionError(f"missing permissions {required}")

        budget = context.budget or {}
        max_retries = int(budget.get("max_retries", 3))
        max_cost = float(budget.get("max_cost", 1000))
        timeout_s = float(budget.get("timeout_s", 30))

        execution_id = f"kern-{uuid.uuid4().hex[:8]}"
        exec_rec = KernelExecution(execution_id=execution_id, tenant_id=tenant_id, capability_id=capability_id, context=context.model_copy(update={"execution_id": execution_id, "correlation_id": context.correlation_id or execution_id}), status="running")
        self._executions[execution_id] = exec_rec
        self._publish("kernel.execution.started", {"execution_id": execution_id, "tenant_id": tenant_id, "capability_id": capability_id})

        t0 = time.monotonic()
        try:
            result = await asyncio.wait_for(self._dispatch(cap, context, inputs or {}), timeout=timeout_s)
            latency = (time.monotonic() - t0) * 1000
            exec_rec = exec_rec.model_copy(update={"status": "completed", "result": result if isinstance(result, dict) else {"output": str(result)}, "completed_at": utc_now(), "latency_ms": latency, "cost": float(budget.get("cost_per_call", 0))})
            self._publish("kernel.execution.completed", {"execution_id": execution_id, "tenant_id": tenant_id, "capability_id": capability_id, "latency_ms": latency})
        except asyncio.TimeoutError as exc:
            exec_rec = exec_rec.model_copy(update={"status": "failed", "error": "timeout", "completed_at": utc_now(), "latency_ms": (time.monotonic() - t0) * 1000})
            self._publish("kernel.execution.failed", {"execution_id": execution_id, "tenant_id": tenant_id, "error": "timeout"})
            raise TimeoutError(f"kernel execution {execution_id} timed out") from exc
        except Exception as exc:
            latency = (time.monotonic() - t0) * 1000
            exec_rec = exec_rec.model_copy(update={"status": "failed", "error": str(exc), "completed_at": utc_now(), "latency_ms": latency})
            self._publish("kernel.execution.failed", {"execution_id": execution_id, "tenant_id": tenant_id, "error": str(exc)})
            if exec_rec.cost > max_cost:
                self._publish("kernel.escalated", {"execution_id": execution_id, "tenant_id": tenant_id, "reason": "budget_exceeded"})
            raise
        else:
            if exec_rec.cost > max_cost:
                self._publish("kernel.escalated", {"execution_id": execution_id, "tenant_id": tenant_id, "reason": "budget_exceeded"})
        self._executions[execution_id] = exec_rec
        return exec_rec

    async def _dispatch(self, cap: Any, context: IntelligenceContext, inputs: dict[str, Any]) -> Any:
        if cap.category.value == "agent" and self._runtime and hasattr(self._runtime, "create_run"):
            from eaip.agents.models import AgentSpec, Goal
            spec = AgentSpec(id=context.agent_id or cap.capability_id, name=cap.name)
            goal = Goal(text=context.goal or context.task or cap.description)
            run = await self._runtime.create_run(spec, goal)
            completed = await self._runtime.start_run(run.id)
            return {"agent_result": getattr(completed, "result", ""), "capability": cap.capability_id}
        return {"capability": cap.capability_id, "inputs": inputs, "context_goal": context.goal}

    def get_execution(self, execution_id: str) -> KernelExecution | None:
        return self._executions.get(execution_id)

    def list_for_tenant(self, tenant_id: str) -> list[KernelExecution]:
        return [v for v in self._executions.values() if v.tenant_id == tenant_id]

    def health(self) -> dict[str, Any]:
        return {"executions": len(self._executions), "status": "healthy"}

    def _publish(self, event_type: str, payload: dict[str, Any]) -> None:
        if not self._event_bus:
            return
        try:
            result = self._event_bus.publish({"type": event_type, **payload})
            if asyncio.iscoroutine(result):
                asyncio.create_task(result)
        except Exception:
            pass
