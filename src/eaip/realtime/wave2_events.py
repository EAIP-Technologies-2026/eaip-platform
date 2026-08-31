from __future__ import annotations

from typing import Any

from eaip.events.event import DomainEvent


class WorkforceEmployeeCreated(DomainEvent):
    event_type: str = "workforce.employee.created"  # type: ignore[assignment]
    employee_id: str = ""
    tenant_id: str = ""


class WorkforceAssignmentCreated(DomainEvent):
    event_type: str = "workforce.assignment.created"  # type: ignore[assignment]
    assignment_id: str = ""
    tenant_id: str = ""


class WorkforceCapacityWarning(DomainEvent):
    event_type: str = "workforce.capacity.warning"  # type: ignore[assignment]
    tenant_id: str = ""
    utilization: float = 0.0


class MethodologySelected(DomainEvent):
    event_type: str = "methodology.selected"  # type: ignore[assignment]
    methodology_id: str = ""
    tenant_id: str = ""


class MethodologyEvaluationCompleted(DomainEvent):
    event_type: str = "methodology.evaluation.completed"  # type: ignore[assignment]
    methodology_id: str = ""
    tenant_id: str = ""


class DocumentIntelligenceStarted(DomainEvent):
    event_type: str = "document.intelligence.started"  # type: ignore[assignment]
    document_id: str = ""
    tenant_id: str = ""


class DocumentIntelligenceCompleted(DomainEvent):
    event_type: str = "document.intelligence.completed"  # type: ignore[assignment]
    document_id: str = ""
    tenant_id: str = ""


class DocumentValidationRequired(DomainEvent):
    event_type: str = "document.validation.required"  # type: ignore[assignment]
    document_id: str = ""
    tenant_id: str = ""


class GovernanceRiskDetected(DomainEvent):
    event_type: str = "governance.risk.detected"  # type: ignore[assignment]
    system_id: str = ""
    tenant_id: str = ""
    risk: str = ""


class GovernanceApprovalRequired(DomainEvent):
    event_type: str = "governance.approval.required"  # type: ignore[assignment]
    system_id: str = ""
    tenant_id: str = ""


class SimulationStarted(DomainEvent):
    event_type: str = "simulation.started"  # type: ignore[assignment]
    scenario_id: str = ""
    tenant_id: str = ""


class SimulationCompleted(DomainEvent):
    event_type: str = "simulation.completed"  # type: ignore[assignment]
    scenario_id: str = ""
    tenant_id: str = ""


class DecisionSimulationCompleted(DomainEvent):
    event_type: str = "decision.simulation.completed"  # type: ignore[assignment]
    decision_id: str = ""
    tenant_id: str = ""


class OperationalInsightDetected(DomainEvent):
    event_type: str = "operational.insight.detected"  # type: ignore[assignment]
    insight_id: str = ""
    tenant_id: str = ""


class OperationalInsightEscalated(DomainEvent):
    event_type: str = "operational.insight.escalated"  # type: ignore[assignment]
    insight_id: str = ""
    tenant_id: str = ""


class ImprovementProposed(DomainEvent):
    event_type: str = "improvement.proposed"  # type: ignore[assignment]
    proposal_id: str = ""
    tenant_id: str = ""


class ImprovementApprovalRequired(DomainEvent):
    event_type: str = "improvement.approval.required"  # type: ignore[assignment]
    proposal_id: str = ""
    tenant_id: str = ""


class ImprovementApplied(DomainEvent):
    event_type: str = "improvement.applied"  # type: ignore[assignment]
    proposal_id: str = ""
    tenant_id: str = ""


WAVE2_EVENT_TYPES: tuple[str, ...] = (
    "workforce.employee.created",
    "workforce.assignment.created",
    "workforce.capacity.warning",
    "methodology.selected",
    "methodology.evaluation.completed",
    "document.intelligence.started",
    "document.intelligence.completed",
    "document.validation.required",
    "governance.risk.detected",
    "governance.approval.required",
    "simulation.started",
    "simulation.completed",
    "decision.simulation.completed",
    "operational.insight.detected",
    "operational.insight.escalated",
    "improvement.proposed",
    "improvement.approval.required",
    "improvement.applied",
)


def tenant_channel(tenant_id: str) -> str:
    return f"tenant:{tenant_id}"


def emit_for_tenant(event_bus: Any, event: DomainEvent) -> Any:
    tenant_id = getattr(event, "tenant_id", "default")
    channel = tenant_channel(str(tenant_id))
    payload = event.model_dump(mode="json") if hasattr(event, "model_dump") else {"type": getattr(event, "event_type", type(event).__name__), "tenant_id": tenant_id}
    payload["_channel"] = channel
    return event_bus.publish(event)


__all__ = [
    "WAVE2_EVENT_TYPES",
    "DecisionSimulationCompleted",
    "DocumentIntelligenceCompleted",
    "DocumentIntelligenceStarted",
    "DocumentValidationRequired",
    "GovernanceApprovalRequired",
    "GovernanceRiskDetected",
    "ImprovementApplied",
    "ImprovementApprovalRequired",
    "ImprovementProposed",
    "MethodologyEvaluationCompleted",
    "MethodologySelected",
    "OperationalInsightDetected",
    "OperationalInsightEscalated",
    "SimulationCompleted",
    "SimulationStarted",
    "WorkforceAssignmentCreated",
    "WorkforceCapacityWarning",
    "WorkforceEmployeeCreated",
    "emit_for_tenant",
    "tenant_channel",
]
