"""Tests for :mod:`eaip.feedback.health`."""

from __future__ import annotations

import pytest

from eaip.feedback.health import FeedbackHealthCheck


class TestFeedbackHealthCheck:
    """Tests for :class:`eaip.feedback.health.FeedbackHealthCheck`."""

    @pytest.mark.asyncio
    async def test_healthy(self) -> None:
        """Test that the health check returns healthy."""
        check = FeedbackHealthCheck()
        report = await check.check()
        assert report.component == "feedback"
        assert report.status.value == "healthy"
