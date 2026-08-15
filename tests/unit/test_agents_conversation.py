from __future__ import annotations

import pytest

from eaip.agents.conversation import ConversationRuntime


class TestConversationRuntime:
    @pytest.fixture
    def runtime(self) -> ConversationRuntime:
        return ConversationRuntime()

    def test_create_session(self, runtime: ConversationRuntime) -> None:
        session = runtime.create_session("s1", "test", participants=["agent1", "agent2"])
        assert session.session_id == "s1"
        assert len(session.participants) == 2

    def test_get_session(self, runtime: ConversationRuntime) -> None:
        runtime.create_session("s1", "test")
        session = runtime.get_session("s1")
        assert session is not None

    def test_get_nonexistent_session(self, runtime: ConversationRuntime) -> None:
        session = runtime.get_session("nonexistent")
        assert session is None

    def test_list_sessions(self, runtime: ConversationRuntime) -> None:
        runtime.create_session("s1", "a")
        runtime.create_session("s2", "b")
        assert len(runtime.list_sessions()) == 2

    def test_add_participant(self, runtime: ConversationRuntime) -> None:
        runtime.create_session("s1", "test")
        result = runtime.add_participant("s1", "agent3")
        assert result is True
        session = runtime.get_session("s1")
        assert session is not None
        assert "agent3" in session.participants

    def test_remove_participant(self, runtime: ConversationRuntime) -> None:
        runtime.create_session("s1", "test", participants=["agent1", "agent2"])
        result = runtime.remove_participant("s1", "agent1")
        assert result is True
        session = runtime.get_session("s1")
        assert session is not None
        assert "agent1" not in session.participants

    def test_submit_turn(self, runtime: ConversationRuntime) -> None:
        runtime.create_session("s1", "test", participants=["agent1"])
        turn = runtime.submit_turn("s1", "agent1", "hello")
        assert turn is not None
        assert turn.message == "hello"

    def test_submit_turn_invalid_agent(self, runtime: ConversationRuntime) -> None:
        runtime.create_session("s1", "test", participants=["agent1"])
        turn = runtime.submit_turn("s1", "unknown", "hello")
        assert turn is None

    def test_complete_turn(self, runtime: ConversationRuntime) -> None:
        runtime.create_session("s1", "test", participants=["agent1"])
        turn = runtime.submit_turn("s1", "agent1", "hello")
        assert turn is not None
        result = runtime.complete_turn("s1", turn.turn_id, "world")
        assert result is True

    def test_handoff(self, runtime: ConversationRuntime) -> None:
        runtime.create_session("s1", "test", participants=["agent1", "agent2"])
        runtime.submit_turn("s1", "agent1", "hello")
        result = runtime.handoff("s1", "agent1", "agent2")
        assert result is True
        session = runtime.get_session("s1")
        assert session is not None
        assert session.current_agent == "agent2"

    def test_get_turns(self, runtime: ConversationRuntime) -> None:
        runtime.create_session("s1", "test", participants=["agent1"])
        runtime.submit_turn("s1", "agent1", "msg1")
        runtime.submit_turn("s1", "agent1", "msg2")
        turns = runtime.get_turns("s1")
        assert len(turns) == 2

    def test_close_session(self, runtime: ConversationRuntime) -> None:
        runtime.create_session("s1", "test")
        result = runtime.close_session("s1")
        assert result is True
        session = runtime.get_session("s1")
        assert session is not None
        assert session.is_active is False
