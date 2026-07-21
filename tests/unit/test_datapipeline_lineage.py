from __future__ import annotations

import pytest

from eaip.datapipeline.lineage import DataLineageTracker


class TestDataLineageTracker:
    @pytest.fixture
    def tracker(self) -> DataLineageTracker:
        return DataLineageTracker()

    @pytest.mark.asyncio
    async def test_record_lineage(self, tracker: DataLineageTracker) -> None:
        await tracker.record_lineage(
            execution_id="exec1",
            source="src1",
            record_id="rec1",
            step_id="step1",
            target="step2",
        )
        lineage = await tracker.get_lineage("rec1")
        assert len(lineage) == 1
        assert lineage[0]["execution_id"] == "exec1"
        assert lineage[0]["record_id"] == "rec1"

    @pytest.mark.asyncio
    async def test_record_lineage_multiple(self, tracker: DataLineageTracker) -> None:
        await tracker.record_lineage("exec1", "src1", "rec1", "step1", "step2")
        await tracker.record_lineage("exec1", "src1", "rec1", "step2", "sink1")
        lineage = await tracker.get_lineage("rec1")
        assert len(lineage) == 2

    @pytest.mark.asyncio
    async def test_get_lineage_empty(self, tracker: DataLineageTracker) -> None:
        lineage = await tracker.get_lineage("nonexistent")
        assert lineage == []

    @pytest.mark.asyncio
    async def test_get_pipeline_lineage(self, tracker: DataLineageTracker) -> None:
        await tracker.record_lineage("pipe1_exec1", "src1", "rec1", "step1", "step2")
        await tracker.record_lineage("pipe1_exec1", "src1", "rec2", "step1", "step2")
        lineage = await tracker.get_pipeline_lineage("pipe1")
        assert len(lineage) == 2

    @pytest.mark.asyncio
    async def test_get_pipeline_lineage_empty(self, tracker: DataLineageTracker) -> None:
        lineage = await tracker.get_pipeline_lineage("nonexistent")
        assert lineage == []

    @pytest.mark.asyncio
    async def test_trace_record(self, tracker: DataLineageTracker) -> None:
        await tracker.record_lineage("exec1", "src1", "rec1", "step1", "step2")
        trace = await tracker.trace_record("rec1")
        assert len(trace) == 1
        assert trace[0]["record_id"] == "rec1"

    @pytest.mark.asyncio
    async def test_trace_record_nonexistent(self, tracker: DataLineageTracker) -> None:
        trace = await tracker.trace_record("nonexistent")
        assert trace == []

    @pytest.mark.asyncio
    async def test_record_lineage_multiple_records(self, tracker: DataLineageTracker) -> None:
        await tracker.record_lineage("exec1", "src1", "rec1", "step1", "sink1")
        await tracker.record_lineage("exec1", "src1", "rec2", "step1", "sink1")
        assert len(await tracker.get_lineage("rec1")) == 1
        assert len(await tracker.get_lineage("rec2")) == 1

    @pytest.mark.asyncio
    async def test_pipeline_lineage_filtering(self, tracker: DataLineageTracker) -> None:
        await tracker.record_lineage("pipe1_exec1", "src1", "rec1", "step1", "step2")
        await tracker.record_lineage("pipe2_exec1", "src2", "rec2", "step1", "step2")
        lineage = await tracker.get_pipeline_lineage("pipe1")
        assert len(lineage) == 1
        assert lineage[0]["execution_id"] == "pipe1_exec1"
