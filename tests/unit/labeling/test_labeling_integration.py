"""Tests for :mod:`eaip.labeling.integration`."""

from __future__ import annotations

import pytest

from eaip.labeling.health import LabelingHealthCheck
from eaip.labeling.integration import LabelingRuntimeModule


class TestLabelingRuntimeModule:
    """Tests for :class:`eaip.labeling.integration.LabelingRuntimeModule`."""

    def test_instantiation(self) -> None:
        """Test creating a module instance."""
        module = LabelingRuntimeModule()
        assert module.name == "labeling"
        assert isinstance(module.health_check, LabelingHealthCheck)

    @pytest.mark.asyncio
    async def test_health_check_healthy(self) -> None:
        """Test that the health check returns healthy."""
        module = LabelingRuntimeModule()
        report = await module.health_check.check()
        assert report.component == "labeling"
        assert report.status.value == "healthy"
