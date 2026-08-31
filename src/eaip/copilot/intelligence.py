"""Assistant Intelligence Service — platform-grounded, permission-aware reasoning.

Connects identity claims, permission context, canonical capability registry,
and platform knowledge graph into grounded, anti-hallucinatory assistant responses.
"""

from __future__ import annotations

import re
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from eaip.capabilities.capability import Capability
from eaip.capabilities.registry import CapabilityRegistry
from eaip.context.permission_context import IdentityScope, PermissionAwareContext
from eaip.context.permission_resolver import PermissionContextResolver
from eaip.kgraph.platform_graph import PlatformKnowledgeService
from eaip.logging.context import get_logger


class GroundedAssistantResponse(BaseModel):
    """Structured response from the grounded assistant intelligence service."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    reply: str = Field(description="Formatted markdown answer grounded in platform knowledge.")
    grounded_capability: str | None = Field(
        default=None, description="Matched capability name if applicable."
    )
    sources: tuple[str, ...] = Field(
        default=(), description="Citations to routes, APIs, or documentation."
    )
    suggested_actions: tuple[str, ...] = Field(
        default=(), description="Context-aware suggested follow-up prompts."
    )
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Confidence score.")
    is_uncertain: bool = Field(
        default=False, description="True if answer represents lack of platform evidence."
    )
    current_route: str = Field(default="/", description="Route context when answered.")
    user_id: str = Field(default="", description="Authenticated subject.")
    tenant_id: str = Field(default="", description="Authenticated tenant boundary.")


class AssistantIntelligenceService:
    """Provides grounded platform intelligence to the Enterprise Assistant."""

    def __init__(
        self,
        capability_registry: CapabilityRegistry,
        permission_resolver: PermissionContextResolver,
        knowledge_service: PlatformKnowledgeService | None = None,
    ) -> None:
        """Initialize the assistant intelligence service.

        Args:
            capability_registry: Authoritative platform capability registry.
            permission_resolver: Permission context resolver.
            knowledge_service: Optional platform knowledge graph service.
        """
        self._registry = capability_registry
        self._resolver = permission_resolver
        self._knowledge = knowledge_service
        self._log = get_logger("eaip.copilot.intelligence")

    async def answer_grounded_query(
        self,
        message: str,
        user: dict[str, Any],
        current_route: str = "/",
        _entity_id: str | None = None,
    ) -> GroundedAssistantResponse:
        """Answer a user query with strict platform grounding and permission awareness.

        Args:
            message: User query or prompt.
            user: Authenticated caller claims (id/user_id, tenant_id, roles).
            current_route: Currently active frontend route.
            entity_id: Optional selected entity ID.

        Returns:
            GroundedAssistantResponse with cited sources and permission boundaries.
        """
        user_id = str(user.get("user_id") or user.get("id") or "anonymous")
        tenant_id = str(user.get("tenant_id") or "default")
        roles = tuple(user.get("roles") or ())

        identity = IdentityScope(
            user_id=user_id,
            tenant_id=tenant_id,
            roles=roles,
            attributes=user.get("attributes") or {},
        )

        perm_ctx = self._resolver.resolve_context(identity)
        text = message.strip()
        text_lower = text.lower()

        # 1. Current page queries ("What is this page?", "What can I do here?", "Where am I?")
        if self._is_current_page_query(text_lower):
            return await self._handle_current_page_query(perm_ctx, current_route)

        # 2. General capabilities discovery ("What can I do?", "What capabilities do I have?")
        if self._is_capabilities_discovery_query(text_lower):
            return self._handle_capabilities_discovery_query(perm_ctx, current_route)

        # 3. Targeted capability query ("Tell me about Agents", "What is Conductor?")
        matched_cap = self._match_capability_in_text(text_lower)
        if matched_cap:
            return await self._handle_capability_query(
                perm_ctx, matched_cap, text_lower, current_route
            )

        # 4. Unknown concept / anti-hallucination check
        return self._handle_unknown_query(perm_ctx, text, current_route)

    def _is_current_page_query(self, text: str) -> bool:
        patterns = [
            r"what (is|does) this (page|view|screen)",
            r"where am i",
            r"what can i do here",
            r"explain this (page|route|view)",
            r"tell me about this (page|view)",
        ]
        return any(re.search(p, text) for p in patterns)

    def _is_capabilities_discovery_query(self, text: str) -> bool:
        patterns = [
            r"what capabilities",
            r"what (features|tools) (do i have|are available)",
            r"what can i do( on eaip)?$",
            r"list (my )?(capabilities|permissions|features)",
        ]
        return any(re.search(p, text) for p in patterns)

    def _match_capability_in_text(self, text: str) -> Capability | None:
        all_caps = self._registry.all()
        # First check exact names/titles
        for cap in all_caps:
            if (
                cap.name.lower() in text
                or cap.title.lower() in text
                or cap.id_or_name().lower() in text
            ):
                return cap
        # Then check search terms
        min_term_length = 3
        for cap in all_caps:
            for term in cap.search_terms:
                if len(term) > min_term_length and term.lower() in text:
                    return cap
        return None

    async def _handle_current_page_query(
        self,
        perm_ctx: PermissionAwareContext,
        current_route: str,
    ) -> GroundedAssistantResponse:
        matching_caps = self._registry.find_by_route(current_route)
        if not matching_caps:
            # Check prefix route match (e.g. /agents/123 -> /agents)
            base_route = (
                "/" + current_route.strip("/").split("/")[0] if current_route != "/" else "/"
            )
            matching_caps = self._registry.find_by_route(base_route)

        if not matching_caps:
            return GroundedAssistantResponse(
                reply=(
                    f"You are currently on route `{current_route}`. "
                    "No specific capability mapping is registered for this route."
                ),
                sources=(current_route,),
                current_route=current_route,
                user_id=perm_ctx.identity.user_id,
                tenant_id=perm_ctx.identity.tenant_id,
            )

        cap = matching_caps[0]
        if not perm_ctx.can_see(cap.name):
            return GroundedAssistantResponse(
                reply=(
                    f"You are viewing `{cap.title}`, but your current role "
                    f"({', '.join(perm_ctx.identity.roles) or 'none'}) "
                    "does not have authorized visibility for this capability."
                ),
                grounded_capability=cap.name,
                sources=(current_route,),
                is_uncertain=False,
                current_route=current_route,
                user_id=perm_ctx.identity.user_id,
                tenant_id=perm_ctx.identity.tenant_id,
            )

        access = perm_ctx.get_access(cap.name)
        can_act = access.executable if access else False
        approval_req = access.approval_required if access else False

        ops_text = ", ".join(str(op).upper() for op in cap.supported_operations)
        reply = (
            f"### {cap.title}\n\n"
            f"{cap.description}\n\n"
            f"- **Domain / Category**: `{cap.domain}` / `{cap.category}`\n"
            f"- **Supported Operations**: {ops_text}\n"
            f"- **Your Access**: {'Can Execute' if can_act else 'Read-Only'}"
            f"{' (Requires Approval)' if approval_req else ''}\n"
        )
        if cap.assistant_description:
            reply += f"\n> {cap.assistant_description}\n"

        sources = list(cap.routes) + list(cap.documentation_references)
        suggestions = (
            f"What operations are supported in {cap.title}?",
            f"What APIs does {cap.title} provide?",
            "What other capabilities can I access?",
        )

        return GroundedAssistantResponse(
            reply=reply,
            grounded_capability=cap.name,
            sources=tuple(sources),
            suggested_actions=suggestions,
            current_route=current_route,
            user_id=perm_ctx.identity.user_id,
            tenant_id=perm_ctx.identity.tenant_id,
        )

    def _handle_capabilities_discovery_query(
        self,
        perm_ctx: PermissionAwareContext,
        current_route: str,
    ) -> GroundedAssistantResponse:
        visible_caps = [
            self._registry.get(cap_name)
            for cap_name in perm_ctx.visible_capability_ids
            if self._registry.has(cap_name)
        ]

        if not visible_caps:
            return GroundedAssistantResponse(
                reply=(
                    "You currently do not have authorized visibility into any "
                    "EAIP platform capabilities. Please check your role "
                    "assignments with a platform administrator."
                ),
                current_route=current_route,
                user_id=perm_ctx.identity.user_id,
                tenant_id=perm_ctx.identity.tenant_id,
            )

        lines = [f"### Available Capabilities ({len(visible_caps)})", ""]
        for cap in visible_caps:
            can_act = perm_ctx.can_act(cap.name)
            badge = "*(Actionable)*" if can_act else "*(Read-only)*"
            lines.append(f"- **{cap.title}** (`{cap.name}`): {cap.description} {badge}")

        suggestions = ("Tell me about Agents", "Tell me about Dashboard", "What is Conductor?")

        return GroundedAssistantResponse(
            reply="\n".join(lines),
            sources=tuple(c.routes[0] for c in visible_caps if c.routes),
            suggested_actions=suggestions,
            current_route=current_route,
            user_id=perm_ctx.identity.user_id,
            tenant_id=perm_ctx.identity.tenant_id,
        )

    async def _handle_capability_query(
        self,
        perm_ctx: PermissionAwareContext,
        cap: Capability,
        query_text: str,
        current_route: str,
    ) -> GroundedAssistantResponse:
        if not perm_ctx.can_see(cap.name):
            return GroundedAssistantResponse(
                reply=(
                    f"Capability `{cap.title}` exists on EAIP, but your role "
                    f"({', '.join(perm_ctx.identity.roles)}) is restricted "
                    "from viewing its details."
                ),
                grounded_capability=cap.name,
                current_route=current_route,
                user_id=perm_ctx.identity.user_id,
                tenant_id=perm_ctx.identity.tenant_id,
            )

        # Check if user asked specifically for topology, APIs, routes, or services
        asked_topology = any(
            k in query_text
            for k in (
                "api",
                "apis",
                "route",
                "service",
                "topology",
                "architecture",
                "dependencies",
                "events",
            )
        )

        lines = [
            f"### {cap.title}",
            f"{cap.description}",
            "",
            f"- **Capability ID**: `{cap.id_or_name()}` (`{cap.name}`)",
            f"- **Category / Domain**: `{cap.category}` / `{cap.domain}`",
            f"- **Owner**: `{cap.owner}`",
            f"- **Version**: `{cap.version}`",
            f"- **Supported Operations**: "
            f"{', '.join(str(op).upper() for op in cap.supported_operations)}",
        ]

        if cap.routes:
            lines.append(f"- **Routes**: {', '.join(f'`{r}`' for r in cap.routes)}")
        if cap.api_operations:
            lines.append(f"- **APIs**: {', '.join(f'`{a}`' for a in cap.api_operations)}")
        if cap.events:
            lines.append(f"- **Domain Events**: {', '.join(f'`{e}`' for e in cap.events)}")

        if self._knowledge and asked_topology:
            topo = await self._knowledge.get_capability_topology(cap.name)
            if "error" not in topo and topo.get("dependencies"):
                dep_titles = [d.name for d in topo["dependencies"]]
                lines.append(f"- **Connected Platform Dependencies**: {', '.join(dep_titles)}")

        sources = list(cap.routes) + list(cap.documentation_references) + list(cap.api_operations)
        suggestions = (
            f"Go to {cap.title}",
            f"What operations can I execute in {cap.title}?",
            "Show all my available capabilities",
        )

        return GroundedAssistantResponse(
            reply="\n".join(lines),
            grounded_capability=cap.name,
            sources=tuple(sources),
            suggested_actions=suggestions,
            current_route=current_route,
            user_id=perm_ctx.identity.user_id,
            tenant_id=perm_ctx.identity.tenant_id,
        )

    def _handle_unknown_query(
        self,
        perm_ctx: PermissionAwareContext,
        _query_text: str,
        current_route: str,
    ) -> GroundedAssistantResponse:
        reply = (
            "I don't have sufficient platform evidence to determine that. "
            "This concept is not present in EAIP's capability registry or "
            "knowledge graph. Please ask about registered platform "
            "capabilities such as Agents, Brains, Knowledge, Workflows, "
            "Monitoring, or Operations."
        )
        return GroundedAssistantResponse(
            reply=reply,
            confidence=0.0,
            is_uncertain=True,
            current_route=current_route,
            suggested_actions=("What capabilities are available?", "Explain this page"),
            user_id=perm_ctx.identity.user_id,
            tenant_id=perm_ctx.identity.tenant_id,
        )


__all__ = ["AssistantIntelligenceService", "GroundedAssistantResponse"]
