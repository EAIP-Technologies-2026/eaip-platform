"""Tests for BlueGreenManager service."""

from __future__ import annotations

import pytest

from eaip.bluegreen.exceptions import BlueGreenError, SwitchError
from eaip.bluegreen.manager import BlueGreenManager
from eaip.bluegreen.models import (
    BlueGreenConfig,
    DeploymentSwitch,
    Environment,
    EnvironmentStatus,
    EnvironmentType,
    SwitchStrategy,
)


class TestBlueGreenManager:
    @pytest.fixture
    def manager(self) -> BlueGreenManager:
        return BlueGreenManager()

    @pytest.fixture
    def blue_env(self) -> Environment:
        return Environment(
            id="blue1",
            name="Blue",
            type=EnvironmentType.BLUE,
            status=EnvironmentStatus.ACTIVE,
            version="v1.0",
        )

    @pytest.fixture
    def green_env(self) -> Environment:
        return Environment(
            id="green1",
            name="Green",
            type=EnvironmentType.GREEN,
            status=EnvironmentStatus.STANDBY,
            version="v2.0",
        )

    class TestRegisterEnvironment:
        async def test_register(self, manager: BlueGreenManager, blue_env: Environment) -> None:
            result = await manager.register_environment(blue_env)
            assert result.id == "blue1"
            assert result.name == "Blue"

        async def test_list_environments(
            self, manager: BlueGreenManager, blue_env: Environment, green_env: Environment
        ) -> None:
            await manager.register_environment(blue_env)
            await manager.register_environment(green_env)
            envs = await manager.list_environments()
            assert len(envs) == 2

    class TestGetEnvironment:
        async def test_get(self, manager: BlueGreenManager, blue_env: Environment) -> None:
            await manager.register_environment(blue_env)
            env = await manager.get_environment("blue1")
            assert env.type == EnvironmentType.BLUE

        async def test_get_not_found(self, manager: BlueGreenManager) -> None:
            with pytest.raises(BlueGreenError):
                await manager.get_environment("nonexistent")

    class TestGetActiveEnvironment:
        async def test_get_active(
            self, manager: BlueGreenManager, blue_env: Environment, green_env: Environment
        ) -> None:
            await manager.register_environment(blue_env)
            await manager.register_environment(green_env)
            active = await manager.get_active_environment()
            assert active is not None
            assert active.id == "blue1"

        async def test_no_active(self, manager: BlueGreenManager) -> None:
            env = Environment(
                id="e1", name="Test", type=EnvironmentType.BLUE, status=EnvironmentStatus.STANDBY
            )
            await manager.register_environment(env)
            active = await manager.get_active_environment()
            assert active is None

    class TestStartSwitch:
        async def test_start_switch(
            self, manager: BlueGreenManager, blue_env: Environment, green_env: Environment
        ) -> None:
            await manager.register_environment(blue_env)
            await manager.register_environment(green_env)
            switch = await manager.start_switch("blue1", "green1")
            assert switch.from_env == "blue1"
            assert switch.to_env == "green1"

        async def test_start_switch_invalid_source(
            self, manager: BlueGreenManager, green_env: Environment
        ) -> None:
            await manager.register_environment(green_env)
            with pytest.raises(BlueGreenError):
                await manager.start_switch("green1", "nonexistent")

        async def test_start_switch_not_found(self, manager: BlueGreenManager) -> None:
            with pytest.raises(BlueGreenError):
                await manager.start_switch("nonexistent", "nonexistent2")

    class TestCompleteSwitch:
        async def test_complete_switch(
            self, manager: BlueGreenManager, blue_env: Environment, green_env: Environment
        ) -> None:
            await manager.register_environment(blue_env)
            await manager.register_environment(green_env)
            switch = await manager.start_switch("blue1", "green1")
            result = await manager.complete_switch(switch.id)
            assert result is not None
            blue = await manager.get_environment("blue1")
            green = await manager.get_environment("green1")
            assert blue.status == EnvironmentStatus.DRAINING
            assert green.status == EnvironmentStatus.ACTIVE

        async def test_complete_switch_not_found(self, manager: BlueGreenManager) -> None:
            with pytest.raises(SwitchError):
                await manager.complete_switch("nonexistent")

    class TestRollbackSwitch:
        async def test_rollback(
            self, manager: BlueGreenManager, blue_env: Environment, green_env: Environment
        ) -> None:
            await manager.register_environment(blue_env)
            await manager.register_environment(green_env)
            switch = await manager.start_switch("blue1", "green1")
            result = await manager.rollback_switch(switch.id, "Health check failed")
            assert result is not None

        async def test_rollback_not_found(self, manager: BlueGreenManager) -> None:
            with pytest.raises(SwitchError):
                await manager.rollback_switch("nonexistent", "Reason")

    class TestHealthFailure:
        async def test_report_health_failure(self, manager: BlueGreenManager) -> None:
            await manager.report_health_failure("sw1", "green1", "Timeout")

    class TestGetSwitch:
        async def test_get_switch(
            self, manager: BlueGreenManager, blue_env: Environment, green_env: Environment
        ) -> None:
            await manager.register_environment(blue_env)
            await manager.register_environment(green_env)
            switch = await manager.start_switch("blue1", "green1")
            result = await manager.get_switch(switch.id)
            assert result.from_env == "blue1"

        async def test_get_switch_not_found(self, manager: BlueGreenManager) -> None:
            with pytest.raises(SwitchError):
                await manager.get_switch("nonexistent")

    class TestConfig:
        def test_default_config(self) -> None:
            m = BlueGreenManager()
            assert m.config.auto_rollback_enabled is True
            assert m.config.health_check_timeout_seconds == 300

        def test_custom_config(self) -> None:
            config = BlueGreenConfig(health_check_timeout_seconds=600, auto_rollback_enabled=False)
            m = BlueGreenManager(config=config)
            assert m.config.health_check_timeout_seconds == 600
            assert m.config.auto_rollback_enabled is False
