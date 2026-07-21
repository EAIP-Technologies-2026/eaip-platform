"""Tests for DeployHealthCheck."""

from __future__ import annotations

import pytest

from eaip.deploy.health import DeployHealthCheck
from eaip.health.checks import HealthStatus


class TestDeployHealthCheck:
    @pytest.mark.asyncio
    async def test_healthy_by_default(self) -> None:
        check = DeployHealthCheck()
        report = await check.check()
        assert report.status is HealthStatus.HEALTHY
        assert report.component == "DeployManager"

    @pytest.mark.asyncio
    async def test_unhealthy_on_failed_deployment(self) -> None:
        check = DeployHealthCheck(last_deployment_status="failed")
        report = await check.check()
        assert report.status is HealthStatus.UNHEALTHY
        assert "last deployment failed" in report.message

    @pytest.mark.asyncio
    async def test_healthy_with_successful_status(self) -> None:
        check = DeployHealthCheck(last_deployment_status="completed")
        report = await check.check()
        assert report.status is HealthStatus.HEALTHY

    @pytest.mark.asyncio
    async def test_with_environments(self) -> None:
        check = DeployHealthCheck(
            environments={"dev": {"status": "healthy"}, "prod": {"status": "healthy"}},
        )
        report = await check.check()
        assert report.status is HealthStatus.HEALTHY
        assert "dev" in report.details["environments"]

    @pytest.mark.asyncio
    async def test_name_attribute(self) -> None:
        check = DeployHealthCheck()
        assert check.name == "eaip.deploy"
