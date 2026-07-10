"""Tests for bulkhead."""

from __future__ import annotations

import pytest

from eaip.resilience.bulkhead import Bulkhead, BulkheadConfig


async def _ok() -> str:
    return "ok"


class TestBulkhead:
    @pytest.mark.asyncio
    async def test_execute_success(self) -> None:
        bh = Bulkhead("test")
        result = await bh.execute(_ok)
        assert result == "ok"

    @pytest.mark.asyncio
    async def test_rejects_when_full(self) -> None:
        bh = Bulkhead(
            "test",
            BulkheadConfig(max_concurrent=0, max_queue_size=0, queue_timeout_seconds=0.1),
        )

        with pytest.raises(Exception):
            await bh.execute(_ok)

    def test_get_metrics(self) -> None:
        bh = Bulkhead("test")
        metrics = bh.get_metrics()
        assert metrics["name"] == "test"
        assert metrics["active_count"] == 0
