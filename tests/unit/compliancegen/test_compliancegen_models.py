"""Tests for compliance report generator Pydantic models."""

from __future__ import annotations

from datetime import datetime

import pytest
from pydantic import ValidationError

from eaip.compliancegen.models import (
    ComplianceFinding,
    ComplianceFramework,
    ComplianceScan,
    FindingStatus,
    GeneratorConfig,
)


class TestComplianceFramework:
    def test_default_values(self) -> None:
        fw = ComplianceFramework(id="nist", name="NIST 800-53", version="r5")
        assert fw.id == "nist"
        assert fw.controls == ()

    def test_frozen(self) -> None:
        fw = ComplianceFramework(id="nist", name="NIST 800-53", version="r5")
        with pytest.raises(ValidationError):
            fw.name = "other"  # type: ignore[misc]


class TestComplianceScan:
    def test_default_values(self) -> None:
        scan = ComplianceScan(id="s1", framework_id="nist", target="acme-vm")
        assert scan.status == "pending"
        assert isinstance(scan.started_at, datetime)

    def test_extra_forbidden(self) -> None:
        with pytest.raises(ValidationError):
            ComplianceScan(id="s1", framework_id="nist", target="acme-vm", unknown=True)  # type: ignore[call-arg]


class TestComplianceFinding:
    def test_default_values(self) -> None:
        f = ComplianceFinding(id="f1", scan_id="s1", control_id="ac-1", status=FindingStatus.PASS)
        assert f.evidence == ""
        assert f.details == ""

    def test_status_enum(self) -> None:
        for status in FindingStatus:
            f = ComplianceFinding(id="f1", scan_id="s1", control_id="ac-1", status=status)
            assert f.status == status

    def test_frozen(self) -> None:
        f = ComplianceFinding(id="f1", scan_id="s1", control_id="ac-1", status=FindingStatus.PASS)
        with pytest.raises(ValidationError):
            f.status = FindingStatus.FAIL  # type: ignore[misc]


class TestGeneratorConfig:
    def test_default_values(self) -> None:
        cfg = GeneratorConfig()
        assert cfg.max_findings_per_scan == 1000
        assert cfg.default_framework == "nist-800-53"
        assert cfg.include_evidence is True
        assert cfg.output_format == "json"
