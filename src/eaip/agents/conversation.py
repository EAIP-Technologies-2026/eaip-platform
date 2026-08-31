"""Multi-agent conversation runtime — sessions, turn management, agent handoff, history."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from eaip.logging.context import get_logger
from eaip.shared.time import utc_now


class TurnStatus(StrEnum):
    ACTIVE = "active"
    COMPLETED = "completed"
    TIMEOUT = "timeout"


class ConversationTurn:
    def __init__(self, turn_id: str, session_id: str, agent_id: str, message: str) -> None:
        self.turn_id = turn_id
        self.session_id = session_id
        self.agent_id = agent_id
        self.message = message
        self.status = TurnStatus.ACTIVE
        self.response: str = ""
        self.started_at = utc_now()
        self.completed_at: datetime | None = None


class ConversationSession:
    def __init__(self, session_id: str, name: str = "") -> None:
        self.session_id = session_id
        self.name = name or session_id
        self.participants: list[str] = []
        self.current_agent: str = ""
        self.created_at = utc_now()
        self.is_active: bool = True


class ConversationRuntime:
    def __init__(self, event_bus: Any = None) -> None:
        self._sessions: dict[str, ConversationSession] = {}
        self._turns: dict[str, list[ConversationTurn]] = {}
        self._event_bus = event_bus
        self._log = get_logger("eaip.agents.conversation")

    def create_session(
        self, session_id: str, name: str = "", participants: list[str] | None = None
    ) -> ConversationSession:
        session = ConversationSession(session_id=session_id, name=name)
        if participants:
            session.participants = list(participants)
        if session.participants:
            session.current_agent = session.participants[0]
        self._sessions[session_id] = session
        self._turns[session_id] = []
        return session

    def get_session(self, session_id: str) -> ConversationSession | None:
        return self._sessions.get(session_id)

    def list_sessions(self) -> list[ConversationSession]:
        return list(self._sessions.values())

    def add_participant(self, session_id: str, agent_id: str) -> bool:
        session = self._sessions.get(session_id)
        if session is None:
            return False
        if agent_id not in session.participants:
            session.participants.append(agent_id)
        return True

    def remove_participant(self, session_id: str, agent_id: str) -> bool:
        session = self._sessions.get(session_id)
        if session is None or agent_id not in session.participants:
            return False
        session.participants.remove(agent_id)
        return True

    def submit_turn(self, session_id: str, agent_id: str, message: str) -> ConversationTurn | None:
        session = self._sessions.get(session_id)
        if session is None or agent_id not in session.participants:
            return None
        turn_id = f"turn-{len(self._turns.get(session_id, [])) + 1}"
        turn = ConversationTurn(
            turn_id=turn_id, session_id=session_id, agent_id=agent_id, message=message
        )
        self._turns.setdefault(session_id, []).append(turn)
        session.current_agent = agent_id
        return turn

    def complete_turn(self, session_id: str, turn_id: str, response: str = "") -> bool:
        turns = self._turns.get(session_id, [])
        for turn in turns:
            if turn.turn_id == turn_id and turn.status == TurnStatus.ACTIVE:
                turn.status = TurnStatus.COMPLETED
                turn.response = response
                turn.completed_at = utc_now()
                return True
        return False

    def handoff(self, session_id: str, from_agent: str, to_agent: str) -> bool:
        session = self._sessions.get(session_id)
        if session is None:
            return False
        if from_agent not in session.participants or to_agent not in session.participants:
            return False
        if session.current_agent != from_agent:
            return False
        session.current_agent = to_agent
        self._log.info(
            "conversation.handoff", session_id=session_id, from_agent=from_agent, to_agent=to_agent
        )
        return True

    def get_turns(self, session_id: str, limit: int = 50) -> list[ConversationTurn]:
        turns = self._turns.get(session_id, [])
        return turns[-limit:]

    def get_active_session(self, agent_id: str) -> ConversationSession | None:
        for session in self._sessions.values():
            if session.is_active and agent_id in session.participants:
                return session
        return None

    def close_session(self, session_id: str) -> bool:
        session = self._sessions.get(session_id)
        if session is None:
            return False
        session.is_active = False
        return True


__all__ = [
    "ConversationRuntime",
    "ConversationSession",
    "ConversationTurn",
    "TurnStatus",
]
