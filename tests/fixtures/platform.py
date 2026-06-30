"""Fixtures that build a Platform for component tests."""

from __future__ import annotations

import pytest

from eaip.application import build_platform
from eaip.platform.platform import Platform


@pytest.fixture
def platform() -> Platform:
    """A freshly built but not-yet-started :class:`Platform`."""
    return build_platform(configure_logging=False)


@pytest.fixture
async def running_platform() -> Platform:
    """A started platform that is stopped on teardown."""
    p = build_platform(configure_logging=False)
    await p.start()
    try:
        yield p
    finally:
        await p.stop()
