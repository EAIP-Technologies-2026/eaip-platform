from __future__ import annotations

from typing import Any


def apex_fixtures(tenant_id: str = "apex") -> dict[str, list[dict[str, Any]]]:
    return {
        "employees": [
            {"employee_id": "apex-emp-001", "tenant_id": tenant_id, "name": "Apex Strategy Lead", "role": "consultant", "department": "Advisory", "capabilities": ["strategy", "risk"], "skills": {"strategy": 0.9, "risk": 0.8}, "availability": "available", "workload": 0.4},
            {"employee_id": "apex-emp-002", "tenant_id": tenant_id, "name": "Apex Digital Analyst", "role": "analyst", "department": "Delivery", "capabilities": ["analysis", "delivery"], "skills": {"analysis": 0.85, "delivery": 0.9}, "availability": "available", "workload": 0.5},
        ],
        "methodologies": [
            {"methodology_id": "apex-mth-risk", "tenant_id": tenant_id, "name": "Apex Risk Framework", "category": "risk", "supported_domains": ["advisory"], "benchmark_score": 0.88},
            {"methodology_id": "apex-mth-decision", "tenant_id": tenant_id, "name": "Apex Decision Matrix", "category": "decision", "supported_domains": ["advisory"], "benchmark_score": 0.82},
        ],
        "documents": [
            {"source": "apex-client-proposal.pdf", "content": "Proposal for Acme Corp | Q1 | 120000 | strategy engagement", "classification": "proposal"},
            {"source": "apex-delivery-report.pdf", "content": "Delivery report | Milestone Build | status at_risk | 65% complete", "classification": "delivery"},
        ],
        "governed_systems": [
            {"system_id": "apex-model-risk", "tenant_id": tenant_id, "type": "model", "name": "Apex Risk Model", "risk": "moderate", "lifecycle": "active"},
            {"system_id": "apex-agent-advisory", "tenant_id": tenant_id, "type": "agent", "name": "Advisory Assistant", "risk": "low", "lifecycle": "active"},
        ],
        "twins": [
            {"enterprise": "apex", "kpis": {"utilization": 0.68, "delivery_risk": 0.32, "client_satisfaction": 0.81}, "risk": {"level": "moderate"}},
        ],
        "scenarios": [
            {"name": "Apex: expand delivery capacity 20%", "baseline_state": {"workload": 0.68, "utilization": 0.72, "active_engagements": 12}},
        ],
        "insights": [
            {"tenant_id": tenant_id, "latency": 1450, "system": "delivery", "event_type": "milestone_delay"},
        ],
        "decisions": [
            {"title": "Apex: prioritize at-risk engagement", "objective": "Mitigate delivery risk for Acme Corp", "alternatives": [{"name": "add_capacity", "cost": 15000, "risk": 0.2, "confidence": 0.8}, {"name": "rescope", "cost": 5000, "risk": 0.4, "confidence": 0.6}]},
        ],
        "improvements": [
            {"source": "ops_intelligence", "problem": {"title": "Repeated delivery delays", "cause": "understaffed Build phase"}, "proposed_change": "Add 2 analysts to Build pod"},
        ],
    }


def nova_fixtures(tenant_id: str = "nova") -> dict[str, list[dict[str, Any]]]:
    return {
        "employees": [
            {"employee_id": "nova-emp-001", "tenant_id": tenant_id, "name": "Nova Line Supervisor", "role": "supervisor", "department": "Production", "capabilities": ["production", "quality"], "skills": {"production": 0.92, "quality": 0.78}, "availability": "available", "workload": 0.6},
            {"employee_id": "nova-emp-002", "tenant_id": tenant_id, "name": "Nova Maintenance Tech", "role": "technician", "department": "Maintenance", "capabilities": ["maintenance", "diagnostics"], "skills": {"maintenance": 0.88, "diagnostics": 0.85}, "availability": "busy", "workload": 0.85},
        ],
        "methodologies": [
            {"methodology_id": "nova-mth-forecast", "tenant_id": tenant_id, "name": "Nova Demand Forecast", "category": "forecasting", "supported_domains": ["manufacturing"], "benchmark_score": 0.91},
            {"methodology_id": "nova-mth-optimization", "tenant_id": tenant_id, "name": "Nova Line Optimizer", "category": "optimization", "supported_domains": ["manufacturing"], "benchmark_score": 0.86},
        ],
        "documents": [
            {"source": "nova-supplier-contract.pdf", "content": "Supplier AlloyWorks | part PN-12345 | delivery 14 days | penalty clause", "classification": "supplier"},
            {"source": "nova-quality-alert.csv", "content": "Line-A | defect_rate | 3.2 | threshold 2.0 | batch batch_abc", "classification": "quality"},
        ],
        "governed_systems": [
            {"system_id": "nova-model-quality", "tenant_id": tenant_id, "type": "model", "name": "Quality Predictor", "risk": "high", "lifecycle": "active"},
            {"system_id": "nova-connector-erp", "tenant_id": tenant_id, "type": "connector", "name": "ERP Connector", "risk": "moderate", "lifecycle": "active"},
        ],
        "twins": [
            {"enterprise": "nova", "kpis": {"throughput": 0.74, "defect_rate": 0.04, "oee": 0.82}, "risk": {"level": "high"}},
        ],
        "scenarios": [
            {"name": "Nova: supplier AlloyWorks unavailable 30 days", "baseline_state": {"supplier": "AlloyWorks", "inventory_days": 12, "demand": 0.85}},
            {"name": "Nova: demand +25%", "baseline_state": {"demand": 1.25, "capacity": 0.9, "backlog": 0.3}},
        ],
        "insights": [
            {"tenant_id": tenant_id, "workforce_utilization": 0.94, "domain": "workforce", "system": "workforce"},
            {"tenant_id": tenant_id, "latency": 2100, "system": "production", "event_type": "line_delay"},
        ],
        "decisions": [
            {"title": "Nova: mitigate AlloyWorks delay", "objective": "Maintain production with alternate supplier", "alternatives": [{"name": "alternate_supplier", "cost": 45000, "risk": 0.3, "confidence": 0.75}, {"name": "reschedule", "cost": 12000, "risk": 0.5, "confidence": 0.55}]},
        ],
        "improvements": [
            {"source": "ops_intelligence", "problem": {"title": "High defect rate on Line-A", "cause": "thermal overrun"}, "proposed_change": "Adjust thermal calibration"},
        ],
    }


def meridian_fixtures(tenant_id: str = "meridian") -> dict[str, list[dict[str, Any]]]:
    return {
        "employees": [
            {"employee_id": "meridian-emp-001", "tenant_id": tenant_id, "name": "Meridian Care Coordinator", "role": "coordinator", "department": "Care", "capabilities": ["care", "compliance"], "skills": {"care": 0.9, "compliance": 0.82}, "availability": "available", "workload": 0.55},
            {"employee_id": "meridian-emp-002", "tenant_id": tenant_id, "name": "Meridian Compliance Officer", "role": "officer", "department": "Compliance", "capabilities": ["compliance", "audit"], "skills": {"compliance": 0.93, "audit": 0.88}, "availability": "available", "workload": 0.45},
        ],
        "methodologies": [
            {"methodology_id": "meridian-mth-evidence", "tenant_id": tenant_id, "name": "Meridian Evidence Review", "category": "evidence", "supported_domains": ["healthcare"], "benchmark_score": 0.89},
            {"methodology_id": "meridian-mth-risk", "tenant_id": tenant_id, "name": "Meridian Clinical Risk", "category": "risk", "supported_domains": ["healthcare"], "benchmark_score": 0.84},
        ],
        "documents": [
            {"source": "meridian-policy-hipaa.pdf", "content": "HIPAA policy | access review | training required | audit due 2026-06-01", "classification": "policy"},
            {"source": "meridian-care-plan.pdf", "content": "Care plan update | Patient pat_abc | action medication_change | ICU", "classification": "care"},
        ],
        "governed_systems": [
            {"system_id": "meridian-prompt-triage", "tenant_id": tenant_id, "type": "prompt", "name": "Triage Prompt v2", "risk": "high", "lifecycle": "active"},
            {"system_id": "meridian-methodology-evidence", "tenant_id": tenant_id, "type": "methodology", "name": "Evidence Review", "risk": "moderate", "lifecycle": "active"},
        ],
        "twins": [
            {"enterprise": "meridian", "kpis": {"bed_occupancy": 0.78, "compliance_score": 0.91, "staffing_ratio": 0.85}, "risk": {"level": "moderate"}},
        ],
        "scenarios": [
            {"name": "Meridian: staffing -20% for 14 days", "baseline_state": {"staffing": 0.8, "demand": 0.85, "compliance_risk": 0.4}},
            {"name": "Meridian: compliance audit in 7 days", "baseline_state": {"audit_readiness": 0.72, "findings": 3, "remediation_days": 7}},
        ],
        "insights": [
            {"tenant_id": tenant_id, "error": "true", "level": "error", "system": "compliance", "event_type": "audit_gap"},
        ],
        "decisions": [
            {"title": "Meridian: staffing contingency", "objective": "Maintain care quality with reduced staffing", "alternatives": [{"name": "overtime", "cost": 25000, "risk": 0.35, "confidence": 0.7}, {"name": "defer_elective", "cost": 8000, "risk": 0.25, "confidence": 0.75}]},
        ],
        "improvements": [
            {"source": "audit", "problem": {"title": "Access review overdue", "cause": "manual review backlog"}, "proposed_change": "Automate quarterly access review"},
        ],
    }


ALL_FIXTURES: dict[str, Any] = {
    "apex": apex_fixtures,
    "nova": nova_fixtures,
    "meridian": meridian_fixtures,
}


__all__ = ["ALL_FIXTURES", "apex_fixtures", "meridian_fixtures", "nova_fixtures"]
