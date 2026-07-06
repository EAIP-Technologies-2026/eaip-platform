"""Tests for :mod:`eaip.application.pipeline`."""

from __future__ import annotations

import pytest

from eaip.application.pipeline import StartupPhase, StartupPipeline
from eaip.exceptions.domain import LifecycleError


class TestStartupPhase:
    def test_phase_values(self) -> None:
        assert StartupPhase.CREATED.value == "created"
        assert StartupPhase.PRE_BOOTSTRAP.value == "pre_bootstrap"
        assert StartupPhase.BOOTSTRAP.value == "bootstrap"
        assert StartupPhase.RUNTIME.value == "runtime"
        assert StartupPhase.POST_BOOTSTRAP.value == "post_bootstrap"
        assert StartupPhase.RUNNING.value == "running"
        assert StartupPhase.SHUTDOWN.value == "shutdown"
        assert StartupPhase.STOPPED.value == "stopped"
        assert StartupPhase.FAILED.value == "failed"


class TestStartupPipelineConstruction:
    def test_create_pipeline(self) -> None:
        pipeline = StartupPipeline()
        assert pipeline.phase is StartupPhase.CREATED
        assert not pipeline.is_running
        assert not pipeline.is_stopped
        assert not pipeline.is_failed
        assert pipeline.started_at is None
        assert pipeline.completed_phases == []
        assert pipeline.hook_count == 0

    def test_register_hook(self) -> None:
        pipeline = StartupPipeline()

        async def my_hook(pipeline, ctx):
            pass

        pipeline.register("pre_bootstrap", my_hook, name="test_hook")
        assert pipeline.hook_count == 1

    def test_register_with_phase_enum(self) -> None:
        pipeline = StartupPipeline()

        def my_hook(pipeline, ctx):
            pass

        pipeline.register(StartupPhase.BOOTSTRAP, my_hook)
        assert pipeline.hook_count == 1

    def test_decorator_registration(self) -> None:
        pipeline = StartupPipeline()

        @pipeline.on("pre_bootstrap", name="decorated_hook")
        async def my_hook(pipeline, ctx):
            pass

        assert pipeline.hook_count == 1


class TestStartupPipelineExecution:
    @pytest.mark.asyncio
    async def test_run_with_no_hooks(self) -> None:
        pipeline = StartupPipeline()
        await pipeline.run()
        assert pipeline.phase is StartupPhase.RUNNING
        assert pipeline.is_running
        assert pipeline.started_at is not None
        assert len(pipeline.completed_phases) == 4

    @pytest.mark.asyncio
    async def test_run_executes_hooks_in_order(self) -> None:
        pipeline = StartupPipeline()
        executed: list[str] = []

        @pipeline.on("pre_bootstrap")
        async def pre_hook(pipeline, ctx):
            executed.append("pre")

        @pipeline.on("bootstrap")
        async def boot_hook(pipeline, ctx):
            executed.append("boot")

        @pipeline.on("runtime")
        async def runtime_hook(pipeline, ctx):
            executed.append("runtime")

        @pipeline.on("post_bootstrap")
        async def post_hook(pipeline, ctx):
            executed.append("post")

        await pipeline.run()
        assert executed == ["pre", "boot", "runtime", "post"]
        assert pipeline.phase is StartupPhase.RUNNING

    @pytest.mark.asyncio
    async def test_run_passes_context(self) -> None:
        pipeline = StartupPipeline()

        @pipeline.on("pre_bootstrap")
        async def check_ctx(pl, ctx):
            assert ctx == {"test": True}

        await pipeline.run(context={"test": True})

    @pytest.mark.asyncio
    async def test_sync_hook_supported(self) -> None:
        pipeline = StartupPipeline()
        called = False

        @pipeline.on("pre_bootstrap")
        def sync_hook(pipeline, ctx):
            nonlocal called
            called = True

        await pipeline.run()
        assert called

    @pytest.mark.asyncio
    async def test_run_already_started_raises(self) -> None:
        pipeline = StartupPipeline()
        await pipeline.run()
        with pytest.raises(LifecycleError):
            await pipeline.run()


class TestStartupPipelineShutdown:
    @pytest.mark.asyncio
    async def test_shutdown_from_running(self) -> None:
        pipeline = StartupPipeline()
        await pipeline.run()
        assert pipeline.is_running

        await pipeline.shutdown()
        assert pipeline.phase is StartupPhase.STOPPED
        assert pipeline.is_stopped

    @pytest.mark.asyncio
    async def test_shutdown_idempotent(self) -> None:
        pipeline = StartupPipeline()
        await pipeline.run()
        await pipeline.shutdown()
        await pipeline.shutdown()
        assert pipeline.is_stopped

    @pytest.mark.asyncio
    async def test_shutdown_from_created_is_noop(self) -> None:
        pipeline = StartupPipeline()
        await pipeline.shutdown()
        assert pipeline.phase is StartupPhase.CREATED

    @pytest.mark.asyncio
    async def test_shutdown_executes_shutdown_hooks(self) -> None:
        pipeline = StartupPipeline()
        shutdown_called = False

        @pipeline.on("shutdown")
        async def shutdown_hook(pipeline, ctx):
            nonlocal shutdown_called
            shutdown_called = True

        await pipeline.run()
        await pipeline.shutdown()
        assert shutdown_called

    @pytest.mark.asyncio
    async def test_shutdown_hooks_in_reverse_order_on_failure(self) -> None:
        pipeline = StartupPipeline()
        executed: list[str] = []

        @pipeline.on("bootstrap")
        async def failing_hook(pipeline, ctx):
            executed.append("boot")
            raise ValueError("bootstrap failed")

        @pipeline.on("shutdown")
        async def shutdown_hook1(pipeline, ctx):
            executed.append("shutdown1")

        @pipeline.on("shutdown")
        async def shutdown_hook2(pipeline, ctx):
            executed.append("shutdown2")

        with pytest.raises(LifecycleError):
            await pipeline.run()
        assert pipeline.phase is StartupPhase.FAILED
        await pipeline.shutdown()
        assert pipeline.phase is StartupPhase.STOPPED

    @pytest.mark.asyncio
    async def test_context_manager(self) -> None:
        pipeline = StartupPipeline()
        async with pipeline:
            assert pipeline.is_running
        assert pipeline.is_stopped


class TestStartupPipelineErrorHandling:
    @pytest.mark.asyncio
    async def test_hook_failure_sets_failed_phase(self) -> None:
        pipeline = StartupPipeline()

        @pipeline.on("pre_bootstrap")
        async def failing(pipeline, ctx):
            raise ValueError("boom")

        with pytest.raises(LifecycleError):
            await pipeline.run()
        assert pipeline.phase is StartupPhase.FAILED
        assert pipeline.is_failed

    @pytest.mark.asyncio
    async def test_hook_failure_in_middle_phase(self) -> None:
        pipeline = StartupPipeline()
        seen: list[str] = []

        @pipeline.on("pre_bootstrap")
        async def pre(pipeline, ctx):
            seen.append("pre")

        @pipeline.on("bootstrap")
        async def boot(pipeline, ctx):
            seen.append("boot")
            raise RuntimeError("boot failed")

        @pipeline.on("runtime")
        async def runtime(pipeline, ctx):
            seen.append("runtime")

        with pytest.raises(LifecycleError):
            await pipeline.run()
        assert seen == ["pre", "boot"]
        assert "runtime" not in seen

    @pytest.mark.asyncio
    async def test_hook_failure_triggers_rollback(self) -> None:
        pipeline = StartupPipeline()
        rollback_called = False

        @pipeline.on("pre_bootstrap")
        async def failing(pipeline, ctx):
            raise RuntimeError("pre failed")

        @pipeline.on("shutdown")
        async def shutdown_hook(pipeline, ctx):
            nonlocal rollback_called
            rollback_called = True

        with pytest.raises(LifecycleError):
            await pipeline.run()
        assert pipeline.is_failed
        await pipeline.shutdown()
        assert pipeline.is_stopped
