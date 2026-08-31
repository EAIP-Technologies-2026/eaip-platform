"""Tests for :mod:`eaip.throttle.integration`."""

from __future__ import annotations

import pytest

from eaip.throttle.health import ThrottleHealthCheck
from eaip.throttle.integration import ThrottleRuntimeModule


class TestThrottleRuntimeModule:
    """Tests for :class:`eaip.throttle.integration.ThrottleRuntimeModule`."""

    def test_instantiation(self) -> None:
        """Test creating a module instance."""
        module = ThrottleRuntimeModule()
        assert module.name == "throttle"
        assert isinstance(module.health_check, ThrottleHealthCheck)

    @pytest.mark.asyncio
    async def test_health_check_healthy(self) -> None:
        """Test that the health check returns healthy."""
        module = ThrottleRuntimeModule()
        report = await module.health_check.check()
        assert report.component == "throttle"
        assert report.status.value == "healthy"
