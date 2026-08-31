"""M9 registries — tenant-isolated, reuses existing engines."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from eaip.executive_os.models import DepartmentId, DepartmentView, ExecutiveBriefing, IndustryId, KPIRecord


class BriefingService:
    def __init__(self) -> None:
        self._briefings: dict[str, ExecutiveBriefing] = {}

    def generate(self, tenant_id: str, context: dict[str, Any] | None = None) -> ExecutiveBriefing:
        ctx = context or {}
        b = ExecutiveBriefing(
            tenant_id=tenant_id,
            what_changed=ctx.get("what_changed", [{"item": "No significant changes", "evidence": "observability timeline"}]),
            why=ctx.get("why", "Stable operations — no anomalies detected"),
            risks=ctx.get("risks", []),
            opportunities=ctx.get("opportunities", []),
            decisions=ctx.get("decisions", []),
            actions=ctx.get("actions", []),
            forecast=ctx.get("forecast", [{"metric": "workload", "prediction": "stable", "confidence": 0.7}]),
            recommendations=ctx.get("recommendations", [{"action": "Continue monitoring", "priority": "low"}]),
        )
        self._briefings[b.briefing_id] = b
        return b

    def get(self, briefing_id: str, tenant_id: str) -> ExecutiveBriefing | None:
        b = self._briefings.get(briefing_id)
        if b and b.tenant_id == tenant_id:
            return b
        return None

    def latest_for_tenant(self, tenant_id: str) -> ExecutiveBriefing | None:
        candidates = [v for v in self._briefings.values() if v.tenant_id == tenant_id]
        if not candidates:
            return None
        return max(candidates, key=lambda x: x.created_at)


class DepartmentRegistry:
    # Department view definitions — consumed from existing engines, no duplicates
    DEPARTMENTS: dict[str, dict[str, Any]] = {
        "executive": {"title": "Executive Cockpit", "sections": ["strategic_health", "kpi_health", "risk_radar", "opportunity_radar", "decision_radar", "workforce_health", "mission_health", "system_health", "ai_quality", "ai_cost", "approvals", "recommendations"]},
        "operations": {"title": "Operations", "sections": ["processes", "workflows", "incidents", "capacity", "bottlenecks", "missions", "workforce", "recommendations"]},
        "finance": {"title": "Finance", "sections": ["cost", "budget", "forecast", "financial_signals", "anomalies", "approvals", "risk"]},
        "sales": {"title": "Sales", "sections": ["pipeline", "opportunities", "customer_intelligence", "forecasts", "risk", "recommended_actions"]},
        "marketing": {"title": "Marketing", "sections": ["campaigns", "performance", "audience_intelligence", "opportunity_signals", "recommendations"]},
        "hr": {"title": "HR / Workforce", "sections": ["capacity", "workload", "performance", "skills", "staffing", "agent_human_collaboration", "escalation"]},
        "it": {"title": "IT", "sections": ["systems", "incidents", "connectors", "runtimes", "reliability"]},
        "compliance": {"title": "Compliance", "sections": ["policies", "approvals", "audit", "data_governance", "exceptions", "risks"]},
        "support": {"title": "Support", "sections": ["tickets", "sla", "escalation", "knowledge", "workforce"]},
    }

    def __init__(self) -> None:
        self._views: dict[str, DepartmentView] = {}

    def get_view(self, department: str, tenant_id: str, industry: str | None = None) -> DepartmentView:
        key = f"{tenant_id}:{department}:{industry or 'general'}"
        if key in self._views:
            return self._views[key]
        cfg = self.DEPARTMENTS.get(department, {"title": department.title(), "sections": []})
        view = DepartmentView(
            department=DepartmentId(department) if department in [e.value for e in DepartmentId] else DepartmentId.executive,  # type: ignore[arg-type]
            tenant_id=tenant_id,
            title=cfg["title"],
            sections=[{"id": s, "title": s.replace("_", " ").title()} for s in cfg["sections"]],
            kpis=[],
        )
        # Try to set industry
        if industry:
            try:
                view.industry = IndustryId(industry)
            except ValueError:
                pass
        self._views[key] = view
        return view

    def list_departments(self) -> list[dict[str, Any]]:
        return [{"id": k, "title": v["title"], "sections": v["sections"]} for k, v in self.DEPARTMENTS.items()]


class KPIRegistry:
    def __init__(self) -> None:
        self._kpis: dict[str, KPIRecord] = {}

    def record(self, kpi: KPIRecord) -> KPIRecord:
        self._kpis[kpi.kpi_id] = kpi
        return kpi

    def list_for_tenant(self, tenant_id: str, department: str | None = None) -> list[KPIRecord]:
        results = [v for v in self._kpis.values() if v.tenant_id == tenant_id]
        if department:
            results = [r for r in results if r.department == department]
        return results

    def get(self, kpi_id: str, tenant_id: str) -> KPIRecord | None:
        k = self._kpis.get(kpi_id)
        if k and k.tenant_id == tenant_id:
            return k
        return None
