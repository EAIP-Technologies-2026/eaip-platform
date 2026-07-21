"""Tests for :mod:`eaip.modelreg.health`."""

from __future__ import annotations

import pytest

from eaip.modelreg.health import ModelRegistryHealthCheck


class TestModelRegistryHealthCheck:
    """Tests for :class:`eaip.modelreg.health.ModelRegistryHealthCheck`."""

    @pytest.mark.asyncio
    async def test_healthy(self) -> None:
        """Test that the health check returns healthy."""
        check = ModelRegistryHealthCheck()
        report = await check.check()
        assert report.component == "modelreg"
        assert report.status.value == "healthy"
