"""Tests for :mod:`eaip.quality.coverage`."""

from __future__ import annotations

import pytest

from eaip.quality.coverage import CoverageAnalyzer
from eaip.quality.exceptions import CoverageError
from eaip.quality.models import CoverageReport


class TestRecordAndGet:
    @pytest.mark.asyncio
    async def test_record_and_get_coverage(self) -> None:
        analyzer = CoverageAnalyzer()
        report = CoverageReport(id="cr1", component="comp1", line_rate=0.85)
        await analyzer.record_coverage(report)
        result = await analyzer.get_coverage("comp1")
        assert result is not None
        assert result.id == "cr1"
        assert result.line_rate == 0.85

    @pytest.mark.asyncio
    async def test_get_coverage_nonexistent(self) -> None:
        analyzer = CoverageAnalyzer()
        result = await analyzer.get_coverage("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_coverage_returns_latest(self) -> None:
        analyzer = CoverageAnalyzer()
        await analyzer.record_coverage(CoverageReport(id="cr1", component="comp1", line_rate=0.5))
        await analyzer.record_coverage(CoverageReport(id="cr2", component="comp1", line_rate=0.9))
        result = await analyzer.get_coverage("comp1")
        assert result is not None
        assert result.id == "cr2"

    @pytest.mark.asyncio
    async def test_get_coverage_history(self) -> None:
        analyzer = CoverageAnalyzer()
        await analyzer.record_coverage(CoverageReport(id="cr1", component="comp1", line_rate=0.5))
        await analyzer.record_coverage(CoverageReport(id="cr2", component="comp1", line_rate=0.9))
        history = await analyzer.get_coverage_history("comp1")
        assert len(history) == 2

    @pytest.mark.asyncio
    async def test_get_coverage_history_limit(self) -> None:
        analyzer = CoverageAnalyzer()
        for i in range(5):
            await analyzer.record_coverage(
                CoverageReport(id=f"cr{i}", component="comp1", line_rate=0.5)
            )
        history = await analyzer.get_coverage_history("comp1", limit=3)
        assert len(history) == 3

    @pytest.mark.asyncio
    async def test_get_coverage_history_empty(self) -> None:
        analyzer = CoverageAnalyzer()
        history = await analyzer.get_coverage_history("comp1")
        assert history == []


class TestCompareCoverage:
    @pytest.mark.asyncio
    async def test_compare_coverage(self) -> None:
        analyzer = CoverageAnalyzer()
        await analyzer.record_coverage(
            CoverageReport(
                id="cr1",
                component="comp1",
                line_rate=0.5,
                branch_rate=0.4,
                function_rate=0.6,
                total_lines=100,
                covered_lines=50,
            )
        )
        await analyzer.record_coverage(
            CoverageReport(
                id="cr2",
                component="comp1",
                line_rate=0.8,
                branch_rate=0.7,
                function_rate=0.9,
                total_lines=100,
                covered_lines=80,
            )
        )
        result = await analyzer.compare_coverage("comp1", "cr1")
        assert result["line_rate_delta"] == pytest.approx(0.3)
        assert result["covered_lines_delta"] == 30

    @pytest.mark.asyncio
    async def test_compare_no_current(self) -> None:
        analyzer = CoverageAnalyzer()
        await analyzer.record_coverage(CoverageReport(id="cr1", component="comp1", line_rate=0.5))
        with pytest.raises(CoverageError):
            await analyzer.compare_coverage("comp2", "cr1")

    @pytest.mark.asyncio
    async def test_compare_no_baseline(self) -> None:
        analyzer = CoverageAnalyzer()
        await analyzer.record_coverage(CoverageReport(id="cr1", component="comp1", line_rate=0.5))
        with pytest.raises(CoverageError):
            await analyzer.compare_coverage("comp1", "nonexistent")


class TestUncoveredLines:
    @pytest.mark.asyncio
    async def test_get_uncovered_lines(self) -> None:
        analyzer = CoverageAnalyzer()
        await analyzer.record_coverage(
            CoverageReport(id="cr1", component="comp1", uncovered_lines=(10, 20, 30))
        )
        lines = await analyzer.get_uncovered_lines("comp1")
        assert lines == [10, 20, 30]

    @pytest.mark.asyncio
    async def test_get_uncovered_lines_empty(self) -> None:
        analyzer = CoverageAnalyzer()
        lines = await analyzer.get_uncovered_lines("comp1")
        assert lines == []


class TestThreshold:
    @pytest.mark.asyncio
    async def test_check_threshold_met(self) -> None:
        analyzer = CoverageAnalyzer()
        await analyzer.record_coverage(CoverageReport(id="cr1", component="comp1", line_rate=0.95))
        result = await analyzer.check_coverage_threshold("comp1", 0.9)
        assert result["met"] is True

    @pytest.mark.asyncio
    async def test_check_threshold_not_met(self) -> None:
        analyzer = CoverageAnalyzer()
        await analyzer.record_coverage(CoverageReport(id="cr1", component="comp1", line_rate=0.5))
        result = await analyzer.check_coverage_threshold("comp1", 0.8)
        assert result["met"] is False

    @pytest.mark.asyncio
    async def test_check_threshold_no_data(self) -> None:
        analyzer = CoverageAnalyzer()
        result = await analyzer.check_coverage_threshold("comp1")
        assert result["met"] is False
