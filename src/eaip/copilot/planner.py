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
            self._plan_scheduling(text),
            self._plan_workforce(text),
            self._plan_marketplace(text),
            self._plan_simulation(text),
            self._plan_integrations(text),
            self._plan_wave2_workforce(text),
            self._plan_wave2_documents(text),
            self._plan_wave2_scenarios(text),
            self._plan_wave2_governance(text),
            self._plan_wave2_anomalies(text),
            self._plan_wave2_improvements(text),
            self._plan_wave2_decision_explain(text),
            self._plan_wave3_erp_connect(text),
            self._plan_wave3_failed_missions(text),
            self._plan_wave3_simulation_start(text),
            self._plan_wave3_agents_available(text),
            self._plan_wave3_decision_why(text),
            self._plan_wave3_audit_proof(text),
            self._plan_wave3_connector_health(text),
            self._plan_wave3_workflow_build(text),
            self._plan_wave3_approval_needed(text),
            self._plan_wave3_scenario_impact(text),
            self._plan_wave4_what_happening(text),
            self._plan_wave4_what_needs_attention(text),
            self._plan_wave4_why_failed(text),
            self._plan_wave4_ai_spend(text),
            self._plan_wave4_underperforming(text),
            self._plan_wave4_top_risks(text),
            self._plan_m1_what_do_we_know(text),
            self._plan_m1_what_happened(text),
            self._plan_m1_why_decision(text),
            self._plan_m1_show_evidence(text),
            self._plan_m1_what_changed(text),
            self._plan_m1_similar_decisions(text),
            self._plan_m1_what_affected(text),
            self._plan_m1_what_depends(text),
            self._plan_m2_what_changed_today(text),
            self._plan_m2_why_kpi(text),
            self._plan_m2_biggest_risks(text),
            self._plan_m2_what_likely(text),
            self._plan_m3_why_failed(text),
            self._plan_m3_recover(text),
            self._plan_m3_which_agent(text),
            self._plan_m3_who_overloaded(text),
            self._plan_m3_build_team(text),
            self._plan_operational_action(text),
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
            self._plan_m6_connector_list(text),
            self._plan_m6_connector_health(text),
            self._plan_m6_connector_access(text),
            self._plan_m6_model_routing(text),
            self._plan_m6_model_why_selected(text),
            self._plan_m6_cheapest_model(text),
            self._plan_m6_failover_why(text),
            self._plan_m7_find_pack(text),
            self._plan_m7_available_agents(text),
            self._plan_m7_trusted(text),
            self._plan_m7_why_cant_install(text),
            self._plan_m7_sandbox_install(text),
            self._plan_m7_version_diff(text),
            self._plan_m7_deployment_status(text),
            self._plan_m8_what_unhealthy(text),
            self._plan_m8_which_runtime(text),
            self._plan_m8_near_capacity(text),
            self._plan_m8_incidents_attention(text),
            self._plan_m8_bottleneck(text),
            self._plan_m8_what_will_fail(text),
            self._plan_m8_failover_what(text),
            self._plan_m9_what_changed(text),
            self._plan_m9_why(text),
            self._plan_m9_needs_attention(text),
            self._plan_m9_should_approve(text),
            self._plan_m9_at_risk(text),
            self._plan_m9_likely_happen(text),
            self._plan_m9_show_evidence(text),
            self._plan_m9_run_scenario(text),
            self._plan_m9_recommend(text),
            self._plan_m4_strategy_priorities(text),
            self._plan_m4_strategy_changed(text),
            self._plan_m4_initiatives_at_risk(text),
            self._plan_m4_missions_for_objective(text),
            self._plan_m4_why_kpi(text),
            self._plan_m4_what_should_change(text),
            self._plan_m4_show_reasoning(text),
            self._plan_m4_show_evidence_strategy(text),
            self._plan_m5_why_did_eaip(text),
            self._plan_m5_show_proof(text),
            self._plan_m5_was_approved(text),
            self._plan_m5_which_policy(text),
            self._plan_m5_what_model_received(text),
            self._plan_m5_what_tool_ran(text),
            self._plan_m5_verify_execution(text),
            self._plan_m5_what_learned(text),
            self._plan_m6_connectors_available(text),
            self._plan_m6_is_healthy(text),
            self._plan_m6_which_systems_access(text),
            self._plan_m6_which_model(text),
            self._plan_m6_why_model_selected(text),
            self._plan_m6_cheapest_model(text),
            self._plan_m6_why_failover(text),
            self._plan_m10_what_happening(text),
            self._plan_m10_why_matters(text),
            self._plan_m10_what_will_happen(text),
            self._plan_m10_what_should_do(text),
            self._plan_m10_why_did_you_do(text),
            self._plan_m10_show_me(text),
            self._plan_m10_undo(text),
            self._plan_m10_learn(text),
            self._plan_demo_request(text),
            self._plan_navigation_request(text),
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

    def _plan_operational_action(self, text: str) -> Plan | None:
        """Route governed operational verbs (pause/resume/restart/cancel) to real runtimes."""
        # "pause | resume | restart | cancel | stop"  +  "agent | workflow"
        is_agent = bool(re.search(r"\b(agent|bot)\b", text))
        is_workflow = bool(re.search(r"\bworkflow\b", text))
        is_pause = bool(re.search(r"\bpause\b", text))
        is_resume = bool(re.search(r"\bresume\b|\bcontinue\b", text))
        is_restart = bool(re.search(r"\brestart\b|\breboot\b|\bstart again\b", text))
        is_cancel = bool(re.search(r"\bcancel\b|\bstop\b|\bkill\b", text))
        if not (is_pause or is_resume or is_restart or is_cancel):
            return None
        # Exclude investigation/analysis phrasing (handled by specialist rules).
        if not (is_agent or is_workflow):
            return None
        if is_agent and is_workflow:
            return None

        target_id = ""
        for ident in re.findall(r"\b(ag-[a-zA-Z0-9_-]+|wf-[a-zA-Z0-9_-]+|ms-[a-zA-Z0-9_-]+)\b", text):
            target_id = ident
            break

        if is_agent:
            if is_pause and "pause_agent" in self._tools:
                tool = "pause_agent"
            elif is_cancel and "cancel_agent_run" in self._tools:
                tool = "cancel_agent_run"
            elif is_restart and "restart_agent" in self._tools:
                tool = "restart_agent"
            elif is_resume and "resume_agent" in self._tools:
                tool = "resume_agent"
            else:
                return None
            reply = f"Applying governed lifecycle change to agent{': ' + target_id if target_id else ''}..."
        else:
            if is_pause and "pause_workflow" in self._tools:
                tool = "pause_workflow"
            elif is_cancel and "cancel_workflow" in self._tools:
                tool = "cancel_workflow"
            elif is_resume and "resume_workflow" in self._tools:
                tool = "resume_workflow"
            else:
                return None
            reply = f"Applying governed lifecycle change to workflow{': ' + target_id if target_id else ''}..."

        args: dict[str, object] = {}
        if target_id:
            args["target_id"] = target_id
        return Plan(reply=reply, tool_call=PlannedToolCall(tool, args))

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

    def _plan_scheduling(self, text: str) -> Plan | None:
        if any(k in text for k in ("schedule", "scheduling", "upcoming", "tomorrow", "calendar")) and "list_schedules" in self._tools:
            return Plan(reply="Fetching scheduled operations...", tool_call=PlannedToolCall("list_schedules", {}))
        if "health" in text and "schedule" in text and "schedule_health" in self._tools:
            return Plan(reply="Checking schedule health...", tool_call=PlannedToolCall("schedule_health", {}))
        return None

    def _plan_workforce(self, text: str) -> Plan | None:
        if any(k in text for k in ("overloaded", "underutilized", "capacity", "workforce", "team load", "utilization")) and "workforce_overview" in self._tools:
            return Plan(reply="Analyzing workforce capacity...", tool_call=PlannedToolCall("workforce_overview", {}))
        if "bottleneck" in text and "workforce_bottlenecks" in self._tools:
            return Plan(reply="Detecting workforce bottlenecks...", tool_call=PlannedToolCall("workforce_bottlenecks", {}))
        return None

    def _plan_marketplace(self, text: str) -> Plan | None:
        if any(k in text for k in ("marketplace", "automation", "integration", "industry pack", "recommend")) and "marketplace_search" in self._tools:
            query = self._extract_query(text)
            return Plan(reply=f"Searching marketplace for '{query}'...", tool_call=PlannedToolCall("marketplace_search", {"query": query}))
        return None

    def _plan_simulation(self, text: str) -> Plan | None:
        if any(k in text for k in ("simulation", "enterprise state", "workload")) and "simulation_state" in self._tools:
            return Plan(reply="Fetching enterprise simulation state...", tool_call=PlannedToolCall("simulation_state", {}))
        return None

    def _plan_integrations(self, text: str) -> Plan | None:
        if any(k in text for k in ("integration", "connector", "mcp", "external tool", "crm", "erp", "inventory", "production backlog")) and "list_integrations" in self._tools:
            return Plan(reply="Listing external integrations...", tool_call=PlannedToolCall("list_integrations", {}))
        return None

    def _plan_wave2_workforce(self, text: str) -> Plan | None:
        if any(k in text for k in ("workforce capacity", "show workforce", "workforce assignment")) and "workforce_capacity" in self._tools:
            return Plan(reply="Checking digital workforce capacity…", tool_call=PlannedToolCall("workforce_capacity", {}))
        if "best suited" in text or "who is best" in text:
            q = self._extract_query(text)
            tool = "workforce_match" if "workforce_match" in self._tools else ("workforce_capacity" if "workforce_capacity" in self._tools else None)
            if tool:
                return Plan(reply=f"Finding best-suited workforce for '{q}'…", tool_call=PlannedToolCall(tool, {"query": q}))
        return None

    def _plan_wave2_documents(self, text: str) -> Plan | None:
        if any(k in text for k in ("analyze this document", "document intelligence", "extract entities", "extract tables")) and "document_analyze" in self._tools:
            q = self._extract_query(text)
            return Plan(reply=f"Running document intelligence for '{q}'…", tool_call=PlannedToolCall("document_analyze", {"query": q}))
        return None

    def _plan_wave2_scenarios(self, text: str) -> Plan | None:
        if any(k in text for k in ("compare these scenarios", "compare scenarios", "what happens if")) and "scenario_compare" in self._tools:
            return Plan(reply="Comparing scenarios…", tool_call=PlannedToolCall("scenario_compare", {}))
        if "scenario" in text and "simulation" in text and "scenario_builder" in self._tools:
            return Plan(reply="Opening scenario builder…", tool_call=PlannedToolCall("scenario_builder", {}))
        return None

    def _plan_wave2_governance(self, text: str) -> Plan | None:
        if any(k in text for k in ("pending ai governance", "governance approvals", "ai governance approvals", "show governance")) and "governance_approvals" in self._tools:
            return Plan(reply="Fetching pending governance approvals…", tool_call=PlannedToolCall("governance_approvals", {}))
        if "risk" in text and "governance" in text and "governance_risk" in self._tools:
            return Plan(reply="Checking governance risk…", tool_call=PlannedToolCall("governance_risk", {}))
        return None

    def _plan_wave2_anomalies(self, text: str) -> Plan | None:
        if any(k in text for k in ("operational anomalies", "show anomalies", "underperforming", "why is this operation")) and "ops_anomalies" in self._tools:
            return Plan(reply="Scanning for operational anomalies…", tool_call=PlannedToolCall("ops_anomalies", {}))
        return None

    def _plan_wave2_improvements(self, text: str) -> Plan | None:
        if any(k in text for k in ("improvement proposals", "show improvement", "continuous improvement")) and "improvement_proposals" in self._tools:
            return Plan(reply="Listing improvement proposals…", tool_call=PlannedToolCall("improvement_proposals", {}))
        return None

    def _plan_wave2_decision_explain(self, text: str) -> Plan | None:
        if "explain this decision" in text and "decision_explain" in self._tools:
            q = self._extract_query(text)
            return Plan(reply=f"Explaining decision '{q}'…", tool_call=PlannedToolCall("decision_explain", {"query": q}))
        return None

    def _plan_wave3_erp_connect(self, text: str) -> Plan | None:
        if "connect our erp" in text or "connect erp" in text:
            tool = "invoke_external_tool" if "invoke_external_tool" in self._tools else ("list_integrations" if "list_integrations" in self._tools else None)
            if tool:
                return Plan(reply="Connecting ERP — listing integrations…", tool_call=PlannedToolCall(tool, {"server_id": "erp", "tool_name": "connect"} if tool == "invoke_external_tool" else {}))
        return None

    def _plan_wave3_failed_missions(self, text: str) -> Plan | None:
        if "failed missions" in text or "show me failed" in text:
            return Plan(reply="Your failed missions are available in Operations.", tool_call=PlannedToolCall("list_recent_activity", {})) if "list_recent_activity" in self._tools else None
        return None

    def _plan_wave3_simulation_start(self, text: str) -> Plan | None:
        if "start a simulation" in text and "simulation_state" in self._tools:
            return Plan(reply="Starting simulation — fetching state…", tool_call=PlannedToolCall("simulation_state", {}))
        return None

    def _plan_wave3_agents_available(self, text: str) -> Plan | None:
        if "which agents are available" in text and "list_agents" in self._tools:
            return Plan(reply="Listing available agents…", tool_call=PlannedToolCall("list_agents", {}))
        return None

    def _plan_wave3_decision_why(self, text: str) -> Plan | None:
        if "why did this decision happen" in text:
            q = self._extract_query(text)
            tool = "decision_explain" if "decision_explain" in self._tools else ("knowledge_search" if "knowledge_search" in self._tools else None)
            if tool:
                return Plan(reply=f"Explaining decision '{q}'…", tool_call=PlannedToolCall(tool, {"query": q}))
        return None

    def _plan_wave3_audit_proof(self, text: str) -> Plan | None:
        if "audit proof" in text or "show me the audit proof" in text:
            return Plan(reply="Fetching audit proof…", tool_call=PlannedToolCall("list_recent_activity", {})) if "list_recent_activity" in self._tools else None
        return None

    def _plan_wave3_connector_health(self, text: str) -> Plan | None:
        if "which connector is unhealthy" in text or "connector is unhealthy" in text:
            return Plan(reply="Checking connector health…", tool_call=PlannedToolCall("list_integrations", {})) if "list_integrations" in self._tools else None
        return None

    def _plan_wave3_workflow_build(self, text: str) -> Plan | None:
        if "build a workflow" in text and "list_workflows" in self._tools:
            q = self._extract_query(text)
            return Plan(reply=f"Building workflow for '{q}'…", tool_call=PlannedToolCall("list_workflows", {}))
        return None

    def _plan_wave3_approval_needed(self, text: str) -> Plan | None:
        if "what needs my approval" in text:
            return Plan(reply="Checking approvals…", tool_call=PlannedToolCall("list_recent_activity", {})) if "list_recent_activity" in self._tools else None
        return None

    def _plan_wave3_scenario_impact(self, text: str) -> Plan | None:
        if "show me the impact of this scenario" in text or "impact of this scenario" in text:
            return Plan(reply="Fetching scenario impact…", tool_call=PlannedToolCall("simulation_state", {})) if "simulation_state" in self._tools else None
        return None

    def _plan_wave4_what_happening(self, text: str) -> Plan | None:
        if "what's happening in my company" in text or "what is happening" in text:
            return Plan(reply="Fetching company overview…", tool_call=PlannedToolCall("system_health" if "system_health" in self._tools else "list_recent_activity", {}))
        return None

    def _plan_wave4_what_needs_attention(self, text: str) -> Plan | None:
        if "what needs my attention" in text or "what needs attention" in text:
            return Plan(reply="Checking what needs your attention…", tool_call=PlannedToolCall("list_recent_activity", {})) if "list_recent_activity" in self._tools else None
        return None

    def _plan_wave4_why_failed(self, text: str) -> Plan | None:
        if "why did this operation fail" in text or "why did operation fail" in text:
            return Plan(reply="Diagnosing failure…", tool_call=PlannedToolCall("runtime_diagnostics", {})) if "runtime_diagnostics" in self._tools else None
        return None

    def _plan_wave4_ai_spend(self, text: str) -> Plan | None:
        if "what is our ai spend" in text or "ai spend" in text:
            return Plan(reply="Fetching AI spend…", tool_call=PlannedToolCall("system_health", {})) if "system_health" in self._tools else None
        return None

    def _plan_wave4_underperforming(self, text: str) -> Plan | None:
        if "which agents are underperforming" in text or "agents underperforming" in text:
            return Plan(reply="Checking agent performance…", tool_call=PlannedToolCall("list_agents", {})) if "list_agents" in self._tools else None
        return None

    def _plan_wave4_top_risks(self, text: str) -> Plan | None:
        if "top operational risks" in text or "show me our top operational risks" in text:
            return Plan(reply="Fetching top risks…", tool_call=PlannedToolCall("system_health", {})) if "system_health" in self._tools else None
        return None

    def _plan_m1_what_do_we_know(self, text: str) -> Plan | None:
        if "what do we know about" in text and "knowledge_search" in self._tools:
            q = self._extract_query(text); return Plan(reply=f"Searching for '{q}'…", tool_call=PlannedToolCall("knowledge_search", {"query": q}))
        return None
    def _plan_m1_what_happened(self, text: str) -> Plan | None:
        if "what happened previously" in text and "list_recent_activity" in self._tools:
            return Plan(reply="Fetching history…", tool_call=PlannedToolCall("list_recent_activity", {}))
        return None
    def _plan_m1_why_decision(self, text: str) -> Plan | None:
        if "why did we make this decision" in text and "knowledge_search" in self._tools:
            return Plan(reply="Explaining decision…", tool_call=PlannedToolCall("knowledge_search", {"query": text}))
        return None
    def _plan_m1_show_evidence(self, text: str) -> Plan | None:
        if "show evidence" in text and "knowledge_search" in self._tools:
            return Plan(reply="Gathering evidence…", tool_call=PlannedToolCall("knowledge_search", {"query": text}))
        return None
    def _plan_m1_what_changed(self, text: str) -> Plan | None:
        if text.strip() == "what changed?" and "list_recent_activity" in self._tools:
            return Plan(reply="Checking what changed…", tool_call=PlannedToolCall("list_recent_activity", {}))
        return None
    def _plan_m1_similar_decisions(self, text: str) -> Plan | None:
        if "what decisions were similar" in text and "list_recent_activity" in self._tools:
            return Plan(reply="Finding similar decisions…", tool_call=PlannedToolCall("list_recent_activity", {}))
        return None
    def _plan_m1_what_affected(self, text: str) -> Plan | None:
        if "what is affected by this" in text and "list_recent_activity" in self._tools:
            return Plan(reply="Finding affected systems…", tool_call=PlannedToolCall("list_recent_activity", {}))
        return None
    def _plan_m1_what_depends(self, text: str) -> Plan | None:
        if "what depends on this" in text and "list_recent_activity" in self._tools:
            return Plan(reply="Finding dependencies…", tool_call=PlannedToolCall("list_recent_activity", {}))
        return None
    def _plan_m2_what_changed_today(self, text: str) -> Plan | None:
        if "what changed today" in text and "list_recent_activity" in self._tools:
            return Plan(reply="Fetching today's changes…", tool_call=PlannedToolCall("list_recent_activity", {}))
        return None
    def _plan_m2_why_kpi(self, text: str) -> Plan | None:
        if "why did this kpi change" in text and "system_health" in self._tools:
            return Plan(reply="Analyzing KPI change…", tool_call=PlannedToolCall("system_health", {}))
        return None
    def _plan_m2_biggest_risks(self, text: str) -> Plan | None:
        if "what are the biggest risks" in text and "system_health" in self._tools:
            return Plan(reply="Fetching biggest risks…", tool_call=PlannedToolCall("system_health", {}))
        return None
    def _plan_m2_what_likely(self, text: str) -> Plan | None:
        if "what is likely to happen next" in text and "system_health" in self._tools:
            return Plan(reply="Predicting next…", tool_call=PlannedToolCall("system_health", {}))
        return None
    def _plan_m3_why_failed(self, text: str) -> Plan | None:
        if "why did this mission fail" in text and "runtime_diagnostics" in self._tools:
            return Plan(reply="Diagnosing mission…", tool_call=PlannedToolCall("runtime_diagnostics", {}))
        return None
    def _plan_m3_recover(self, text: str) -> Plan | None:
        if "recover this mission" in text and "runtime_diagnostics" in self._tools:
            return Plan(reply="Recovering mission…", tool_call=PlannedToolCall("runtime_diagnostics", {}))
        return None
    def _plan_m3_which_agent(self, text: str) -> Plan | None:
        if "which agent should handle this" in text and "list_agents" in self._tools:
            return Plan(reply="Finding best agent…", tool_call=PlannedToolCall("list_agents", {}))
        return None
    def _plan_m3_who_overloaded(self, text: str) -> Plan | None:
        if "who is overloaded" in text and "workforce_overview" in self._tools:
            return Plan(reply="Checking overload…", tool_call=PlannedToolCall("workforce_overview", {}))
        return None
    def _plan_m3_build_team(self, text: str) -> Plan | None:
        if "build a team for this objective" in text and "list_agents" in self._tools:
            return Plan(reply="Building team…", tool_call=PlannedToolCall("list_agents", {}))
        return None

    def _plan_page_context(self, text: str) -> Plan | None:
        """Answer questions about the current page context — COPILOT-NATIVE GUIDANCE."""
        # "What am I looking at?" / "Explain this" — context-aware via frontend's current_route
        # The frontend sends current_route in the Copilot context; the service layer
        # can resolve it to a human description. For the planner, we match the
        # utterance and return a direct explanation without requiring a tool call,
        # unless the user asks for navigation/action.
        context_phrases = (
            "what am i looking at",
            "what is this",
            "explain this",
            "what am i seeing",
            "describe this page",
            "what does this do",
            "what does this page do",
            "where am i",
        )
        if any(p in text for p in context_phrases):
            return Plan(
                reply=(
                    "You are viewing the EAIP Enterprise Console. "
                    "The dashboard is your command center: it summarizes operating state, active agents, "
                    "missions, workflows, knowledge and business intelligence. "
                    "The Knowledge Graph shows how enterprise entities connect. "
                    "Missions execute governed workflows; agents are your AI workforce. "
                    "Ask me to navigate ('Show me the knowledge graph'), explain a specific item ('Explain this node'), "
                    "or say 'Give me a demo' for a guided walkthrough of the full platform."
                )
            )
        if "looking at" in text or "route" in text or "page" in text:
            return Plan(reply="You are currently viewing the EAIP Enterprise Console interface.")
        return None

    def _plan_demo_request(self, text: str) -> Plan | None:
        """Safe full-platform demo — COPILOT-NATIVE GUIDANCE (no 'Start Demo' button)."""
        demo_phrases = (
            "give me a demo",
            "show me what eaip can do",
            "show me how eaip works",
            "take me through",
            "complete demo",
            "full demo",
            "walk me through",
            "show me the platform",
            "explain how this works",
        )
        if any(p in text for p in demo_phrases):
            return Plan(
                reply=(
                    "I will walk you through EAIP — a safe, synthetic demonstration:\n\n"
                    "1. **Dashboard** — your enterprise command center (operating state, agents, success rate)\n"
                    "2. **Knowledge Intelligence** — entities and relationships in the graph\n"
                    "3. **Agents & Workforce** — your AI workforce and capacity\n"
                    "4. **Missions** — governed, long-running objectives\n"
                    "5. **Workflows** — orchestration across agents and tools\n"
                    "6. **Simulation** — what-if scenarios before execution\n"
                    "7. **Governance** — approvals, policies, audit trail\n"
                    "8. **Enterprise Loop** — the bounded autonomous cycle\n\n"
                    "Say 'Next' to step through, or ask about any area directly. "
                    "Ask 'Show me the knowledge graph' to jump there, or 'Which agents are working?' to inspect the workforce. "
                    "All operations are synthetic and governed — nothing destructive will run."
                )
            )
        return None

    def _plan_navigation_request(self, text: str) -> Plan | None:
        """Navigate/Inspect intents — COPILOT-NATIVE GUIDANCE."""
        nav_map: dict[str, str] = {
            "show me the knowledge graph": "The Knowledge Graph visualizes enterprise entities. It is at /knowledge/graph — I can describe its data or you can navigate there directly.",
            "open the active missions": "Active missions are at /missions — each shows status, progress, and governance. Use the sync icon to inspect a specific mission.",
            "explain this node": "Select a node in the graph — its detail panel shows type, description, connected entities, and confidence.",
            "run a simulation": "Simulations are at /simulation — they model enterprise outcomes before execution. Use 'Run simulation' to create a new run.",
            "which agents are working": "Active workforce is at /workforce — or ask 'Which agents are working right now?' and I will list them.",
            "what decisions were made": "Decisions are tracked in the activity feed and governance audit — ask 'What decisions were made today?' for specifics.",
            "show me the biggest risk": "Risk intelligence is in your briefing — ask 'What is our biggest current risk?' and I will surface the top ranked risk.",
            "why is this kpi down": "KPI movement is explained by its linked objectives and execution history — ask about a specific KPI by name.",
        }
        for phrase, reply in nav_map.items():
            if phrase in text:
                return Plan(reply=reply)
        # Generic navigation
        nav_keywords: dict[str, str] = {
            "show me the dashboard": "Your dashboard is the command center at /dashboard.",
            "open knowledge": "Knowledge is at /knowledge — collections, search, and document intelligence.",
            "open workflows": "Workflows are at /workflows — active and completed orchestrations.",
            "open workforce": "Workforce is at /workforce — agent capacity and assignments.",
            "open governance": "Governance is at /governance — policies, approvals, and audit.",
            "open monitoring": "Monitoring is at /monitoring — system health and alerts.",
        }
        for phrase, reply in nav_keywords.items():
            if phrase in text:
                return Plan(reply=reply)
        return None

    # ------------------------------------------------------------------
    # M6 — Connector & Model Fabric intents
    # ------------------------------------------------------------------

    def _plan_m6_connector_list(self, text: str) -> Plan | None:
        """Route 'what connectors are available?' to list_capabilities."""
        if any(k in text for k in ("what connectors are available", "list connectors", "available connectors", "connector list")) and "list_integrations" in self._tools:
            return Plan(reply="Listing available connectors and their capabilities...", tool_call=PlannedToolCall("list_integrations", {}))
        return None

    def _plan_m6_connector_health(self, text: str) -> Plan | None:
        """Route 'is salesforce healthy?' to connector health check."""
        if any(k in text for k in ("is salesforce healthy", "connector health", "is slack healthy", "is jira healthy", "is github healthy", "connector status")) and "list_integrations" in self._tools:
            return Plan(reply="Checking connector health status...", tool_call=PlannedToolCall("list_integrations", {}))
        return None

    def _plan_m6_connector_access(self, text: str) -> Plan | None:
        """Route 'which systems can I access?' to connector availability."""
        if any(k in text for k in ("which systems can i access", "what systems are available", "what can i connect to", "accessible systems")) and "list_integrations" in self._tools:
            return Plan(reply="Checking your accessible systems...", tool_call=PlannedToolCall("list_integrations", {}))
        return None

    def _plan_m6_model_routing(self, text: str) -> Plan | None:
        """Route 'which model should handle this?' to model routing."""
        if any(k in text for k in ("which model should handle", "best model for", "route to model", "model recommendation", "which model should i use")) and "system_health" in self._tools:
            return Plan(reply="Analyzing task requirements to recommend the best model...", tool_call=PlannedToolCall("system_health", {}))
        return None

    def _plan_m6_model_why_selected(self, text: str) -> Plan | None:
        """Route 'why was this model selected?' to routing explanation."""
        if any(k in text for k in ("why was this model selected", "why this model", "model selection reason", "explain model choice")) and "system_health" in self._tools:
            return Plan(reply="Retrieving model routing decision details...", tool_call=PlannedToolCall("system_health", {}))
        return None

    def _plan_m6_cheapest_model(self, text: str) -> Plan | None:
        """Route 'what's the cheapest approved model?' to model comparison."""
        if any(k in text for k in ("cheapest model", "lowest cost model", "most affordable model", "cheapest approved")) and "system_health" in self._tools:
            return Plan(reply="Comparing model costs across approved models...", tool_call=PlannedToolCall("system_health", {}))
        return None

    def _plan_m6_failover_why(self, text: str) -> Plan | None:
        """Route 'why did EAIP fail over?' to failover chain inspection."""
        if any(k in text for k in ("why did eaip fail over", "failover reason", "why failover", "model failover", "failover chain")) and "runtime_diagnostics" in self._tools:
            return Plan(reply="Inspecting failover chain and decision...", tool_call=PlannedToolCall("runtime_diagnostics", {}))
        return None

    # M7 — Marketplace + Deployment intents
    def _plan_m7_find_pack(self, text: str) -> Plan | None:
        if "find a" in text and "solution pack" in text and "marketplace_search" in self._tools:
            return Plan(reply="Searching for solution packs…", tool_call=PlannedToolCall("marketplace_search", {"query": text}))
        return None
    def _plan_m7_available_agents(self, text: str) -> Plan | None:
        if "what agents are available" in text and "list_agents" in self._tools:
            return Plan(reply="Listing available agents…", tool_call=PlannedToolCall("list_agents", {}))
        return None
    def _plan_m7_trusted(self, text: str) -> Plan | None:
        if "is this package trusted" in text or "is this trusted" in text:
            return Plan(reply="Checking package trust — use marketplace detail to verify signatures.", tool_call=PlannedToolCall("marketplace_search", {"query": text}) if "marketplace_search" in self._tools else None)  # type: ignore[arg-type]
        return None
    def _plan_m7_why_cant_install(self, text: str) -> Plan | None:
        if "why can't i install" in text:
            return Plan(reply="Checking install requirements: trust, dependencies, compatibility, and permissions.")
        return None
    def _plan_m7_sandbox_install(self, text: str) -> Plan | None:
        if "install this package in sandbox" in text:
            return Plan(reply="Sandbox flow: verify → dependency check → security → test → governance → approval → install.")
        return None
    def _plan_m7_version_diff(self, text: str) -> Plan | None:
        if "what changed between versions" in text:
            return Plan(reply="Version history shows changelog, compatibility, and deprecation per artifact.")
        return None
    def _plan_m7_deployment_status(self, text: str) -> Plan | None:
        if "show me the deployment status" in text or "deployment status" in text:
            return Plan(reply="Deployment validation returns READY / NOT READY / HUMAN CONFIGURATION REQUIRED.")
        return None
    # M8 — Scale + Ops intents
    def _plan_m8_what_unhealthy(self, text: str) -> Plan | None:
        if "what is unhealthy" in text and "system_health" in self._tools:
            return Plan(reply="Checking health across runtimes and services…", tool_call=PlannedToolCall("system_health", {}))
        return None
    def _plan_m8_which_runtime(self, text: str) -> Plan | None:
        if "which runtime should handle" in text and "list_agents" in self._tools:
            return Plan(reply="Routing via capability-matched runtime scheduler…", tool_call=PlannedToolCall("list_agents", {}))
        return None
    def _plan_m8_near_capacity(self, text: str) -> Plan | None:
        if "are we near capacity" in text and "system_health" in self._tools:
            return Plan(reply="Checking capacity forecasts…", tool_call=PlannedToolCall("system_health", {}))
        return None
    def _plan_m8_incidents_attention(self, text: str) -> Plan | None:
        if "what incidents need attention" in text:
            return Plan(reply="Incidents are correlated, diagnosed, and prioritized in the ops center.")
        return None
    def _plan_m8_bottleneck(self, text: str) -> Plan | None:
        if "where is the bottleneck" in text and "workforce_bottlenecks" in self._tools:
            return Plan(reply="Detecting bottlenecks…", tool_call=PlannedToolCall("workforce_bottlenecks", {}))
        return None
    def _plan_m8_what_will_fail(self, text: str) -> Plan | None:
        if "what will fail next" in text and "system_health" in self._tools:
            return Plan(reply="Running failure prediction…", tool_call=PlannedToolCall("system_health", {}))
        return None
    def _plan_m8_failover_what(self, text: str) -> Plan | None:
        if "what would fail over" in text:
            return Plan(reply="Failover would route to next healthy capability-matched runtime.")
        return None
    # M9 — Executive OS intents
    def _plan_m9_what_changed(self, text: str) -> Plan | None:
        if text.strip() in ("what changed?", "what changed") and "list_recent_activity" in self._tools:
            return Plan(reply="Fetching executive briefing: what changed…", tool_call=PlannedToolCall("list_recent_activity", {}))
        return None
    def _plan_m9_why(self, text: str) -> Plan | None:
        if text.strip() == "why?" and "list_recent_activity" in self._tools:
            return Plan(reply="Explaining causal context…", tool_call=PlannedToolCall("list_recent_activity", {}))
        return None
    def _plan_m9_needs_attention(self, text: str) -> Plan | None:
        if "what needs my attention" in text and "list_recent_activity" in self._tools:
            return Plan(reply="Checking executive attention items…", tool_call=PlannedToolCall("list_recent_activity", {}))
        return None
    def _plan_m9_should_approve(self, text: str) -> Plan | None:
        if "what should i approve" in text:
            return Plan(reply="Pending approvals: financial_change, external_write, destructive — check governance queue.")
        return None
    def _plan_m9_at_risk(self, text: str) -> Plan | None:
        if "what is at risk" in text and "system_health" in self._tools:
            return Plan(reply="Fetching risk radar…", tool_call=PlannedToolCall("system_health", {}))
        return None
    def _plan_m9_likely_happen(self, text: str) -> Plan | None:
        if "what is likely to happen" in text and "system_health" in self._tools:
            return Plan(reply="Forecasting likely outcomes…", tool_call=PlannedToolCall("system_health", {}))
        return None
    def _plan_m9_show_evidence(self, text: str) -> Plan | None:
        if "show me evidence" in text and "knowledge_search" in self._tools:
            return Plan(reply="Gathering evidence chain…", tool_call=PlannedToolCall("knowledge_search", {"query": text}))
        return None
    def _plan_m9_run_scenario(self, text: str) -> Plan | None:
        if "run the scenario" in text and "simulation_state" in self._tools:
            return Plan(reply="Running scenario simulation…", tool_call=PlannedToolCall("simulation_state", {}))
        return None
    def _plan_m9_recommend(self, text: str) -> Plan | None:
        if "recommend a response" in text and "system_health" in self._tools:
            return Plan(reply="Generating recommendation…", tool_call=PlannedToolCall("system_health", {}))
        return None
    # M4 — PSF + RIL + EGE + KCR intents
    def _plan_m4_strategy_priorities(self, text: str) -> Plan | None:
        if "strategic priorities" in text or "what are our priorities" in text:
            return Plan(reply="Fetching strategic priorities from the framework…", tool_call=PlannedToolCall("list_objectives", {"status": "active"}))
        return None
    def _plan_m4_strategy_changed(self, text: str) -> Plan | None:
        if "what changed in strategy" in text or "strategy changed" in text:
            return Plan(reply="Comparing strategic state history…", tool_call=PlannedToolCall("list_recent_activity", {}))
        return None
    def _plan_m4_initiatives_at_risk(self, text: str) -> Plan | None:
        if "initiatives at risk" in text or "which initiatives" in text:
            return Plan(reply="Checking initiatives with elevated risk…", tool_call=PlannedToolCall("system_health", {}))
        return None
    def _plan_m4_missions_for_objective(self, text: str) -> Plan | None:
        if "missions support this objective" in text or "missions for objective" in text:
            return Plan(reply="Tracing objective → initiatives → missions…", tool_call=PlannedToolCall("list_recent_activity", {}))
        return None
    def _plan_m4_why_kpi(self, text: str) -> Plan | None:
        if "why are we missing this kpi" in text or "why is kpi failing" in text:
            return Plan(reply="Tracing KPI → objective → execution chain…", tool_call=PlannedToolCall("system_health", {}))
        return None
    def _plan_m4_what_should_change(self, text: str) -> Plan | None:
        if "what should change" in text:
            return Plan(reply="Analyzing strategic gaps and proposing changes…", tool_call=PlannedToolCall("system_health", {}))
        return None
    def _plan_m4_show_reasoning(self, text: str) -> Plan | None:
        if "show the reasoning" in text or "show reasoning" in text:
            return Plan(reply="Showing intelligence cycle reasoning…", tool_call=PlannedToolCall("list_recent_activity", {}))
        return None
    def _plan_m4_show_evidence_strategy(self, text: str) -> Plan | None:
        if "show the evidence" in text and "strategy" in text:
            return Plan(reply="Gathering provenance chain for strategy decisions…", tool_call=PlannedToolCall("knowledge_search", {"query": "strategy provenance"}))
        return None
    # M5 — Learning + Governance + Audit intents
    def _plan_m5_why_did_eaip(self, text: str) -> Plan | None:
        if "why did eaip do this" in text or "why did the system do this" in text:
            return Plan(reply="Inspecting execution proof to explain why EAIP took this action…", tool_call=PlannedToolCall("inspect_execution", {}))
        return None
    def _plan_m5_show_proof(self, text: str) -> Plan | None:
        if "show me the execution proof" in text or "show execution proof" in text:
            return Plan(reply="Retrieving execution proof…", tool_call=PlannedToolCall("inspect_execution", {}))
        return None
    def _plan_m5_was_approved(self, text: str) -> Plan | None:
        if "was this action approved" in text or "was this approved" in text:
            return Plan(reply="Checking approval proof for this action…", tool_call=PlannedToolCall("list_recent_activity", {}))
        return None
    def _plan_m5_which_policy(self, text: str) -> Plan | None:
        if "which policy allowed" in text or "which policy governs" in text:
            return Plan(reply="Tracing governance policy that authorized this action…", tool_call=PlannedToolCall("list_recent_activity", {}))
        return None
    def _plan_m5_what_model_received(self, text: str) -> Plan | None:
        if "what did the model receive" in text or "what did model receive" in text:
            return Plan(reply="Inspecting model input hash and context…", tool_call=PlannedToolCall("inspect_execution", {}))
        return None
    def _plan_m5_what_tool_ran(self, text: str) -> Plan | None:
        if "what tool ran" in text or "which tool ran" in text:
            return Plan(reply="Inspecting tool execution from audit chain…", tool_call=PlannedToolCall("inspect_execution", {}))
        return None
    def _plan_m5_verify_execution(self, text: str) -> Plan | None:
        if "can i verify this execution" in text or "verify this execution" in text:
            return Plan(reply="Verifying execution chain integrity…", tool_call=PlannedToolCall("inspect_execution", {}))
        return None
    def _plan_m5_what_learned(self, text: str) -> Plan | None:
        if "what did eaip learn" in text or "what has eaip learned" in text:
            return Plan(reply="Fetching organizational lessons learned…", tool_call=PlannedToolCall("list_recent_activity", {}))
        return None
    # M6 — Connectors + Model Fabric intents
    def _plan_m6_connectors_available(self, text: str) -> Plan | None:
        if "what connectors are available" in text or "which connectors" in text:
            return Plan(reply="Listing available connectors and their capabilities…", tool_call=PlannedToolCall("list_connectors", {}))
        return None
    def _plan_m6_is_healthy(self, text: str) -> Plan | None:
        if "is salesforce healthy" in text or "is" in text and "healthy" in text and "connector" in text:
            return Plan(reply="Checking connector health…", tool_call=PlannedToolCall("connector_health", {}))
        return None
    def _plan_m6_which_systems_access(self, text: str) -> Plan | None:
        if "which systems can i access" in text or "which systems available" in text:
            return Plan(reply="Listing tenant-accessible systems…", tool_call=PlannedToolCall("list_connectors", {}))
        return None
    def _plan_m6_which_model(self, text: str) -> Plan | None:
        if "which model should handle this" in text or "which model for this" in text:
            return Plan(reply="Routing to the best model for this task…", tool_call=PlannedToolCall("model_route", {}))
        return None
    def _plan_m6_why_model_selected(self, text: str) -> Plan | None:
        if "why was this model selected" in text or "why this model" in text:
            return Plan(reply="Explaining model routing decision…", tool_call=PlannedToolCall("model_route", {}))
        return None
    def _plan_m6_cheapest_model(self, text: str) -> Plan | None:
        if "cheapest approved model" in text or "cheapest model" in text:
            return Plan(reply="Finding lowest-cost approved model…", tool_call=PlannedToolCall("model_route", {}))
        return None
    def _plan_m6_why_failover(self, text: str) -> Plan | None:
        if "why did eaip fail over" in text or "why failover" in text:
            return Plan(reply="Tracing failover chain and policy decision…", tool_call=PlannedToolCall("inspect_execution", {}))
        return None

    # M10 — Autonomous Enterprise Loop intents
    def _plan_m10_what_happening(self, text: str) -> Plan | None:
        if text.strip() in ("what is happening?", "what is happening") and "list_recent_activity" in self._tools:
            return Plan(reply="Current loop phase: OBSERVE→UNDERSTAND→… — checking enterprise loop…", tool_call=PlannedToolCall("list_recent_activity", {}))
        return None
    def _plan_m10_why_matters(self, text: str) -> Plan | None:
        if "what matters" in text and "list_recent_activity" in self._tools:
            return Plan(reply="Prioritizing by impact, risk, and KPI gap…", tool_call=PlannedToolCall("list_recent_activity", {}))
        return None
    def _plan_m10_what_will_happen(self, text: str) -> Plan | None:
        if "what will happen" in text and "system_health" in self._tools:
            return Plan(reply="Simulating forward…", tool_call=PlannedToolCall("system_health", {}))
        return None
    def _plan_m10_what_should_do(self, text: str) -> Plan | None:
        if text.strip() in ("what should we do?", "what should we do", "do it.") and "list_recent_activity" in self._tools:
            return Plan(reply="Recommending governed next action…", tool_call=PlannedToolCall("list_recent_activity", {}))
        return None
    def _plan_m10_why_did_you_do(self, text: str) -> Plan | None:
        if "why did you do that" in text:
            return Plan(reply="Every autonomous step has proof: intent, policy, decision, proof ref — see audit chain.")
        return None
    def _plan_m10_show_me(self, text: str) -> Plan | None:
        if text.strip() == "show me." and "list_recent_activity" in self._tools:
            return Plan(reply="Showing control-plane state…", tool_call=PlannedToolCall("list_recent_activity", {}))
        return None
    def _plan_m10_undo(self, text: str) -> Plan | None:
        if "undo" in text or "recover" in text:
            return Plan(reply="Recovery: checkpoint resume with governance — see long-missions and loop recovery.")
        return None
    def _plan_m10_learn(self, text: str) -> Plan | None:
        if "learn from this" in text:
            return Plan(reply="Learning loop: outcome → evaluation → learning record → lesson — governed adaptation.")
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
