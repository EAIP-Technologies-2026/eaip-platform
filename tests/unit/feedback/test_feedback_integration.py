"""Tests for :mod:`eaip.feedback.integration`."""

from __future__ import annotations

import pytest

from eaip.feedback.health import FeedbackHealthCheck
from eaip.feedback.integration import FeedbackRuntimeModule


class TestFeedbackRuntimeModule:
    """Tests for :class:`eaip.feedback.integration.FeedbackRuntimeModule`."""

    def test_instantiation(self) -> None:
        """Test creating a module instance."""
        module = FeedbackRuntimeModule()
        assert module.name == "feedback"
        assert isinstance(module.health_check, FeedbackHealthCheck)

    @pytest.mark.asyncio
    async def test_health_check_healthy(self) -> None:
        """Test that the health check returns healthy."""
        module = FeedbackRuntimeModule()
        report = await module.health_check.check()
        assert report.component == "feedback"
        assert report.status.value == "healthy"
