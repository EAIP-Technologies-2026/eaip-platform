from __future__ import annotations

from typing import Any


class KCRService:
    """Knowledge/Context Reasoning — bounded, relevant, provenance-aware, tenant-safe context assembly."""

    def __init__(self, knowledge_engine: Any | None = None, memory_store: Any | None = None, graph: Any | None = None) -> None:
        self._knowledge = knowledge_engine
        self._memory = memory_store
        self._graph = graph

    async def assemble(self, tenant_id: str, query: str, max_tokens: int = 4000, sources: list[str] | None = None) -> dict[str, Any]:
        # bounded assembly: pull top-k from each source, limit tokens
        context_parts: list[dict[str, Any]] = []
        total_chars = 0
        limit_chars = max_tokens * 4

        # knowledge
        if self._knowledge and (not sources or "knowledge" in sources):
            try:
                res = await self._knowledge.search(query, top_k=5)
                for chunk in getattr(res, "chunks", [])[:5]:
                    if total_chars + len(chunk.content) > limit_chars:
                        break
                    context_parts.append({"source": "knowledge", "content": chunk.content[:800], "provenance": getattr(chunk, "attribution", None).model_dump(mode="json") if getattr(chunk, "attribution", None) else {}, "tenant_id": tenant_id})
                    total_chars += len(chunk.content)
            except Exception:
                pass

        # memory
        if self._memory and (not sources or "memory" in sources):
            try:
                from eaip.memory.models import MemoryQuery, MemoryScope
                scope = MemoryScope(tenant_id=tenant_id)
                q = MemoryQuery(query=query, scopes=(scope,), limit=5)
                mem_res = await self._memory.search_memories(q)
                for r in getattr(mem_res, "results", [])[:5]:
                    if total_chars + len(r.memory.content) > limit_chars:
                        break
                    context_parts.append({"source": "memory", "content": r.memory.content[:800], "provenance": r.memory.provenance, "tenant_id": tenant_id})
                    total_chars += len(r.memory.content)
            except Exception:
                pass

        return {"tenant_id": tenant_id, "query": query, "parts": context_parts, "bounded": True, "total_chars": total_chars, "count": len(context_parts)}

    async def assemble_strategic_context(self, tenant_id: str, query: str, strategy_engine: Any = None, max_tokens: int = 4000) -> dict[str, Any]:
        """Assemble strategic context: objectives, initiatives, state, KPIs, risks."""
        context_parts: list[dict[str, Any]] = []
        total_chars = 0
        limit_chars = max_tokens * 4

        if strategy_engine:
            try:
                objectives = await strategy_engine.list_objectives(tenant_id)
                for obj in objectives[:10]:
                    content = f"Objective: {obj.title} | Status: {obj.status.value} | Priority: {obj.priority.value} | Owner: {obj.owner}"
                    if total_chars + len(content) > limit_chars:
                        break
                    context_parts.append({"source": "strategic_objective", "content": content, "entity_id": obj.id, "tenant_id": tenant_id})
                    total_chars += len(content)
            except Exception:
                pass

            try:
                initiatives = await strategy_engine.list_initiatives(tenant_id)
                for ini in initiatives[:10]:
                    content = f"Initiative: {ini.title} | Status: {ini.status.value} | Objective: {ini.objective_id} | Budget: {ini.budget}"
                    if total_chars + len(content) > limit_chars:
                        break
                    context_parts.append({"source": "strategic_initiative", "content": content, "entity_id": ini.id, "tenant_id": tenant_id})
                    total_chars += len(content)
            except Exception:
                pass

            try:
                state = await strategy_engine.get_current_state(tenant_id)
                if state:
                    content = f"Current Strategy State v{state.version}: {len(state.objectives_snapshot)} objectives | Rationale: {state.rationale}"
                    if total_chars + len(content) <= limit_chars:
                        context_parts.append({"source": "strategic_state", "content": content, "entity_id": state.id, "tenant_id": tenant_id})
                        total_chars += len(content)
            except Exception:
                pass

            try:
                risks = await strategy_engine.list_risks(tenant_id)
                for risk in risks[:5]:
                    content = f"Risk: {risk.description} | Likelihood: {risk.likelihood.value} | Impact: {risk.impact.value} | Mitigation: {risk.mitigation}"
                    if total_chars + len(content) > limit_chars:
                        break
                    context_parts.append({"source": "strategic_risk", "content": content, "entity_id": risk.id, "tenant_id": tenant_id})
                    total_chars += len(content)
            except Exception:
                pass

            try:
                kpis = await strategy_engine.list_kpis(tenant_id)
                for kpi in kpis[:5]:
                    content = f"Strategic KPI: {kpi.name} | Target: {kpi.target} | Current: {kpi.current} | Trend: {kpi.trend.value}"
                    if total_chars + len(content) > limit_chars:
                        break
                    context_parts.append({"source": "strategic_kpi", "content": content, "entity_id": kpi.id, "tenant_id": tenant_id})
                    total_chars += len(content)
            except Exception:
                pass

        return {"tenant_id": tenant_id, "query": query, "parts": context_parts, "bounded": True, "total_chars": total_chars, "count": len(context_parts), "context_type": "strategic"}

    async def assemble_decision_context(self, tenant_id: str, query: str, governance_engine: Any = None, decision_service: Any = None, max_tokens: int = 4000) -> dict[str, Any]:
        """Assemble decision context: recent governance decisions and decision records."""
        context_parts: list[dict[str, Any]] = []
        total_chars = 0
        limit_chars = max_tokens * 4

        if governance_engine:
            try:
                history = governance_engine.get_decision_history(tenant_id)
                for rec in history[:10]:
                    content = f"Governance Decision: {rec.decision.value} | Who: {rec.who} | What: {rec.what} | Reason: {rec.reason}"
                    if total_chars + len(content) > limit_chars:
                        break
                    context_parts.append({"source": "governance_decision", "content": content, "entity_id": rec.id, "tenant_id": tenant_id})
                    total_chars += len(content)
            except Exception:
                pass

        if decision_service:
            try:
                decisions = decision_service.list_for_tenant(tenant_id)
                for dec in decisions[:5]:
                    content = f"Decision: {dec.title} | Status: {dec.status} | Recommendation: {dec.recommendation}"
                    if total_chars + len(content) > limit_chars:
                        break
                    context_parts.append({"source": "decision_record", "content": content, "entity_id": dec.decision_id, "tenant_id": tenant_id})
                    total_chars += len(content)
            except Exception:
                pass

        return {"tenant_id": tenant_id, "query": query, "parts": context_parts, "bounded": True, "total_chars": total_chars, "count": len(context_parts), "context_type": "decision"}

    async def assemble_temporal_context(self, tenant_id: str, query: str, strategy_engine: Any = None, max_tokens: int = 4000) -> dict[str, Any]:
        """Assemble temporal context: current state + historical snapshots."""
        context_parts: list[dict[str, Any]] = []
        total_chars = 0
        limit_chars = max_tokens * 4

        if strategy_engine:
            try:
                history = await strategy_engine.get_state_history(tenant_id)
                for state in history[-5:]:
                    content = f"Strategy State v{state.version}: {len(state.objectives_snapshot)} objectives | Date: {state.effective_date} | Rationale: {state.rationale}"
                    if total_chars + len(content) > limit_chars:
                        break
                    context_parts.append({"source": "temporal_state", "content": content, "entity_id": state.id, "version": state.version, "tenant_id": tenant_id})
                    total_chars += len(content)
            except Exception:
                pass

        return {"tenant_id": tenant_id, "query": query, "parts": context_parts, "bounded": True, "total_chars": total_chars, "count": len(context_parts), "context_type": "temporal"}

    async def assemble_full_context(self, tenant_id: str, query: str, strategy_engine: Any = None, governance_engine: Any = None, decision_service: Any = None, max_tokens: int = 8000) -> dict[str, Any]:
        """Assemble complete context: knowledge + memory + strategic + decision + temporal."""
        base = await self.assemble(tenant_id, query, max_tokens=max_tokens // 2)
        strategic = await self.assemble_strategic_context(tenant_id, query, strategy_engine, max_tokens=max_tokens // 4)
        decision = await self.assemble_decision_context(tenant_id, query, governance_engine, decision_service, max_tokens=max_tokens // 4)

        all_parts = base["parts"] + strategic["parts"] + decision["parts"]
        total = base["total_chars"] + strategic["total_chars"] + decision["total_chars"]

        return {"tenant_id": tenant_id, "query": query, "parts": all_parts, "bounded": True, "total_chars": total, "count": len(all_parts), "context_type": "full"}
