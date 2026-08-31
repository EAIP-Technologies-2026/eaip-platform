"""Tests for :mod:`eaip.resquota.integration`."""

from __future__ import annotations

import pytest

from eaip.resquota.health import QuotaHealthCheck
from eaip.resquota.integration import QuotaRuntimeModule


class TestQuotaRuntimeModule:
    """Tests for :class:`eaip.resquota.integration.QuotaRuntimeModule`."""

    def test_instantiation(self) -> None:
        """Test creating a module instance."""
        module = QuotaRuntimeModule()
        assert module.name == "resquota"
        assert isinstance(module.health_check, QuotaHealthCheck)

    @pytest.mark.asyncio
    async def test_health_check_healthy(self) -> None:
        """Test that the health check returns healthy."""
        module = QuotaRuntimeModule()
        report = await module.health_check.check()
        assert report.component == "resquota"
        assert report.status.value == "healthy"
