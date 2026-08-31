"""Tests for :mod:`eaip.security.compliance`."""

from __future__ import annotations

import pytest

from eaip.security.compliance import ComplianceService
from eaip.security.events import ComplianceCheckCompleted
from eaip.security.exceptions import ComplianceCheckError
from eaip.security.models import ComplianceFramework, ComplianceStatus, ControlStatus


class TestComplianceService:
    async def test_run_soc2_check(self) -> None:
        svc = ComplianceService()
        report = await svc.run_compliance_check(ComplianceFramework.SOC2)
        assert report.framework is ComplianceFramework.SOC2
        assert report.status in (ComplianceStatus.PASS, ComplianceStatus.FAIL)
        assert len(report.controls) == 5
        assert report.score is not None

    async def test_run_hipaa_check(self) -> None:
        svc = ComplianceService()
        report = await svc.run_compliance_check(ComplianceFramework.HIPAA)
        assert report.framework is ComplianceFramework.HIPAA
        assert len(report.controls) == 5

    async def test_run_gdpr_check(self) -> None:
        svc = ComplianceService()
        report = await svc.run_compliance_check(ComplianceFramework.GDPR)
        assert report.framework is ComplianceFramework.GDPR
        assert len(report.controls) == 5

    async def test_run_pci_check(self) -> None:
        svc = ComplianceService()
        report = await svc.run_compliance_check(ComplianceFramework.PCI)
        assert report.framework is ComplianceFramework.PCI
        assert len(report.controls) == 5

    async def test_get_compliance_report(self) -> None:
        svc = ComplianceService()
        await svc.run_compliance_check(ComplianceFramework.SOC2)
        report = await svc.get_compliance_report(ComplianceFramework.SOC2)
        assert report is not None
        assert report.framework is ComplianceFramework.SOC2

    async def test_get_compliance_report_nonexistent(self) -> None:
        svc = ComplianceService()
        report = await svc.get_compliance_report(ComplianceFramework.GDPR)
        assert report is None

    async def test_list_frameworks(self) -> None:
        svc = ComplianceService()
        frameworks = await svc.list_frameworks()
        assert ComplianceFramework.SOC2 in frameworks
        assert ComplianceFramework.HIPAA in frameworks
        assert ComplianceFramework.GDPR in frameworks
        assert ComplianceFramework.PCI in frameworks
        assert len(frameworks) == 4

    async def test_get_control_status(self) -> None:
        svc = ComplianceService()
        await svc.run_compliance_check(ComplianceFramework.SOC2)
        ctrl = await svc.get_control_status("soc2-cc1")
        assert ctrl is not None
        assert ctrl.id == "soc2-cc1"
        assert ctrl.status is ControlStatus.PASS

    async def test_get_control_status_nonexistent(self) -> None:
        svc = ComplianceService()
        ctrl = await svc.get_control_status("nonexistent")
        assert ctrl is None

    async def test_update_control_evidence(self) -> None:
        svc = ComplianceService()
        await svc.run_compliance_check(ComplianceFramework.SOC2)
        ctrl = await svc.update_control_evidence(
            "soc2-cc1", {"policy_url": "https://example.com/policy"}
        )
        assert ctrl.id == "soc2-cc1"
        assert ctrl.evidence["policy_url"] == "https://example.com/policy"

    async def test_update_control_evidence_not_found(self) -> None:
        svc = ComplianceService()
        with pytest.raises(ComplianceCheckError):
            await svc.update_control_evidence("nonexistent", {})

    async def test_run_check_event_emitted(self) -> None:
        svc = ComplianceService()
        await svc.run_compliance_check(ComplianceFramework.SOC2)
        assert any(
            isinstance(e, ComplianceCheckCompleted) and e.framework == "soc2" for e in svc.event_log
        )

    async def test_report_score_calculation(self) -> None:
        svc = ComplianceService()
        report = await svc.run_compliance_check(ComplianceFramework.PCI)
        assert report.score == 100.0
        assert report.status is ComplianceStatus.PASS
