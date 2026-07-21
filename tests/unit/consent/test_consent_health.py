from __future__ import annotations

import pytest

from eaip.consent.health import ConsentHealthCheck


class TestConsentHealth:
    @pytest.mark.asyncio
    async def test_healthy(self) -> None:
        check = ConsentHealthCheck()
        report = await check.check()
        assert report.status.value == "healthy"
        assert "healthy" in report.message

    def test_name(self) -> None:
        check = ConsentHealthCheck()
        assert check.name == "consent"
