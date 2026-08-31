"""Tests for WFTemplatesHealthCheck."""

from __future__ import annotations

from eaip.health.checks import HealthStatus
from eaip.wftemplates.health import WFTemplatesHealthCheck


class TestWFTemplatesHealthCheck:
    async def test_healthy_with_templates(self) -> None:
        check = WFTemplatesHealthCheck(
            total_templates=10, published_templates=5, total_categories=3
        )
        report = await check.check()
        assert report.status is HealthStatus.HEALTHY

    async def test_no_templates(self) -> None:
        check = WFTemplatesHealthCheck()
        report = await check.check()
        assert report.status is HealthStatus.HEALTHY
        assert "no templates" in report.message

    async def test_no_published_templates(self) -> None:
        check = WFTemplatesHealthCheck(total_templates=5, published_templates=0, total_categories=2)
        report = await check.check()
        assert report.status is HealthStatus.DEGRADED
        assert "no published" in report.message

    async def test_name_property(self) -> None:
        check = WFTemplatesHealthCheck()
        assert check.name == "eaip.wftemplates"

    async def test_details(self) -> None:
        check = WFTemplatesHealthCheck(total_templates=3, published_templates=1, total_categories=2)
        report = await check.check()
        assert report.details["total_templates"] == 3
        assert report.details["published_templates"] == 1
        assert report.details["total_categories"] == 2
