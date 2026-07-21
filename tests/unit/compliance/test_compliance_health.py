from __future__ import annotations

import anyio
import pytest

from eaip.compliance.health import ComplianceHealthCheck


class TestComplianceHealth:
    @pytest.mark.asyncio
    async def test_healthy(self) -> None:
        check = ComplianceHealthCheck(regulation_count=3, control_count=10, last_scan_passed=True)
        report = await check.check()
        assert report.component == "compliance"
        assert report.status.value == "healthy"
        assert "3 regulation(s)" in report.message

    @pytest.mark.asyncio
    async def test_degraded_no_regulations(self) -> None:
        check = ComplianceHealthCheck(regulation_count=0, control_count=0, last_scan_passed=True)
        report = await check.check()
        assert report.status.value == "degraded"
        assert "No regulations configured" in report.message

    @pytest.mark.asyncio
    async def test_degraded_scan_failed(self) -> None:
        check = ComplianceHealthCheck(regulation_count=2, control_count=5, last_scan_passed=False)
        report = await check.check()
        assert report.status.value == "degraded"
        assert "Last compliance scan failed" in report.message

    def test_name(self) -> None:
        check = ComplianceHealthCheck()
        assert check.name == "compliance"

    def test_properties(self) -> None:
        check = ComplianceHealthCheck(regulation_count=3, control_count=10, last_scan_passed=True)
        assert check.regulation_count == 3
        assert check.control_count == 10
        assert check.last_scan_passed is True

    def test_defaults(self) -> None:
        check = ComplianceHealthCheck()
        assert check.regulation_count == 0
        assert check.control_count == 0
        assert check.last_scan_passed is True

    def test_details_in_report(self) -> None:
        check = ComplianceHealthCheck(regulation_count=2, control_count=5, last_scan_passed=True)
        report = anyio.run(check.check)
        assert report.details["regulation_count"] == 2
        assert report.details["control_count"] == 5
        assert report.details["last_scan_passed"] is True
