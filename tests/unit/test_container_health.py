"""Tests for :mod:`eaip.container.health`."""

from __future__ import annotations

import pytest

from eaip.container.health import ContainerHealthCheck


class TestContainerHealthCheck:
    @pytest.mark.asyncio
    async def test_healthy_with_containers(self) -> None:
        check = ContainerHealthCheck(container_count=3, deployment_count=2)
        report = await check.check()
        assert report.component == "container"
        assert report.status.value == "healthy"

    @pytest.mark.asyncio
    async def test_degraded_no_containers(self) -> None:
        check = ContainerHealthCheck(container_count=0, deployment_count=0)
        report = await check.check()
        assert report.status.value == "degraded"
        assert "No containers" in report.message

    @pytest.mark.asyncio
    async def test_details(self) -> None:
        check = ContainerHealthCheck(container_count=5, deployment_count=3)
        report = await check.check()
        assert report.details["container_count"] == 5
        assert report.details["deployment_count"] == 3
