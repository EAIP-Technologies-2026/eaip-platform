"""Pytest configuration & top-level fixtures."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

import eaip.logging.config as _cfg

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
