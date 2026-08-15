"""Tests for EnvironmentVariableManager."""

from __future__ import annotations

import pytest

from eaip.envmgr.exceptions import VariableNotFoundError
from eaip.envmgr.manager import EnvironmentVariableManager
from eaip.envmgr.models import EnvironmentVariable, EnvMgrConfig, VariableGroup


class TestEnvironmentVariableManager:
    @pytest.fixture
    def manager(self) -> EnvironmentVariableManager:
        return EnvironmentVariableManager()

    @pytest.fixture
    def sample_variable(self) -> EnvironmentVariable:
        return EnvironmentVariable(id="v1", name="DB_HOST", value="localhost", environment="prod")

    class TestCreateVariable:
        async def test_creates_variable(
            self, manager: EnvironmentVariableManager, sample_variable: EnvironmentVariable
        ) -> None:
            result = await manager.create_variable(sample_variable)
            assert result.id == "v1"
            assert result.name == "DB_HOST"

        async def test_stores_variable(
            self, manager: EnvironmentVariableManager, sample_variable: EnvironmentVariable
        ) -> None:
            await manager.create_variable(sample_variable)
            stored = await manager.get_variable("v1")
            assert stored.value == "localhost"

    class TestGetVariable:
        async def test_returns_variable(
            self, manager: EnvironmentVariableManager, sample_variable: EnvironmentVariable
        ) -> None:
            await manager.create_variable(sample_variable)
            result = await manager.get_variable("v1")
            assert result.environment == "prod"

        async def test_raises_on_missing(self, manager: EnvironmentVariableManager) -> None:
            with pytest.raises(VariableNotFoundError):
                await manager.get_variable("nonexistent")

    class TestUpdateVariable:
        async def test_updates_value(
            self, manager: EnvironmentVariableManager, sample_variable: EnvironmentVariable
        ) -> None:
            await manager.create_variable(sample_variable)
            result = await manager.update_variable("v1", value="newhost")
            assert result.value == "newhost"
            assert result.version == 2

        async def test_raises_on_missing(self, manager: EnvironmentVariableManager) -> None:
            with pytest.raises(VariableNotFoundError):
                await manager.update_variable("nonexistent", value="x")

    class TestDeleteVariable:
        async def test_deletes_variable(
            self, manager: EnvironmentVariableManager, sample_variable: EnvironmentVariable
        ) -> None:
            await manager.create_variable(sample_variable)
            await manager.delete_variable("v1")
            assert await manager.list_variables() == []

        async def test_raises_on_missing(self, manager: EnvironmentVariableManager) -> None:
            with pytest.raises(VariableNotFoundError):
                await manager.delete_variable("nonexistent")

    class TestListVariables:
        async def test_filters_by_environment(
            self, manager: EnvironmentVariableManager, sample_variable: EnvironmentVariable
        ) -> None:
            await manager.create_variable(sample_variable)
            v2 = EnvironmentVariable(id="v2", name="API_KEY", value="secret", environment="dev")
            await manager.create_variable(v2)
            variables = await manager.list_variables(environment="prod")
            assert len(variables) == 1

    class TestCreateGroup:
        async def test_creates_group(self, manager: EnvironmentVariableManager) -> None:
            group = VariableGroup(
                id="g1", name="app-config", environment="prod", variables=("v1", "v2")
            )
            result = await manager.create_group(group)
            assert result.id == "g1"

    class TestGetStatistics:
        async def test_returns_stats(
            self, manager: EnvironmentVariableManager, sample_variable: EnvironmentVariable
        ) -> None:
            await manager.create_variable(sample_variable)
            stats = await manager.get_statistics()
            assert stats["total_variables"] == 1

    class TestConfig:
        def test_default_config(self) -> None:
            svc = EnvironmentVariableManager()
            assert svc.config.max_variable_value_length == 8192

        def test_custom_config(self) -> None:
            cfg = EnvMgrConfig(max_variable_value_length=4096)
            svc = EnvironmentVariableManager(config=cfg)
            assert svc.config.max_variable_value_length == 4096
