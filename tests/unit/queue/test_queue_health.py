from __future__ import annotations

import pytest

from eaip.queue.health import QueueHealthCheck


def _make_mock_queue(name: str, **stats_kw: int) -> object:
    """Create a mock queue for testing."""
    cfg = type("Config", (), {"name": name})()

    class _Stats:
        current_depth = stats_kw.get("current_depth", 0)
        dead_letter_depth = stats_kw.get("dead_letter_depth", 0)
        total_enqueued = stats_kw.get("total_enqueued", 0)
        total_dequeued = stats_kw.get("total_dequeued", 0)
        total_failed = stats_kw.get("total_failed", 0)

    stats = _Stats()

    _MockQueue = type("MockQueue", (), {"config": cfg, "get_stats": staticmethod(lambda: stats)})
    return _MockQueue()


class TestQueueHealth:
    @pytest.mark.asyncio
    async def test_healthy_empty(self) -> None:
        check = QueueHealthCheck()
        report = await check.check()
        assert report.status.value == "healthy"
        assert "empty" in report.message

    @pytest.mark.asyncio
    async def test_healthy_with_depth(self) -> None:
        check = QueueHealthCheck()
        mock = _make_mock_queue("test", current_depth=5)
        check.register_queue(mock)
        report = await check.check()
        assert report.status.value == "healthy"
        assert "5 message(s)" in report.message

    @pytest.mark.asyncio
    async def test_degraded_dlq(self) -> None:
        check = QueueHealthCheck()
        mock = _make_mock_queue("test", current_depth=5, dead_letter_depth=3)
        check.register_queue(mock)
        report = await check.check()
        assert report.status.value == "degraded"
        assert "dead-letter" in report.message

    def test_name(self) -> None:
        check = QueueHealthCheck()
        assert check.name == "eaip.queue"

    def test_register_unregister(self) -> None:
        check = QueueHealthCheck()
        mock = _make_mock_queue("test")
        check.register_queue(mock)
        check.unregister_queue("test")
