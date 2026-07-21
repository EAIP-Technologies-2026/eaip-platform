from __future__ import annotations

import anyio
import pytest

from eaip.dataquality.health import DataQualityHealthCheck


class TestDataqualityHealth:
    @pytest.mark.asyncio
    async def test_healthy(self) -> None:
        check = DataQualityHealthCheck(active_rules=3, active_checks=5)
        report = await check.check()
        assert report.component == "dataquality"
        assert report.status.value == "healthy"
        assert "3 rule(s)" in report.message

    @pytest.mark.asyncio
    async def test_degraded_no_rules(self) -> None:
        check = DataQualityHealthCheck(active_rules=0, active_checks=0)
        report = await check.check()
        assert report.status.value == "degraded"
        assert "No quality rules configured" in report.message

    @pytest.mark.asyncio
    async def test_degraded_check_failed(self) -> None:
        check = DataQualityHealthCheck(active_rules=2, active_checks=1, last_check_passed=False)
        report = await check.check()
        assert report.status.value == "degraded"
        assert "Last quality check failed" in report.message

    def test_name(self) -> None:
        check = DataQualityHealthCheck()
        assert check.name == "dataquality"

    def test_properties(self) -> None:
        check = DataQualityHealthCheck(active_rules=10, active_checks=5, last_check_passed=False)
        assert check.active_rules == 10
        assert check.active_checks == 5
        assert check.last_check_passed is False

    def test_defaults(self) -> None:
        check = DataQualityHealthCheck()
        assert check.active_rules == 0
        assert check.active_checks == 0
        assert check.last_check_passed is True

    def test_details_in_report(self) -> None:
        check = DataQualityHealthCheck(active_rules=4, active_checks=2, last_check_passed=True)
        report = anyio.run(check.check)
        assert report.details["active_rules"] == 4
        assert report.details["active_checks"] == 2
        assert report.details["last_check_passed"] is True
