from __future__ import annotations

import pytest

from eaip.application import build_platform
from eaip.exceptions.domain import LifecycleError
from eaip.runtime import RuntimeKernel
from eaip.runtime.context import RuntimeContext, current_context, scoped_runtime_context
from eaip.runtime.hooks import HookPoint


@pytest.fixture
def platform():
    return build_platform(configure_logging=False)


class TestRuntimeContext:
    def test_current_returns_default(self):
        ctx = current_context()
        assert ctx.run_id is None
        assert ctx.correlation_id is None

    def test_scoped_context_binds_values(self):
        with scoped_runtime_context(tenant_id="t1") as ctx:
            assert ctx.tenant_id == "t1"
            assert current_context().tenant_id == "t1"
        assert current_context().tenant_id is None

    def test_with_creates_derived_context(self):
        parent = RuntimeContext(tenant_id="t1")
        child = parent.with_(run_id="r1")
        assert child.tenant_id == "t1"
        assert child.run_id == "r1"

    def test_bind_sets_context_var(self):
        ctx = RuntimeContext(run_id="r2")
        ctx.bind()
        assert current_context().run_id == "r2"


class TestRuntimeKernel:
    async def test_boot_transitions_to_running(self, platform):
        kernel = RuntimeKernel(platform)
        assert kernel.phase.value == "created"
        await kernel.boot()
        assert kernel.phase.value == "running"

    async def test_shutdown_transitions_to_stopped(self, platform):
        async with RuntimeKernel(platform) as kernel:
            assert kernel.phase.value == "running"
        assert kernel.phase.value == "stopped"

    async def test_double_boot_raises(self, platform):
        kernel = RuntimeKernel(platform)
        await kernel.boot()
        with pytest.raises(LifecycleError):
            await kernel.boot()

    async def test_register_and_get_module(self, platform):
        kernel = RuntimeKernel(platform)
        kernel.register_module("test_mod", {"key": "value"})
        assert kernel.get_module("test_mod") == {"key": "value"}
        assert kernel.get_module("nonexistent") is None

    async def test_register_duplicate_module_raises(self, platform):
        kernel = RuntimeKernel(platform)
        kernel.register_module("m1", object())
        with pytest.raises(ValueError, match="already registered"):
            kernel.register_module("m1", object())

    async def test_scheduler_is_accessible(self, platform):
        kernel = RuntimeKernel(platform)
        assert kernel.scheduler is not None
        assert kernel.scheduler.task_count == 0

    async def test_hooks_are_integrated(self, platform):
        kernel = RuntimeKernel(platform)
        events: list[str] = []

        async def pre_start(**kwargs):
            events.append("pre_start")

        async def post_start(**kwargs):
            events.append("post_start")

        kernel.add_hook("pre", pre_start, HookPoint.PRE_START)
        kernel.add_hook("post", post_start, HookPoint.POST_START)

        await kernel.boot()
        assert "pre_start" in events
        assert "post_start" in events
        await kernel.shutdown()
