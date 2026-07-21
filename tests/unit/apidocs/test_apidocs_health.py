"""Tests for ApiDocsHealthCheck."""

from __future__ import annotations

from eaip.apidocs.health import ApiDocsHealthCheck
from eaip.health.checks import HealthStatus


class TestApiDocsHealthCheck:
    async def test_healthy_default(self) -> None:
        check = ApiDocsHealthCheck()
        report = await check.check()
        assert report.status is HealthStatus.HEALTHY

    async def test_healthy_with_endpoints(self) -> None:
        check = ApiDocsHealthCheck(registered_endpoints=5, published_docs=2, changelogs=1)
        report = await check.check()
        assert report.status is HealthStatus.HEALTHY

    async def test_details(self) -> None:
        check = ApiDocsHealthCheck(registered_endpoints=3, published_docs=1, changelogs=0)
        report = await check.check()
        assert report.details["registered_endpoints"] == 3
        assert report.details["published_docs"] == 1

    async def test_name_property(self) -> None:
        check = ApiDocsHealthCheck()
        assert check.name == "eaip.apidocs"
