"""Tests for :mod:`eaip.gitsvc.health`."""

from __future__ import annotations

import pytest

from eaip.gitsvc.health import GitServiceHealthCheck


class TestGitServiceHealthCheck:
    @pytest.mark.asyncio
    async def test_healthy(self) -> None:
        check = GitServiceHealthCheck()
        report = await check.check()
        assert report.component == "gitsvc"
        assert report.status.value == "healthy"
