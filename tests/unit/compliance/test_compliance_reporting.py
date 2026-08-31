from __future__ import annotations

import pytest

from eaip.compliance.models import ComplianceReport, Control
from eaip.compliance.reporting import ComplianceReportGenerator


class TestComplianceReportGenerator:
    @pytest.fixture
    def generator(self) -> ComplianceReportGenerator:
        return ComplianceReportGenerator()

    @pytest.fixture
    def compliant_control(self) -> Control:
        return Control(
            control_id="c1",
            regulation_id="gdpr",
            category="access",
            description="Access control",
            severity="high",
            status="compliant",
        )

    @pytest.fixture
    def non_compliant_control(self) -> Control:
        return Control(
            control_id="c2",
            regulation_id="gdpr",
            category="encryption",
            description="Encryption",
            severity="critical",
            status="non_compliant",
        )

    @pytest.fixture
    def mixed_controls(
        self, compliant_control: Control, non_compliant_control: Control
    ) -> tuple[Control, ...]:
        return (compliant_control, non_compliant_control)

    def test_generate_report(
        self, generator: ComplianceReportGenerator, mixed_controls: tuple[Control, ...]
    ) -> None:
        report = generator.generate_report("r1", "gdpr", mixed_controls)
        assert report.report_id == "r1"
        assert report.regulation_id == "gdpr"
        assert report.total_controls == 2
        assert report.compliant_count == 1
        assert report.non_compliant_count == 1
        assert report.score == 50.0
        assert report.overall_status == "partially_compliant"

    def test_generate_report_all_compliant(
        self, generator: ComplianceReportGenerator, compliant_control: Control
    ) -> None:
        controls = (compliant_control,)
        report = generator.generate_report("r2", "gdpr", controls)
        assert report.score == 100.0
        assert report.overall_status == "compliant"

    def test_generate_report_no_applicable(self, generator: ComplianceReportGenerator) -> None:
        control = Control(
            control_id="c3",
            regulation_id="gdpr",
            category="network",
            description="Network security",
            severity="medium",
            status="not_applicable",
        )
        report = generator.generate_report("r3", "gdpr", (control,))
        assert report.score == 100.0
        assert report.overall_status == "compliant"

    def test_filter_by_regulation(self, generator: ComplianceReportGenerator) -> None:
        r1 = ComplianceReport(
            report_id="r1",
            generated_at="2024-01-01T00:00:00",
            regulation_id="gdpr",
            overall_status="compliant",
            total_controls=1,
            compliant_count=1,
            non_compliant_count=0,
            score=100.0,
        )
        r2 = ComplianceReport(
            report_id="r2",
            generated_at="2024-01-01T00:00:00",
            regulation_id="hipaa",
            overall_status="compliant",
            total_controls=1,
            compliant_count=1,
            non_compliant_count=0,
            score=100.0,
        )
        reports = (r1, r2)
        filtered = generator.filter_by_regulation(reports, "gdpr")
        assert len(filtered) == 1
        assert filtered[0].regulation_id == "gdpr"

    def test_filter_by_status(self, generator: ComplianceReportGenerator) -> None:
        r1 = ComplianceReport(
            report_id="r1",
            generated_at="2024-01-01T00:00:00",
            regulation_id="gdpr",
            overall_status="compliant",
            total_controls=1,
            compliant_count=1,
            non_compliant_count=0,
            score=100.0,
        )
        r2 = ComplianceReport(
            report_id="r2",
            generated_at="2024-01-01T00:00:00",
            regulation_id="gdpr",
            overall_status="non_compliant",
            total_controls=1,
            compliant_count=0,
            non_compliant_count=1,
            score=0.0,
        )
        reports = (r1, r2)
        filtered = generator.filter_by_status(reports, "compliant")
        assert len(filtered) == 1
        assert filtered[0].overall_status == "compliant"

    def test_filter_by_score_range(self, generator: ComplianceReportGenerator) -> None:
        r1 = ComplianceReport(
            report_id="r1",
            generated_at="2024-01-01T00:00:00",
            regulation_id="gdpr",
            overall_status="compliant",
            total_controls=1,
            compliant_count=1,
            non_compliant_count=0,
            score=95.0,
        )
        r2 = ComplianceReport(
            report_id="r2",
            generated_at="2024-01-01T00:00:00",
            regulation_id="gdpr",
            overall_status="partially_compliant",
            total_controls=1,
            compliant_count=1,
            non_compliant_count=1,
            score=60.0,
        )
        reports = (r1, r2)
        filtered = generator.filter_by_score_range(reports, 80.0, 100.0)
        assert len(filtered) == 1
        assert filtered[0].score == 95.0

    def test_filter_controls_by_status(
        self, generator: ComplianceReportGenerator, mixed_controls: tuple[Control, ...]
    ) -> None:
        compliant = generator.filter_controls_by_status(mixed_controls, "compliant")
        assert len(compliant) == 1
        assert compliant[0].control_id == "c1"

        non_compliant = generator.filter_controls_by_status(mixed_controls, "non_compliant")
        assert len(non_compliant) == 1
        assert non_compliant[0].control_id == "c2"

    def test_compute_trend_insufficient_reports(self, generator: ComplianceReportGenerator) -> None:
        r1 = ComplianceReport(
            report_id="r1",
            generated_at="2024-01-01T00:00:00",
            regulation_id="gdpr",
            overall_status="compliant",
            total_controls=1,
            compliant_count=1,
            non_compliant_count=0,
            score=100.0,
        )
        trend = generator.compute_trend((r1,))
        assert trend["direction"] == "stable"
        assert trend["current_score"] == 100.0

    def test_compute_trend_improving(self, generator: ComplianceReportGenerator) -> None:
        r1 = ComplianceReport(
            report_id="r1",
            generated_at="2024-01-01T00:00:00",
            regulation_id="gdpr",
            overall_status="non_compliant",
            total_controls=2,
            compliant_count=0,
            non_compliant_count=2,
            score=30.0,
        )
        r2 = ComplianceReport(
            report_id="r2",
            generated_at="2024-06-01T00:00:00",
            regulation_id="gdpr",
            overall_status="compliant",
            total_controls=2,
            compliant_count=2,
            non_compliant_count=0,
            score=90.0,
        )
        trend = generator.compute_trend((r1, r2))
        assert trend["direction"] == "improving"
        assert trend["change"] == 60.0

    def test_compute_trend_declining(self, generator: ComplianceReportGenerator) -> None:
        r1 = ComplianceReport(
            report_id="r1",
            generated_at="2024-01-01T00:00:00",
            regulation_id="gdpr",
            overall_status="compliant",
            total_controls=2,
            compliant_count=2,
            non_compliant_count=0,
            score=90.0,
        )
        r2 = ComplianceReport(
            report_id="r2",
            generated_at="2024-06-01T00:00:00",
            regulation_id="gdpr",
            overall_status="non_compliant",
            total_controls=2,
            compliant_count=0,
            non_compliant_count=2,
            score=30.0,
        )
        trend = generator.compute_trend((r1, r2))
        assert trend["direction"] == "declining"
        assert trend["change"] == -60.0

    def test_compute_trend_stable(self, generator: ComplianceReportGenerator) -> None:
        r1 = ComplianceReport(
            report_id="r1",
            generated_at="2024-01-01T00:00:00",
            regulation_id="gdpr",
            overall_status="compliant",
            total_controls=2,
            compliant_count=2,
            non_compliant_count=0,
            score=85.0,
        )
        r2 = ComplianceReport(
            report_id="r2",
            generated_at="2024-06-01T00:00:00",
            regulation_id="gdpr",
            overall_status="compliant",
            total_controls=2,
            compliant_count=2,
            non_compliant_count=0,
            score=85.5,
        )
        trend = generator.compute_trend((r1, r2))
        assert trend["direction"] == "stable"

    def test_summarize(
        self, generator: ComplianceReportGenerator, mixed_controls: tuple[Control, ...]
    ) -> None:
        report = generator.generate_report("r1", "gdpr", mixed_controls)
        summary = generator.summarize(report)
        assert summary["report_id"] == "r1"
        assert summary["regulation_id"] == "gdpr"
        assert summary["overall_status"] == "partially_compliant"
        assert summary["score"] == 50.0
        assert summary["total_controls"] == 2
        assert summary["compliance_rate"] == 50.0
