"""Load test orchestrator — defines and executes load test scenarios."""

from __future__ import annotations

import asyncio
import math
import uuid
from typing import Any

from eaip.perf.events import LoadTestCompleted, LoadTestStarted
from eaip.perf.exceptions import LoadTestError
from eaip.perf.models import BenchmarkRunStatus, LoadTestResult, LoadTestScenario
from eaip.shared.time import utc_now


class LoadTestOrchestrator:
    def __init__(self) -> None:
        self._scenarios: dict[str, LoadTestScenario] = {}
        self._results: dict[str, LoadTestResult] = {}
        self._cancel_events: dict[str, asyncio.Event] = {}
        self._event_callback: Any = None

    def set_event_callback(self, callback: Any) -> None:
        self._event_callback = callback

    def _emit(self, event: Any) -> None:
        if self._event_callback is not None:
            self._event_callback(event)

    def create_scenario(self, scenario: LoadTestScenario) -> LoadTestScenario:
        self._scenarios[scenario.id] = scenario
        return scenario

    def get_scenario(self, scenario_id: str) -> LoadTestScenario:
        if scenario_id not in self._scenarios:
            raise LoadTestError(f"Scenario {scenario_id!r} not found")
        return self._scenarios[scenario_id]

    def update_scenario(self, scenario_id: str, **updates: Any) -> LoadTestScenario:
        existing = self.get_scenario(scenario_id)
        updated = existing.model_copy(update=updates)
        self._scenarios[scenario_id] = updated
        return updated

    def delete_scenario(self, scenario_id: str) -> None:
        if scenario_id not in self._scenarios:
            raise LoadTestError(f"Scenario {scenario_id!r} not found")
        del self._scenarios[scenario_id]

    def list_scenarios(
        self,
        target_component: str | None = None,
        enabled: bool | None = None,
    ) -> list[LoadTestScenario]:
        results: list[LoadTestScenario] = list(self._scenarios.values())
        if target_component is not None:
            results = [s for s in results if s.target_component == target_component]
        if enabled is not None:
            results = [s for s in results if s.enabled is enabled]
        return results

    async def execute_scenario(
        self,
        scenario_id: str,
        metadata: dict[str, Any] | None = None,
    ) -> LoadTestResult:
        scenario = self.get_scenario(scenario_id)
        if not scenario.enabled:
            raise LoadTestError(f"Scenario {scenario_id!r} is disabled")

        result_id = str(uuid.uuid4())
        cancel_event = asyncio.Event()
        self._cancel_events[result_id] = cancel_event

        result = LoadTestResult(
            id=result_id,
            scenario_id=scenario_id,
            status=BenchmarkRunStatus.RUNNING,
            started_at=utc_now(),
            metadata=metadata or {},
        )
        self._results[result_id] = result

        self._emit(
            LoadTestStarted(
                result_id=result_id,
                scenario_id=scenario_id,
                target_component=scenario.target_component,
            )
        )

        try:
            sim_result = await self._simulate(scenario, cancel_event)
            completed = utc_now()
            if result.started_at:
                duration = (completed - result.started_at).total_seconds() * 1000.0
            else:
                duration = 0.0

            result = LoadTestResult(
                id=result_id,
                scenario_id=scenario_id,
                status=BenchmarkRunStatus.COMPLETED,
                started_at=result.started_at,
                completed_at=completed,
                duration_ms=duration,
                metadata=metadata or {},
                **sim_result,
            )

            self._emit(
                LoadTestCompleted(
                    result_id=result_id,
                    scenario_id=scenario_id,
                    total_requests=sim_result["total_requests"],
                    successful_requests=sim_result["successful_requests"],
                    failed_requests=sim_result["failed_requests"],
                    avg_response_time_ms=sim_result["avg_response_time_ms"],
                    error_rate=sim_result["error_rate"],
                )
            )

        except Exception:
            completed = utc_now()
            if result.started_at:
                duration = (completed - result.started_at).total_seconds() * 1000.0
            else:
                duration = 0.0
            result = LoadTestResult(
                id=result_id,
                scenario_id=scenario_id,
                status=BenchmarkRunStatus.FAILED,
                started_at=result.started_at,
                completed_at=completed,
                duration_ms=duration,
                metadata=metadata or {},
            )
        finally:
            self._cancel_events.pop(result_id, None)

        self._results[result_id] = result
        return result

    async def _simulate(
        self,
        scenario: LoadTestScenario,
        cancel_event: asyncio.Event,
    ) -> dict[str, Any]:
        total_steps = scenario.duration_seconds
        concurrency = scenario.concurrency_level
        base_latency = 50.0 + abs(hash(scenario.id)) % 200
        throughput_base = concurrency * (1000.0 / base_latency)

        successful = 0
        failed = 0
        latencies: list[float] = []

        for step in range(total_steps):
            if cancel_event.is_set():
                break

            await asyncio.sleep(1.0)
            step_successful = int(throughput_base * (1.0 + math.sin(step / 5.0) * 0.1))
            jitter = 1.0 + abs(math.cos(step / 3.0)) * 0.5
            step_failed = max(0, int(throughput_base * 0.01 * jitter))
            successful += step_successful
            failed += step_failed

            for _ in range(min(step_successful + step_failed, 100)):
                latencies.append(base_latency + abs(math.sin(step + len(latencies))) * 20)

        total = successful + failed
        avg_latency = sum(latencies) / len(latencies) if latencies else 0.0
        sorted_lats = sorted(latencies)
        p50 = sorted_lats[len(sorted_lats) // 2] if sorted_lats else 0.0
        p95 = sorted_lats[int(len(sorted_lats) * 0.95)] if sorted_lats else 0.0
        p99 = sorted_lats[int(len(sorted_lats) * 0.99)] if sorted_lats else 0.0
        throughput = total / (scenario.duration_seconds or 1)
        error_rate = failed / total if total > 0 else 0.0

        return {
            "total_requests": total,
            "successful_requests": successful,
            "failed_requests": failed,
            "avg_response_time_ms": round(avg_latency, 2),
            "p50_response_time": round(p50, 2),
            "p95_response_time": round(p95, 2),
            "p99_response_time": round(p99, 2),
            "throughput_reqs_per_sec": round(throughput, 2),
            "error_rate": round(error_rate, 4),
        }

    async def cancel_scenario(self, run_id: str) -> None:
        if run_id not in self._results:
            raise LoadTestError(f"Load test result {run_id!r} not found")
        cancel_event = self._cancel_events.get(run_id)
        if cancel_event is not None:
            cancel_event.set()

    async def get_result(self, result_id: str) -> LoadTestResult:
        if result_id not in self._results:
            raise LoadTestError(f"Load test result {result_id!r} not found")
        return self._results[result_id]

    async def list_results(
        self,
        scenario_id: str | None = None,
        limit: int = 100,
    ) -> list[LoadTestResult]:
        results: list[LoadTestResult] = list(self._results.values())
        if scenario_id is not None:
            results = [r for r in results if r.scenario_id == scenario_id]
        results.sort(key=lambda r: r.started_at or utc_now(), reverse=True)
        return results[:limit]
