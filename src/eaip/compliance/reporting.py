"""Compliance report generation and trend analysis."""

from __future__ import annotations

from typing import Any

from eaip.compliance.models import ComplianceReport, Control
from eaip.logging.context import get_logger
from eaip.shared.time import utc_now


class ComplianceReportGenerator:
    """Generates compliance reports with filtering and trend analysis."""

    def __init__(self) -> None:
        """Initialize the report generator."""
        self._log = get_logger("eaip.compliance.reporting")

    def generate_report(
        self,
        report_id: str,
        regulation_id: str,
        controls: tuple[Control, ...],
    ) -> ComplianceReport:
        """Generate a compliance report."""
        total = len(controls)
        compliant = sum(1 for c in controls if c.status == "compliant")
        non_compliant = sum(1 for c in controls if c.status == "non_compliant")
        applicable = total - sum(1 for c in controls if c.status == "not_applicable")
        score = round(compliant / applicable * 100, 2) if applicable > 0 else 100.0

        if score >= 90.0:  # noqa: PLR2004
            status = "compliant"
        elif score >= 50.0:  # noqa: PLR2004
            status = "partially_compliant"
        else:
            status = "non_compliant"

        report = ComplianceReport(
            report_id=report_id,
            generated_at=utc_now(),
            regulation_id=regulation_id,
            overall_status=status,
            controls=controls,
            total_controls=total,
            compliant_count=compliant,
            non_compliant_count=non_compliant,
            score=score,
        )
        self._log.info("report.generated", report_id=report_id, regulation_id=regulation_id)
        return report

    def filter_by_regulation(
        self,
        reports: tuple[ComplianceReport, ...],
        regulation_id: str,
    ) -> tuple[ComplianceReport, ...]:
        """Filter reports by regulation ID."""
        return tuple(r for r in reports if r.regulation_id == regulation_id)

    def filter_by_status(
        self,
        reports: tuple[ComplianceReport, ...],
        status: str,
    ) -> tuple[ComplianceReport, ...]:
        """Filter reports by status."""
        return tuple(r for r in reports if r.overall_status == status)

    def filter_by_score_range(
        self,
        reports: tuple[ComplianceReport, ...],
        min_score: float,
        max_score: float = 100.0,
    ) -> tuple[ComplianceReport, ...]:
        """Filter reports by score range."""
        return tuple(r for r in reports if min_score <= r.score <= max_score)

    def filter_controls_by_status(
        self,
        controls: tuple[Control, ...],
        status: str,
    ) -> tuple[Control, ...]:
        """Filter controls by status."""
        return tuple(c for c in controls if c.status == status)

    def compute_trend(
        self,
        reports: tuple[ComplianceReport, ...],
    ) -> dict[str, Any]:
        """Compute score trend from a series of reports."""
        sorted_reports = sorted(reports, key=lambda r: r.generated_at)
        if len(sorted_reports) < 2:  # noqa: PLR2004
            return {
                "direction": "stable",
                "change": 0.0,
                "current_score": sorted_reports[-1].score if sorted_reports else 0.0,
            }

        first = sorted_reports[0].score
        last = sorted_reports[-1].score
        change = round(last - first, 2)

        if change > 1.0:
            direction = "improving"
        elif change < -1.0:
            direction = "declining"
        else:
            direction = "stable"

        return {
            "direction": direction,
            "change": change,
            "current_score": last,
        }

    def summarize(
        self,
        report: ComplianceReport,
    ) -> dict[str, Any]:
        """Summarize a compliance report."""
        return {
            "report_id": report.report_id,
            "regulation_id": report.regulation_id,
            "overall_status": report.overall_status,
            "score": report.score,
            "total_controls": report.total_controls,
            "compliant_count": report.compliant_count,
            "non_compliant_count": report.non_compliant_count,
            "compliance_rate": round(report.compliant_count / report.total_controls * 100, 2)
            if report.total_controls > 0
            else 0.0,
        }
