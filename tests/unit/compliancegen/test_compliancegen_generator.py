"""Tests for ComplianceReportGenerator."""

from __future__ import annotations

import pytest

from eaip.compliancegen.generator import ComplianceReportGenerator
from eaip.compliancegen.models import (
    ComplianceFinding,
    ComplianceFramework,
    ComplianceScan,
    FindingStatus,
    GeneratorConfig,
)


class TestComplianceReportGenerator:
    @pytest.mark.asyncio
    async def test_register_framework(self) -> None:
        gen = ComplianceReportGenerator()
        fw = ComplianceFramework(id="nist", name="NIST 800-53", version="r5")
        result = await gen.register_framework(fw)
        assert result.id == "nist"

    @pytest.mark.asyncio
    async def test_get_framework_found(self) -> None:
        gen = ComplianceReportGenerator()
        fw = ComplianceFramework(id="nist", name="NIST 800-53", version="r5")
        await gen.register_framework(fw)
        result = await gen.get_framework("nist")
        assert result is not None

    @pytest.mark.asyncio
    async def test_get_framework_not_found(self) -> None:
        gen = ComplianceReportGenerator()
        result = await gen.get_framework("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_start_and_get_scan(self) -> None:
        gen = ComplianceReportGenerator()
        scan = ComplianceScan(id="s1", framework_id="nist", target="acme-vm")
        await gen.start_scan(scan)
        result = await gen.get_scan("s1")
        assert result is not None
        assert result.target == "acme-vm"

    @pytest.mark.asyncio
    async def test_add_and_get_findings(self) -> None:
        gen = ComplianceReportGenerator()
        scan = ComplianceScan(id="s1", framework_id="nist", target="acme-vm")
        await gen.start_scan(scan)
        f1 = ComplianceFinding(id="f1", scan_id="s1", control_id="ac-1", status=FindingStatus.PASS)
        f2 = ComplianceFinding(id="f2", scan_id="s1", control_id="ac-2", status=FindingStatus.FAIL)
        await gen.add_finding(f1)
        await gen.add_finding(f2)
        findings = await gen.get_findings_for_scan("s1")
        assert len(findings) == 2

    @pytest.mark.asyncio
    async def test_config(self) -> None:
        cfg = GeneratorConfig(max_findings_per_scan=500, output_format="html")
        gen = ComplianceReportGenerator(config=cfg)
        assert gen.config.max_findings_per_scan == 500
        assert gen.config.output_format == "html"
