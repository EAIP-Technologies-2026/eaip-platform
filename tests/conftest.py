"""Pytest configuration & top-level fixtures."""

from __future__ import annotations

import os
import sys
from contextlib import suppress
from pathlib import Path

import pytest

import eaip.logging.config as _cfg
from eaip.infrastructure.db.connection import DatabaseConnection

# Ensure src/ is on the path even when tests are run from arbitrary cwd.
_SRC = Path(__file__).resolve().parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

# Default to the LOCAL environment so settings load deterministically.
os.environ.setdefault("EAIP_CORE__ENVIRONMENT", "local")

# Default JWT signing secret for test isolation.
os.environ.setdefault("EAIP_AUTH_SECRET", "test-secret-do-not-use-in-production")


@pytest.fixture(autouse=True)
def _restore_logging_config() -> None:
    """Reset logging state between tests so configuration is hermetic."""
    yield
    _cfg._state.configured = False


@pytest.fixture(autouse=True)
async def _reset_database_pool() -> None:
    """Close the asyncpg pool between tests.

    The pool is bound to the running event loop; pytest-asyncio creates a new
    loop per test, so we must release it to avoid cross-loop connection errors.
    The underlying Postgres data persists across tests as expected.

    Module-scoped fixtures may create the pool on a module-level loop while the
    autouse teardown runs on a function-level loop; tolerate that mismatch by
    releasing the reference even when the loop-local close fails.
    """
    yield
    if DatabaseConnection.get_pool() is not None:
        with suppress(Exception):
            # The pool may be owned by a module-scoped loop (e.g. module-scoped
            # app fixtures); closing it from this function-scoped teardown fails
            # with a cross-loop error. Leave the reference in place so the
            # owning loop's teardown (lifecycle.stop) closes it properly.
            await DatabaseConnection.close()

