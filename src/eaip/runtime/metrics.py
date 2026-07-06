"""Runtime metrics collectors for command bus, query bus, and worker pool.

Each collector aggregates counters and timing data that can be used for
monitoring, dashboards, or hooking into external telemetry systems.

Usage::

    from eaip.runtime.commands import CommandBus
    from eaip.runtime.metrics import CommandMetrics

    bus = CommandBus()
    metrics = CommandMetrics()
    bus.set_validator(metrics.validator)

    result = await bus.dispatch(SomeCommand())
    print(metrics.report())
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field

from eaip.logging.context import get_logger

# ---------------------------------------------------------------------------
# Command metrics
# ---------------------------------------------------------------------------


@dataclass
class CommandMetricsReport:
    """Snapshot of command execution metrics.

    Attributes:
    ----------
    total_dispatched:
        Total number of command dispatch calls.
    total_succeeded:
        Number of commands completed without error.
    total_failed:
        Number of commands that raised an exception.
    total_retries:
        Total number of retry attempts across all commands.
    per_command:
        Per-command-type breakdown of counts.
    """

    total_dispatched: int = 0
    total_succeeded: int = 0
    total_failed: int = 0
    total_retries: int = 0
    per_command: dict[str, dict[str, int]] = field(default_factory=dict)


class CommandMetrics:
    """Collects execution metrics for commands dispatched through a CommandBus.

    Usage::

        metrics = CommandMetrics()

        # Use as a validator wrapper to capture every dispatch.
        bus.set_validator(metrics.validator)
    """

    def __init__(self) -> None:
        """Initialize the command metrics collector with zeroed counters."""
        self._dispatched: Counter[str] = Counter()
        self._succeeded: Counter[str] = Counter()
        self._failed: Counter[str] = Counter()
        self._retries: Counter[str] = Counter()
        self._log = get_logger("eaip.runtime.metrics.commands")

    def record_dispatch(self, command_type: str) -> None:
        """Record a command dispatch."""
        self._dispatched[command_type] += 1

    def record_success(self, command_type: str) -> None:
        """Record a successful command execution."""
        self._succeeded[command_type] += 1

    def record_failure(self, command_type: str, _error: str = "") -> None:
        """Record a failed command execution."""
        self._failed[command_type] += 1

    def record_retry(self, command_type: str) -> None:
        """Record a retry attempt."""
        self._retries[command_type] += 1

    def report(self) -> CommandMetricsReport:
        """Produce a snapshot of current metrics."""
        all_types = set(self._dispatched) | set(self._succeeded) | set(self._failed)
        per_command = {}
        for t in sorted(all_types):
            per_command[t] = {
                "dispatched": self._dispatched.get(t, 0),
                "succeeded": self._succeeded.get(t, 0),
                "failed": self._failed.get(t, 0),
                "retries": self._retries.get(t, 0),
            }

        return CommandMetricsReport(
            total_dispatched=sum(self._dispatched.values()),
            total_succeeded=sum(self._succeeded.values()),
            total_failed=sum(self._failed.values()),
            total_retries=sum(self._retries.values()),
            per_command=per_command,
        )

    def reset(self) -> None:
        """Reset all collected metrics to zero."""
        self._dispatched.clear()
        self._succeeded.clear()
        self._failed.clear()
        self._retries.clear()


# ---------------------------------------------------------------------------
# Query metrics
# ---------------------------------------------------------------------------


@dataclass
class QueryMetricsReport:
    """Snapshot of query execution metrics.

    Attributes:
    ----------
    total_dispatched:
        Total number of query dispatch calls.
    total_succeeded:
        Number of queries completed without error.
    total_failed:
        Number of queries that raised an exception.
    cache_hits:
        Number of cache hits.
    cache_misses:
        Number of cache misses (cache configured but no entry found).
    per_query:
        Per-query-type breakdown of counts.
    """

    total_dispatched: int = 0
    total_succeeded: int = 0
    total_failed: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    per_query: dict[str, dict[str, int]] = field(default_factory=dict)


class QueryMetrics:
    """Collects execution metrics for queries dispatched through a QueryBus.

    Usage::

        metrics = QueryMetrics()

        # Wrap the bus dispatch to collect metrics.
        original = bus.dispatch

        async def wrapped(query, **kw):
            metrics.record_dispatch(type(query).__name__)
            result = await original(query, **kw)
            if result.cached:
                metrics.record_cache_hit(type(query).__name__)
            if result.success:
                metrics.record_success(type(query).__name__)
            else:
                metrics.record_failure(type(query).__name__)
            return result

        bus.dispatch = wrapped
    """

    def __init__(self) -> None:
        """Initialize the query metrics collector with zeroed counters."""
        self._dispatched: Counter[str] = Counter()
        self._succeeded: Counter[str] = Counter()
        self._failed: Counter[str] = Counter()
        self._cache_hits: Counter[str] = Counter()
        self._cache_misses: Counter[str] = Counter()
        self._log = get_logger("eaip.runtime.metrics.queries")

    def record_dispatch(self, query_type: str) -> None:
        """Record a query dispatch."""
        self._dispatched[query_type] += 1

    def record_success(self, query_type: str) -> None:
        """Record a successful query execution."""
        self._succeeded[query_type] += 1

    def record_failure(self, query_type: str) -> None:
        """Record a failed query execution."""
        self._failed[query_type] += 1

    def record_cache_hit(self, query_type: str) -> None:
        """Record a cache hit for the given query type."""
        self._cache_hits[query_type] += 1

    def record_cache_miss(self, query_type: str) -> None:
        """Record a cache miss for the given query type."""
        self._cache_misses[query_type] += 1

    def report(self) -> QueryMetricsReport:
        """Produce a snapshot of current metrics."""
        all_types = (
            set(self._dispatched)
            | set(self._succeeded)
            | set(self._failed)
            | set(self._cache_hits)
            | set(self._cache_misses)
        )
        per_query = {}
        for t in sorted(all_types):
            per_query[t] = {
                "dispatched": self._dispatched.get(t, 0),
                "succeeded": self._succeeded.get(t, 0),
                "failed": self._failed.get(t, 0),
                "cache_hits": self._cache_hits.get(t, 0),
                "cache_misses": self._cache_misses.get(t, 0),
            }

        return QueryMetricsReport(
            total_dispatched=sum(self._dispatched.values()),
            total_succeeded=sum(self._succeeded.values()),
            total_failed=sum(self._failed.values()),
            cache_hits=sum(self._cache_hits.values()),
            cache_misses=sum(self._cache_misses.values()),
            per_query=per_query,
        )

    def reset(self) -> None:
        """Reset all counters to zero."""
        self._dispatched.clear()
        self._succeeded.clear()
        self._failed.clear()
        self._cache_hits.clear()
        self._cache_misses.clear()


__all__ = [
    "CommandMetrics",
    "CommandMetricsReport",
    "QueryMetrics",
    "QueryMetricsReport",
]
