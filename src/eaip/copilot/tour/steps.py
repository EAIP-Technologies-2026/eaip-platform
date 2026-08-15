"""Deterministic tour step definitions for the EAIP platform.

Each step maps to a real route in the enterprise console.  The tour sequence
is bounded and predictable — the assistant can dynamically explain or answer
questions, but the step ordering is fixed.
"""

from __future__ import annotations

from typing import Any

from eaip.copilot.tour.models import TourStep

TOUR_STEPS: tuple[TourStep, ...] = (
    TourStep(
        id="dashboard",
        order=0,
        route="/dashboard",
        application="enterprise_console",
        title="Dashboard",
        narration=(
            "Let's start with the Dashboard. This is your operational overview of EAIP. "
            "It gives you a quick view of system health, agents, activity, and current "
            "operational context."
        ),
        why_it_matters=(
            "The Dashboard is where you begin every session. It surfaces what needs "
            "your attention right now."
        ),
        demo_description="Showing real-time health and agent status cards.",
        demo_safe=True,
    ),
    TourStep(
        id="agents",
        order=1,
        route="/agents",
        application="enterprise_console",
        title="Agents",
        narration=(
            "You're now looking at Agents. Agents are the execution workers inside EAIP. "
            "Each agent has tools, permissions, and a governed lifecycle."
        ),
        why_it_matters=(
            "Agents do the actual work — they run workflows, search knowledge, "
            "and interact with enterprise systems on your behalf."
        ),
        demo_description="Listing registered agents with their current status.",
        demo_safe=True,
    ),
    TourStep(
        id="brains",
        order=2,
        route="/brains",
        application="enterprise_console",
        title="Second Brain / Brains",
        narration=(
            "This is Brains — your Second Brain. It organizes knowledge, context, "
            "and reasoning into structured brain instances."
        ),
        why_it_matters=(
            "Brains let you build specialized knowledge repositories that agents "
            "and workflows can draw from."
        ),
        demo_description="Showing available brain instances.",
        demo_safe=True,
    ),
    TourStep(
        id="knowledge",
        order=3,
        route="/knowledge",
        application="enterprise_console",
        title="Knowledge",
        narration=(
            "Knowledge is your enterprise knowledge base. Documents, policies, "
            "and operational knowledge are stored here and made searchable."
        ),
        why_it_matters=(
            "When agents need grounded answers, they search the Knowledge base. "
            "Keeping it current improves every agent response."
        ),
        demo_description="Searching the knowledge base for a sample query.",
        demo_safe=True,
    ),
    TourStep(
        id="missions",
        order=4,
        route="/missions",
        application="enterprise_console",
        title="Missions",
        narration=(
            "Missions are orchestrated multi-step operations. A mission coordinates "
            "agents, workflows, and approvals to achieve a goal."
        ),
        why_it_matters=(
            "Complex enterprise tasks often need multiple steps. Missions "
            "give you visibility and control over those operations."
        ),
        demo_description="Showing mission history and active missions.",
        demo_safe=True,
    ),
    TourStep(
        id="monitoring",
        order=5,
        route="/monitoring",
        application="enterprise_console",
        title="Monitoring",
        narration=(
            "Monitoring gives you real-time operational telemetry. Health checks, "
            "performance metrics, and system alerts appear here."
        ),
        why_it_matters=(
            "When something goes wrong, Monitoring is where you find it first. "
            "It connects to the System Twin for a unified operational view."
        ),
        demo_description="Displaying current system health metrics.",
        demo_safe=True,
    ),
    TourStep(
        id="activity",
        order=6,
        route="/activity",
        application="enterprise_console",
        title="Activity",
        narration=(
            "Activity is your operational audit trail. Every action, every tool "
            "invocation, and every governance decision is recorded here."
        ),
        why_it_matters=(
            "Audit trails are essential for enterprise governance. You can always "
            "trace what happened, when, and who authorized it."
        ),
        demo_description="Showing recent platform activity entries.",
        demo_safe=True,
    ),
    TourStep(
        id="administration",
        order=7,
        route="/administration",
        application="enterprise_console",
        title="Administration",
        narration=(
            "Administration is where platform operators manage users, roles, "
            "permissions, and enterprise settings."
        ),
        why_it_matters=(
            "This is the control center for who can do what on the platform. "
            "All changes here go through normal governance and audit."
        ),
        demo_description="Showing the administration overview.",
        demo_safe=True,
    ),
    TourStep(
        id="marketplace",
        order=8,
        route="/marketplace",
        application="enterprise_console",
        title="Marketplace",
        narration=(
            "The Marketplace is where you discover and install skills for your "
            "agents and the Conductor. Skills extend what the platform can do."
        ),
        why_it_matters=(
            "New capabilities can be added without changing core platform code. "
            "Each skill goes through trust verification before installation."
        ),
        demo_description="Browsing available marketplace skills.",
        demo_safe=True,
    ),
    TourStep(
        id="memory",
        order=9,
        route="/memory",
        application="enterprise_console",
        title="Memory",
        narration=(
            "Memory is your governed personal enterprise memory. The Conductor "
            "remembers preferences, investigations, and context on your behalf."
        ),
        why_it_matters=(
            "Memory makes your assistant personally useful over time. "
            "All memory is governed — it has retention, sensitivity, and audit."
        ),
        demo_description="Showing your current governed memory items.",
        demo_safe=True,
    ),
    TourStep(
        id="system-twin",
        order=10,
        route="/dashboard",
        application="enterprise_console",
        title="System Twin",
        narration=(
            "The System Twin is a normalized operational model of your entire "
            "EAIP instance. It rolls up agents, workflows, missions, and health "
            "into a single coherent state."
        ),
        why_it_matters=(
            "Instead of checking five different screens, the System Twin gives "
            "you one authoritative view of platform operational state."
        ),
        demo_description="Retrieving the current System Twin state.",
        demo_safe=True,
    ),
    TourStep(
        id="conductor",
        order=11,
        route="/dashboard",
        application="enterprise_console",
        title="Personal Assistant / Conductor",
        narration=(
            "And this — the Conductor — is your personal assistant. It's the "
            "governed AI that can inspect the platform, run tools, and help you "
            "operate EAIP using natural language or voice."
        ),
        why_it_matters=(
            "The Conductor is how you interact with EAIP conversationally. "
            "Every action it takes goes through governance, approval, and audit."
        ),
        demo_description="Demonstrating a safe Conductor query.",
        demo_safe=True,
    ),
)


STEP_CAPABILITY_MAP: dict[str, str] = {
    "dashboard": "eaip.dashboard",
    "agents": "eaip.agents",
    "brains": "eaip.brains",
    "knowledge": "eaip.knowledge",
    "missions": "eaip.missions",
    "monitoring": "eaip.monitoring",
    "activity": "eaip.investigations",
    "administration": "eaip.administration",
    "marketplace": "eaip.marketplace",
    "memory": "eaip.memory",
    "system-twin": "eaip.conductor",
    "conductor": "eaip.enterprise_assistant",
}


def get_tour_steps() -> tuple[TourStep, ...]:
    """Return the full ordered tour step sequence."""
    return TOUR_STEPS


def get_dynamic_tour_steps(
    context: Any | None = None,
    start_route: str = "/",
) -> tuple[TourStep, ...]:
    """Return ordered tour steps filtered by the caller's PermissionAwareContext.

    Args:
        context: Optional PermissionAwareContext.
        start_route: Current route to contextually re-align tour starting point.

    Returns:
        Filtered, ordered tuple of TourStep instances.
    """
    eligible_steps: list[TourStep] = []

    for step in TOUR_STEPS:
        cap_name = STEP_CAPABILITY_MAP.get(step.id)
        # If context provided, check if identity can see this capability
        if (
            context is not None
            and cap_name is not None
            and hasattr(context, "can_see")
            and not context.can_see(cap_name)
        ):
            continue
        eligible_steps.append(step)

    if not eligible_steps:
        return ()

    # Contextual starting route re-alignment
    if start_route and start_route != "/":
        start_idx = 0
        for i, step in enumerate(eligible_steps):
            if step.route == start_route:
                start_idx = i
                break
        if start_idx > 0:
            eligible_steps = eligible_steps[start_idx:] + eligible_steps[:start_idx]

    # Re-assign continuous order indices
    ordered_steps = [
        step.model_copy(update={"order": idx}) for idx, step in enumerate(eligible_steps)
    ]
    return tuple(ordered_steps)


def get_step_by_id(step_id: str) -> TourStep | None:
    """Look up a step by its id."""
    for step in TOUR_STEPS:
        if step.id == step_id:
            return step
    return None


def get_step_by_route(route: str) -> TourStep | None:
    """Look up the first step matching a route."""
    for step in TOUR_STEPS:
        if step.route == route:
            return step
    return None


__all__ = [
    "STEP_CAPABILITY_MAP",
    "TOUR_STEPS",
    "get_dynamic_tour_steps",
    "get_step_by_id",
    "get_step_by_route",
    "get_tour_steps",
]
