"""Tests for :mod:`eaip.phealth.integration`."""

from __future__ import annotations

import pytest

from eaip.phealth.health import PlatformHealthHealthCheck
from eaip.phealth.integration import PlatformHealthRuntimeModule


class TestPlatformHealthRuntimeModule:
    """Tests for :class:`eaip.phealth.integration.PlatformHealthRuntimeModule`."""

    def test_instantiation(self) -> None:
        """Test creating a module instance."""
        module = PlatformHealthRuntimeModule()
        assert module.name == "phealth"
        assert isinstance(module.health_check, PlatformHealthHealthCheck)

    @pytest.mark.asyncio
    async def test_health_check_healthy(self) -> None:
        """Test that the health check returns healthy."""
        module = PlatformHealthRuntimeModule()
        report = await module.health_check.check()
        assert report.component == "phealth"
        assert report.status.value == "healthy"
