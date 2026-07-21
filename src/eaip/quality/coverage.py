"""Coverage analyzer — track and compare code coverage reports."""

from __future__ import annotations

from typing import Any

from eaip.quality.exceptions import CoverageError
from eaip.quality.models import CoverageReport


class CoverageAnalyzer:
    def __init__(self) -> None:
        self._reports: list[CoverageReport] = []

    async def record_coverage(self, report: CoverageReport) -> None:
        self._reports.append(report)

    async def get_coverage(self, component: str) -> CoverageReport | None:
        matching = [r for r in self._reports if r.component == component]
        if not matching:
            return None
        return max(matching, key=lambda r: r.generated_at)

    async def get_coverage_history(
        self,
        component: str,
        limit: int = 10,
    ) -> list[CoverageReport]:
        matching = [r for r in self._reports if r.component == component]
        matching.sort(key=lambda r: r.generated_at, reverse=True)
        return matching[:limit]

    async def compare_coverage(
        self,
        component: str,
        baseline_report_id: str,
    ) -> dict[str, Any]:
        current = await self.get_coverage(component)
        baseline: CoverageReport | None = None
        for r in self._reports:
            if r.id == baseline_report_id:
                baseline = r
                break

        if current is None:
            raise CoverageError(f"No coverage data for component {component!r}")
        if baseline is None:
            raise CoverageError(f"Baseline report {baseline_report_id!r} not found")

        return {
            "component": component,
            "baseline_id": baseline.id,
            "current_id": current.id,
            "line_rate_delta": current.line_rate - baseline.line_rate,
            "branch_rate_delta": current.branch_rate - baseline.branch_rate,
            "function_rate_delta": current.function_rate - baseline.function_rate,
            "total_lines_delta": current.total_lines - baseline.total_lines,
            "covered_lines_delta": current.covered_lines - baseline.covered_lines,
        }

    async def get_uncovered_lines(self, component: str) -> list[int]:
        current = await self.get_coverage(component)
        if current is None:
            return []
        return list(current.uncovered_lines)

    async def check_coverage_threshold(
        self,
        component: str,
        threshold: float | None = None,
    ) -> dict[str, Any]:
        current = await self.get_coverage(component)
        if current is None:
            return {"component": component, "met": False, "reason": "No coverage data"}

        effective_threshold = threshold if threshold is not None else 0.8
        met = current.line_rate >= effective_threshold
        return {
            "component": component,
            "line_rate": current.line_rate,
            "threshold": effective_threshold,
            "met": met,
            "reason": ""
            if met
            else f"Line rate {current.line_rate:.1%} below {effective_threshold:.0%}",
        }
