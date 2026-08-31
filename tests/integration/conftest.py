"""Integration-test fixtures for B01 persistence tests.

pytest-asyncio runs each test in a fresh event loop, and asyncpg pools are
bound to the loop they were created on.  The ``db`` fixture is therefore
*function-scoped*: it initializes the pool and applies any pending migrations in
the same loop as the test, then closes the pool on teardown.

If PostgreSQL is unreachable the tests are skipped rather than failed — they
require the dev stack (docker compose up -d).
"""

from __future__ import annotations

import pytest

from eaip.infrastructure.db.connection import DatabaseConnection
from eaip.infrastructure.db.migrations import MigrationEngine
from eaip.infrastructure.migrations import load_all_migrations

DSN = "postgresql://eaip:eaip_dev_password@localhost:5432/eaip_test"


@pytest.fixture(autouse=True)
async def _reset_database_pool() -> None:
    """Shadow the top-level autouse teardown — ``db`` owns the pool lifecycle."""
    yield


@pytest.fixture
async def db() -> None:
    """Function-scoped PostgreSQL pool with pending migrations applied."""
    try:
        import asyncpg  # noqa: F401

        conn = await asyncpg.connect(DSN)
        await conn.close()
    except Exception as exc:  # noqa: BLE001
        pytest.skip(f"PostgreSQL unavailable at {DSN}: {exc}")

    await DatabaseConnection.initialize("test", dsn=DSN, min_size=1, max_size=4)
    engine = MigrationEngine(DatabaseConnection, table_name="_eaip_test_migrations")
    await engine.initialize()
    for migration in load_all_migrations():
        engine.register(migration)
    await engine.run_pending()

    yield

    await DatabaseConnection.close()


@pytest.fixture(autouse=True)
async def _clean_tables(db: None) -> None:
    """Truncate B01 tables between tests for isolation."""
    for table in (
        "dead_letters",
        "runtime_events",
        "audit_events",
        "workflow_runs",
        "agent_runs",
        "agents",
        "workflows",
    ):
        try:
            await DatabaseConnection.execute(f"DELETE FROM {table}")
        except Exception:
            pass


async def _fresh_pool() -> None:
    """Close and re-initialize the pool — simulates a process restart."""
    await DatabaseConnection.close()
    await DatabaseConnection.initialize("test", dsn=DSN, min_size=1, max_size=4)


@pytest.fixture
async def fresh_pool(db: None, _clean_tables: None) -> None:
    yield _fresh_pool