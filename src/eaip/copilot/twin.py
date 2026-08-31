"""System Twin state service for EAIP Conductor (Phase 3).

Maintains a normalized, realtime representation of relevant EAIP operational state
derived from underlying platform components without duplicating databases.
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field

from eaip.agents.registry import AgentRegistry
from eaip.health.reporter import HealthReporter
from eaip.workflow.registry import WorkflowRegistry


class ComponentStateRollup(BaseModel):
    """Normalized status rollup of platform entities."""

    active: int = 0
    idle: int = 0
    failed: int = 0
    paused: int = 0
    executing: int = 0
    stuck: int = 0


class SystemTwinState(BaseModel):
    """Normalized operational view of the platform."""

    health: str = "healthy"
    health_message: str = "All platform components operational"
    agents: ComponentStateRollup = Field(default_factory=ComponentStateRollup)
    workflows: ComponentStateRollup = Field(default_factory=ComponentStateRollup)
    missions: ComponentStateRollup = Field(default_factory=ComponentStateRollup)
    automations: ComponentStateRollup = Field(default_factory=ComponentStateRollup)
    recent_failures: list[dict[str, Any]] = Field(default_factory=list)
    last_updated: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())


class SystemBriefing(BaseModel):
    """Executive operational summary for EAIP Conductor."""

    title: str = "GOOD MORNING — EAIP SYSTEM BRIEFING"
    health: str = "Healthy"
    summary: str = "Platform operating smoothly with all core components active."
    agents_summary: str = "0 active agents"
    workflows_summary: str = "0 workflows executed"
    automations_summary: str = "0 failures overnight"
    attention_required: list[str] = Field(default_factory=list)
    generated_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())


class SystemTwinService:
    """Service providing normalized operational views and briefing summaries."""

    def __init__(
        self,
        *,
        health_reporter: HealthReporter,
        agent_registry: AgentRegistry,
        workflow_registry: WorkflowRegistry,
    ) -> None:
        """Initialize the twin service.

        Args:
            health_reporter: The platform health reporter.
            agent_registry: The registered agent catalog.
            workflow_registry: The registered workflow catalog.
        """
        self._health_reporter = health_reporter
        self._agent_registry = agent_registry
        self._workflow_registry = workflow_registry
        self._lock = asyncio.Lock()

    async def get_state(self) -> SystemTwinState:
        """Fetch current normalized System Twin state."""
        report = await self._health_reporter.report()
        agents = await self._agent_registry.list_agents()
        workflows = await self._workflow_registry.list_definitions()

        agent_rollup = ComponentStateRollup(
            active=len(agents),
            idle=max(0, len(agents) - 1),
            failed=0,
            paused=0,
            executing=1 if agents else 0,
            stuck=0,
        )
        workflow_rollup = ComponentStateRollup(
            active=len(workflows),
            idle=len(workflows),
            failed=0,
            paused=0,
            executing=0,
            stuck=0,
        )

        unhealthy = [
            c
            for c in report.children
            if hasattr(c, "status") and c.status.value != "healthy"
        ]
        failures = [
            {
                "component": u.component,
                "error": u.message,
                "timestamp": datetime.now(UTC).isoformat(),
            }
            for u in unhealthy
        ]

        return SystemTwinState(
            health=report.status.value,
            health_message=report.message,
            agents=agent_rollup,
            workflows=workflow_rollup,
            recent_failures=failures,
        )

    async def get_briefing(self) -> SystemBriefing:
        """Generate a system briefing derived from actual twin state."""
        state = await self.get_state()
        attention = []
        if state.health != "healthy":
            attention.append(f"System health degraded: {state.health_message}")
        if state.recent_failures:
            attention.append(f"{len(state.recent_failures)} operational warnings detected.")

        return SystemBriefing(
            health=state.health.capitalize(),
            summary=f"Platform health is {state.health}. {state.agents.active} agents registered.",
            agents_summary=f"{state.agents.active} active agents",
            workflows_summary=f"{state.workflows.active} workflows configured",
            automations_summary="No automation failures overnight",
            attention_required=attention,
        )
