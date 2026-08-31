from __future__ import annotations

import anyio
import pytest

from eaip.filestore.health import FileStoreHealthCheck


class TestFilestoreHealth:
    @pytest.mark.asyncio
    async def test_healthy(self) -> None:
        check = FileStoreHealthCheck(asset_count=5, provider_available=True)
        report = await check.check()
        assert report.component == "filestore"
        assert report.status.value == "healthy"
        assert "5 asset(s)" in report.message

    @pytest.mark.asyncio
    async def test_degraded_provider_unavailable(self) -> None:
        check = FileStoreHealthCheck(asset_count=5, provider_available=False)
        report = await check.check()
        assert report.status.value == "degraded"
        assert "unavailable" in report.message

    @pytest.mark.asyncio
    async def test_degraded_no_assets(self) -> None:
        check = FileStoreHealthCheck(asset_count=0, provider_available=True)
        report = await check.check()
        assert report.status.value == "healthy"
        assert "0 asset(s)" in report.message

    def test_name(self) -> None:
        check = FileStoreHealthCheck()
        assert check.name == "filestore"

    def test_properties(self) -> None:
        check = FileStoreHealthCheck(asset_count=10, provider_available=False)
        assert check.asset_count == 10
        assert check.provider_available is False

    def test_defaults(self) -> None:
        check = FileStoreHealthCheck()
        assert check.asset_count == 0
        assert check.provider_available is True

    def test_details_in_report(self) -> None:
        check = FileStoreHealthCheck(asset_count=3, provider_available=True)
        report = anyio.run(check.check)
        assert report.details["asset_count"] == 3
        assert report.details["provider_available"] is True
