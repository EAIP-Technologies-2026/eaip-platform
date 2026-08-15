"""ConductorPlanner — deterministic intent routing.

The platform's stub LLM adapter does not emit tool calls, so Conductor uses a
small deterministic planner to map a user message onto a governed tool call.
It is intentionally swappable for a real LLM adapter that produces the same
:class:`Plan` contract.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from eaip.tools.base import Tool


@dataclass(frozen=True, slots=True)
class PlannedToolCall:
    """A tool Conductor intends to invoke for a turn."""

    tool_name: str
    arguments: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class Plan:
    """The result of planning a single user message."""

    reply: str
    tool_call: PlannedToolCall | None = None
    confidence: float = 1.0


class ConductorPlanner:
    """Route messages to governed tools using lightweight keyword intent."""

    def __init__(self, tools: dict[str, Tool]) -> None:
        """Initialize the planner.

        Args:
            tools: The governed tool set available to Conductor.
        """
        self._tools = tools

    def plan(self, message: str) -> Plan:
        """Plan a turn for the given user message.

        Args:
            message: The raw user message.

        Returns:
            A :class:`Plan` with a reply and an optional tool call.
        """
        text = message.strip().lower()
        if not text:
            return Plan(reply=self._default_reply())
        routed = self._route(text, message)
        if routed is None:
            return Plan(reply=self._default_reply())
        return routed

    def _route(self, text: str, message: str) -> Plan | None:
        """Try each intent rule in order, returning the first match."""
        for outcome in (
            self._plan_forget_memory(text),
            self._plan_remember_memory(text, message),
            self._plan_recall_memory(text),
            self._plan_briefing(text),
            self._plan_twin(text),
            self._plan_health(text),
            self._plan_diagnostics(text),
            self._plan_failures(text),
            self._plan_agents(text),
            self._plan_activity(text),
            self._plan_time(text),
            self._plan_global_search(text),
            self._plan_knowledge(text),
            self._plan_create_agent(text, message),
            self._plan_workflows(text),
            self._plan_investigations(text, message),
            self._plan_orchestration(text, message),
            self._plan_page_context(text),
        ):
            if outcome is not None:
                return outcome
        return None

    def _plan_recall_memory(self, text: str) -> Plan | None:
        """Route explicit memory questions to governed retrieval."""
        if (
            ("remember" in text or "memory" in text or "investigation" in text)
            and any(
                phrase in text
                for phrase in ("what do", "show", "recall", "continue", "tell me")
            )
            and "recall_memory" in self._tools
        ):
            query = self._extract_memory_query(text)
            return Plan(
                reply="Retrieving relevant governed memory as historical context...",
                tool_call=PlannedToolCall("recall_memory", {"query": query}),
            )
        return None

    def _plan_remember_memory(self, text: str, message: str) -> Plan | None:
        """Route explicit remember requests to governed storage."""
        explicit_remember = re.search(r"\bremember(?:\s+that|\s+this)?\b", text)
        if (
            "remember_memory" not in self._tools
            or explicit_remember is None
            or text.startswith("what do you remember")
            or "forget" in text
        ):
            return None
        content = re.sub(r"^.*?\bremember\b(?:\s+that)?\s*", "", message, flags=re.I).strip()
        if not content:
            return None
        return Plan(
            reply="I can remember that as governed personal context.",
            tool_call=PlannedToolCall("remember_memory", {"content": content}),
        )

    def _plan_forget_memory(self, text: str) -> Plan | None:
        """Route explicit forget requests to the existing approval service."""
        if "forget_memory" not in self._tools or "forget" not in text:
            return None
        match = re.search(r"(?:memory|item)\s+([a-z0-9_-]+)", text)
        arguments = {"memory_id": match.group(1)} if match else {"query": ""}
        return Plan(
            reply="Forgetting memory is a destructive action and requires your approval.",
            tool_call=PlannedToolCall("forget_memory", arguments),
        )

    def _plan_briefing(self, text: str) -> Plan | None:
        """Route briefing questions to the system briefing tool."""
        keywords = ("briefing", "morning", "summary")
        if any(k in text for k in keywords) and "get_system_briefing" in self._tools:
            return Plan(
                reply="Generating executive system briefing...",
                tool_call=PlannedToolCall("get_system_briefing", {}),
            )
        return None

    def _plan_twin(self, text: str) -> Plan | None:
        """Route twin questions to the system twin tool."""
        keywords = ("twin", "state", "overview")
        if any(k in text for k in keywords) and "get_system_twin" in self._tools:
            return Plan(
                reply="Retrieving System Twin operational state...",
                tool_call=PlannedToolCall("get_system_twin", {}),
            )
        return None


    def _plan_health(self, text: str) -> Plan | None:
        """Route health-status questions to the system health tool."""
        if (
            "health" in text or "status" in text or "doing" in text or "healthy" in text
        ) and "system_health" in self._tools:
            return Plan(
                reply="Checking platform health...",
                tool_call=PlannedToolCall("system_health", {}),
            )
        return None

    def _plan_diagnostics(self, text: str) -> Plan | None:
        """Route diagnosis questions to the runtime diagnostics tool."""
        if (
            "diagnose" in text or "failing" in text or "stuck" in text or "issue" in text
        ) and "runtime_diagnostics" in self._tools:
            return Plan(
                reply="Running operational diagnostics...",
                tool_call=PlannedToolCall("runtime_diagnostics", {}),
            )
        return None

    def _plan_failures(self, text: str) -> Plan | None:
        """Route failure questions to the recent-failures tool."""
        if ("failure" in text or "failures" in text or "error" in text) and (
            "recent_failures" in self._tools
        ):
            return Plan(
                reply="Fetching recent operational failure events...",
                tool_call=PlannedToolCall("recent_failures", {}),
            )
        return None

    def _plan_agents(self, text: str) -> Plan | None:
        """Route agent questions to the agent roster tool."""
        if (
            "agent" in text or "bot" in text or "running" in text
        ) and "list_agents" in self._tools and "create" not in text and "get" not in text:
            return Plan(
                reply="Pulling the registered agent roster...",
                tool_call=PlannedToolCall("list_agents", {}),
            )
        return None

    def _plan_activity(self, text: str) -> Plan | None:
        """Route activity questions to the recent-activity tool."""
        if ("activity" in text or "history" in text) and "list_recent_activity" in self._tools:
            return Plan(
                reply="Retrieving recent platform operational activity...",
                tool_call=PlannedToolCall("list_recent_activity", {}),
            )
        return None

    def _plan_time(self, text: str) -> Plan | None:
        """Route time questions to the current-time tool."""
        if ("time" in text or "clock" in text) and "current_time" in self._tools:
            return Plan(
                reply="Fetching current system UTC timestamp...",
                tool_call=PlannedToolCall("current_time", {}),
            )
        return None

    def _plan_global_search(self, text: str) -> Plan | None:
        """Route global-search questions to the global search tool."""
        if "global" in text and "search" in text and "global_search" in self._tools:
            query = self._extract_query(text)
            return Plan(
                reply=f"Performing global search for '{query}'...",
                tool_call=PlannedToolCall("global_search", {"query": query}),
            )
        return None

    def _plan_knowledge(self, text: str) -> Plan | None:
        """Route knowledge questions to the knowledge search tool."""
        if (
            re.search(r"(search|find|look\s*up|onboarding)", text) or "knowledge" in text
        ) and ("knowledge_search" in self._tools or "search_knowledge" in self._tools):
            query = self._extract_query(text)
            tool_name = (
                "knowledge_search"
                if "knowledge_search" in self._tools
                else "search_knowledge"
            )
            return Plan(
                reply=f"Searching knowledge base for '{query}'...",
                tool_call=PlannedToolCall(tool_name, {"query": query, "top_k": 5}),
            )
        return None

    def _plan_create_agent(self, text: str, message: str) -> Plan | None:
        """Route agent-creation requests to the approval-gated tool."""
        if (
            "create" in text and re.search(r"agent|bot", text) and "create_agent" in self._tools
        ):
            name = self._extract_agent_name(message)
            return Plan(
                reply=f"Creating agent {name!r} — this requires your approval.",
                tool_call=PlannedToolCall("create_agent", {"name": name}),
            )
        return None

    def _plan_workflows(self, text: str) -> Plan | None:
        """Route workflow questions to the workflow list tool."""
        if re.search(r"workflows?", text) and "list_workflows" in self._tools:
            return Plan(
                reply="Fetching workflow definitions...",
                tool_call=PlannedToolCall("list_workflows", {}),
            )
        return None

    def _plan_investigations(  # noqa: PLR0911
        self, text: str, message: str
    ) -> Plan | None:
        """Route investigation-related intents."""
        has_investigate = bool(
            re.search(r"\binvestigat", text)
        )
        has_create = bool(
            re.search(
                r"\b(investigate|start|begin|create|open)\b",
                text,
            )
        )
        has_list = bool(
            re.search(
                r"\b(list|show|my|all)\b.*\binvestigation", text
            )
        )
        has_continue = bool(
            re.search(
                r"\b(continue|resume|pick up|go back to)\b"
                r".*\b(investigation|where we left)",
                text,
            )
        )
        has_pause = bool(
            re.search(r"\bpause\b.*\binvestigation", text)
        )
        has_resolve = bool(
            re.search(
                r"\b(resolve|complete|finish|close)\b"
                r".*\binvestigation",
                text,
            )
        )
        has_evidence = bool(
            re.search(
                r"\b(evidence|what do we know|what did we find|"
                r"what have we found|discoveries)\b",
                text,
            )
        )
        has_unresolved = bool(
            re.search(
                r"\b(unresolved|unsure|unknown|open questions)\b",
                text,
            )
        )

        if has_investigate and has_create and not has_list:
            title = re.sub(
                r"\b(please|can you|could you|investigate|"
                r"start an? investigation|look into)\b",
                "",
                message,
                flags=re.I,
            ).strip(" .?!")[:120]
            if not title:
                title = "New Investigation"
            return Plan(
                reply=(
                    f"I'll create an investigation into: "
                    f"{title}"
                ),
                tool_call=PlannedToolCall(
                    "create_investigation",
                    {
                        "title": title,
                        "objective": (
                            f"Determine the root cause of: "
                            f"{title}"
                        ),
                    },
                ),
            )

        if has_list:
            return Plan(
                reply="Retrieving your investigations...",
                tool_call=PlannedToolCall(
                    "list_investigations", {"limit": 10}
                ),
            )

        if has_continue:
            return Plan(
                reply=(
                    "Let me find your most recent investigation "
                    "to resume."
                ),
                tool_call=PlannedToolCall(
                    "list_investigations",
                    {"status": "active", "limit": 1},
                ),
            )

        if has_evidence or has_unresolved:
            return Plan(
                reply="Retrieving investigation details...",
                tool_call=PlannedToolCall(
                    "list_investigations",
                    {"status": "active", "limit": 1},
                ),
            )

        if has_pause:
            return Plan(
                reply=(
                    "To pause an investigation, I need its ID. "
                    "Let me show your active investigations."
                ),
                tool_call=PlannedToolCall(
                    "list_investigations",
                    {"status": "active", "limit": 5},
                ),
            )

        if has_resolve:
            return Plan(
                reply=(
                    "To resolve an investigation, I need its ID. "
                    "Let me show your active investigations."
                ),
                tool_call=PlannedToolCall(
                    "list_investigations",
                    {"status": "active", "limit": 5},
                ),
            )

        if has_investigate:
            return Plan(
                reply=(
                    "I can help you investigate. Would you like "
                    "to start a new investigation or continue "
                    "an existing one?"
                ),
                tool_call=PlannedToolCall(
                    "list_investigations",
                    {"limit": 5},
                ),
            )

        return None

    def _plan_orchestration(  # noqa: PLR0911
        self, text: str, message: str
    ) -> Plan | None:
        """Route orchestration-related intents."""
        has_plan = bool(
            re.search(r"\b(plan|orchestrat|readiness|prepare)\b", text)
        )
        has_create = bool(
            re.search(
                r"\b(create|make|build|prepare|start|draft)\b", text
            )
        )
        has_list = bool(
            re.search(
                r"\b(list|show|my|all)\b.*\b(plan|orchestrat)", text
            )
        )
        has_execute = bool(
            re.search(r"\b(execute|run|start)\b.*\bplan", text)
        )
        has_approve = bool(
            re.search(r"\b(approve)\b.*\bplan", text)
        )
        has_pause = bool(
            re.search(r"\b(pause)\b.*\bplan", text)
        )
        has_cancel = bool(
            re.search(r"\b(cancel|stop)\b.*\bplan", text)
        )
        has_rollback = bool(
            re.search(r"\b(rollback|roll back|undo)\b.*\bplan", text)
        )

        if has_plan and has_create and not has_list:
            objective = re.sub(
                r"\b(please|can you|could you|create|make|"
                r"build|prepare|plan|orchestrat|start|draft)\b",
                "",
                message,
                flags=re.I,
            ).strip(" .?!")[:200]
            if not objective:
                objective = "New orchestration plan"
            return Plan(
                reply=(
                    f"I'll create an orchestration plan: "
                    f"{objective}"
                ),
                tool_call=PlannedToolCall(
                    "create_orchestration_plan",
                    {"objective": objective},
                ),
            )

        if has_list:
            return Plan(
                reply="Retrieving orchestration plans...",
                tool_call=PlannedToolCall(
                    "list_orchestration_plans", {"limit": 10}
                ),
            )

        if has_execute or has_approve or has_pause or has_cancel or has_rollback:
            return Plan(
                reply=(
                    "Let me show your plans so you can "
                    "select one."
                ),
                tool_call=PlannedToolCall(
                    "list_orchestration_plans",
                    {"limit": 10},
                ),
            )

        if has_plan:
            return Plan(
                reply=(
                    "I can help you create an orchestration plan. "
                    "What would you like to accomplish?"
                ),
            )

        return None

    def _plan_page_context(self, text: str) -> Plan | None:
        """Answer questions about the current page context."""
        if "looking at" in text or "route" in text or "page" in text:
            return Plan(reply="You are currently viewing the EAIP Enterprise Console interface.")
        return None

    @staticmethod
    def _extract_memory_query(text: str) -> str:
        """Extract a bounded historical query without treating it as instructions."""
        cleaned = re.sub(
            r"\b(what do you remember|what did we discover|show me|recall|"
            r"continue|tell me|about)\b",
            "",
            text,
        )
        return cleaned.strip(" ?.:") or "recent context"

    @staticmethod
    def _default_reply() -> str:
        """Return the fallback reply when no tool matches the message."""
        return (
            "I can help you inspect this EAIP instance: ask about system health, "
            "agents, workflows, or search the knowledge base. Actions like creating "
            "an agent will ask for your approval first. I can also remember explicit "
            "preferences and investigations, or show you what is remembered."
        )

    @staticmethod
    def _extract_query(text: str) -> str:
        """Extract the substantive part of a search request."""
        match = re.search(
            r"(?:search|find|look\s*up)(?:\s+(?:for|about|the knowledge base for))?\s*(.+?)\s*$",
            text,
        )
        if match:
            query = match.group(1).strip().rstrip("?.")
            if query and query not in {"knowledge base", "knowledge", "documentation"}:
                return query
        cleaned = re.sub(r"\b(please|can you|could you|search|find)\b", "", text).strip()
        cleaned = re.sub(r"\?+$", "", cleaned).strip()
        return cleaned or "general"

    @staticmethod
    def _extract_agent_name(message: str) -> str:
        """Extract the agent name from a creation request, preserving case."""
        match = re.search(
            r"(?:named|called)\s+([a-zA-Z0-9_-]+)", message, flags=re.IGNORECASE
        )
        if match:
            return match.group(1)
        match = re.search(
            r"create\s+(?:an?\s+)?(?:agent|bot)\s+([a-zA-Z0-9_-]+)",
            message,
            flags=re.IGNORECASE,
        )
        if match:
            return match.group(1)
        cleaned = re.sub(
            r"\b(please|can you|could you)\b", "", message, flags=re.IGNORECASE
        ).strip()
        cleaned = re.sub(
            r"\bcreate\s+(?:an?\s+)?(?:agent|bot)\b", "", cleaned, flags=re.IGNORECASE
        ).strip()
        cleaned = re.sub(r"\?+$", "", cleaned).strip()
        return cleaned or "Conductor Agent"


__all__ = ["ConductorPlanner", "Plan", "PlannedToolCall"]
