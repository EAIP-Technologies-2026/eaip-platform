"""Tests for ApplicationLifecycle."""

from __future__ import annotations

import pytest

from eaip.app.lifecycle import ApplicationLifecycle
from eaip.application import build_platform
from eaip.exceptions.domain import LifecycleError
from eaip.lifecycle.phases import LifecyclePhase
from eaip.runtime import RuntimeKernel


@pytest.fixture
def platform():
    return build_platform(configure_logging=False)


class TestApplicationLifecycle:
    async def test_initial_phase_is_created(self, platform):
        app = ApplicationLifecycle(platform)
        assert app.phase is LifecyclePhase.CREATED
        assert not app.is_running

    async def test_start_transitions_to_running(self, platform):
        app = ApplicationLifecycle(platform)
        await app.start()
        assert app.phase is LifecyclePhase.RUNNING
        assert app.is_running

    async def test_stop_transitions_to_stopped(self, platform):
        app = ApplicationLifecycle(platform)
        await app.start()
        await app.stop()
        assert app.phase is LifecyclePhase.STOPPED
        assert not app.is_running

    async def test_double_start_raises(self, platform):
        app = ApplicationLifecycle(platform)
        await app.start()
        with pytest.raises(LifecycleError, match="cannot start"):
            await app.start()

    async def test_stop_before_start_raises(self, platform):
        app = ApplicationLifecycle(platform)
        with pytest.raises(LifecycleError, match="cannot stop application that has not started"):
            await app.stop()

    async def test_context_manager(self, platform):
        async with ApplicationLifecycle(platform) as app:
            assert app.phase is LifecyclePhase.RUNNING
        assert app.phase is LifecyclePhase.STOPPED

    async def test_with_kernel(self, platform):
        kernel = RuntimeKernel(platform)
        app = ApplicationLifecycle(platform, kernel=kernel)
        await app.start()
        assert app.phase is LifecyclePhase.RUNNING
        assert app.kernel is kernel
        assert kernel.phase.value == "running"
        await app.stop()
        assert kernel.phase.value == "stopped"

    async def test_platform_property(self, platform):
        app = ApplicationLifecycle(platform)
        assert app.platform is platform

    async def test_kernel_property_none_by_default(self, platform):
        app = ApplicationLifecycle(platform)
        assert app.kernel is None

    async def test_stop_idempotent(self, platform):
        app = ApplicationLifecycle(platform)
        await app.start()
        await app.stop()
        await app.stop()  # second stop should not raise
        assert app.phase is LifecyclePhase.STOPPED

    async def test_failed_start_sets_failed_phase(self, platform):
        # Simulate a failing platform start by making lifecycle.start fail
        original_start = platform._lifecycle.start

        async def failing_start():
            raise RuntimeError("start failed")

        platform._lifecycle.start = failing_start
        app = ApplicationLifecycle(platform)
        with pytest.raises(RuntimeError, match="start failed"):
            await app.start()
        assert app.phase is LifecyclePhase.FAILED
        platform._lifecycle.start = original_start
