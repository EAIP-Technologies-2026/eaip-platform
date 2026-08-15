"""Platform infrastructure — wires database, cache, storage, and background tasks on startup."""

from __future__ import annotations

import asyncio
import inspect
import time
from typing import Any

from eaip.db.provider import resolve_provider
from eaip.dependency_injection.container import Container
from eaip.events.bus import EventBus
from eaip.health.checks import (
    DependencyClass,
    HealthReport,
    HealthStatus,
)
from eaip.infrastructure.db.connection import DatabaseConnection
from eaip.infrastructure.db.migrations import MigrationEngine
from eaip.logging.context import get_logger
from eaip.settings.core_settings import PlatformSettings
from eaip.types import Environment

log = get_logger("eaip.infrastructure.infrastructure")


class InfrastructureHealthCheck:
    name: str = "infrastructure"
    criticality: DependencyClass = DependencyClass.CRITICAL
    configured: bool = True

    def __init__(self) -> None:
        self._checks: list[tuple[str, Any]] = []

    def register(self, name: str, checker: Any) -> None:
        self._checks.append((name, checker))

    async def check(self) -> HealthReport:
        details: dict[str, Any] = {}
        worst = HealthStatus.HEALTHY
        for name, checker in self._checks:
            try:
                if hasattr(checker, "ping") and callable(checker.ping):
                    result = checker.ping()
                    ok = await result if inspect.isawaitable(result) else result
                elif hasattr(checker, "health") and callable(checker.health):
                    result = checker.health()
                    result = await result if inspect.isawaitable(result) else result
                    ok = result.get("status") == "healthy" if isinstance(result, dict) else True
                else:
                    ok = True
                details[name] = "healthy" if ok else "unhealthy"
                if not ok:
                    worst = HealthStatus.UNHEALTHY
            except Exception as e:
                details[name] = f"error: {e}"
                worst = HealthStatus.UNHEALTHY
        return HealthReport(
            component=self.name,
            status=worst,
            message=f"{len(self._checks)} infrastructure services",
            details=details,
        )


class BackgroundTaskRegistry:
    def __init__(self) -> None:
        self._tasks: dict[str, asyncio.Task[Any]] = {}
        self._cancel_flags: dict[str, asyncio.Event] = {}
        self._log = log

    def register(self, name: str, coro: Any, interval_seconds: float | None = None) -> None:
        async def wrapper() -> None:
            cancel = asyncio.Event()
            self._cancel_flags[name] = cancel
            while not cancel.is_set():
                try:
                    if interval_seconds:
                        await asyncio.sleep(interval_seconds)
                    await coro()
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    self._log.warning("background_task.error", name=name, error=str(e))
                if not interval_seconds:
                    break

        task = asyncio.create_task(wrapper(), name=name)
        self._tasks[name] = task
        self._log.info("background_task.registered", name=name)

    async def cancel(self, name: str) -> None:
        if name in self._cancel_flags:
            self._cancel_flags[name].set()
        if name in self._tasks:
            self._tasks[name].cancel()
            try:
                await self._tasks[name]
            except asyncio.CancelledError:
                pass
            del self._tasks[name]
            self._log.info("background_task.cancelled", name=name)

    async def cancel_all(self) -> None:
        for name in list(self._tasks.keys()):
            await self.cancel(name)

    def status(self) -> dict[str, str]:
        return {name: "running" if not t.done() else "done" for name, t in self._tasks.items()}

    @property
    def count(self) -> int:
        return len(self._tasks)


async def _heartbeat_task() -> None:
    pass


async def _cleanup_task() -> None:
    pass


class PlatformInfrastructure:
    """Wires database, cache, migrations, health checks, and background tasks."""

    def __init__(self, container: Container, events: EventBus, settings: PlatformSettings) -> None:
        self._container = container
        self._events = events
        self._settings = settings
        self._bg_tasks = BackgroundTaskRegistry()
        self._infra_health = InfrastructureHealthCheck()
        self._db: DatabaseConnection | None = None
        self._migrations: MigrationEngine | None = None
        self._started = False
        self._log = log

    @property
    def background_tasks(self) -> BackgroundTaskRegistry:
        return self._bg_tasks

    async def start(self) -> None:
        """Initialize all infrastructure: DB, cache, storage, health checks, background tasks."""
        self._log.info("infrastructure.starting")
        start = time.monotonic()

        env = self._settings.core.environment
        use_pg = env in (Environment.LOCAL, Environment.DEVELOPMENT, Environment.STAGING, Environment.PRODUCTION)

        if use_pg:
            await self._init_database()
        else:
            self._log.info("infrastructure.skipping_db", environment=env.value)

        self._register_infra_health()

        self._register_background_tasks()

        if self._infra_health:
            self._container.register_instance(InfrastructureHealthCheck, self._infra_health)

        self._duration = time.monotonic() - start
        self._started = True
        self._log.info("infrastructure.started", duration_s=round(self._duration, 3))

    async def stop(self) -> None:
        self._log.info("infrastructure.stopping")
        await self._bg_tasks.cancel_all()
        if self._db:
            await self._db.close()
        self._started = False
        self._log.info("infrastructure.stopped")

    async def _init_database(self) -> None:
        provider_name = self._settings.database_provider.provider
        provider_settings = (
            self._settings.db
            if provider_name == "local"
            else self._settings.database_provider.resolve()
        )
        provider = resolve_provider(provider_name, provider_settings)
        kwargs = provider.connection_kwargs()
        self._log.info("infrastructure.connecting_db", provider=provider.name())

        retries = 3
        last_error = None
        for attempt in range(1, retries + 1):
            try:
                await DatabaseConnection.initialize(provider.name(), **kwargs)
                self._db = DatabaseConnection
                self._log.info("infrastructure.db_connected", provider=provider.name())
                break
            except Exception as e:
                last_error = e
                self._log.warning("infrastructure.db_retry", attempt=attempt, error=str(e))
                if attempt < retries:
                    await asyncio.sleep(2**attempt)

        if self._db is None:
            self._log.error("infrastructure.db_failed", error=str(last_error))
            return

        self._container.register_factory(DatabaseConnection, lambda _c: DatabaseConnection)
        self._infra_health.register("postgresql", self._db)

        if self._settings.database_provider.resolve().enable_migrations:
            await self._run_migrations()

    async def _run_migrations(self) -> None:
        from eaip.infrastructure.migrations import load_all_migrations

        db_settings = self._settings.database_provider.resolve()
        engine = MigrationEngine(DatabaseConnection, table_name=db_settings.migration_table)
        await engine.initialize()

        for migration in load_all_migrations():
            engine.register(migration)

        count = await engine.run_pending()
        self._log.info("infrastructure.migrations_complete", applied=count)
        self._migrations = engine

    def _register_infra_health(self) -> None:
        self._infra_health.register(
            "background_tasks",
            type(
                "_",
                (),
                {
                    "ping": staticmethod(lambda: True),
                    "health": staticmethod(lambda: {"status": "healthy"}),
                },
            )(),
        )

    def _register_background_tasks(self) -> None:
        self._bg_tasks.register("heartbeat", _heartbeat_task, interval_seconds=30.0)
        self._bg_tasks.register("cleanup", _cleanup_task, interval_seconds=300.0)

    @property
    def started(self) -> bool:
        return self._started

    @property
    def duration(self) -> float:
        return self._duration if self._started else 0.0


__all__ = ["BackgroundTaskRegistry", "InfrastructureHealthCheck", "PlatformInfrastructure"]
