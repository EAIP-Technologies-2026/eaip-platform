"""Tests for deploy domain models."""

from __future__ import annotations

from datetime import datetime

import pytest

from eaip.deploy.models import (
    Artifact,
    Deployment,
    DeploymentConfig,
    DeploymentLog,
    EnvironmentStatus,
    Release,
    RollbackPlan,
)


class TestRelease:
    def test_required_fields(self) -> None:
        r = Release(release_id="r1", version="1.0.0", name="Initial Release")
        assert r.release_id == "r1"
        assert r.version == "1.0.0"
        assert r.name == "Initial Release"
        assert r.description is None
        assert r.artifacts == ()
        assert r.status == "draft"
        assert isinstance(r.created_at, datetime)
        assert r.deployed_at is None
        assert r.metadata == {}

    def test_frozen(self) -> None:
        r = Release(release_id="r1", version="1.0", name="N")
        with pytest.raises(ValueError):
            r.name = "changed"  # type: ignore[misc]

    def test_with_all_fields(self) -> None:
        now = datetime.now()
        artifact = Artifact(
            artifact_id="a1",
            name="app.jar",
            type="jar",
            uri="https://repo/app.jar",
            checksum="abc123",
            size_bytes=1024,
        )
        r = Release(
            release_id="r1",
            version="2.0.0",
            name="Major Release",
            description="Major release with breaking changes",
            artifacts=(artifact,),
            status="deployed",
            created_at=now,
            deployed_at=now,
            metadata={"author": "alice"},
        )
        assert r.description == "Major release with breaking changes"
        assert len(r.artifacts) == 1
        assert r.status == "deployed"
        assert r.deployed_at == now
        assert r.metadata == {"author": "alice"}


class TestArtifact:
    def test_required_fields(self) -> None:
        a = Artifact(
            artifact_id="a1",
            name="service.jar",
            type="jar",
            uri="s3://bucket/service.jar",
            checksum="sha256:abc",
            size_bytes=2048,
        )
        assert a.artifact_id == "a1"
        assert a.name == "service.jar"
        assert a.type == "jar"
        assert a.uri == "s3://bucket/service.jar"
        assert a.checksum == "sha256:abc"
        assert a.size_bytes == 2048

    def test_frozen(self) -> None:
        a = Artifact(
            artifact_id="a1",
            name="n",
            type="docker",
            uri="u",
            checksum="c",
            size_bytes=0,
        )
        with pytest.raises(ValueError):
            a.name = "changed"  # type: ignore[misc]


class TestDeploymentConfig:
    def test_required_fields(self) -> None:
        c = DeploymentConfig(
            config_id="c1",
            environment="prod",
            strategy="rolling",
        )
        assert c.config_id == "c1"
        assert c.environment == "prod"
        assert c.strategy == "rolling"
        assert c.auto_rollback is True
        assert c.health_check_timeout_seconds == 300
        assert c.max_retries == 3

    def test_custom_values(self) -> None:
        c = DeploymentConfig(
            config_id="c1",
            environment="staging",
            strategy="blue-green",
            auto_rollback=False,
            health_check_timeout_seconds=600,
            max_retries=5,
        )
        assert c.auto_rollback is False
        assert c.health_check_timeout_seconds == 600
        assert c.max_retries == 5

    def test_frozen(self) -> None:
        c = DeploymentConfig(config_id="c1", environment="dev", strategy="recreate")
        with pytest.raises(ValueError):
            c.strategy = "rolling"  # type: ignore[misc]


class TestDeploymentLog:
    def test_required_fields(self) -> None:
        log = DeploymentLog(level="info", message="started", component="deployer")
        assert log.level == "info"
        assert log.message == "started"
        assert log.component == "deployer"
        assert isinstance(log.timestamp, datetime)

    def test_frozen(self) -> None:
        log = DeploymentLog(level="info", message="m", component="c")
        with pytest.raises(ValueError):
            log.message = "changed"  # type: ignore[misc]


class TestDeployment:
    def test_required_fields(self) -> None:
        config = DeploymentConfig(
            config_id="c1",
            environment="prod",
            strategy="rolling",
        )
        d = Deployment(
            deployment_id="d1",
            release_id="r1",
            environment="prod",
            strategy="rolling",
            config=config,
        )
        assert d.deployment_id == "d1"
        assert d.release_id == "r1"
        assert d.environment == "prod"
        assert d.status == "pending"
        assert d.started_at is None
        assert d.completed_at is None
        assert d.log == ()

    def test_with_logs(self) -> None:
        config = DeploymentConfig(
            config_id="c1",
            environment="dev",
            strategy="canary",
        )
        log = DeploymentLog(level="info", message="deploying", component="deployer")
        d = Deployment(
            deployment_id="d1",
            release_id="r1",
            environment="dev",
            strategy="canary",
            status="in_progress",
            started_at=datetime.now(),
            log=(log,),
            config=config,
        )
        assert d.status == "in_progress"
        assert len(d.log) == 1

    def test_frozen(self) -> None:
        config = DeploymentConfig(
            config_id="c1",
            environment="dev",
            strategy="recreate",
        )
        d = Deployment(
            deployment_id="d1",
            release_id="r1",
            environment="dev",
            strategy="recreate",
            config=config,
        )
        with pytest.raises(ValueError):
            d.status = "completed"  # type: ignore[misc]


class TestRollbackPlan:
    def test_required_fields(self) -> None:
        p = RollbackPlan(
            plan_id="p1",
            deployment_id="d1",
            reason="deployment failed",
        )
        assert p.plan_id == "p1"
        assert p.deployment_id == "d1"
        assert p.reason == "deployment failed"
        assert p.steps == ()
        assert isinstance(p.created_at, datetime)

    def test_with_steps(self) -> None:
        steps = ("step1", "step2", "step3")
        p = RollbackPlan(
            plan_id="p1",
            deployment_id="d1",
            reason="rollback",
            steps=steps,
        )
        assert len(p.steps) == 3
        assert p.steps == ("step1", "step2", "step3")

    def test_frozen(self) -> None:
        p = RollbackPlan(plan_id="p1", deployment_id="d1", reason="r")
        with pytest.raises(ValueError):
            p.reason = "changed"  # type: ignore[misc]


class TestEnvironmentStatus:
    def test_required_fields(self) -> None:
        s = EnvironmentStatus(
            environment="prod",
            current_release_id="r1",
            health_status="healthy",
            version="1.0.0",
        )
        assert s.environment == "prod"
        assert s.current_release_id == "r1"
        assert s.health_status == "healthy"
        assert s.version == "1.0.0"
        assert s.last_deployed_at is None

    def test_frozen(self) -> None:
        s = EnvironmentStatus(
            environment="dev",
            current_release_id="r1",
            health_status="healthy",
            version="1.0",
        )
        with pytest.raises(ValueError):
            s.health_status = "degraded"  # type: ignore[misc]
