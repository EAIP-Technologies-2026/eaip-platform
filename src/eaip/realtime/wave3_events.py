from __future__ import annotations

WAVE3_EVENT_TYPES: tuple[str, ...] = (
    "mcp.connected",
    "mcp.disconnected",
    "mcp.tool.discovered",
    "mcp.tool.invoked",
    "connector.health_changed",
    "swarm.started",
    "swarm.completed",
    "agent.collaboration.started",
    "agent.handoff",
    "mission.checkpointed",
    "mission.recovered",
    "mission.escalated",
    "autonomy.approval_required",
    "workflow.composed",
    "runtime.started",
    "runtime.failed",
    "marketplace.artifact.published",
    "marketplace.artifact.verified",
    "marketplace.artifact.revoked",
    "audit.execution.verified",
    "federation.access.granted",
    "federation.access.denied",
    "simulation.branch.created",
    "onboarding.step.completed",
    "solution_pack.installed",
    "external.integration.connected",
    "cross_system_workflow.started",
    "cross_system_workflow.completed",
)

__all__ = ["WAVE3_EVENT_TYPES"]
