from __future__ import annotations

import pydantic
import pytest

from eaip.compliance.models import (
    ComplianceReport,
    ComplianceScanConfig,
    Control,
    EvidenceRecord,
    Regulation,
    RemediationItem,
)


class TestRegulation:
    def test_defaults(self) -> None:
        r = Regulation(
            regulation_id="gdpr",
            name="GDPR",
            description="General Data Protection Regulation",
            version="1.0",
        )
        assert r.regulation_id == "gdpr"
        assert r.name == "GDPR"
        assert r.required_controls == ()

    def test_with_controls(self) -> None:
        r = Regulation(
            regulation_id="soc2",
            name="SOC 2",
            description="SOC 2",
            version="2.0",
            required_controls=("c1", "c2"),
        )
        assert r.required_controls == ("c1", "c2")

    def test_frozen(self) -> None:
        r = Regulation(
            regulation_id="gdpr",
            name="GDPR",
            description="desc",
            version="1.0",
        )
        with pytest.raises(pydantic.ValidationError):
            r.name = "HIPAA"  # type: ignore[misc]

    def test_extra_forbidden(self) -> None:
        with pytest.raises(pydantic.ValidationError):
            Regulation(
                regulation_id="x",
                name="x",
                description="x",
                version="x",
                unknown=True,  # type: ignore[call-arg]
            )


class TestControl:
    def test_defaults(self) -> None:
        c = Control(
            control_id="c1",
            regulation_id="gdpr",
            category="access",
            description="Access control",
            severity="high",
            status="unknown",
        )
        assert c.control_id == "c1"
        assert c.regulation_id == "gdpr"
        assert c.severity == "high"
        assert c.status == "unknown"

    def test_frozen(self) -> None:
        c = Control(
            control_id="c1",
            regulation_id="gdpr",
            category="access",
            description="desc",
            severity="high",
            status="unknown",
        )
        with pytest.raises(pydantic.ValidationError):
            c.status = "compliant"  # type: ignore[misc]

    def test_extra_forbidden(self) -> None:
        with pytest.raises(pydantic.ValidationError):
            Control(
                control_id="c1",
                regulation_id="gdpr",
                category="access",
                description="desc",
                severity="high",
                status="unknown",
                unknown="x",  # type: ignore[call-arg]
            )


class TestComplianceReport:
    def test_defaults(self) -> None:
        report = ComplianceReport(
            report_id="r1",
            generated_at="2024-01-01T00:00:00",
            regulation_id="gdpr",
            overall_status="compliant",
            total_controls=10,
            compliant_count=8,
            non_compliant_count=2,
            score=80.0,
        )
        assert report.report_id == "r1"
        assert report.controls == ()
        assert report.score == 80.0

    def test_frozen(self) -> None:
        report = ComplianceReport(
            report_id="r1",
            generated_at="2024-01-01T00:00:00",
            regulation_id="gdpr",
            overall_status="compliant",
            total_controls=1,
            compliant_count=1,
            non_compliant_count=0,
            score=100.0,
        )
        with pytest.raises(pydantic.ValidationError):
            report.score = 50.0  # type: ignore[misc]

    def test_extra_forbidden(self) -> None:
        with pytest.raises(pydantic.ValidationError):
            ComplianceReport(
                report_id="r1",
                generated_at="2024-01-01T00:00:00",
                regulation_id="gdpr",
                overall_status="compliant",
                total_controls=1,
                compliant_count=1,
                non_compliant_count=0,
                score=100.0,
                unknown="x",  # type: ignore[call-arg]
            )


class TestComplianceScanConfig:
    def test_defaults(self) -> None:
        cfg = ComplianceScanConfig(regulations=("gdpr",))
        assert cfg.regulations == ("gdpr",)
        assert cfg.scan_interval_hours == 24
        assert cfg.auto_remediate is False
        assert cfg.notify_on_findings is True

    def test_custom_values(self) -> None:
        cfg = ComplianceScanConfig(
            regulations=("gdpr", "hipaa"),
            scan_interval_hours=12,
            auto_remediate=True,
            notify_on_findings=False,
        )
        assert cfg.regulations == ("gdpr", "hipaa")
        assert cfg.scan_interval_hours == 12
        assert cfg.auto_remediate is True
        assert cfg.notify_on_findings is False

    def test_frozen(self) -> None:
        cfg = ComplianceScanConfig(regulations=("gdpr",))
        with pytest.raises(pydantic.ValidationError):
            cfg.scan_interval_hours = 48  # type: ignore[misc]

    def test_extra_forbidden(self) -> None:
        with pytest.raises(pydantic.ValidationError):
            ComplianceScanConfig(regulations=("gdpr",), unknown="x")  # type: ignore[call-arg]


class TestEvidenceRecord:
    def test_defaults(self) -> None:
        rec = EvidenceRecord(
            evidence_id="e1",
            control_id="c1",
            source="audit",
            timestamp="2024-01-01T00:00:00",
            data={"key": "val"},
            collected_by="collector",
        )
        assert rec.evidence_id == "e1"
        assert rec.valid is True
        assert rec.data["key"] == "val"

    def test_frozen(self) -> None:
        rec = EvidenceRecord(
            evidence_id="e1",
            control_id="c1",
            source="audit",
            timestamp="2024-01-01T00:00:00",
            data={},
            collected_by="collector",
        )
        with pytest.raises(pydantic.ValidationError):
            rec.valid = False  # type: ignore[misc]

    def test_extra_forbidden(self) -> None:
        with pytest.raises(pydantic.ValidationError):
            EvidenceRecord(
                evidence_id="e1",
                control_id="c1",
                source="audit",
                timestamp="2024-01-01T00:00:00",
                data={},
                collected_by="collector",
                unknown="x",  # type: ignore[call-arg]
            )


class TestRemediationItem:
    def test_defaults(self) -> None:
        item = RemediationItem(item_id="r1", control_id="c1", description="fix", status="open")
        assert item.item_id == "r1"
        assert item.control_id == "c1"
        assert item.status == "open"
        assert item.resolved_at is None
        assert item.assigned_to is None

    def test_with_assignment(self) -> None:
        item = RemediationItem(
            item_id="r1",
            control_id="c1",
            description="fix",
            status="open",
            assigned_to="alice",
        )
        assert item.assigned_to == "alice"

    def test_frozen(self) -> None:
        item = RemediationItem(item_id="r1", control_id="c1", description="fix", status="open")
        with pytest.raises(pydantic.ValidationError):
            item.status = "resolved"  # type: ignore[misc]

    def test_extra_forbidden(self) -> None:
        with pytest.raises(pydantic.ValidationError):
            RemediationItem(
                item_id="r1",
                control_id="c1",
                description="fix",
                unknown="x",  # type: ignore[call-arg]
            )
