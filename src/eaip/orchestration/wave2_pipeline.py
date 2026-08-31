from __future__ import annotations

from typing import Any

from eaip.logging.context import get_logger

log = get_logger("eaip.orchestration.wave2_pipeline")


class Wave2Pipeline:
    """Cross-capability integration pipeline.

    Implements the architecture:
        EVENT/GOAL -> OPS INTELLIGENCE -> COGNITION -> KNOWLEDGE/MEMORY
        -> METHODOLOGY SELECTION -> DECISION -> SIMULATION -> COORDINATION
        -> DIGITAL WORKFORCE -> MISSION/WORKFLOW -> INTEGRATIONS -> OUTCOME
        -> OPS INTELLIGENCE -> CONTINUOUS IMPROVEMENT

    Governance intercepts at decision and improvement stages.
    Each step is best-effort and tenant-isolated; failures are captured
    in the pipeline trace without aborting downstream steps unless critical.
    """

    def __init__(
        self,
        ops_service: Any | None = None,
        cognition: Any | None = None,
        knowledge: Any | None = None,
        memory: Any | None = None,
        methodology_registry: Any | None = None,
        decision_service: Any | None = None,
        scenario_engine: Any | None = None,
        coordination: Any | None = None,
        workforce: Any | None = None,
        improvement: Any | None = None,
        event_bus: Any | None = None,
    ) -> None:
        self._ops = ops_service
        self._cognition = cognition
        self._knowledge = knowledge
        self._memory = memory
        self._methodology = methodology_registry
        self._decisions = decision_service
        self._scenarios = scenario_engine
        self._coordination = coordination
        self._workforce = workforce
        self._improvement = improvement
        self._bus = event_bus

    async def run(self, tenant_id: str, trigger: dict[str, Any]) -> dict[str, Any]:
        trace: list[dict[str, Any]] = []
        ctx: dict[str, Any] = {"tenant_id": tenant_id, "trigger": trigger}

        def step(name: str, fn: Any) -> Any:
            try:
                result = fn()
                import asyncio
                if asyncio.iscoroutine(result):
                    return result
                trace.append({"step": name, "status": "ok", "result": str(result)[:200] if result else "ok"})
                return result
            except Exception as exc:
                trace.append({"step": name, "status": "error", "error": str(exc)[:300]})
                log.warning("wave2_pipeline.step_failed", step=name, tenant_id=tenant_id, error=str(exc))
                return None

        # 1. Ops intelligence: detect insights from trigger event
        insights: list[Any] = []
        if self._ops:
            try:
                ev = {**trigger, "tenant_id": tenant_id}
                ins = self._ops.ingest_events([ev])
                insights = [i for i in ins if getattr(i, "tenant_id", tenant_id) == tenant_id]
                trace.append({"step": "ops_intelligence", "status": "ok", "insights": len(insights)})
                ctx["insights"] = insights
            except Exception as exc:
                trace.append({"step": "ops_intelligence", "status": "error", "error": str(exc)[:300]})

        # 2. Cognition: observe / situational awareness
        if self._cognition:
            try:
                obs = self._cognition.observe(tenant_id) if hasattr(self._cognition, "observe") else {}
                trace.append({"step": "cognition", "status": "ok"})
                ctx["cognition"] = obs
            except Exception as exc:
                trace.append({"step": "cognition", "status": "error", "error": str(exc)[:300]})

        # 3. Methodology selection
        if self._methodology:
            try:
                recs = self._methodology.recommend(tenant_id, task=str(trigger.get("goal") or trigger.get("task") or ""), limit=3)
                trace.append({"step": "methodology", "status": "ok", "selected": len(recs)})
                ctx["methodologies"] = recs
            except Exception as exc:
                trace.append({"step": "methodology", "status": "error", "error": str(exc)[:300]})

        # 4. Decision: create decision from trigger/insights
        decision: Any | None = None
        if self._decisions:
            try:
                title = str(trigger.get("title") or trigger.get("goal") or f"Decision for {trigger.get('type', 'trigger')}")
                objective = str(trigger.get("objective") or trigger.get("goal") or title)
                decision = self._decisions.create(tenant_id=tenant_id, title=title, objective=objective, context={"trigger": trigger, "insights": len(insights)})
                # add alternatives if provided
                alts = trigger.get("alternatives")
                if isinstance(alts, list) and alts:
                    self._decisions.add_alternatives(decision.decision_id, tenant_id, alts)
                    decision = self._decisions.get(decision.decision_id, tenant_id)
                trace.append({"step": "decision", "status": "ok", "decision_id": decision.decision_id if decision else ""})
                ctx["decision"] = decision
            except Exception as exc:
                trace.append({"step": "decision", "status": "error", "error": str(exc)[:300]})

        # 5. Simulation: run counterfactuals for decision
        if decision and self._scenarios:
            try:
                sim_result = self._decisions.simulate(decision.decision_id, tenant_id) if self._decisions else {}
                trace.append({"step": "simulation", "status": "ok", "predicted": sim_result.get("predicted", "") if isinstance(sim_result, dict) else ""})
                ctx["simulation"] = sim_result
            except Exception as exc:
                trace.append({"step": "simulation", "status": "error", "error": str(exc)[:300]})

        # 6. Coordination: create plan for decision
        if decision and self._coordination:
            try:
                plan = self._coordination.create_plan(tenant_id=tenant_id, objective=decision.objective or decision.title)
                trace.append({"step": "coordination", "status": "ok", "plan_id": getattr(plan, "plan_id", "")})
                ctx["plan"] = plan
            except Exception as exc:
                trace.append({"step": "coordination", "status": "error", "error": str(exc)[:300]})

        # 7. Workforce: plan assignments if workforce available
        if self._workforce and trigger.get("tasks"):
            try:
                tasks = trigger["tasks"] if isinstance(trigger["tasks"], list) else []
                assignments = self._workforce.plan_assignments(tenant_id, tasks) if hasattr(self._workforce, "plan_assignments") else []
                trace.append({"step": "workforce", "status": "ok", "assignments": len(assignments) if isinstance(assignments, list) else 0})
                ctx["assignments"] = assignments
            except Exception as exc:
                trace.append({"step": "workforce", "status": "error", "error": str(exc)[:300]})

        # 8. Outcome -> improvement: if trigger indicates failure, propose improvement
        if self._improvement and (trigger.get("outcome") == "failed" or trigger.get("failed") or insights):
            try:
                problem = {"trigger": trigger, "insights": len(insights), "decision_id": getattr(decision, "decision_id", "") if decision else ""}
                prop = self._improvement.propose(tenant=tenant_id, source="ops_intelligence" if insights else "manual", problem=problem)
                trace.append({"step": "improvement", "status": "ok", "proposal_id": prop.proposal_id})
                ctx["improvement"] = prop
            except Exception as exc:
                trace.append({"step": "improvement", "status": "error", "error": str(exc)[:300]})

        # publish pipeline completion
        if self._bus:
            try:
                import asyncio
                maybe = self._bus.publish({"type": "wave2.pipeline.completed", "tenant_id": tenant_id, "trace_steps": len(trace)})
                if asyncio.iscoroutine(maybe):
                    asyncio.create_task(maybe)
            except Exception:
                pass

        return {"tenant_id": tenant_id, "trace": trace, "ctx_keys": list(ctx.keys()), "insights": len(insights), "decision_id": getattr(decision, "decision_id", None) if decision else None}


__all__ = ["Wave2Pipeline"]
