"""Tests for Deployer."""

from __future__ import annotations

import pytest

from eaip.deploy.deployer import Deployer
from eaip.deploy.exceptions import DeploymentFailedError
from eaip.deploy.models import DeploymentConfig


class TestDeployer:
    def test_create_deployment(self) -> None:
        deployer = Deployer()
        config = DeploymentConfig(
            config_id="c1",
            environment="prod",
            strategy="rolling",
        )
        d = deployer.create_deployment(
            deployment_id="d1",
            release_id="r1",
            environment="prod",
            config=config,
        )
        assert d.deployment_id == "d1"
        assert d.release_id == "r1"
        assert d.environment == "prod"
        assert d.status == "pending"

    def test_get_deployment_found(self) -> None:
        deployer = Deployer()
        config = DeploymentConfig(
            config_id="c1",
            environment="dev",
            strategy="recreate",
        )
        deployer.create_deployment(
            deployment_id="d1",
            release_id="r1",
            environment="dev",
            config=config,
        )
        d = deployer.get_deployment("d1")
        assert d is not None

    def test_get_deployment_not_found(self) -> None:
        deployer = Deployer()
        d = deployer.get_deployment("nonexistent")
        assert d is None

    def test_execute_deployment_success(self) -> None:
        deployer = Deployer()
        config = DeploymentConfig(
            config_id="c1",
            environment="dev",
            strategy="rolling",
        )
        deployer.create_deployment(
            deployment_id="d1",
            release_id="r1",
            environment="dev",
            config=config,
        )
        result = deployer.execute_deployment("d1")
        assert result.status == "completed"
        assert result.started_at is not None
        assert result.completed_at is not None

    def test_execute_deployment_not_found(self) -> None:
        deployer = Deployer()
        with pytest.raises(DeploymentFailedError):
            deployer.execute_deployment("nonexistent")

    def test_execute_deployment_health_check_fails(self) -> None:
        deployer = Deployer()
        config = DeploymentConfig(
            config_id="c1",
            environment="dev",
            strategy="rolling",
        )
        deployer.create_deployment(
            deployment_id="d1",
            release_id="r1",
            environment="dev",
            config=config,
        )
        with pytest.raises(DeploymentFailedError):
            deployer.execute_deployment("d1", health_check=lambda: False)

    def test_execute_deployment_health_check_passes(self) -> None:
        deployer = Deployer()
        config = DeploymentConfig(
            config_id="c1",
            environment="dev",
            strategy="rolling",
        )
        deployer.create_deployment(
            deployment_id="d1",
            release_id="r1",
            environment="dev",
            config=config,
        )
        result = deployer.execute_deployment("d1", health_check=lambda: True)
        assert result.status == "completed"

    def test_add_log(self) -> None:
        deployer = Deployer()
        config = DeploymentConfig(
            config_id="c1",
            environment="dev",
            strategy="rolling",
        )
        deployer.create_deployment(
            deployment_id="d1",
            release_id="r1",
            environment="dev",
            config=config,
        )
        d = deployer.add_log("d1", "info", "started", "deployer")
        assert d is not None
        assert len(d.log) == 1
        assert d.log[0].message == "started"

    def test_add_log_not_found(self) -> None:
        deployer = Deployer()
        d = deployer.add_log("nonexistent", "info", "msg", "cmp")
        assert d is None

    def test_unsupported_strategy(self) -> None:
        deployer = Deployer()
        config = DeploymentConfig(
            config_id="c1",
            environment="dev",
            strategy="unknown",
        )
        deployer.create_deployment(
            deployment_id="d1",
            release_id="r1",
            environment="dev",
            config=config,
        )
        with pytest.raises(DeploymentFailedError):
            deployer.execute_deployment("d1")

    def test_strategies_property(self) -> None:
        deployer = Deployer()
        assert "rolling" in deployer.strategies
        assert "blue-green" in deployer.strategies
        assert "canary" in deployer.strategies
        assert "recreate" in deployer.strategies

    def test_deployments_property(self) -> None:
        deployer = Deployer()
        config = DeploymentConfig(
            config_id="c1",
            environment="dev",
            strategy="rolling",
        )
        deployer.create_deployment(
            deployment_id="d1",
            release_id="r1",
            environment="dev",
            config=config,
        )
        assert "d1" in deployer.deployments
