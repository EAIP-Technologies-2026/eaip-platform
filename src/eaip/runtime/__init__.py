"""Runtime Kernel — Layer 2 of the EAIP architecture.

This package provides the core runtime primitives:

- :class:`~eaip.runtime.context.RuntimeContext` — ambient execution context.
- :class:`~eaip.runtime.module.RuntimeModule` — protocol for runtime modules.
- :class:`~eaip.runtime.module.BaseRuntimeModule` — abstract base class.
- :class:`~eaip.runtime.host.RuntimeHost` — lifecycle orchestrator.
- :class:`~eaip.runtime.loader.ModuleLoader` — module registry.
- :class:`~eaip.runtime.graph.DependencyGraph` — topological startup ordering.
- :class:`~eaip.runtime.health.RuntimeHealthCheck` — per-module health adapter.
- :class:`~eaip.runtime.hooks.ObservabilityHooks` — synchronous lifecycle hooks.
- :mod:`~eaip.runtime.events` — typed domain events.
- :mod:`~eaip.runtime.exceptions` — runtime-specific exception hierarchy.
- :class:`~eaip.runtime.bootstrap.BootstrapManager` — pre/post start hooks.
- :class:`~eaip.runtime.builder.RuntimeBuilder` — fluent kernel construction.
- :class:`~eaip.runtime.composition.CompositionRoot` — platform wiring.
- :class:`~eaip.runtime.kernel.RuntimeKernel` — top-level orchestrator.
- :class:`~eaip.runtime.registry.RuntimeRegistry` — central module registry.
- :class:`~eaip.runtime.pipeline.Pipeline` — composable middleware chain.
- :class:`~eaip.runtime.scheduler.SchedulerModule` — task scheduling module.
- :class:`~eaip.runtime.commands.CommandBus` — CQRS command dispatch.
- :class:`~eaip.runtime.queries.QueryBus` — CQRS query dispatch with caching.
"""

from __future__ import annotations

from eaip.runtime.bootstrap import BootstrapManager
from eaip.runtime.builder import RuntimeBuilder
from eaip.runtime.bus import RuntimeEventBus
from eaip.runtime.cache import InMemoryQueryCache
from eaip.runtime.commands import Command, CommandBus, CommandHandler, CommandResult, RetryPolicy
from eaip.runtime.composition import CompositionRoot
from eaip.runtime.context import (
    RuntimeContext,
    current_context,
    require_context,
    reset_context,
    run_with_context,
    set_context,
)
from eaip.runtime.di import RuntimeContainer
from eaip.runtime.events import (
    ModuleRegistered,
    ModuleStarted,
    ModuleStartFailed,
    ModuleStopFailed,
    ModuleStopped,
    RuntimeEvent,
    RuntimeRunning,
    RuntimeStarting,
    RuntimeStopped,
    RuntimeStopping,
)
from eaip.runtime.exceptions import (
    DependencyResolutionError,
    KernelError,
    ModuleActivationError,
    ModuleLoadError,
    RuntimeContextError,
)
from eaip.runtime.graph import DependencyGraph
from eaip.runtime.health import RuntimeDiagnostics, RuntimeHealthCheck
from eaip.runtime.hooks import ObservabilityHooks
from eaip.runtime.host import RuntimeHost
from eaip.runtime.kernel import RuntimeKernel
from eaip.runtime.kernel_events import KernelEvent, KernelStarted, KernelStopped
from eaip.runtime.loader import ModuleLoader
from eaip.runtime.metrics import (
    CommandMetrics,
    CommandMetricsReport,
    QueryMetrics,
    QueryMetricsReport,
)
from eaip.runtime.module import BaseRuntimeModule, RuntimeModule
from eaip.runtime.pipeline import (
    Handler as PipelineHandler,
    Middleware,
    NextCall,
    Pipeline,
    PipelineContext,
    cancellation_middleware,
    logging_middleware,
)
from eaip.runtime.plugin import RuntimePluginAdapter
from eaip.runtime.queries import Query, QueryBus, QueryCache, QueryHandler, QueryResult
from eaip.runtime.registry import ModuleEntry, RuntimeRegistry
from eaip.runtime.scheduler import JobFn, ScheduledJob, SchedulerModule
from eaip.runtime.workers import BackgroundWorker, TaskResult, WorkFn

__all__ = [
    "BackgroundWorker",
    "BaseRuntimeModule",
    "BootstrapManager",
    "Command",
    "CommandBus",
    "CommandHandler",
    "CommandMetrics",
    "CommandMetricsReport",
    "CommandResult",
    "CompositionRoot",
    "DependencyGraph",
    "DependencyResolutionError",
    "InMemoryQueryCache",
    "JobFn",
    "KernelError",
    "KernelEvent",
    "KernelStarted",
    "KernelStopped",
    "Middleware",
    "ModuleActivationError",
    "ModuleEntry",
    "ModuleLoadError",
    "ModuleLoader",
    "ModuleRegistered",
    "ModuleStartFailed",
    "ModuleStarted",
    "ModuleStopFailed",
    "ModuleStopped",
    "NextCall",
    "ObservabilityHooks",
    "Pipeline",
    "PipelineContext",
    "PipelineHandler",
    "Query",
    "QueryBus",
    "QueryCache",
    "QueryHandler",
    "QueryMetrics",
    "QueryMetricsReport",
    "QueryResult",
    "RetryPolicy",
    "RuntimeBuilder",
    "RuntimeContainer",
    "RuntimeContext",
    "RuntimeContextError",
    "RuntimeDiagnostics",
    "RuntimeEvent",
    "RuntimeEventBus",
    "RuntimeHealthCheck",
    "RuntimeHost",
    "RuntimeKernel",
    "RuntimeModule",
    "RuntimePluginAdapter",
    "RuntimeRegistry",
    "RuntimeRunning",
    "RuntimeStarting",
    "RuntimeStopped",
    "RuntimeStopping",
    "ScheduledJob",
    "SchedulerModule",
    "TaskResult",
    "WorkFn",
    "cancellation_middleware",
    "current_context",
    "logging_middleware",
    "require_context",
    "reset_context",
    "run_with_context",
    "set_context",
]
