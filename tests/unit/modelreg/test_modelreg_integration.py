"""Tests for :mod:`eaip.modelreg.integration`."""

from __future__ import annotations

import pytest

from eaip.modelreg.health import ModelRegistryHealthCheck
from eaip.modelreg.integration import ModelRegistryRuntimeModule


class TestModelRegistryRuntimeModule:
    """Tests for :class:`eaip.modelreg.integration.ModelRegistryRuntimeModule`."""

    def test_instantiation(self) -> None:
        """Test creating a module instance."""
        module = ModelRegistryRuntimeModule()
        assert module.name == "modelreg"
        assert isinstance(module.health_check, ModelRegistryHealthCheck)

    @pytest.mark.asyncio
    async def test_health_check_healthy(self) -> None:
        """Test that the health check returns healthy."""
        module = ModelRegistryRuntimeModule()
        report = await module.health_check.check()
        assert report.component == "modelreg"
        assert report.status.value == "healthy"
