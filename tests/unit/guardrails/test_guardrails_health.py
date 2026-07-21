"""Tests for :mod:`eaip.guardrails.health`."""

from __future__ import annotations

import pytest

from eaip.guardrails.health import GuardrailHealthCheck


class TestGuardrailHealthCheck:
    """Tests for :class:`eaip.guardrails.health.GuardrailHealthCheck`."""

    @pytest.mark.asyncio
    async def test_healthy(self) -> None:
        """Test that the health check returns healthy."""
        check = GuardrailHealthCheck()
        report = await check.check()
        assert report.component == "guardrails"
        assert report.status.value == "healthy"
        assert "healthy" in report.message
