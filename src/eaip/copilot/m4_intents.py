"""M4 Conductor intents — strategy, intelligence cycles, governance."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from eaip.tools.base import Tool


@dataclass(frozen=True, slots=True)
class M4PlannedToolCall:
    tool_name: str
    arguments: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class M4Plan:
    reply: str
    tool_call: M4PlannedToolCall | None = None
    confidence: float = 1.0


def register_m4_intents(planner: Any) -> None:
    """Monkey-patch M4 strategy intents onto an existing ConductorPlanner instance."""
    original_route = planner._route

    def _m4_route(self: Any, text: str, message: str) -> Any:
        # try M4 intents first
        for outcome in (
            _plan_strategy_priorities(text, self._tools),
            _plan_strategy_changes(text, self._tools),
            _plan_strategy_risk(text, self._tools),
            _plan_strategy_missions_for_objective(text, self._tools),
            _plan_strategy_why_kpi(text, self._tools),
            _plan_strategy_what_should_change(text, self._tools),
            _plan_strategy_show_reasoning(text, self._tools),
            _plan_strategy_show_evidence(text, self._tools),
        ):
            if outcome is not None:
                return outcome
        # fall back to original
        return original_route(text, message)

    import types
    planner._route = types.MethodType(_m4_route, planner)


def _plan_strategy_priorities(text: str, tools: dict[str, Tool]) -> M4Plan | None:
    if ("strategic priorit" in text or "strategy priorit" in text or "our objectives" in text) and "list_objectives" in tools:
        return M4Plan(reply="Fetching strategic priorities…", tool_call=M4PlannedToolCall("list_objectives", {}))
    return None


def _plan_strategy_changes(text: str, tools: dict[str, Tool]) -> M4Plan | None:
    if ("what changed in strategy" in text or "strategy changes" in text) and "get_state_history" in tools:
        return M4Plan(reply="Retrieving strategy change history…", tool_call=M4PlannedToolCall("get_state_history", {}))
    return None


def _plan_strategy_risk(text: str, tools: dict[str, Tool]) -> M4Plan | None:
    if ("initiatives at risk" in text or "strategic risks" in text or "which initiatives are at risk" in text) and "list_risks" in tools:
        return M4Plan(reply="Analyzing strategic risks…", tool_call=M4PlannedToolCall("list_risks", {}))
    return None


def _plan_strategy_missions_for_objective(text: str, tools: dict[str, Tool]) -> M4Plan | None:
    if ("missions support" in text or "which missions" in text) and "trace_objective" in tools:
        return M4Plan(reply="Tracing strategy-to-execution chain…", tool_call=M4PlannedToolCall("trace_objective", {}))
    return None


def _plan_strategy_why_kpi(text: str, tools: dict[str, Tool]) -> M4Plan | None:
    if ("why are we missing" in text and "kpi" in text) and "list_kpis" in tools:
        return M4Plan(reply="Analyzing KPI gap through strategy chain…", tool_call=M4PlannedToolCall("list_kpis", {}))
    return None


def _plan_strategy_what_should_change(text: str, tools: dict[str, Tool]) -> M4Plan | None:
    if ("what should change" in text) and "list_cycles" in tools:
        return M4Plan(reply="Reviewing intelligence cycle reflections…", tool_call=M4PlannedToolCall("list_cycles", {}))
    return None


def _plan_strategy_show_reasoning(text: str, tools: dict[str, Tool]) -> M4Plan | None:
    if ("show the reasoning" in text or "reasoning chain" in text) and "replay_cycle" in tools:
        return M4Plan(reply="Replaying intelligence cycle…", tool_call=M4PlannedToolCall("replay_cycle", {}))
    return None


def _plan_strategy_show_evidence(text: str, tools: dict[str, Tool]) -> M4Plan | None:
    if ("show the evidence" in text or "evidence chain" in text) and "get_decision_history" in tools:
        return M4Plan(reply="Fetching decision evidence chain…", tool_call=M4PlannedToolCall("get_decision_history", {}))
    return None


__all__ = ["register_m4_intents"]
