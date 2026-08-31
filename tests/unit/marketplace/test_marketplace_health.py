from __future__ import annotations

import anyio
import pytest

from eaip.marketplace.health import MarketplaceHealthCheck


class TestMarketplaceHealth:
    @pytest.mark.asyncio
    async def test_healthy(self) -> None:
        check = MarketplaceHealthCheck(package_count=5, active_installations=3)
        report = await check.check()
        assert report.component == "marketplace"
        assert report.status.value == "healthy"
        assert "5 package(s), 3 installation(s)." in report.message

    @pytest.mark.asyncio
    async def test_degraded_no_packages(self) -> None:
        check = MarketplaceHealthCheck(package_count=0, active_installations=3)
        report = await check.check()
        assert report.status.value == "degraded"

    @pytest.mark.asyncio
    async def test_degraded_no_installations(self) -> None:
        check = MarketplaceHealthCheck(package_count=5, active_installations=0)
        report = await check.check()
        assert report.status.value == "degraded"

    @pytest.mark.asyncio
    async def test_degraded_both_zero(self) -> None:
        check = MarketplaceHealthCheck(package_count=0, active_installations=0)
        report = await check.check()
        assert report.status.value == "degraded"

    def test_name(self) -> None:
        check = MarketplaceHealthCheck()
        assert check.name == "marketplace"

    def test_properties(self) -> None:
        check = MarketplaceHealthCheck(package_count=10, active_installations=5)
        assert check.package_count == 10
        assert check.active_installations == 5

    def test_defaults(self) -> None:
        check = MarketplaceHealthCheck()
        assert check.package_count == 0
        assert check.active_installations == 0

    def test_details_in_report(self) -> None:
        check = MarketplaceHealthCheck(package_count=3, active_installations=2)
        report = anyio.run(check.check)
        assert report.details["package_count"] == 3
        assert report.details["active_installations"] == 2
