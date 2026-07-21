"""Tests for :mod:`eaip.labeling.health`."""

from __future__ import annotations

import pytest

from eaip.labeling.health import LabelingHealthCheck


class TestLabelingHealthCheck:
    """Tests for :class:`eaip.labeling.health.LabelingHealthCheck`."""

    @pytest.mark.asyncio
    async def test_healthy(self) -> None:
        """Test that the health check returns healthy."""
        check = LabelingHealthCheck()
        report = await check.check()
        assert report.component == "labeling"
        assert report.status.value == "healthy"
