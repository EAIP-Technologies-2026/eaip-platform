"""M5 Conductor intent extensions for learning, audit, and governance."""

from __future__ import annotations

import re
from typing import Any

from eaip.copilot.planner import Plan, PlannedToolCall


class M5IntentRouter:
    """Routes M5-specific intents for learning, audit proof, and governance queries."""

    def __init__(self, tools: dict[str, Any]) -> None:
        self._tools = tools

    def route(self, text: str, message: str) -> Plan | None:
        """Try each M5 intent rule, returning the first match."""
        for outcome in (
            self._plan_why_did_eaip_do_this(text),
            self._plan_show_execution_proof(text),
            self._plan_was_action_approved(text),
            self._plan_which_policy_allowed(text),
            self._plan_what_did_model_receive(text),
            self._plan_what_tool_ran(text),
            self._plan_verify_execution(text),
            self._plan_what_did_eaip_learn(text),
            self._plan_show_recent_lessons(text),
            self._plan_pending_adaptations(text),
        ):
            if outcome is not None:
                return outcome
        return None

    def _plan_why_did_eaip_do_this(self, text: str) -> Plan | None:
        if any(p in text for p in ("why did eaip", "why did the system", "why did it do")):
            return Plan(
                reply="Let me inspect the execution proof to show you why EAIP took that action.",
                tool_call=PlannedToolCall("inspect_execution", {}),
            )
        return None

    def _plan_show_execution_proof(self, text: str) -> Plan | None:
        if any(p in text for p in ("show me the execution proof", "show proof", "execution proof", "show the proof")):
            match = re.search(r"(?:proof|execution)\s+(?:for\s+)?([a-z0-9_-]+)", text)
            execution_id = match.group(1) if match else ""
            return Plan(
                reply="Here is the execution proof with full cryptographic verification.",
                tool_call=PlannedToolCall("get_execution_proof", {"execution_id": execution_id}),
            )
        return None

    def _plan_was_action_approved(self, text: str) -> Plan | None:
        if any(p in text for p in ("was this approved", "was this action approved", "is this approved", "approval status")):
            return Plan(
                reply="Let me look up the approval proof for this action.",
                tool_call=PlannedToolCall("check_approval_proof", {}),
            )
        return None

    def _plan_which_policy_allowed(self, text: str) -> Plan | None:
        if any(p in text for p in ("which policy", "what policy", "policy allowed", "policy allowed it")):
            return Plan(
                reply="Tracing the policy decision for this execution.",
                tool_call=PlannedToolCall("trace_policy_decision", {}),
            )
        return None

    def _plan_what_did_model_receive(self, text: str) -> Plan | None:
        if any(p in text for p in ("what did the model receive", "model input", "what was sent to the model")):
            return Plan(
                reply="Here is the input hash inspection showing what the model received.",
                tool_call=PlannedToolCall("inspect_model_input", {}),
            )
        return None

    def _plan_what_tool_ran(self, text: str) -> Plan | None:
        if any(p in text for p in ("what tool ran", "which tool", "tool that ran", "tool hash")):
            return Plan(
                reply="Here is the tool hash inspection for this execution.",
                tool_call=PlannedToolCall("inspect_tool_hash", {}),
            )
        return None

    def _plan_verify_execution(self, text: str) -> Plan | None:
        if any(p in text for p in ("can i verify", "verify this execution", "verify execution", "chain verification")):
            return Plan(
                reply="Running full chain verification for your tenant.",
                tool_call=PlannedToolCall("verify_chain", {}),
            )
        return None

    def _plan_what_did_eaip_learn(self, text: str) -> Plan | None:
        if any(p in text for p in ("what did eaip learn", "what has eaip learned", "learning history", "what has been learned")):
            return Plan(
                reply="Here is the organizational learning history.",
                tool_call=PlannedToolCall("get_learning_history", {}),
            )
        return None

    def _plan_show_recent_lessons(self, text: str) -> Plan | None:
        if any(p in text for p in ("show recent lessons", "recent lessons", "show lessons", "what lessons")):
            return Plan(
                reply="Here are the recent lessons learned by EAIP.",
                tool_call=PlannedToolCall("list_lessons", {}),
            )
        return None

    def _plan_pending_adaptations(self, text: str) -> Plan | None:
        if any(p in text for p in ("pending adaptations", "adaptations pending", "what adaptations", "proposed changes")):
            return Plan(
                reply="Here are the pending adaptation proposals.",
                tool_call=PlannedToolCall("list_adaptations", {}),
            )
        return None


__all__ = ["M5IntentRouter"]
