from __future__ import annotations

import asyncio
import uuid
from typing import Any

from eaip.logging.context import get_logger
from eaip.swarm.models import AutonomyLevel, CollaborationPattern, SwarmDefinition, SwarmExecution, SwarmStatus

log = get_logger("eaip.swarm.engine")


class SwarmEngine:
    def __init__(self, agent_runtime: Any | None = None, event_bus: Any | None = None) -> None:
        self._runtime = agent_runtime
        self._event_bus = event_bus
        self._swarms: dict[str, SwarmDefinition] = {}
        self._executions: dict[str, SwarmExecution] = {}

    def _key(self, tenant_id: str, swarm_id: str) -> str:
        return f"{tenant_id}:{swarm_id}"

    def create_swarm(self, swarm: SwarmDefinition) -> SwarmDefinition:
        self._swarms[self._key(swarm.tenant_id, swarm.swarm_id)] = swarm
        return swarm

    def get_swarm(self, swarm_id: str, tenant_id: str) -> SwarmDefinition | None:
        return self._swarms.get(self._key(tenant_id, swarm_id))

    def list_for_tenant(self, tenant_id: str) -> list[SwarmDefinition]:
        return [v for k, v in self._swarms.items() if k.startswith(f"{tenant_id}:")]

    async def execute(self, swarm_id: str, tenant_id: str, autonomy_level: AutonomyLevel | None = None) -> SwarmExecution:
        swarm = self.get_swarm(swarm_id, tenant_id)
        if not swarm:
            raise ValueError(f"swarm {swarm_id!r} not found")
        level = autonomy_level or swarm.autonomy_level
        execution_id = f"swarm-exec-{uuid.uuid4().hex[:8]}"
        execution = SwarmExecution(execution_id=execution_id, swarm_id=swarm_id, tenant_id=tenant_id, status=SwarmStatus.running)

        results: list[dict[str, Any]] = []
        self._publish("swarm.started", {"swarm_id": swarm_id, "tenant_id": tenant_id, "execution_id": execution_id, "pattern": swarm.pattern.value})
        if swarm.pattern == CollaborationPattern.sequential:
            for task in swarm.tasks:
                if not self._deps_satisfied(task, results):
                    results.append({"task_id": task.task_id, "status": "skipped", "reason": "dependencies not satisfied"})
                    continue
                res = await self._run_task(task, swarm, level)
                results.append({"task_id": task.task_id, "result": res, "status": "completed", "assigned_to": task.assigned_to, "consensus": swarm.consensus_config})
        elif swarm.pattern == CollaborationPattern.parallel:
            coros = [self._run_task(t, swarm, level) for t in swarm.tasks]
            completed = await asyncio.gather(*coros, return_exceptions=True)
            for task, res in zip(swarm.tasks, completed):
                if isinstance(res, Exception):
                    if task.fallback_agent:
                        try:
                            fb_res = await self._run_task(task.model_copy(update={"assigned_to": task.fallback_agent}), swarm, level)
                            results.append({"task_id": task.task_id, "result": fb_res, "status": "completed", "fallback": True})
                        except Exception as e2:
                            results.append({"task_id": task.task_id, "error": str(e2), "status": "failed"})
                    else:
                        results.append({"task_id": task.task_id, "error": str(res), "status": "failed"})
                else:
                    results.append({"task_id": task.task_id, "result": res, "status": "completed", "assigned_to": task.assigned_to})
        elif swarm.pattern in (CollaborationPattern.debate, CollaborationPattern.consensus, CollaborationPattern.handoff, CollaborationPattern.supervisor):
            for task in swarm.tasks:
                res = await self._run_task(task, swarm, level)
                results.append({"task_id": task.task_id, "result": res, "status": "completed", "pattern": swarm.pattern.value})
        else:
            for task in swarm.tasks:
                res = await self._run_task(task, swarm, level)
                results.append({"task_id": task.task_id, "result": res, "status": "completed", "pattern": swarm.pattern.value})
        consensus = self._evaluate_consensus(swarm, results)

        failed = any(r.get("status") == "failed" for r in results)
        aggregated = "; ".join(r.get("result", "") for r in results if r.get("result"))
        execution = execution.model_copy(update={"task_results": tuple(results), "aggregated_result": aggregated, "consensus": consensus, "status": SwarmStatus.failed if failed else SwarmStatus.completed})
        self._executions[execution_id] = execution
        self._swarms[self._key(tenant_id, swarm_id)] = swarm.model_copy(update={"status": execution.status})
        self._publish("swarm.completed", {"swarm_id": swarm_id, "tenant_id": tenant_id, "execution_id": execution_id, "status": execution.status.value})
        return execution

    async def _run_task(self, task: Any, swarm: SwarmDefinition, level: AutonomyLevel) -> str:
        if level == AutonomyLevel.read_only:
            return f"[READ_ONLY] {task.description} — no execution"
        if level == AutonomyLevel.suggest:
            return f"[SUGGEST] {task.description}"
        if self._runtime and hasattr(self._runtime, "create_run"):
            try:
                from eaip.agents.models import AgentSpec, Goal
                spec = AgentSpec(id=task.assigned_to or swarm.coordinator or "swarm-agent", name=task.assigned_to or "swarm-agent")
                goal = Goal(text=task.description)
                run = await self._runtime.create_run(spec, goal)
                completed = await self._runtime.start_run(run.id)
                return str(getattr(completed, "result", "") or f"executed: {task.description}")
            except Exception as exc:
                return f"error: {exc}"
        return f"executed: {task.description} (no runtime)"

    def plan(self, goal: str, capabilities: list[str] | None = None) -> dict[str, Any]:
        import uuid as _uuid
        caps = capabilities or ["general"]
        tasks = []
        for i, cap in enumerate(caps[:5]):
            tasks.append({"task_id": f"task-{i}", "description": f"{goal} — {cap}", "required_capability": cap, "risk": "low" if i == 0 else "medium", "budget": {"cost": 100 * (i+1)}, "dependencies": [f"task-{i-1}"] if i>0 else [], "expected_output": f"output-{i}"})
        return {"goal": goal, "task_graph": tasks, "count": len(tasks)}

    def _deps_satisfied(self, task: Any, results: list[dict[str, Any]]) -> bool:
        if not task.dependencies:
            return True
        done = {r["task_id"] for r in results if r.get("status") == "completed"}
        return all(d in done for d in task.dependencies)

    def _evaluate_consensus(self, swarm: SwarmDefinition, results: list[dict[str, Any]]) -> dict[str, Any]:
        cfg = swarm.consensus_config or {}
        strategy = cfg.get("strategy", "majority")
        threshold = float(cfg.get("threshold", 0.5))
        n = len(results)
        if n == 0:
            return {"strategy": strategy, "reached": False, "count": 0}
        completed = sum(1 for r in results if r.get("status") == "completed")
        if strategy == "majority":
            reached = (completed / n) >= threshold
        elif strategy == "weighted":
            reached = (completed / n) >= threshold
        else:
            reached = completed == n
        return {"strategy": strategy, "reached": reached, "completed": completed, "total": n}

    def get_execution(self, execution_id: str) -> SwarmExecution | None:
        return self._executions.get(execution_id)

    def list_executions(self, tenant_id: str) -> list[SwarmExecution]:
        return [v for v in self._executions.values() if v.tenant_id == tenant_id]

    def _publish(self, event_type: str, payload: dict[str, Any]) -> None:
        if not self._event_bus:
            return
        try:
            result = self._event_bus.publish({"type": event_type, **payload})
            if asyncio.iscoroutine(result):
                asyncio.create_task(result)
        except Exception:
            pass
