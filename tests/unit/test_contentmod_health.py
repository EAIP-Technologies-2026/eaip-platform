"""Tests for :mod:`eaip.contentmod.health`."""

from __future__ import annotations

import pytest

from eaip.contentmod.health import ContentModerationHealthCheck


class TestContentModerationHealthCheck:
    @pytest.mark.asyncio
    async def test_healthy_with_rules(self) -> None:
        check = ContentModerationHealthCheck(rule_count=5, pending_count=10)
        report = await check.check()
        assert report.component == "contentmod"
        assert report.status.value == "healthy"

    @pytest.mark.asyncio
    async def test_degraded_no_rules(self) -> None:
        check = ContentModerationHealthCheck(rule_count=0, pending_count=0)
        report = await check.check()
        assert report.status.value == "degraded"
        assert "No moderation rules" in report.message

    @pytest.mark.asyncio
    async def test_details(self) -> None:
        check = ContentModerationHealthCheck(rule_count=3, pending_count=7)
        report = await check.check()
        assert report.details["rule_count"] == 3
        assert report.details["pending_count"] == 7
