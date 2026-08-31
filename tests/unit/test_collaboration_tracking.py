"""Tests for ExecutionTracker."""

from __future__ import annotations

import pytest

from eaip.collaboration.tracking import ExecutionTracker


class TestExecutionTracker:
    @pytest.fixture
    def tracker(self) -> ExecutionTracker:
        return ExecutionTracker()

    async def test_record_event(self, tracker: ExecutionTracker) -> None:
        await tracker.record_event("s1", "task.completed", {"task_id": "t1"}, agent_id="a1")
        timeline = await tracker.get_session_timeline("s1")
        assert len(timeline) == 1
        assert timeline[0]["event_type"] == "task.completed"
        assert timeline[0]["agent_id"] == "a1"

    async def test_get_session_timeline(self, tracker: ExecutionTracker) -> None:
        await tracker.record_event("s1", "event.1", {"seq": 1})
        await tracker.record_event("s1", "event.2", {"seq": 2})
        await tracker.record_event("s2", "other", {})
        timeline = await tracker.get_session_timeline("s1")
        assert len(timeline) == 2

    async def test_get_agent_timeline(self, tracker: ExecutionTracker) -> None:
        await tracker.record_event("s1", "task.started", {}, agent_id="a1")
        await tracker.record_event("s1", "task.completed", {}, agent_id="a1")
        await tracker.record_event("s1", "task.started", {}, agent_id="a2")
        timeline = await tracker.get_agent_timeline("a1")
        assert len(timeline) == 2
        timeline_a2 = await tracker.get_agent_timeline("a2")
        assert len(timeline_a2) == 1

    async def test_generate_report(self, tracker: ExecutionTracker) -> None:
        await tracker.record_event("s1", "session.started", {"strategy": "parallel"})
        await tracker.record_event("s1", "task.completed", {"task": "t1"}, agent_id="a1")
        await tracker.record_event("s1", "session.completed", {"status": "ok"})
        report = await tracker.generate_report("s1")
        assert report["session_id"] == "s1"
        assert report["event_count"] == 3
        assert "a1" in report["agents_involved"]
        assert report["event_types"]["session.started"] == 1
        assert report["event_types"]["task.completed"] == 1

    async def test_generate_report_empty(self, tracker: ExecutionTracker) -> None:
        report = await tracker.generate_report("nonexistent")
        assert report["event_count"] == 0

    async def test_get_metrics(self, tracker: ExecutionTracker) -> None:
        await tracker.record_event("s1", "session.started", {})
        await tracker.record_event("s1", "task.completed", {}, agent_id="a1")
        await tracker.record_event("s1", "task.failed", {"error": "err"}, agent_id="a1")
        metrics = await tracker.get_metrics("s1")
        assert metrics["event_count"] == 3
        assert metrics["agents"] == 1
        assert metrics["error_count"] == 1

    async def test_get_metrics_empty(self, tracker: ExecutionTracker) -> None:
        metrics = await tracker.get_metrics("nonexistent")
        assert metrics["event_count"] == 0

    async def test_multiple_sessions_independent(self, tracker: ExecutionTracker) -> None:
        await tracker.record_event("s1", "event.1", {})
        await tracker.record_event("s2", "event.2", {})
        s1_timeline = await tracker.get_session_timeline("s1")
        s2_timeline = await tracker.get_session_timeline("s2")
        assert len(s1_timeline) == 1
        assert len(s2_timeline) == 1
