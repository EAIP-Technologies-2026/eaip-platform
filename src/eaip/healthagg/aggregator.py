"""Health Aggregator — component registration, aggregation, snapshots."""

from __future__ import annotations

import asyncio
import time
import uuid
from collections.abc import Sequence
from typing import Any

from eaip.health.checks import HealthCheck, HealthReport, HealthStatus
from eaip.healthagg.dependencies import DependencyGraph
from eaip.healthagg.events import (
    ComponentStatusChanged,
    HealthCheckCompleted,
    HealthDegraded,
    HealthRestored,
    SnapshotCaptured,
)
from eaip.healthagg.exceptions import ComponentNotFoundError
from eaip.healthagg.models import HealthAggregationConfig, HealthSnapshot
from eaip.logging.context import get_logger


class HealthAggregator:
    def __init__(
        self,
        config: HealthAggregationConfig | None = None,
        dependency_graph: DependencyGraph | None = None,
        event_bus: Any | None = None,
    ) -> None:
        self._config = config or HealthAggregationConfig()
        self._graph = dependency_graph or DependencyGraph()
        self._event_bus = event_bus
        self._checks: dict[str, HealthCheck] = {}
        self._previous_statuses: dict[str, HealthStatus] = {}
        self._snapshots: list[HealthSnapshot] = []
        self._log = get_logger("eaip.healthagg.aggregator")

    @property
    def config(self) -> HealthAggregationConfig:
        return self._config

    @property
    def dependency_graph(self) -> DependencyGraph:
        return self._graph

    def register_component(self, name: str, check: HealthCheck | None = None) -> None:
        if check is not None:
            self._checks[name] = check

    def unregister_component(self, name: str) -> bool:
        self._previous_statuses.pop(name, None)
        return self._checks.pop(name, None) is not None

    async def aggregate(self) -> HealthReport:
        if not self._checks:
            return HealthReport(
                component="healthagg",
                status=HealthStatus.HEALTHY,
                message="no components registered",
            )

        results = await asyncio.gather(
            *(self._safe_check(name, c) for name, c in self._checks.items()),
            return_exceptions=False,
        )
        children = tuple(results)
        worst = max((r.status for r in children), key=lambda s: s.numeric)
        message = {
            HealthStatus.HEALTHY: "all components healthy",
            HealthStatus.DEGRADED: "one or more components degraded",
            HealthStatus.UNHEALTHY: "one or more components unhealthy",
        }[worst]

        return HealthReport(
            component="healthagg",
            status=worst,
            message=message,
            children=children,
        )

    async def _safe_check(self, name: str, check: HealthCheck) -> HealthReport:
        start = time.perf_counter()
        try:
            report = await check.check()
        except BaseException as exc:
            self._log.error("healthagg.check_failed", component=name, error=repr(exc))
            report = HealthReport(
                component=name,
                status=HealthStatus.UNHEALTHY,
                message=f"check raised: {exc!r}",
            )
        elapsed_ms = (time.perf_counter() - start) * 1000

        self._publish_event(
            HealthCheckCompleted(component=name, status=report.status, duration_ms=elapsed_ms)
        )
        self._check_status_change(name, report.status)
        return report

    def _check_status_change(self, component: str, new_status: HealthStatus) -> None:
        prev = self._previous_statuses.get(component)
        if prev is not None and prev != new_status:
            self._publish_event(
                ComponentStatusChanged(
                    component=component, previous_status=prev, new_status=new_status
                )
            )
            if new_status is HealthStatus.UNHEALTHY:
                self._publish_event(
                    HealthDegraded(
                        component=component, previous_status=prev, current_status=new_status
                    )
                )
            elif prev is HealthStatus.UNHEALTHY and new_status in (
                HealthStatus.HEALTHY,
                HealthStatus.DEGRADED,
            ):
                self._publish_event(
                    HealthRestored(
                        component=component, previous_status=prev, current_status=new_status
                    )
                )
        self._previous_statuses[component] = new_status

    async def get_component_health(self, name: str) -> HealthReport:
        check = self._checks.get(name)
        if check is None:
            raise ComponentNotFoundError(
                f"component {name!r} not found",
                context={"component": name},
            )
        return await check.check()

    async def get_all_components(self) -> dict[str, HealthStatus]:
        result: dict[str, HealthStatus] = {}
        for name, check in self._checks.items():
            try:
                report = await check.check()
                result[name] = report.status
            except BaseException:
                result[name] = HealthStatus.UNHEALTHY
        return result

    async def capture_snapshot(self) -> HealthSnapshot:
        start = time.perf_counter()
        statuses = await self.get_all_components()
        elapsed_ms = (time.perf_counter() - start) * 1000
        overall = (
            max((s for s in statuses.values()), key=lambda s: s.numeric)
            if statuses
            else HealthStatus.HEALTHY
        )
        deps_evaluated = len(self._graph._dependencies)

        snap = HealthSnapshot(
            id=str(uuid.uuid4()),
            component_statuses=statuses,
            overall_status=overall,
            dependencies_evaluated=deps_evaluated,
            duration_ms=elapsed_ms,
        )
        self._snapshots.append(snap)
        self._trim_snapshots()
        self._publish_event(
            SnapshotCaptured(
                snapshot_id=snap.id, overall_status=overall, component_count=len(statuses)
            )
        )
        return snap

    async def get_snapshots(self, limit: int = 10) -> Sequence[HealthSnapshot]:
        return self._snapshots[-limit:]

    def _trim_snapshots(self) -> None:
        if len(self._snapshots) > self._config.max_snapshots:
            excess = len(self._snapshots) - self._config.max_snapshots
            self._snapshots = self._snapshots[excess:]

    def _publish_event(self, event: Any) -> None:
        if self._event_bus is not None:
            try:
                self._event_bus.publish(event)
            except BaseException:
                self._log.warning("healthagg.event_publish_failed", event_type=type(event).__name__)


__all__ = ["HealthAggregator"]
