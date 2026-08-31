"""Tests for EnvironmentManager."""

from __future__ import annotations

import pytest

from eaip.deploy.environment import EnvironmentManager
from eaip.deploy.exceptions import InvalidEnvironmentError


class TestEnvironmentManager:
    def test_add_environment(self) -> None:
        mgr = EnvironmentManager()
        status = mgr.add_environment("dev", version="1.0.0")
        assert status.environment == "dev"
        assert status.version == "1.0.0"
        assert status.health_status == "healthy"
        assert status.current_release_id == ""

    def test_add_invalid_environment(self) -> None:
        mgr = EnvironmentManager()
        with pytest.raises(InvalidEnvironmentError):
            mgr.add_environment("invalid-env")

    def test_get_environment_found(self) -> None:
        mgr = EnvironmentManager()
        mgr.add_environment("staging")
        status = mgr.get_environment("staging")
        assert status is not None

    def test_get_environment_not_found(self) -> None:
        mgr = EnvironmentManager()
        status = mgr.get_environment("nonexistent")
        assert status is None

    def test_update_deployment(self) -> None:
        mgr = EnvironmentManager()
        mgr.add_environment("prod")
        status = mgr.update_deployment(
            environment="prod",
            release_id="r1",
            version="2.0.0",
        )
        assert status.current_release_id == "r1"
        assert status.version == "2.0.0"
        assert status.last_deployed_at is not None

    def test_update_deployment_invalid_env(self) -> None:
        mgr = EnvironmentManager()
        with pytest.raises(InvalidEnvironmentError):
            mgr.update_deployment("invalid", release_id="r1", version="1.0")

    def test_set_health_status(self) -> None:
        mgr = EnvironmentManager()
        mgr.add_environment("dev")
        status = mgr.set_health_status("dev", "degraded")
        assert status is not None
        assert status.health_status == "degraded"

    def test_set_health_status_not_found(self) -> None:
        mgr = EnvironmentManager()
        status = mgr.set_health_status("nonexistent", "healthy")
        assert status is None

    def test_get_health_summary(self) -> None:
        mgr = EnvironmentManager()
        mgr.add_environment("dev", health_status="healthy")
        mgr.add_environment("staging", health_status="degraded")
        summary = mgr.get_health_summary()
        assert summary == {"dev": "healthy", "staging": "degraded"}

    def test_environments_property(self) -> None:
        mgr = EnvironmentManager()
        mgr.add_environment("dev")
        mgr.add_environment("staging")
        assert len(mgr.environments) == 2
