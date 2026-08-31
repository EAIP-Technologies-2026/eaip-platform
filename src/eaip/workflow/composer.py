from __future__ import annotations

import uuid
from typing import Any

from eaip.workflow.models import WorkflowDefinition, WorkflowEdge, WorkflowStatus, WorkflowStep


class WorkflowComposer:
    def __init__(self, available_tools: list[str] | None = None, allowed_agents: list[str] | None = None) -> None:
        self._tools = set(available_tools or ["knowledge_search", "agent_execute", "notify", "mcp_invoke"])
        self._agents = set(allowed_agents or [])

    def compose(self, goal: str, constraints: dict[str, Any] | None = None) -> dict[str, Any]:
        constraints = constraints or {}
        budget = float(constraints.get("budget", 1000))
        steps: list[WorkflowStep] = []
        edges: list[WorkflowEdge] = []
        # Decompose goal into 2-4 steps capability-matched
        subgoals = [s.strip() for s in goal.split(";") if s.strip()] or [goal]
        for i, sg in enumerate(subgoals[:4]):
            tool = "knowledge_search" if i == 0 else ("agent_execute" if i % 2 == 0 else "notify")
            if tool not in self._tools:
                tool = next(iter(self._tools))
            step = WorkflowStep(id=f"step-{i}", name=sg[:40] or f"Step {i+1}", tool_name=tool, prompt=sg, input={"goal": sg}, timeout_seconds=30.0)
            steps.append(step)
            if i > 0:
                edges.append(WorkflowEdge(source_id=f"step-{i-1}", target_id=f"step-{i}", label="next"))
        wf = WorkflowDefinition(id=f"wf-{uuid.uuid4().hex[:8]}", name=f"Composed: {goal[:40]}", description=f"Autonomously composed for: {goal}", steps=tuple(steps), edges=tuple(edges), version="0.1.0")
        # Validation
        issues: list[str] = []
        if self._has_cycle(wf):
            issues.append("cycle detected")
        for s in steps:
            if s.tool_name not in self._tools:
                issues.append(f"tool {s.tool_name!r} unavailable")
        # Cost/risk check (mock)
        cost = len(steps) * 10
        if cost > budget:
            issues.append(f"cost {cost} exceeds budget {budget}")
        # Risk stub
        risk = "high" if "destructive" in goal.lower() else "low"
        status = "draft" if not issues else "needs_review"
        return {"workflow": wf.model_dump(mode="json"), "issues": issues, "risk": risk, "cost": cost, "status": status, "requires_approval": bool(issues or risk == "high")}

    def _has_cycle(self, wf: WorkflowDefinition) -> bool:
        adj = {s.id: [] for s in wf.steps}
        for e in wf.edges:
            if e.source_id in adj:
                adj[e.source_id].append(e.target_id)
        visited: set[str] = set()
        stack: set[str] = set()
        def dfs(n: str) -> bool:
            visited.add(n); stack.add(n)
            for nb in adj.get(n, []):
                if nb not in visited and dfs(nb):
                    return True
                if nb in stack:
                    return True
            stack.discard(n); return False
        return any(n not in visited and dfs(n) for n in adj)


__all__ = ["WorkflowComposer"]
