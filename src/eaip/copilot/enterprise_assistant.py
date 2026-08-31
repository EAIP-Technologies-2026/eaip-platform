"""Enterprise Assistant Service — Phase 5 role-aware assistant orchestration.

Composes the authoritative A1004 grounded intelligence, A1007 operational
intelligence, A1006 guided tour engine, A1005 governed action executor, the
Phase 5 role-aware context builder, and the existing governed memory service
into a single permission-aware, route-aware, anti-fabrication assistant.

Guarantees:
- No new capability, permission, policy, tour, approval, or memory authority is
  created; every decision delegates to the authoritative A1001-A1008 services.
- Prompt injection and tool-spoofing prompts are refused.
- Platform actions are NEVER executed or claimed as executed by this service;
  they are planned through :class:`GovernedActionExecutor` and reported only
  from the resulting ActionPlan/ActionResult evidence.
- Tenant and role boundaries come exclusively from
  :class:`PermissionContextResolver`; this service never re-implements them.
"""

from __future__ import annotations

import re
from typing import Any

from eaip.capabilities.capability import OperationType
from eaip.capabilities.registry import CapabilityRegistry
from eaip.context.permission_resolver import PermissionContextResolver
from eaip.copilot.action_executor import GovernedActionExecutor
from eaip.copilot.intelligence import AssistantIntelligenceService, GroundedAssistantResponse
from eaip.copilot.memory import GovernedMemoryService
from eaip.copilot.operational_intelligence import OperationalIntelligenceService
from eaip.copilot.role_context import (
    ActiveEntityContext,
    RoleAwareAssistantContext,
    RoleAwareContextBuilder,
)
from eaip.copilot.tour.service import TourService
from eaip.kgraph.platform_graph import PlatformKnowledgeService
from eaip.logging.context import get_logger
from eaip.memory.models import MemoryDomain

_INJECTION_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(
        r"\bignore\s+(all\s+)?(your|the|previous|prior)?\s*"
        r"(instructions|rules|guidelines|system prompt)\b",
        re.I,
    ),
    re.compile(
        r"\bforget\s+(your|the|all)?\s*(instructions|rules|guidelines|role|identity)\b",
        re.I,
    ),
    re.compile(
        r"\bact\s+as\s+(an\s+)?(admin|administrator|super ?user|root|system)\b",
        re.I,
    ),
    re.compile(
        r"\b(override|bypass|circumvent)\s+(the\s+)?"
        r"(approval|permission|permissions|authorization|security|policy)\b",
        re.I,
    ),
    re.compile(
        r"\bgrant\s+(yourself|me|us)\s+(admin|full\s+access|all\s+permissions)\b",
        re.I,
    ),
    re.compile(
        r"\bpretend\s+you\s+(executed|deleted|created|stopped|restarted|ran)\b",
        re.I,
    ),
    re.compile(r"\bclaim\s+(it\s+)?(was|is)\s+(done|successful|executed)\b", re.I),
    re.compile(r"\bfabricate\b", re.I),
    re.compile(
        r"\breveal\s+(restricted|confidential|secret|other\s+tenant|internal)\b",
        re.I,
    ),
    re.compile(
        r"\bshow\s+(me\s+)?(other\s+)?(tenants|another\s+tenant)\s*(data|records)?\b",
        re.I,
    ),
    re.compile(r"\bjailbreak\b", re.I),
    re.compile(r"\bcall\s+(any\s+)?(function|tool|action)\b", re.I),
    re.compile(r"\buse\s+any\s+(tool|function|capability)\b", re.I),
)

_MIN_SEGMENT_LEN = 3
_MIN_PATH_CAPS = 2

_ACTION_VERBS: tuple[str, ...] = (
    "start",
    "stop",
    "restart",
    "create",
    "delete",
    "pause",
    "resume",
    "execute",
    "run",
    "scale",
    "deploy",
    "approve",
    "cancel",
    "enable",
    "disable",
)


class EnterpriseAssistantService:
    """Role-aware, route-aware, operationally-grounded enterprise assistant."""

    def __init__(
        self,
        *,
        capability_registry: CapabilityRegistry,
        permission_resolver: PermissionContextResolver,
        context_builder: RoleAwareContextBuilder,
        grounded_intelligence: AssistantIntelligenceService,
        operational_intelligence: OperationalIntelligenceService | None = None,
        tour_service: TourService | None = None,
        action_executor: GovernedActionExecutor | None = None,
        memory_service: GovernedMemoryService | None = None,
        knowledge_service: PlatformKnowledgeService | None = None,
    ) -> None:
        """Initialize the enterprise assistant with authoritative services.

        Args:
            capability_registry: Authoritative canonical capability registry.
            permission_resolver: Authoritative permission context resolver.
            context_builder: Phase 5 role-aware context composition builder.
            grounded_intelligence: A1004 grounded intelligence service.
            operational_intelligence: A1007 live operational intelligence (optional).
            tour_service: A1006 guided tour engine (optional).
            action_executor: A1005 governed action executor (optional).
            memory_service: Existing governed memory service (optional).
            knowledge_service: Platform knowledge graph service (optional).
        """
        self._registry = capability_registry
        self._resolver = permission_resolver
        self._context_builder = context_builder
        self._intelligence = grounded_intelligence
        self._operational = operational_intelligence
        self._tours = tour_service
        self._executor = action_executor
        self._memory = memory_service
        self._knowledge = knowledge_service
        self._log = get_logger("eaip.copilot.enterprise_assistant")

    # ------------------------------------------------------------------ #
    # Security guard
    # ------------------------------------------------------------------ #
    def detect_injection(self, message: str) -> str | None:
        """Return the matched injection pattern description, or None when safe."""
        for pattern in _INJECTION_PATTERNS:
            if pattern.search(message):
                return pattern.pattern
        return None

    def _injection_refusal(
        self, user: dict[str, Any], current_route: str, matched: str
    ) -> GroundedAssistantResponse:
        user_id = str(user.get("user_id") or user.get("id") or "anonymous")
        tenant_id = str(user.get("tenant_id") or "default")
        self._log.warning(
            "Prompt injection refused",
            extra={"user_id": user_id, "pattern": matched},
        )
        return GroundedAssistantResponse(
            reply=(
                "I cannot comply with that request. It appears to attempt to override EAIP's "
                "permission boundaries, approval gates, or grounding controls. Your access "
                "is strictly limited to what your role permits, and I never fabricate execution "
                "results.\n\n"
                "Ask me what you *can* do instead — I will describe exactly what your role "
                "authorizes."
            ),
            grounded_capability=None,
            sources=(),
            suggested_actions=("What can I do here?", "What requires approval?"),
            confidence=1.0,
            is_uncertain=False,
            current_route=current_route,
            user_id=user_id,
            tenant_id=tenant_id,
        )

    # ------------------------------------------------------------------ #
    # Query classifiers
    # ------------------------------------------------------------------ #
    def _is_tour_command(self, text: str) -> bool:
        patterns = [
            r"^start (the )?(guided )?tour",
            r"^begin (the )?(guided )?tour",
            r"^show me (the )?(guided )?tour",
            r"^start (the )?onboarding",
            r"^(next|continue|advance) (the )?tour",
            r"^next (step|capability)",
            r"^what('s| is) (the )?next (step|capability)",
        ]
        return any(re.search(p, text) for p in patterns)

    def _is_self_knowledge_assistant(self, text: str) -> bool:
        patterns = [
            r"what can you (do|help (me )?with)",
            r"what are your capabilities",
            r"what (tools|skills|abilities) do you have",
            r"how can you help (me )?",
            r"what do you do",
            r"^help$",
        ]
        return any(re.search(p, text) for p in patterns)

    def _is_self_knowledge_user(self, text: str) -> bool:
        patterns = [
            r"what can i do",
            r"what (capabilities|permissions|access) do i have",
            r"what (am i|do i) (allowed|authorized) to",
            r"what can i access",
        ]
        return any(re.search(p, text) for p in patterns)

    def _is_why_cannot(self, text: str) -> bool:
        patterns = [
            r"why (can'?t|can not|can't) i",
            r"why (is|are) (this|it|that|the [a-z ]+) (restricted|blocked|denied|disabled)",
            r"why (do i not have|am i not allowed)",
        ]
        return any(re.search(p, text) for p in patterns)

    def _is_requires_approval(self, text: str) -> bool:
        patterns = [
            r"what (requires|needs|needed) (human )?approval",
            r"which (actions|operations|capabilities) (require|need) approval",
            r"what (needs|must|has to) be approved",
        ]
        return any(re.search(p, text) for p in patterns)

    def _is_operations_available(self, text: str) -> bool:
        patterns = [
            r"what operations (are available|can i perform|can i run|may i run)",
            r"what (actions|operations) (can|may) i take",
            r"what (operations|actions) (are|is) available for",
            r"what can i do here",
            r"what is available here",
        ]
        return any(re.search(p, text) for p in patterns)

    def _is_consequence_query(self, text: str) -> bool:
        patterns = [
            r"what happens if (i|we) (cancel|restart|pause|delete|stop|run)",
            r"what (is|are) the (consequences|impact|effects) of "
            r"(cancelling|restarting|pausing|deleting)",
            r"what happens if this (fails|is cancelled|is stopped)",
        ]
        return any(re.search(p, text) for p in patterns)

    def _is_platform_entities(self, text: str) -> bool:
        patterns = [
            r"what (systems|entities|services|components|capabilities|apis|events|routes) "
            r"(are|is) (connected|related) to",
            r"what (systems|entities|services|components|capabilities|apis|events|routes) "
            r"(does|do|are|is|power|expose)",
            r"what (does|do|is) [a-z0-9_.-]+ (depend on|touch|use|emit|expose)",
            r"what (is|are) connected to (this|it)",
            r"what depends on (this|it|[a-z0-9_.-]+)",
            r"what (could|can|might) be affected if",
            r"which (services|apis|events|workflows|capabilities) (does|do|are|power|expose)",
            r"which api (powers|exposes)",
            r"what events (does|are|is) (this|it|[a-z0-9_.-]+) emit",
            r"show me the topology",
            r"topology (around|of|for)",
            r"how does (this|it|[a-z0-9_.-]+) work internally",
            r"how (does|do) [a-z0-9_.-]+ connect to [a-z0-9_.-]+",
            r"what documentation explains",
            r"where can i learn more",
            r"what is eaip('s)? architecture",
            r"platform architecture",
        ]
        return any(re.search(p, text) for p in patterns)

    def _is_action_intent(
        self,
        text: str,
        _current_route: str = "/",
        _entity_type: str | None = None,
    ) -> bool:
        if (
            self._is_consequence_query(text)
            or self._is_why_cannot(text)
            or self._is_operations_available(text)
        ):
            return False
        return any(re.search(rf"\b{verb}\b", text, re.I) for verb in _ACTION_VERBS)

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #
    def _cap_titles(self, names: tuple[str, ...]) -> list[str]:
        titles = []
        for n in names:
            cap = self._registry.try_get(n)
            titles.append(f"**{cap.title if cap else n}**")
        return titles

    def _match_capability_in_text(  # noqa: PLR0911
        self,
        text: str,
        current_route: str = "/",
        entity_type: str | None = None,
    ) -> str | None:
        text_lower = text.lower()
        if (
            "approv" in text_lower
            or "reject" in text_lower
            or bool(re.search(r"appr-[a-zA-Z0-9_-]+", text_lower))
        ):
            return "eaip.operations"

        for cap in self._registry.all():
            if cap.name.lower() in text_lower:
                return cap.name
            title = cap.title.lower()
            if title and title in text_lower:
                return cap.name
            last_segment = cap.name.rsplit(".", 1)[-1]
            if last_segment in text_lower:
                return cap.name
            singular = last_segment.rstrip("s")
            if singular and len(singular) > _MIN_SEGMENT_LEN and singular in text_lower:
                return cap.name

        # Contextual match: "this", "it", "here", "current"
        if any(w in text_lower for w in ("this", "it", "here", "current", "selected")):
            if entity_type:
                for cap in self._registry.all():
                    if entity_type in cap.name.lower() or entity_type in cap.title.lower():
                        return cap.name
            if current_route and current_route != "/":
                route_matches = self._registry.find_by_route(current_route)
                if route_matches:
                    return route_matches[0].name
        return None

    def _response(
        self,
        reply: str,
        user: dict[str, Any],
        current_route: str,
        *,
        capability: str | None = None,
        sources: tuple[str, ...] = (),
        suggestions: tuple[str, ...] = (),
        confidence: float = 1.0,
        uncertain: bool = False,
    ) -> GroundedAssistantResponse:
        return GroundedAssistantResponse(
            reply=reply,
            grounded_capability=capability,
            sources=sources,
            suggested_actions=suggestions,
            confidence=confidence,
            is_uncertain=uncertain,
            current_route=current_route,
            user_id=str(user.get("user_id") or user.get("id") or "anonymous"),
            tenant_id=str(user.get("tenant_id") or "default"),
        )

    # ------------------------------------------------------------------ #
    # Self-knowledge handlers (grounded in the composed context)
    # ------------------------------------------------------------------ #
    def _handle_assistant_self_knowledge(
        self, ctx: RoleAwareAssistantContext, user: dict[str, Any], current_route: str
    ) -> GroundedAssistantResponse:
        lines = [
            "### What I can do for you",
            "",
            "I am the EAIP Enterprise Assistant. My capabilities are grounded in the platform "
            "registry and limited by your exact role permissions:",
            "",
            f"- **Explore** — I can answer questions about any of your "
            f"**{len(ctx.visible_capabilities)} visible capabilities**.",
            f"- **Operate** — you can act on **{len(ctx.executable_capabilities)} executable "
            f"capabilities**; I plan those actions and they pass through approval gates.",
            "- **Observe** — I can report live operational telemetry (system health, agents, "
            "workflows, recent incidents) with freshness markers.",
            "- **Guide** — I can start a guided tour personalized to your permissions.",
            "- **Remember** — I retain bounded, scoped memory within your tenant only.",
            "",
        ]
        if ctx.current_capabilities:
            lines.append(
                "Right now you are on a route tied to "
                + ", ".join(self._cap_titles(ctx.current_capabilities))
                + "."
            )
        else:
            lines.append("This route is not mapped to a specific capability.")
        lines.append("")
        lines.append("Ask me *\"What can I do here?\"* to see your actions on this page.")
        return self._response(
            "\n".join(lines), user, current_route,
            suggestions=(
                "What can I do here?",
                "What capabilities do I have?",
                "What requires approval?",
            ),
        )

    def _handle_user_self_knowledge(
        self, ctx: RoleAwareAssistantContext, user: dict[str, Any], current_route: str
    ) -> GroundedAssistantResponse:
        lines = [
            f"### Your authorized access ({', '.join(ctx.roles) or 'no roles'})",
            "",
            f"- **Visible capabilities:** {len(ctx.visible_capabilities)}",
            f"- **Executable capabilities:** {len(ctx.executable_capabilities)}",
            f"- **Readable capabilities:** {len(ctx.readable_capabilities)}",
            f"- **Mutable capabilities:** {len(ctx.mutable_capabilities)}",
            f"- **Restricted capabilities:** {len(ctx.restricted_capabilities)}",
            "",
        ]
        if ctx.executable_capabilities:
            lines.append("You can operate on:")
            lines.extend(f"- {t}" for t in self._cap_titles(ctx.executable_capabilities))
            lines.append("")
        if ctx.approval_required_capabilities:
            lines.append("The following capabilities require approval for their actions:")
            lines.extend(f"- {t}" for t in self._cap_titles(ctx.approval_required_capabilities))
            lines.append("")
        if ctx.restricted_capabilities:
            lines.append(
                f"{len(ctx.restricted_capabilities)} capabilities are restricted from your "
                "role and will not be described."
            )
        return self._response(
            "\n".join(lines), user, current_route,
            suggestions=(
                "What can I do here?",
                "What requires approval?",
                "Why can't I access agents?",
            ),
        )

    def _handle_why_cannot(
        self, ctx: RoleAwareAssistantContext, user: dict[str, Any], current_route: str, text: str
    ) -> GroundedAssistantResponse:
        matched = self._match_capability_in_text(text)
        if matched is None:
            for name in ctx.restricted_capabilities:
                if name.split(".")[-1] in text.lower() or name in text.lower():
                    matched = name
                    break
        if matched is None:
            return self._response(
                "I could not identify a specific capability you are asking about. "
                "Tell me which capability (e.g. *Agents*, *Workflows*, *Marketplace*) "
                "so I can check why access is limited.",
                user, current_route, uncertain=True,
            )
        access = ctx.permission_aware.get_access(matched)
        cap = self._registry.try_get(matched)
        title = cap.title if cap else matched
        if access is None or access.restricted:
            reply = (
                f"**{title}** is restricted for your role. Your role "
                f"({', '.join(ctx.roles) or 'none'}) does not include visibility into that "
                "capability, so I cannot describe or operate on it."
            )
        elif not access.visible:
            reply = (
                f"**{title}** is not visible to your role, so it does not appear in your "
                "navigation or search."
            )
        elif access.approval_required and not access.executable:
            reply = (
                f"**{title}** is visible and readable to you, but taking action on it requires "
                "human approval. I can plan the action and submit it for approval if you want."
            )
        elif not access.executable:
            reply = (
                f"**{title}** is visible and readable to you, but your role does not grant "
                "execution rights for its operations."
            )
        else:
            reply = (
                f"You *do* have access to **{title}**. If something appears blocked, it may "
                "be a specific operation requiring approval rather than the capability itself."
            )
        return self._response(reply, user, current_route, capability=matched)

    def _handle_requires_approval(
        self, ctx: RoleAwareAssistantContext, user: dict[str, Any], current_route: str
    ) -> GroundedAssistantResponse:
        if not ctx.approval_required_capabilities:
            return self._response(
                "No actions are approval-gated for your role. Everything you can execute is "
                "authorized directly.",
                user, current_route,
            )
        lines = [
            "### Actions requiring human approval",
            "",
            "The following capabilities have approval gates on their actions. I will plan the "
            "action and route it to the approval queue — I will never bypass that gate:",
            "",
        ]
        lines.extend(f"- {t}" for t in self._cap_titles(ctx.approval_required_capabilities))
        lines.append("")
        lines.append("You can ask e.g. *\"restart the workflow\"* and I will prepare the plan.")
        return self._response("\n".join(lines), user, current_route,
                              suggestions=("What can I do here?", "What actions can I take?"))

    def _handle_operations_available(
        self,
        ctx: RoleAwareAssistantContext,
        user: dict[str, Any],
        current_route: str,
        text: str = "",
    ) -> GroundedAssistantResponse:
        text_lower = text.lower()
        matched = self._match_capability_in_text(text, current_route, ctx.active_entity.entity_type)
        if matched and ("available for" in text_lower or "operations for" in text_lower):
            cap = self._registry.try_get(matched)
            cap_title = cap.title if cap else matched
            access = ctx.permission_aware.get_access(matched)
            ops = access.effective_operations if access else ()
            op_strs = [op.value for op in ops] if ops else ["none"]
            appr = "yes" if access and access.approval_required else "no"
            vis = "yes" if access and access.visible else "no"
            return self._response(
                f"### Operations available for {cap_title}\n\n"
                f"- **Capability ID:** `{matched}`\n"
                f"- **Visible:** {vis}\n"
                f"- **Authorized Operations:** {', '.join(sorted(op_strs))}\n"
                f"- **Approval Required:** {appr}\n",
                user, current_route, capability=matched,
            )

        route_caps = ctx.current_capabilities
        lines = ["### Operations available here", ""]
        if not route_caps:
            lines.append("This route is not mapped to a platform capability.")
        else:
            for name in route_caps:
                cap = self._registry.try_get(name)
                lines.append(f"- **{cap.title if cap else name}**")
                access = ctx.permission_aware.get_access(name)
                ops = access.effective_operations if access else ()
                if ops:
                    lines.append(f"  - Operations: {', '.join(sorted(op.value for op in ops))}")
                appr = "yes" if access and access.approval_required else "no"
                lines.append(f"  - Requires approval: {appr}")
                if access is None or not access.visible:
                    lines.append("  - Restricted from your role")
        lines.append("")
        if ctx.available_actions:
            lines.append(
                f"Across your executable capabilities you have "
                f"**{len(ctx.available_actions)} authorized operations** available."
            )
        else:
            lines.append("You have no executable operations from this route.")
        return self._response("\n".join(lines), user, current_route)

    async def _handle_consequences(
        self, ctx: RoleAwareAssistantContext, user: dict[str, Any], current_route: str, text: str
    ) -> GroundedAssistantResponse:
        matched = self._match_capability_in_text(text, current_route, ctx.active_entity.entity_type)
        if matched is None:
            matched = ctx.current_capabilities[0] if ctx.current_capabilities else "eaip.workflows"
        cap = self._registry.try_get(matched)
        cap_title = cap.title if cap else matched

        op = "cancel"
        text_lower = text.lower()
        if "restart" in text_lower:
            op = "restart"
        elif "delete" in text_lower:
            op = "delete"
        elif "pause" in text_lower:
            op = "pause"

        risk = "DESTRUCTIVE" if op in ("cancel", "delete") else "ACTION"
        approval = "Mandatory Human Approval" if risk == "DESTRUCTIVE" else "Conditional"
        reversibility = "Non-reversible" if op in ("cancel", "delete") else "Reversible"

        lines = [
            f"### Consequence Analysis: {op.upper()} on {cap_title}",
            "",
            f"- **Target Capability:** {cap_title} (`{matched}`)",
            f"- **Operation:** {op.upper()}",
            f"- **Risk Classification:** `{risk}`",
            f"- **Reversibility:** `{reversibility}`",
            f"- **Approval Policy:** `{approval}`",
            "",
        ]
        if self._knowledge is not None:
            dependents = await self._knowledge.get_dependents(
                matched, context=ctx.permission_aware
            )
            if dependents:
                dep_names = ", ".join(f"`{d.name}`" for d in dependents[:6])
                lines.append(f"**Downstream Systems Impacted:**\n{dep_names}\n")
        lines.append(
            f"Performing `{op}` will immediately halt active execution steps and emit an immutable "
            "audit event. Because this operation carries operational risk, it cannot execute "
            "without required governance gates."
        )
        return self._response("\n".join(lines), user, current_route, capability=matched)

    def _handle_architecture_overview(
        self, ctx: RoleAwareAssistantContext, user: dict[str, Any], current_route: str
    ) -> GroundedAssistantResponse:
        visible_caps = ctx.visible_capabilities
        lines = [
            "### EAIP Platform Architecture Overview",
            "",
            "EAIP is structured into autonomous execution domains, governance layers, "
            "and intelligence surfaces:",
            "",
            f"- **Active Visible Capabilities:** {len(visible_caps)} capabilities "
            "authorized for your role.",
            "- **Execution Core:** Autonomous Agents (`eaip.agents`), "
            "Workflows (`eaip.workflows`), Multi-Agent Missions (`eaip.missions`), "
            "Cognitive Brains (`eaip.brains`).",
            "- **Governance & Control:** Policy Engine (`eaip.policy`), "
            "Governed Action Executor, Memory System (`eaip.memory`), "
            "Audit Logging (`eaip.security.audit`).",
            "- **Operational Intelligence:** Live Metrics, Telemetry & Monitoring, "
            "Platform Knowledge Graph.",
            "- **User Interfaces:** Enterprise Console, Mission Control, Mobile, "
            "Operational Conductor.",
            "",
            "Ask about any specific capability or entity (e.g. *\"What services power Agents?\"*) "
            "for deep topology.",
        ]
        return self._response(
            "\n".join(lines), user, current_route,
            suggestions=("What is connected to agents?", "What depends on workflows?"),
        )

    async def _handle_capability_path(
        self, ctx: RoleAwareAssistantContext, user: dict[str, Any], current_route: str, text: str
    ) -> GroundedAssistantResponse | None:
        if self._knowledge is None:
            return None
        all_caps = self._registry.all()
        found: list[str] = []
        for cap in all_caps:
            last = cap.name.rsplit(".", 1)[-1].lower()
            title_lower = cap.title.lower() if cap.title else ""
            has_title = bool(title_lower) and title_lower in text
            matched_name = last in text or cap.name.lower() in text or has_title
            if matched_name and cap.name not in found:
                found.append(cap.name)
        if len(found) >= _MIN_PATH_CAPS:
            c1, c2 = found[0], found[1]
            if not ctx.permission_aware.can_see(c1) or not ctx.permission_aware.can_see(c2):
                return self._response(
                    "One or more requested capabilities are restricted from your role.",
                    user, current_route,
                )
            path_nodes = await self._knowledge.find_path(c1, c2, context=ctx.permission_aware)
            if not path_nodes:
                return self._response(
                    f"No direct relationship path found between **{c1}** and **{c2}** "
                    "in the knowledge graph.",
                    user, current_route,
                )
            rendered_path = " -> ".join(f"`{n}`" for n in path_nodes)
            return self._response(
                f"### Connection between {c1} and {c2}\n\n"
                f"**Path in Knowledge Graph:**\n{rendered_path}",
                user, current_route,
                sources=(f"cap:{c1}", f"cap:{c2}"),
            )
        return None

    async def _handle_platform_entities(  # noqa: PLR0911, PLR0912, PLR0915
        self, ctx: RoleAwareAssistantContext, user: dict[str, Any], current_route: str, text: str
    ) -> GroundedAssistantResponse:
        text_lower = text.lower()

        if "architecture" in text_lower or "high level" in text_lower:
            return self._handle_architecture_overview(ctx, user, current_route)

        if "connect to" in text_lower or "relationship between" in text_lower:
            path_resp = await self._handle_capability_path(ctx, user, current_route, text_lower)
            if path_resp is not None:
                return path_resp

        matched = self._match_capability_in_text(
            text,
            current_route=current_route,
            entity_type=ctx.active_entity.entity_type,
        )
        if matched is None:
            if ctx.current_capabilities:
                matched = ctx.current_capabilities[0]
            elif ctx.active_entity.entity_type:
                type_map = {
                    "agent": "eaip.agents",
                    "agents": "eaip.agents",
                    "workflow": "eaip.workflows",
                    "workflows": "eaip.workflows",
                    "brain": "eaip.brains",
                    "brains": "eaip.brains",
                    "mission": "eaip.missions",
                    "missions": "eaip.missions",
                }
                matched = type_map.get(ctx.active_entity.entity_type.lower())

        if matched is None:
            return self._response(
                "I need a specific capability or entity to describe its connected systems.",
                user, current_route, uncertain=True,
            )

        access = ctx.permission_aware.get_access(matched)
        if access is None or not access.visible:
            cap = self._registry.try_get(matched)
            return self._response(
                f"**{cap.title if cap else matched}** is restricted from your role, so I cannot "
                "describe its connected systems.",
                user, current_route, capability=matched,
            )

        if self._knowledge is None:
            return self._response(
                "The platform knowledge graph is not connected in this build, so I cannot list "
                "connected systems right now.",
                user, current_route, uncertain=True,
            )

        cap_obj = self._registry.try_get(matched)
        cap_title = cap_obj.title if cap_obj else matched

        # 1. Dependents / Impact analysis
        dep_words = ("depend on this", "depends on", "affected if", "impact of", "dependents")
        if any(w in text_lower for w in dep_words):
            dependents = await self._knowledge.get_dependents(
                matched, context=ctx.permission_aware
            )
            if not dependents:
                return self._response(
                    f"No downstream capabilities or entities depend on **{cap_title}** "
                    "according to the platform knowledge graph.",
                    user, current_route, capability=matched,
                )
            names = ", ".join(f"`{d.name}`" for d in dependents[:8])
            return self._response(
                f"### Downstream dependencies for {cap_title}\n\n"
                f"The following visible systems depend on or connect to **{cap_title}**:\n"
                f"- {names}\n\n"
                f"If **{cap_title}** is modified, these systems may be impacted.",
                user, current_route, capability=matched, sources=(f"cap:{matched}",),
            )

        # 2. Services query
        if "service" in text_lower:
            services = await self._knowledge.get_related_services(
                matched, context=ctx.permission_aware
            )
            if not services:
                return self._response(
                    f"No specific background services are registered for **{cap_title}** "
                    "in the knowledge graph.",
                    user, current_route, capability=matched,
                )
            svc_names = ", ".join(f"**{s.name}**" for s in services)
            return self._response(
                f"### Services powering {cap_title}\n\n"
                f"**{cap_title}** is powered by the following platform service(s):\n- {svc_names}",
                user, current_route, capability=matched, sources=(f"cap:{matched}",),
            )

        # 3. API query
        if "api" in text_lower:
            apis = await self._knowledge.get_related_apis(matched, context=ctx.permission_aware)
            if not apis:
                return self._response(
                    f"No API operations are registered for **{cap_title}** in the knowledge graph.",
                    user, current_route, capability=matched,
                )
            api_list = "\n".join(f"- `{a.name}`" for a in apis[:10])
            return self._response(
                f"### APIs exposing {cap_title}\n\n"
                f"The following API operations power **{cap_title}**:\n{api_list}",
                user, current_route, capability=matched, sources=(f"cap:{matched}",),
            )

        # 4. Events query
        if "event" in text_lower or "emit" in text_lower:
            events = await self._knowledge.get_related_events(
                matched, context=ctx.permission_aware
            )
            if not events:
                return self._response(
                    f"No domain events are registered for **{cap_title}** in the knowledge graph.",
                    user, current_route, capability=matched,
                )
            event_list = "\n".join(f"- `{e.name}`" for e in events[:10])
            return self._response(
                f"### Domain events emitted by {cap_title}\n\n"
                f"The following events are emitted by **{cap_title}**:\n{event_list}",
                user, current_route, capability=matched, sources=(f"cap:{matched}",),
            )

        # 5. Documentation query
        if any(w in text_lower for w in ("documentation", "docs", "learn more")):
            docs = await self._knowledge.get_related_documentation(
                matched, context=ctx.permission_aware
            )
            if not docs:
                return self._response(
                    f"No documentation references are registered for **{cap_title}** "
                    "in the knowledge graph.",
                    user, current_route, capability=matched,
                )
            doc_list = "\n".join(
                f"- [{d.name}]({d.description})" if d.description else f"- `{d.name}`"
                for d in docs
            )
            return self._response(
                f"### Documentation for {cap_title}\n\n{doc_list}",
                user, current_route, capability=matched, sources=(f"cap:{matched}",),
            )

        # 6. Related Workflows / Capabilities query
        rel_words = ("workflow", "related capabilit", "related to the current")
        if any(w in text_lower for w in rel_words):
            related = await self._knowledge.get_related_capabilities(
                matched, context=ctx.permission_aware
            )
            if not related:
                return self._response(
                    f"No other capabilities are directly linked to **{cap_title}** "
                    "in your visible scope.",
                    user, current_route, capability=matched,
                )
            rel_list = "\n".join(
                f"- **{r.name}** (`{r.id.removeprefix('cap:')}`)" for r in related[:8]
            )
            return self._response(
                f"### Capabilities related to {cap_title}\n\n{rel_list}",
                user, current_route, capability=matched, sources=(f"cap:{matched}",),
            )

        # 7. Default: Full Connected Systems / Topology
        topology = await self._knowledge.get_capability_topology(
            matched, context=ctx.permission_aware
        )
        if "error" in topology:
            return self._response(
                f"No topology found for **{cap_title}** in the platform graph.",
                user, current_route, uncertain=True,
            )

        lines = [f"### Systems connected to {cap_title}", ""]
        if cap_obj and cap_obj.description:
            lines.append(f"*{cap_obj.description}*")
            lines.append("")

        for key, label in (
            ("services", "Services"),
            ("dependencies", "Connected Capabilities"),
            ("entities", "Domain Entities"),
            ("routes", "Routes"),
            ("apis", "APIs"),
            ("events", "Events"),
            ("documentation", "Documentation"),
        ):
            items = topology.get(key) or ()
            if items:
                names = ", ".join(getattr(i, "name", str(i)) for i in items[:8])
                lines.append(f"- **{label}:** {names}")
        lines.append("")
        lines.append(f"Sources: `cap:{matched}`")
        return self._response("\n".join(lines), user, current_route, capability=matched)

    # ------------------------------------------------------------------ #
    # Governed action planning & execution (never fabrication)
    # ------------------------------------------------------------------ #
    async def _handle_action_intent(  # noqa: PLR0911, PLR0912, PLR0915
        self,
        text: str,
        user: dict[str, Any],
        current_route: str,
        entity_context: ActiveEntityContext | dict[str, Any] | None = None,
    ) -> GroundedAssistantResponse:
        ent_type: str | None = None
        ent_id: str | None = None
        if isinstance(entity_context, ActiveEntityContext):
            ent_type = entity_context.entity_type
            ent_id = entity_context.entity_id
        elif isinstance(entity_context, dict):
            ent_type = entity_context.get("entity_type")
            ent_id = entity_context.get("entity_id")

        text_lower = text.lower()

        # 1. Governance decision (approve / reject)
        if any(w in text_lower for w in ("approve", "reject")):
            is_approve = "approve" in text_lower
            matched_appr = re.search(r"\b(appr-[a-zA-Z0-9_-]+)\b", text)
            appr_id = (
                matched_appr.group(1)
                if matched_appr
                else (ent_id if ent_id and ent_id.startswith("appr-") else None)
            )

            ctx = await self._context_builder.build(
                user, current_route, entity_context=entity_context
            )
            can_govern = ctx.permission_aware.can_act(
                "eaip.operations"
            ) or ctx.permission_aware.can_act("eaip.administration")
            if not can_govern:
                return self._response(
                    f"Your role ({', '.join(ctx.roles) or 'none'}) is not authorized to "
                    "approve or reject actions. This operation requires governance permissions.",
                    user, current_route, capability="eaip.operations",
                )
            if self._executor is None:
                return self._response(
                    "Governed action execution is not connected in this build.",
                    user, current_route, uncertain=True,
                )
            if appr_id is None and hasattr(self._executor._approvals, "list_pending"):
                pending = self._executor._approvals.list_pending()
                if pending:
                    appr_id = pending[0].id
            if appr_id is None:
                return self._response(
                    "Please specify the approval request ID (e.g. `appr-12345`) to decide on.",
                    user, current_route, uncertain=True,
                )

            tool_name = "approve_action" if is_approve else "reject_action"
            plan = await self._executor.plan_action(
                intent=text,
                user=user,
                capability_name="eaip.operations",
                operation=OperationType.UPDATE,
                tool_name=tool_name,
                target_id=appr_id,
            )
            result = await self._executor.execute_action(plan, user, approved=True)
            action_word = "approved" if is_approve else "rejected"
            return self._response(
                f"### Action Approval Resolved\n\n"
                f"Approval request `{appr_id}` has been **{action_word}** by "
                f"`{user.get('user_id', 'operator')}`.\n\n"
                f"- **Status:** `{result.status}`\n"
                f"- **Audit Entry:** `{result.audit_entry_id or 'none'}`",
                user, current_route, capability="eaip.operations",
            )

        # 2. Target entity ID resolution
        for pattern in (
            r"\b(ag-[a-zA-Z0-9_-]+)\b",
            r"\b(wf-[a-zA-Z0-9_-]+)\b",
            r"\b(ms-[a-zA-Z0-9_-]+)\b",
            r"\b(br-[a-zA-Z0-9_-]+)\b",
        ):
            m = re.search(pattern, text)
            if m:
                ent_id = m.group(1)
                break

        matched = self._match_capability_in_text(text, current_route, ent_type)
        if matched is None:
            return self._response(
                "I can plan governed actions for you. Tell me the target capability (e.g. "
                "*Agents*, *Workflows*) and the operation (start, stop, restart, create, "
                "delete, pause, resume).",
                user, current_route, uncertain=True,
            )

        ctx = await self._context_builder.build(
            user, current_route, entity_context=entity_context
        )
        if not ctx.permission_aware.can_act(matched):
            cap = self._registry.try_get(matched)
            role_desc = ", ".join(ctx.roles) or "none"
            return self._response(
                f"Your role ({role_desc}) is not authorized to execute actions on "
                f"**{cap.title if cap else matched}**. I cannot plan or perform that action.",
                user, current_route, capability=matched,
            )

        if self._executor is None:
            return self._response(
                f"I can see you are authorized to act on **{matched}**, but governed execution "
                "is not connected in this build. No action was taken.",
                user, current_route, capability=matched, uncertain=True,
            )

        # Determine operation type
        op_type = OperationType.EXECUTE
        if "cancel" in text_lower or "stop" in text_lower:
            op_type = OperationType.CANCEL
        elif "pause" in text_lower:
            op_type = OperationType.PAUSE
        elif "resume" in text_lower:
            op_type = OperationType.RESUME
        elif "delete" in text_lower:
            op_type = OperationType.DELETE
        elif "create" in text_lower or "deploy" in text_lower:
            op_type = OperationType.CREATE
        elif "restart" in text_lower or "start" in text_lower or "run" in text_lower:
            op_type = OperationType.EXECUTE

        plan = await self._executor.plan_action(
            intent=text,
            user=user,
            capability_name=matched,
            operation=op_type,
            target_id=ent_id,
            target_entity_type=ent_type,
        )

        if plan.requires_approval:
            exec_res = await self._executor.execute_action(plan, user, approved=False)
            reply = (
                f"### Action plan prepared — approval required\n\n"
                f"**{plan.preview}**\n\n"
                f"This action is gated behind human approval. I have submitted it to the "
                f"approval queue (plan `{plan.plan_id}`, "
                f"approval request `{exec_res.approval_id}`). "
                f"It will **not** execute until approved."
            )
        else:
            reply = (
                f"### Action plan prepared\n\n"
                f"**{plan.preview}**\n\n"
                f"Plan `{plan.plan_id}` is authorized (risk: {plan.risk_tier.value}). "
                f"No execution has occurred from this assistant turn — execute it through the "
                f"governed action channel to proceed."
            )
        return self._response(
            reply, user, current_route, capability=matched,
            suggestions=("What requires approval?", "What can I do here?")
        )

    # ------------------------------------------------------------------ #
    # Continuity (existing governed memory, never cross-tenant)
    # ------------------------------------------------------------------ #
    async def _recall_continuity(
        self, user: dict[str, Any], current_route: str
    ) -> list[str]:
        if self._memory is None:
            return []
        try:
            items = await self._memory.retrieve(
                user, query=current_route, limit=3
            )
        except Exception:  # pragma: no cover - defensive
            self._log.debug("Continuity recall skipped")
            return []
        return [i.content for i in items]

    async def _store_continuity(
        self, user: dict[str, Any], message: str, current_route: str
    ) -> None:
        if self._memory is None:
            return
        try:
            await self._memory.create(
                user,
                content=f"route={current_route}; asked: {message[:120]}",
                domain=MemoryDomain.CONVERSATION,
                importance=0.4,
                tags=("assistant", "continuity"),
            )
        except Exception:  # pragma: no cover - defensive
            self._log.debug("Continuity store skipped")

    # ------------------------------------------------------------------ #
    # Main entry point
    # ------------------------------------------------------------------ #
    async def answer(  # noqa: PLR0911, PLR0912
        self,
        message: str,
        user: dict[str, Any],
        current_route: str = "/",
        *,
        entity_context: ActiveEntityContext | dict[str, Any] | None = None,
    ) -> GroundedAssistantResponse:
        """Answer with full role-aware, route-aware, anti-fabrication behavior.

        Args:
            message: User query or prompt.
            user: Authenticated caller claims (user_id, tenant_id, roles).
            current_route: Active frontend route.
            entity_context: Optional active entity / view context.

        Returns:
            GroundedAssistantResponse grounded in authoritative platform data.
        """
        text = message.strip()
        if not text:
            return self._response(
                "Ask me anything about your platform — what you can do, what requires "
                "approval, live operational status, or how to navigate EAIP.",
                user, current_route, uncertain=True,
            )

        matched_injection = self.detect_injection(text)
        if matched_injection is not None:
            return self._injection_refusal(user, current_route, matched_injection)

        text_lower = text.lower()
        ent_type: str | None = None
        if isinstance(entity_context, ActiveEntityContext):
            ent_type = entity_context.entity_type
        elif isinstance(entity_context, dict):
            ent_type = entity_context.get("entity_type")

        # Tour commands -> A1006 guided tour engine.
        if self._is_tour_command(text_lower):
            if self._tours is None:
                return self._response(
                    "Guided tours are not connected in this build. You can still explore "
                    "capabilities by asking about them.",
                    user, current_route, uncertain=True,
                )
            ctx = await self._context_builder.build(
                user, current_route, entity_context=entity_context
            )
            tour = await self._tours.start_tour(
                user,
                permission_context=ctx.permission_aware,
                current_route=current_route,
            )
            reply = (
                f"### Guided tour started\n\n{tour.narration}\n\n"
                f"Tour session: `{tour.tour_session_id}` — "
                f"{tour.total_steps} steps personalized to your role."
            )
            return self._response(reply, user, current_route,
                                  sources=(f"tour:{tour.tour_session_id}",),
                                  suggestions=("Next step", "What can I do here?"))

        # Operational queries -> A1007 live intelligence.
        if self._operational is not None and self._operational.is_operational_query(text_lower):
            ctx = await self._context_builder.build(
                user, current_route, entity_context=entity_context
            )
            return await self._operational.answer_operational_query(
                text, ctx.identity, current_route
            )

        # Action intents -> A1005 governed planning and execution.
        if self._is_action_intent(text_lower, current_route, ent_type):
            return await self._handle_action_intent(
                text, user, current_route, entity_context=entity_context
            )

        ctx = await self._context_builder.build(
            user, current_route, entity_context=entity_context
        )
        continuity = await self._recall_continuity(user, current_route)

        # Self-knowledge, consequences, and platform queries.
        if self._is_self_knowledge_assistant(text_lower):
            result = self._handle_assistant_self_knowledge(ctx, user, current_route)
        elif self._is_self_knowledge_user(text_lower):
            result = self._handle_user_self_knowledge(ctx, user, current_route)
        elif self._is_why_cannot(text_lower):
            result = self._handle_why_cannot(ctx, user, current_route, text_lower)
        elif self._is_consequence_query(text_lower):
            result = await self._handle_consequences(ctx, user, current_route, text_lower)
        elif self._is_requires_approval(text_lower):
            result = self._handle_requires_approval(ctx, user, current_route)
        elif self._is_operations_available(text_lower):
            result = self._handle_operations_available(ctx, user, current_route, text_lower)
        elif self._is_platform_entities(text_lower):
            result = await self._handle_platform_entities(ctx, user, current_route, text_lower)
        else:
            # Delegate standard grounded Q&A to A1004.
            result = await self._intelligence.answer_grounded_query(
                text, user, current_route
            )

        await self._store_continuity(user, text, current_route)
        if continuity:
            prior = continuity[-1][:200]
            reply = f"*Recalling your prior context:* {prior}\n\n{result.reply}"
            result = result.model_copy(update={"reply": reply})
        return result


__all__ = [
    "EnterpriseAssistantService",
    "GroundedAssistantResponse",
]
