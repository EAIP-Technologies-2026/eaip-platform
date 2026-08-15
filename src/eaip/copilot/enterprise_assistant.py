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

from eaip.capabilities.registry import CapabilityRegistry
from eaip.context.permission_resolver import PermissionContextResolver
from eaip.copilot.action_executor import GovernedActionExecutor
from eaip.copilot.intelligence import AssistantIntelligenceService, GroundedAssistantResponse
from eaip.copilot.memory import GovernedMemoryService
from eaip.copilot.operational_intelligence import OperationalIntelligenceService
from eaip.copilot.role_context import RoleAwareAssistantContext, RoleAwareContextBuilder
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
            r"what can i do here",
            r"what is available here",
        ]
        return any(re.search(p, text) for p in patterns)

    def _is_platform_entities(self, text: str) -> bool:
        patterns = [
            r"what (systems|entities|services|components) (are|is) (connected|related) to",
            r"what (does|do) [a-z]+ (depend on|touch|use)",
        ]
        return any(re.search(p, text) for p in patterns)

    def _is_action_intent(self, text: str) -> bool:
        if not any(re.search(rf"\b{verb}\b", text, re.I) for verb in _ACTION_VERBS):
            return False
        return self._match_capability_in_text(text) is not None

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #
    def _cap_titles(self, names: tuple[str, ...]) -> list[str]:
        titles = []
        for n in names:
            cap = self._registry.try_get(n)
            titles.append(f"**{cap.title if cap else n}**")
        return titles

    def _match_capability_in_text(self, text: str) -> str | None:
        text_lower = text.lower()
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
        self, ctx: RoleAwareAssistantContext, user: dict[str, Any], current_route: str
    ) -> GroundedAssistantResponse:
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

    async def _handle_platform_entities(
        self, ctx: RoleAwareAssistantContext, user: dict[str, Any], current_route: str, text: str
    ) -> GroundedAssistantResponse:
        matched = self._match_capability_in_text(text)
        if matched is None:
            matched = ctx.current_capabilities[0] if ctx.current_capabilities else None
        if matched is None:
            return self._response(
                "I need a specific capability to describe its connected systems.",
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
        topology = await self._knowledge.get_capability_topology(matched)
        if "error" in topology:
            return self._response(
                f"No topology found for **{matched}** in the platform graph.",
                user, current_route, uncertain=True,
            )
        lines = [f"### Systems connected to {matched}", ""]
        for key, label in (
            ("services", "Services"),
            ("entities", "Entities"),
            ("routes", "Routes"),
            ("apis", "APIs"),
            ("events", "Events"),
            ("dependencies", "Dependencies"),
        ):
            items = topology.get(key) or ()
            if items:
                names = ", ".join(getattr(i, "name", str(i)) for i in items[:8])
                lines.append(f"- **{label}:** {names}")
        lines.append("")
        lines.append(f"Sources: `cap:{matched}`")
        return self._response("\n".join(lines), user, current_route, capability=matched)

    # ------------------------------------------------------------------ #
    # Governed action planning (never fabrication)
    # ------------------------------------------------------------------ #
    async def _handle_action_intent(
        self, text: str, user: dict[str, Any], current_route: str
    ) -> GroundedAssistantResponse:
        matched = self._match_capability_in_text(text)
        if matched is None:
            return self._response(
                "I can plan governed actions for you. Tell me the target capability (e.g. "
                "*Agents*, *Workflows*) and the operation (start, stop, restart, create, "
                "delete, pause, resume).",
                user, current_route, uncertain=True,
            )
        ctx = await self._context_builder.build(user, current_route)
        if not ctx.permission_aware.can_act(matched):
            cap = self._registry.try_get(matched)
            return self._response(
                f"Your role is not authorized to execute actions on "
                f"**{cap.title if cap else matched}**. I cannot plan or perform that action.",
                user, current_route, capability=matched,
            )
        if self._executor is None:
            return self._response(
                f"I can see you are authorized to act on **{matched}**, but governed execution "
                "is not connected in this build. No action was taken.",
                user, current_route, capability=matched, uncertain=True,
            )
        plan = await self._executor.plan_action(
            intent=text,
            user=user,
            capability_name=matched,
        )
        if plan.requires_approval:
            reply = (
                f"### Action plan prepared — approval required\n\n"
                f"**{plan.preview}**\n\n"
                f"This action is gated behind human approval. I have submitted it to the "
                f"approval queue (plan `{plan.plan_id}`). It will **not** execute until approved."
            )
        else:
            reply = (
                f"### Action plan prepared\n\n"
                f"**{plan.preview}**\n\n"
                f"Plan `{plan.plan_id}` is authorized (risk: {plan.risk_tier.value}). "
                f"No execution has occurred from this assistant turn — execute it through the "
                f"governed action channel to proceed."
            )
        return self._response(reply, user, current_route, capability=matched,
                              suggestions=("What requires approval?", "What can I do here?"))

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
    ) -> GroundedAssistantResponse:
        """Answer with full role-aware, route-aware, anti-fabrication behavior.

        Args:
            message: User query or prompt.
            user: Authenticated caller claims (user_id, tenant_id, roles).
            current_route: Active frontend route.

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

        # Tour commands -> A1006 guided tour engine.
        if self._is_tour_command(text_lower):
            if self._tours is None:
                return self._response(
                    "Guided tours are not connected in this build. You can still explore "
                    "capabilities by asking about them.",
                    user, current_route, uncertain=True,
                )
            ctx = await self._context_builder.build(user, current_route)
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
            ctx = await self._context_builder.build(user, current_route)
            return await self._operational.answer_operational_query(
                text, ctx.identity, current_route
            )

        # Action intents -> A1005 governed planning (no execution from the assistant).
        if self._is_action_intent(text_lower):
            return await self._handle_action_intent(text, user, current_route)

        ctx = await self._context_builder.build(user, current_route)
        continuity = await self._recall_continuity(user, current_route)

        # Phase 5 self-knowledge handlers.
        if self._is_self_knowledge_assistant(text_lower):
            result = self._handle_assistant_self_knowledge(ctx, user, current_route)
        elif self._is_self_knowledge_user(text_lower):
            result = self._handle_user_self_knowledge(ctx, user, current_route)
        elif self._is_why_cannot(text_lower):
            result = self._handle_why_cannot(ctx, user, current_route, text_lower)
        elif self._is_requires_approval(text_lower):
            result = self._handle_requires_approval(ctx, user, current_route)
        elif self._is_operations_available(text_lower):
            result = self._handle_operations_available(ctx, user, current_route)
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
