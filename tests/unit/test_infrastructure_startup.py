"""Tests for :mod:`eaip.infrastructure.infrastructure` — startup flow and DB init."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

from eaip.dependency_injection.container import Container
from eaip.events.bus import EventBus
from eaip.infrastructure.infrastructure import PlatformInfrastructure
from eaip.settings.core_settings import CoreSettings, PlatformSettings
from eaip.types import Environment


def _settings(environment: Environment) -> PlatformSettings:
    return PlatformSettings(core=CoreSettings(environment=environment))


class TestPlatformInfrastructureStartup:
    async def test_local_env_skips_db(self) -> None:
        infra = PlatformInfrastructure(
            Container(), EventBus(), _settings(Environment.LOCAL)
        )
        with patch(
            "eaip.infrastructure.infrastructure.DatabaseConnection.initialize",
            new=AsyncMock(),
        ) as init:
            await infra.start()
            init.assert_not_called()
        assert infra.started is True

    async def test_production_env_initializes_db(self) -> None:
        infra = PlatformInfrastructure(
            Container(), EventBus(), _settings(Environment.PRODUCTION)
        )
        with patch(
            "eaip.infrastructure.infrastructure.DatabaseConnection.initialize",
            new=AsyncMock(),
        ), patch(
            "eaip.infrastructure.infrastructure.PlatformInfrastructure._run_migrations",
            new=AsyncMock(),
        ):
            await infra.start()
        assert infra._db is not None
        assert infra.started is True

    async def test_db_retry_then_success(self) -> None:
        infra = PlatformInfrastructure(
            Container(), EventBus(), _settings(Environment.PRODUCTION)
        )
        with patch(
            "eaip.infrastructure.infrastructure.DatabaseConnection.initialize",
            new=AsyncMock(side_effect=[RuntimeError("down"), None]),
        ), patch(
            "eaip.infrastructure.infrastructure.asyncio.sleep",
            new=AsyncMock(),
        ), patch(
            "eaip.infrastructure.infrastructure.PlatformInfrastructure._run_migrations",
            new=AsyncMock(),
        ):
            await infra.start()
        assert infra._db is not None

    async def test_db_failure_logs_and_continues(self) -> None:
        infra = PlatformInfrastructure(
            Container(), EventBus(), _settings(Environment.PRODUCTION)
        )
        with patch(
            "eaip.infrastructure.infrastructure.DatabaseConnection.initialize",
            new=AsyncMock(side_effect=RuntimeError("down")),
        ), patch(
            "eaip.infrastructure.infrastructure.asyncio.sleep",
            new=AsyncMock(),
        ):
            await infra.start()
        assert infra._db is None
        assert infra.started is True

    async def test_stop_closes_db(self) -> None:
        infra = PlatformInfrastructure(
            Container(), EventBus(), _settings(Environment.PRODUCTION)
        )
        with patch(
            "eaip.infrastructure.infrastructure.DatabaseConnection.initialize",
            new=AsyncMock(),
        ), patch(
            "eaip.infrastructure.infrastructure.DatabaseConnection.close",
            new=AsyncMock(),
        ) as close_mock, patch(
            "eaip.infrastructure.infrastructure.PlatformInfrastructure._run_migrations",
            new=AsyncMock(),
        ):
            await infra.start()
            await infra.stop()
            close_mock.assert_called_once()


__all__: list[str] = []
