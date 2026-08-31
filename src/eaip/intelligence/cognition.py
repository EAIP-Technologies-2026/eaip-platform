from __future__ import annotations

import uuid
from typing import Any

from eaip.intelligence.models import CognitiveHypothesis
from eaip.shared.time import utc_now


class CognitiveEngine:
    def __init__(self, knowledge_engine: Any | None = None, memory_engine: Any | None = None, event_bus: Any | None = None) -> None:
        self._knowledge = knowledge_engine
        self._memory = memory_engine
        self._event_bus = event_bus
        self._hypotheses: dict[str, CognitiveHypothesis] = {}
        self._contexts: dict[str, dict[str, Any]] = {}

    def observe(self, tenant_id: str) -> dict[str, Any]:
        signals = []
        if self._knowledge:
            signals.append({"source": "knowledge", "status": "available"})
        if self._memory:
            signals.append({"source": "memory", "status": "available"})
        signals.append({"source": "workforce", "status": "available"})
        signals.append({"source": "missions", "status": "available"})
        return {"tenant_id": tenant_id, "signals": signals, "timestamp": utc_now().isoformat()}

    def situational_awareness(self, tenant_id: str) -> dict[str, Any]:
        obs = self.observe(tenant_id)
        return {"tenant_id": tenant_id, "operations": "normal", "risks": [], "active_missions": 0, "workforce_state": "stable", "anomalies": [], "pending_decisions": 0, "observation": obs}

    async def reason(self, tenant_id: str, query: str, strategy: str = "direct") -> CognitiveHypothesis:
        evidence: list[dict[str, Any]] = []
        confidence = 0.5
        if strategy == "evidence_first" and self._knowledge:
            try:
                from eaip.knowledge.models import RetrievalQuery
                result = await self._knowledge.search(query, top_k=3)
                for chunk in getattr(result, "chunks", [])[:3]:
                    evidence.append({"source": getattr(chunk, "document_id", "unknown"), "content": getattr(chunk, "content", "")[:200], "score": getattr(chunk, "score", 0), "authority": "knowledge", "freshness": "recent"})
                confidence = 0.7 if evidence else 0.4
            except Exception:
                evidence.append({"source": "fallback", "content": query, "authority": "low"})
                confidence = 0.3
        elif strategy == "decomposition":
            evidence.append({"source": "decomposition", "content": f"Decomposed: {query}", "authority": "reasoning"})
            confidence = 0.6
        else:
            evidence.append({"source": "direct", "content": query, "authority": "medium"})
            confidence = 0.5

        hyp = CognitiveHypothesis(hypothesis_id=f"hyp-{uuid.uuid4().hex[:8]}", tenant_id=tenant_id, title=query[:80], evidence=tuple(evidence), confidence=confidence, reasoning_strategy=strategy)
        self._hypotheses[hyp.hypothesis_id] = hyp
        return hyp

    def generate_hypotheses(self, tenant_id: str, problem: str) -> list[CognitiveHypothesis]:
        candidates = [
            ("Supplier delay", "evidence: lead time variance", 0.6),
            ("Workforce shortage", "evidence: capacity < demand", 0.5),
            ("Machine downtime", "evidence: maintenance logs", 0.4),
            ("Scheduling conflict", "evidence: overlapping windows", 0.55),
            ("Quality rework", "evidence: rework rate increase", 0.45),
        ]
        hyps: list[CognitiveHypothesis] = []
        for title, ev, conf in candidates:
            h = CognitiveHypothesis(hypothesis_id=f"hyp-{uuid.uuid4().hex[:8]}", tenant_id=tenant_id, title=f"{problem}: {title}", evidence=({"source": "synthetic", "content": ev, "authority": "medium"},), confidence=conf, reasoning_strategy="hypothesis_generation")
            self._hypotheses[h.hypothesis_id] = h
            hyps.append(h)
        return hyps

    def evaluate_evidence(self, evidence: list[dict[str, Any]]) -> list[dict[str, Any]]:
        scored = []
        for ev in evidence:
            relevance = ev.get("relevance", 0.5)
            freshness = 1.0 if ev.get("freshness") == "recent" else 0.5
            authority = {"high": 1.0, "medium": 0.6, "low": 0.3}.get(ev.get("authority", "medium"), 0.5)
            score = relevance * 0.4 + freshness * 0.3 + authority * 0.3
            scored.append({**ev, "score": round(score, 2)})
        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored

    def recommend(self, hypotheses: list[CognitiveHypothesis]) -> dict[str, Any]:
        if not hypotheses:
            return {"recommendation": "insufficient evidence", "confidence": "low", "uncertainty": "high"}
        best = max(hypotheses, key=lambda h: h.confidence)
        level = "high" if best.confidence > 0.7 else "medium" if best.confidence > 0.4 else "low"
        return {"recommendation": best.title, "confidence": level, "hypothesis_id": best.hypothesis_id, "evidence_count": len(best.evidence)}
