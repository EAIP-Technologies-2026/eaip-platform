from __future__ import annotations

from typing import Any

from pydantic.json_schema import JsonSchemaValue


class WorkforceCapacityTool:
    name = "workforce_capacity"
    description = "Show digital workforce capacity, utilization and availability."

    @property
    def parameters(self) -> JsonSchemaValue:
        return {"type": "object", "properties": {}}

    async def execute(self, **kwargs: object) -> str:
        svc = kwargs.get("_workforce_service")
        tenant_id = str(kwargs.get("tenant_id") or kwargs.get("tenantId") or "default")
        if svc and hasattr(svc, "get_capacity"):
            try:
                cap = svc.get_capacity(tenant_id)
                return f"Workforce capacity for {tenant_id}: total={cap.get('total', 0)} available={cap.get('available', 0)} busy={cap.get('busy', 0)} utilization={cap.get('utilization', 0):.0%}"
            except Exception as exc:
                return f"Workforce capacity unavailable: {exc}"
        return f"Workforce capacity for {tenant_id} is not yet wired."


class WorkforceMatchTool:
    name = "workforce_match"
    description = "Find best-suited workforce members for a task."

    @property
    def parameters(self) -> JsonSchemaValue:
        return {"type": "object", "properties": {"query": {"type": "string", "description": "Task or skill query"}, "requirements": {"type": "object", "description": "Skill requirements map"}}}

    async def execute(self, **kwargs: object) -> str:
        svc = kwargs.get("_workforce_service")
        tenant_id = str(kwargs.get("tenant_id") or "default")
        query = str(kwargs.get("query", ""))
        reqs = kwargs.get("requirements") if isinstance(kwargs.get("requirements"), dict) else {}
        if not reqs and query:
            reqs = {query: 1.0}
        if svc and hasattr(svc, "match_skill"):
            try:
                matches = svc.match_skill(tenant_id, reqs or {query: 1.0})
                if not matches:
                    return f"No workforce match found for '{query}' in tenant {tenant_id}."
                top = matches[:3]
                return f"Best match for '{query}': " + ", ".join(f"{eid} (score {s:.2f})" for eid, s in top)
            except Exception as exc:
                return f"Workforce match failed: {exc}"
        return f"Workforce match for '{query}' not wired."


class DocumentAnalyzeTool:
    name = "document_analyze"
    description = "Analyze a document via Document Intelligence (OCR, entities, tables)."

    @property
    def parameters(self) -> JsonSchemaValue:
        return {"type": "object", "properties": {"query": {"type": "string"}, "document_id": {"type": "string"}}}

    async def execute(self, **kwargs: object) -> str:
        eng = kwargs.get("_document_engine")
        tenant_id = str(kwargs.get("tenant_id") or "default")
        doc_id = str(kwargs.get("document_id") or kwargs.get("query") or "")
        if eng and hasattr(eng, "get"):
            try:
                rec = eng.get(doc_id, tenant_id)
                if rec:
                    return f"Document {doc_id}: status={rec.status} entities={len(rec.extracted_entities)} tables={len(rec.extracted_tables)} confidence={rec.confidence:.2f}"
                lst = eng.list_for_tenant(tenant_id) if hasattr(eng, "list_for_tenant") else []
                if lst:
                    return f"Found {len(lst)} documents for {tenant_id}. Provide document_id to analyze."
                return f"No documents found for tenant {tenant_id}."
            except Exception as exc:
                return f"Document analysis failed: {exc}"
        return "Document Intelligence not wired."


class ScenarioCompareTool:
    name = "scenario_compare"
    description = "Compare enterprise simulation scenarios."

    @property
    def parameters(self) -> JsonSchemaValue:
        return {"type": "object", "properties": {"scenario_ids": {"type": "array", "items": {"type": "string"}}, "scenarioIds": {"type": "array", "items": {"type": "string"}}}}

    async def execute(self, **kwargs: object) -> str:
        eng = kwargs.get("_scenario_engine")
        tenant_id = str(kwargs.get("tenant_id") or "default")
        ids = kwargs.get("scenario_ids") or kwargs.get("scenarioIds") or []
        if not isinstance(ids, list):
            ids = []
        if eng and hasattr(eng, "compare") and ids:
            try:
                result = eng.compare([str(x) for x in ids], tenant_id)
                return f"Scenario comparison for {tenant_id}: " + ", ".join(f"{k}: cost={v.get('cost', '?')} risk={v.get('risk', '?')}" for k, v in result.items() if isinstance(v, dict))
            except Exception as exc:
                return f"Scenario comparison failed: {exc}"
        if eng and hasattr(eng, "list_for_tenant"):
            lst = eng.list_for_tenant(tenant_id)
            return f"Found {len(lst)} scenarios for {tenant_id}. Provide scenario_ids to compare."
        return "Scenario engine not wired."


class GovernanceApprovalsTool:
    name = "governance_approvals"
    description = "Show pending AI governance approvals."

    @property
    def parameters(self) -> JsonSchemaValue:
        return {"type": "object", "properties": {}}

    async def execute(self, **kwargs: object) -> str:
        tenant_id = str(kwargs.get("tenant_id") or "default")
        return f"Governance approvals for {tenant_id}: check /api/governance2/systems?lifecycle=pending or /api/governance2/policies"


class GovernanceRiskTool:
    name = "governance_risk"
    description = "Show governance risk for systems."

    @property
    def parameters(self) -> JsonSchemaValue:
        return {"type": "object", "properties": {"system_id": {"type": "string"}, "query": {"type": "string"}}}

    async def execute(self, **kwargs: object) -> str:
        return "Governance risk: check /api/governance2/systems?risk=high and /api/governance2/systems/{id}/risk"


class OpsAnomaliesTool:
    name = "ops_anomalies"
    description = "Show operational anomalies and insights."

    @property
    def parameters(self) -> JsonSchemaValue:
        return {"type": "object", "properties": {"severity": {"type": "string"}, "type": {"type": "string"}}}

    async def execute(self, **kwargs: object) -> str:
        svc = kwargs.get("_ops_service")
        tenant_id = str(kwargs.get("tenant_id") or "default")
        if svc and hasattr(svc, "list_for_tenant"):
            try:
                insights = svc.list_for_tenant(tenant_id)
                if not insights:
                    return f"No operational insights for {tenant_id}."
                by_sev: dict[str, int] = {}
                for ins in insights:
                    by_sev[ins.severity] = by_sev.get(ins.severity, 0) + 1
                return f"Ops insights for {tenant_id}: {len(insights)} total " + ", ".join(f"{k}={v}" for k, v in by_sev.items())
            except Exception as exc:
                return f"Ops anomalies unavailable: {exc}"
        return f"Ops anomalies for {tenant_id} not wired. Check /api/ops-intelligence/insights"


class ImprovementProposalsTool:
    name = "improvement_proposals"
    description = "Show continuous improvement proposals."

    @property
    def parameters(self) -> JsonSchemaValue:
        return {"type": "object", "properties": {"status": {"type": "string"}}}

    async def execute(self, **kwargs: object) -> str:
        svc = kwargs.get("_improvement_service")
        tenant_id = str(kwargs.get("tenant_id") or "default")
        if svc and hasattr(svc, "list_for_tenant"):
            try:
                props = svc.list_for_tenant(tenant_id)
                if not props:
                    return f"No improvement proposals for {tenant_id}."
                by_status: dict[str, int] = {}
                for p in props:
                    by_status[p.status] = by_status.get(p.status, 0) + 1
                return f"Improvements for {tenant_id}: {len(props)} total " + ", ".join(f"{k}={v}" for k, v in by_status.items())
            except Exception as exc:
                return f"Improvements unavailable: {exc}"
        return f"Improvements for {tenant_id} not wired. Check /api/improvements"


class DecisionExplainTool:
    name = "decision_explain"
    description = "Explain a decision (evidence, methodology, constraints, approval)."

    @property
    def parameters(self) -> JsonSchemaValue:
        return {"type": "object", "properties": {"query": {"type": "string"}, "decision_id": {"type": "string"}}}

    async def execute(self, **kwargs: object) -> str:
        svc = kwargs.get("_decision_service")
        tenant_id = str(kwargs.get("tenant_id") or "default")
        did = str(kwargs.get("decision_id") or kwargs.get("query") or "")
        if svc and hasattr(svc, "get") and did:
            try:
                rec = svc.get(did, tenant_id)
                if rec:
                    return f"Decision {did}: title='{rec.title}' status={rec.status} recommendation={rec.recommendation} alternatives={len(rec.alternatives)} evidence={len(rec.evidence)}"
                lst = svc.list_for_tenant(tenant_id) if hasattr(svc, "list_for_tenant") else []
                return f"Decision {did} not found. Found {len(lst)} decisions for {tenant_id}."
            except Exception as exc:
                return f"Decision explain failed: {exc}"
        return "Decision service not wired. Check /api/intelligence/decisions"


__all__ = [
    "DecisionExplainTool",
    "DocumentAnalyzeTool",
    "GovernanceApprovalsTool",
    "GovernanceRiskTool",
    "ImprovementProposalsTool",
    "OpsAnomaliesTool",
    "ScenarioCompareTool",
    "WorkforceCapacityTool",
    "WorkforceMatchTool",
]
