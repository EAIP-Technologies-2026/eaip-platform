"""Tests for SandboxManager."""

from __future__ import annotations

from datetime import timedelta

import pytest

from eaip.sandbox.exceptions import EnvironmentNotFoundError, SandboxNotFoundError
from eaip.sandbox.manager import SandboxManager
from eaip.sandbox.models import (
    Environment,
    EnvironmentStatus,
    EnvironmentType,
    Sandbox,
    SandboxConfig,
    SandboxStatus,
)
from eaip.shared.time import utc_now


class TestSandboxManager:
    @pytest.fixture
    def manager(self) -> SandboxManager:
        return SandboxManager()

    @pytest.fixture
    def sample_env(self) -> Environment:
        return Environment(id="env1", name="Development", type=EnvironmentType.DEV)

    @pytest.fixture
    def sample_sandbox(self) -> Sandbox:
        return Sandbox(id="sb1", name="test-sandbox", environment_id="env1", ttl_minutes=30)

    class TestCreateEnvironment:
        async def test_create(self, manager: SandboxManager, sample_env: Environment) -> None:
            result = await manager.create_environment(sample_env)
            assert result.id == "env1"
            assert result.name == "Development"
            assert result.type == EnvironmentType.DEV

        async def test_list(self, manager: SandboxManager, sample_env: Environment) -> None:
            await manager.create_environment(sample_env)
            envs = await manager.list_environments()
            assert len(envs) == 1

    class TestGetEnvironment:
        async def test_get(self, manager: SandboxManager, sample_env: Environment) -> None:
            await manager.create_environment(sample_env)
            env = await manager.get_environment("env1")
            assert env.name == "Development"

        async def test_not_found(self, manager: SandboxManager) -> None:
            with pytest.raises(EnvironmentNotFoundError):
                await manager.get_environment("nonexistent")

    class TestDeleteEnvironment:
        async def test_delete(self, manager: SandboxManager, sample_env: Environment) -> None:
            await manager.create_environment(sample_env)
            await manager.delete_environment("env1")
            with pytest.raises(EnvironmentNotFoundError):
                await manager.get_environment("env1")

        async def test_not_found(self, manager: SandboxManager) -> None:
            with pytest.raises(EnvironmentNotFoundError):
                await manager.delete_environment("nonexistent")

    class TestCreateSandbox:
        async def test_create(
            self, manager: SandboxManager, sample_env: Environment, sample_sandbox: Sandbox
        ) -> None:
            await manager.create_environment(sample_env)
            result = await manager.create_sandbox(sample_sandbox)
            assert result.id == "sb1"
            assert result.status == SandboxStatus.RUNNING
            assert result.expires_at > result.created_at

        async def test_env_not_found(
            self, manager: SandboxManager, sample_sandbox: Sandbox
        ) -> None:
            with pytest.raises(EnvironmentNotFoundError):
                await manager.create_sandbox(sample_sandbox)

    class TestGetSandbox:
        async def test_get(
            self, manager: SandboxManager, sample_env: Environment, sample_sandbox: Sandbox
        ) -> None:
            await manager.create_environment(sample_env)
            await manager.create_sandbox(sample_sandbox)
            sb = await manager.get_sandbox("sb1")
            assert sb.name == "test-sandbox"

        async def test_not_found(self, manager: SandboxManager) -> None:
            with pytest.raises(SandboxNotFoundError):
                await manager.get_sandbox("nonexistent")

    class TestListSandboxes:
        async def test_list(
            self, manager: SandboxManager, sample_env: Environment, sample_sandbox: Sandbox
        ) -> None:
            await manager.create_environment(sample_env)
            await manager.create_sandbox(sample_sandbox)
            all_sb = await manager.list_sandboxes()
            assert len(all_sb) == 1

        async def test_list_by_env(
            self, manager: SandboxManager, sample_env: Environment, sample_sandbox: Sandbox
        ) -> None:
            await manager.create_environment(sample_env)
            await manager.create_sandbox(sample_sandbox)
            env_sb = await manager.list_sandboxes(environment_id="env1")
            assert len(env_sb) == 1
            other_sb = await manager.list_sandboxes(environment_id="env2")
            assert len(other_sb) == 0

    class TestStopSandbox:
        async def test_stop(
            self, manager: SandboxManager, sample_env: Environment, sample_sandbox: Sandbox
        ) -> None:
            await manager.create_environment(sample_env)
            await manager.create_sandbox(sample_sandbox)
            stopped = await manager.stop_sandbox("sb1")
            assert stopped.status == SandboxStatus.STOPPED
            assert stopped.stopped_at is not None

        async def test_stop_not_found(self, manager: SandboxManager) -> None:
            with pytest.raises(SandboxNotFoundError):
                await manager.stop_sandbox("nonexistent")

    class TestDeleteSandbox:
        async def test_delete(
            self, manager: SandboxManager, sample_env: Environment, sample_sandbox: Sandbox
        ) -> None:
            await manager.create_environment(sample_env)
            await manager.create_sandbox(sample_sandbox)
            await manager.delete_sandbox("sb1")
            with pytest.raises(SandboxNotFoundError):
                await manager.get_sandbox("sb1")

        async def test_not_found(self, manager: SandboxManager) -> None:
            with pytest.raises(SandboxNotFoundError):
                await manager.delete_sandbox("nonexistent")

    class TestExpireStale:
        async def test_expire_stale(self, manager: SandboxManager, sample_env: Environment) -> None:
            await manager.create_environment(sample_env)
            sb = Sandbox(
                id="sb_expired",
                name="expired",
                environment_id="env1",
                ttl_minutes=1,
            )
            await manager.create_sandbox(sb)
            past = utc_now()
            expired_sb = sb.model_copy(
                update={"expires_at": past - timedelta(minutes=5), "status": SandboxStatus.RUNNING},
                deep=True,
            )
            manager._sandboxes["sb_expired"] = expired_sb
            expired = await manager.expire_stale()
            assert len(expired) > 0
            assert expired[0].status == SandboxStatus.EXPIRED

        async def test_no_stale(self, manager: SandboxManager) -> None:
            expired = await manager.expire_stale()
            assert len(expired) == 0

    class TestConfig:
        def test_default_config(self) -> None:
            m = SandboxManager()
            assert m.config.default_ttl_minutes == 60
            assert m.config.max_sandboxes_per_environment == 10

        def test_custom_config(self) -> None:
            config = SandboxConfig(default_ttl_minutes=120, max_sandboxes_per_environment=5)
            m = SandboxManager(config=config)
            assert m.config.default_ttl_minutes == 120
            assert m.config.max_sandboxes_per_environment == 5
