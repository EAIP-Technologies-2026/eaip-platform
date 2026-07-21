from __future__ import annotations

import pytest

from eaip.diagnostics.health import DiagnosticsHealthCheck


class TestDiagnosticsHealth:
    @pytest.mark.asyncio
    async def test_healthy(self) -> None:
        check = DiagnosticsHealthCheck()
        report = await check.check()
        assert report.status.value == "healthy"

    def test_name(self) -> None:
        check = DiagnosticsHealthCheck()
        assert check.name == "diagnostics"
