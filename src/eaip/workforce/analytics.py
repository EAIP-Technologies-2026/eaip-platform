from __future__ import annotations

from collections import defaultdict
from datetime import timedelta
from typing import Any

from eaip.logging.context import get_logger
from eaip.shared.time import utc_now
from eaip.workforce.models import AssignmentStatus, WorkerType

log = get_logger("eaip.workforce.analytics")


def _categorize_worker(worker: Any) -> str:
    tags = {str(t).lower() for t in getattr(worker, "tags", ())}
    meta = getattr(worker, "metadata", {}) or {}
    if "human" in tags or meta.get("worker_mode") == "human" or meta.get("category") == "human":
        return "human"
    if "hybrid" in tags or meta.get("worker_mode") == "hybrid" or meta.get("category") == "hybrid":
        return "hybrid"
    if "ai" in tags or meta.get("worker_mode") == "ai" or meta.get("category") == "ai":
        return "ai"
    wt = getattr(worker, "worker_type", None)
    if wt == WorkerType.AGENT:
        return "ai"
    if wt == WorkerType.WORKFLOW:
        return "hybrid"
    return "human"


class WorkforceAnalyticsService:
    def __init__(self, registry: Any, orchestrator: Any, event_bus: Any = None) -> None:
        self._registry = registry
        self._orchestrator = orchestrator
        self._event_bus = event_bus
        self._log = get_logger("eaip.workforce.analytics")

    def _all_workers(self) -> list[Any]:
        try:
            return list(self._registry.list_workers())
        except Exception:
            return []

    def _all_assignments(self) -> list[Any]:
        try:
            assignments = getattr(self._orchestrator, "_assignments", None)
            if isinstance(assignments, dict):
                return list(assignments.values())
            if hasattr(self._orchestrator, "list_assignments"):
                return list(self._orchestrator.list_assignments())
            return []
        except Exception:
            return []

    def _assignments_for_tenant(self, tenant_id: str) -> list[Any]:
        assignments = self._all_assignments()
        if not assignments:
            return []
        filtered: list[Any] = []
        for a in assignments:
            meta = getattr(a, "metadata", None)
            if isinstance(meta, dict) and "tenant_id" in meta:
                if meta.get("tenant_id") == tenant_id:
                    filtered.append(a)
            else:
                filtered.append(a)
        return filtered

    def _workers_for_tenant(self, tenant_id: str) -> list[Any]:
        workers = self._all_workers()
        if not workers:
            return []
        filtered: list[Any] = []
        for w in workers:
            meta = getattr(w, "metadata", None)
            if isinstance(meta, dict) and "tenant_id" in meta:
                if meta.get("tenant_id") == tenant_id:
                    filtered.append(w)
            else:
                filtered.append(w)
        return filtered

    def get_overview(self, tenant_id: str) -> dict[str, Any]:
        workers = self._workers_for_tenant(tenant_id)
        total_workers = len(workers)
        human_workers = 0
        ai_agents = 0
        hybrid_workers = 0
        for w in workers:
            cat = _categorize_worker(w)
            if cat == "human":
                human_workers += 1
            elif cat == "ai":
                ai_agents += 1
            else:
                hybrid_workers += 1

        active_workers = 0
        idle_workers = 0
        overloaded_workers = 0
        unavailable_workers = 0
        utilizations: list[float] = []

        for w in workers:
            active = self._registry.active_count(w.id) if hasattr(self._registry, "active_count") else 0
            maxc = getattr(w, "max_concurrent_runs", 1) or 1
            util = active / maxc if maxc else 0.0
            utilizations.append(util)
            if active > 0:
                active_workers += 1
            else:
                idle_workers += 1
            if util > 0.8 or active >= maxc:
                overloaded_workers += 1
            meta = getattr(w, "metadata", {}) or {}
            tags = {str(t).lower() for t in getattr(w, "tags", ())}
            if meta.get("status") == "unavailable" or "unavailable" in tags or maxc == 0:
                unavailable_workers += 1

        utilization = round(sum(utilizations) / len(utilizations), 4) if utilizations else 0.0

        assignments = self._assignments_for_tenant(tenant_id)
        total = len(assignments)
        pending = sum(1 for a in assignments if getattr(a, "status", None) == AssignmentStatus.PENDING)
        running = sum(1 for a in assignments if getattr(a, "status", None) == AssignmentStatus.RUNNING)
        completed = sum(1 for a in assignments if getattr(a, "status", None) == AssignmentStatus.COMPLETED)
        failed = sum(1 for a in assignments if getattr(a, "status", None) == AssignmentStatus.FAILED)

        workload = pending + running
        throughput = completed
        completion_rate = round(completed / total, 4) if total else 0.0
        failure_rate = round(failed / total, 4) if total else 0.0
        queue_depth = pending

        return {
            "total_workers": total_workers,
            "human_workers": human_workers,
            "ai_agents": ai_agents,
            "hybrid_workers": hybrid_workers,
            "active_workers": active_workers,
            "idle_workers": idle_workers,
            "overloaded_workers": overloaded_workers,
            "unavailable_workers": unavailable_workers,
            "utilization": utilization,
            "workload": workload,
            "throughput": throughput,
            "completion_rate": completion_rate,
            "failure_rate": failure_rate,
            "queue_depth": queue_depth,
        }

    def get_utilization_timeseries(self, tenant_id: str, days: int = 7) -> list[dict[str, Any]]:
        workers = self._workers_for_tenant(tenant_id)
        total_workers = len(workers) or 1
        assignments = self._assignments_for_tenant(tenant_id)

        grouped: dict[str, list[Any]] = defaultdict(list)
        for a in assignments:
            ts = getattr(a, "assigned_at", None)
            if ts is None:
                continue
            try:
                key = ts.date().isoformat()
            except Exception:
                continue
            grouped[key] = grouped.get(key, [])
            grouped[key].append(a)

        now_date = utc_now().date()
        result: list[dict[str, Any]] = []
        for i in range(days - 1, -1, -1):
            d = now_date - timedelta(days=i)
            key = d.isoformat()
            day_assignments = grouped.get(key, [])
            distinct_workers = {getattr(a, "worker_id", "") for a in day_assignments}
            active = len(distinct_workers) if day_assignments else 0
            if not day_assignments:
                active_count_assignments = 0
            else:
                active_count_assignments = sum(
                    1 for a in day_assignments if getattr(a, "status", None) in (AssignmentStatus.RUNNING, AssignmentStatus.COMPLETED)
                )
                if active_count_assignments == 0 and day_assignments:
                    active = min(len(day_assignments), total_workers) if total_workers else 0
                else:
                    active = len({getattr(a, "worker_id", "") for a in day_assignments if getattr(a, "status", None) in (AssignmentStatus.RUNNING, AssignmentStatus.COMPLETED, AssignmentStatus.PENDING)})
            idle = max(0, total_workers - active)
            utilization = round(active / total_workers, 4) if total_workers else 0.0
            result.append({"date": key, "utilization": utilization, "active": active, "idle": idle})
        return result

    def get_workload_distribution(self, tenant_id: str) -> list[dict[str, Any]]:
        workers = self._workers_for_tenant(tenant_id)
        result: list[dict[str, Any]] = []
        for w in workers:
            active = self._registry.active_count(w.id) if hasattr(self._registry, "active_count") else 0
            maxc = getattr(w, "max_concurrent_runs", 1) or 1
            util = round(active / maxc * 100, 2) if maxc else 0.0
            result.append(
                {
                    "worker_id": w.id,
                    "name": getattr(w, "name", w.id),
                    "load": active,
                    "utilization_pct": util,
                    "active_count": active,
                    "max_concurrent": maxc,
                }
            )
        result.sort(key=lambda x: x["utilization_pct"], reverse=True)
        return result

    def detect_bottlenecks(self, tenant_id: str) -> list[dict[str, Any]]:
        workers = self._workers_for_tenant(tenant_id)
        assignments = self._assignments_for_tenant(tenant_id)
        pending_total = sum(1 for a in assignments if getattr(a, "status", None) == AssignmentStatus.PENDING)
        pending_by_worker: dict[str, int] = defaultdict(int)
        for a in assignments:
            if getattr(a, "status", None) == AssignmentStatus.PENDING:
                pending_by_worker[getattr(a, "worker_id", "")] += 1

        bottlenecks: list[dict[str, Any]] = []

        for w in workers:
            active = self._registry.active_count(w.id) if hasattr(self._registry, "active_count") else 0
            maxc = getattr(w, "max_concurrent_runs", 1) or 1
            util = active / maxc if maxc else 0.0
            if util > 0.8:
                if util >= 1.0:
                    severity = "critical"
                elif util > 0.9:
                    severity = "high"
                else:
                    severity = "medium"
                bottlenecks.append(
                    {
                        "worker_id": w.id,
                        "type": "overload",
                        "severity": severity,
                        "description": f"Worker {getattr(w, 'name', w.id)} overloaded at {util*100:.1f}% utilization ({active}/{maxc})",
                        "affected_workers": 1,
                        "suggested_action": "Scale max_concurrent_runs or redistribute load to idle workers",
                    }
                )
            pending = pending_by_worker.get(w.id, 0)
            if pending > 5:
                severity = "critical" if pending > 15 else "high" if pending > 10 else "medium"
                bottlenecks.append(
                    {
                        "worker_id": w.id,
                        "type": "queue",
                        "severity": severity,
                        "description": f"Queue depth {pending} exceeds threshold for worker {getattr(w, 'name', w.id)}",
                        "affected_workers": pending,
                        "suggested_action": "Add capacity or drain queue via additional workers",
                    }
                )

        if pending_total > 5:
            severity = "critical" if pending_total > 15 else "high" if pending_total > 10 else "medium"
            bottlenecks.append(
                {
                    "worker_id": "global",
                    "type": "queue",
                    "severity": severity,
                    "description": f"Global queue depth {pending_total} exceeds threshold",
                    "affected_workers": pending_total,
                    "suggested_action": "Scale workforce capacity or prioritize queue processing",
                }
            )

        return bottlenecks

    def get_capacity(self, tenant_id: str) -> dict[str, Any]:
        workers = self._workers_for_tenant(tenant_id)
        total_capacity = sum(getattr(w, "max_concurrent_runs", 0) or 0 for w in workers)
        used_capacity = 0
        for w in workers:
            try:
                used_capacity += self._registry.active_count(w.id)
            except Exception:
                pass
        available_capacity = max(0, total_capacity - used_capacity)
        assignments = self._assignments_for_tenant(tenant_id)
        demand = sum(1 for a in assignments if getattr(a, "status", None) == AssignmentStatus.PENDING)
        shortage = max(0, demand - available_capacity)
        utilization_pct = round(used_capacity / total_capacity * 100, 2) if total_capacity else 0.0
        return {
            "total_capacity": total_capacity,
            "used_capacity": used_capacity,
            "available_capacity": available_capacity,
            "demand": demand,
            "shortage": shortage,
            "utilization_pct": utilization_pct,
        }

    def get_recommendations(self, tenant_id: str) -> list[dict[str, Any]]:
        workers = self._workers_for_tenant(tenant_id)
        capacity = self.get_capacity(tenant_id)
        overview = self.get_overview(tenant_id)
        bottlenecks = self.detect_bottlenecks(tenant_id)

        recommendations: list[dict[str, Any]] = []
        rid = 1

        for w in workers:
            active = self._registry.active_count(w.id) if hasattr(self._registry, "active_count") else 0
            maxc = getattr(w, "max_concurrent_runs", 1) or 1
            util = active / maxc if maxc else 0.0
            if util < 0.2 and active == 0 and total_capacity_hint(workers) > 1:
                recommendations.append(
                    {
                        "id": f"rec-{rid:03d}",
                        "type": "scale_down",
                        "title": f"Underutilized worker: {getattr(w, 'name', w.id)}",
                        "description": f"Worker {getattr(w, 'name', w.id)} at {util*100:.1f}% utilization with no active assignments. Consider reassigning or scaling down.",
                        "priority": "low",
                        "worker_id": w.id,
                    }
                )
                rid += 1
            if util == 0 and maxc > 1 and len(workers) > 1:
                pass

        if capacity["shortage"] > 0:
            recommendations.append(
                {
                    "id": f"rec-{rid:03d}",
                    "type": "scale_up",
                    "title": "Capacity shortage detected",
                    "description": f"Demand ({capacity['demand']}) exceeds available capacity ({capacity['available_capacity']}). Shortage of {capacity['shortage']} slots. Add workers or increase max_concurrent_runs.",
                    "priority": "high" if capacity["shortage"] > 5 else "medium",
                    "worker_id": "",
                }
            )
            rid += 1

        overloaded_ids = {b["worker_id"] for b in bottlenecks if b["type"] == "overload"}
        idle_workers = [w for w in workers if (self._registry.active_count(w.id) if hasattr(self._registry, "active_count") else 0) == 0]
        if overloaded_ids and idle_workers:
            recommendations.append(
                {
                    "id": f"rec-{rid:03d}",
                    "type": "redistribute",
                    "title": "Redistribute load from overloaded to idle workers",
                    "description": f"{len(overloaded_ids)} overloaded worker(s) and {len(idle_workers)} idle worker(s) detected. Consider routing new assignments to idle workers: {', '.join(w.id for w in idle_workers[:3])}",
                    "priority": "high",
                    "worker_id": next(iter(overloaded_ids)),
                }
            )
            rid += 1

        if overview["failure_rate"] > 0.2:
            recommendations.append(
                {
                    "id": f"rec-{rid:03d}",
                    "type": "reliability",
                    "title": "High failure rate",
                    "description": f"Failure rate {overview['failure_rate']*100:.1f}% exceeds threshold. Investigate failed assignments and worker health.",
                    "priority": "high",
                    "worker_id": "",
                }
            )
            rid += 1
        elif overview["failure_rate"] > 0.05:
            recommendations.append(
                {
                    "id": f"rec-{rid:03d}",
                    "type": "reliability",
                    "title": "Elevated failure rate",
                    "description": f"Failure rate {overview['failure_rate']*100:.1f}% suggests reliability review.",
                    "priority": "medium",
                    "worker_id": "",
                }
            )
            rid += 1

        if not recommendations and total_capacity_hint(workers) == 0:
            recommendations.append(
                {
                    "id": f"rec-{rid:03d}",
                    "type": "setup",
                    "title": "No workers registered",
                    "description": "No workers found for tenant. Register workers to enable workforce operations.",
                    "priority": "high",
                    "worker_id": "",
                }
            )

        return recommendations

    def get_trends(self, tenant_id: str, days: int = 30) -> dict[str, Any]:
        series = self.get_utilization_timeseries(tenant_id, days=days)
        assignments = self._assignments_for_tenant(tenant_id)

        grouped: dict[str, list[Any]] = defaultdict(list)
        for a in assignments:
            ts = getattr(a, "assigned_at", None)
            if ts is None:
                continue
            try:
                key = ts.date().isoformat()
            except Exception:
                continue
            grouped[key].append(a)

        now_date = utc_now().date()
        throughput_series: list[int] = []
        for i in range(days - 1, -1, -1):
            d = now_date - timedelta(days=i)
            key = d.isoformat()
            day_items = grouped.get(key, [])
            completed = sum(1 for a in day_items if getattr(a, "status", None) == AssignmentStatus.COMPLETED)
            throughput_series.append(completed)

        half = days // 2 or 1
        util_values = [p["utilization"] for p in series]
        first_util = sum(util_values[:half]) / len(util_values[:half]) if util_values[:half] else 0.0
        second_util = sum(util_values[half:]) / len(util_values[half:]) if util_values[half:] else 0.0
        util_change = round(((second_util - first_util) / first_util * 100) if first_util else (100.0 if second_util else 0.0), 2)
        if abs(util_change) < 2:
            util_dir = "stable"
        elif util_change > 0:
            util_dir = "up"
        else:
            util_dir = "down"

        first_thr = sum(throughput_series[:half]) / (half or 1)
        second_thr = sum(throughput_series[half:]) / (len(throughput_series) - half or 1)
        thr_change = round(((second_thr - first_thr) / first_thr * 100) if first_thr else (100.0 if second_thr else 0.0), 2)
        if abs(thr_change) < 2:
            thr_dir = "stable"
        elif thr_change > 0:
            thr_dir = "up"
        else:
            thr_dir = "down"

        return {
            "utilization": {
                "direction": util_dir,
                "change_percent": util_change,
                "previous_avg": round(first_util, 4),
                "current_avg": round(second_util, 4),
                "series": series,
            },
            "throughput": {
                "direction": thr_dir,
                "change_percent": thr_change,
                "previous_avg": round(first_thr, 2),
                "current_avg": round(second_thr, 2),
                "series": throughput_series,
            },
            "period_days": days,
        }

    def get_worker_performance(self, worker_id: str, tenant_id: str) -> dict[str, Any]:
        try:
            worker = self._registry.get_worker(worker_id)
        except Exception:
            return {"worker_id": worker_id, "error": "worker not found", "tenant_id": tenant_id}

        assignments = [a for a in self._assignments_for_tenant(tenant_id) if getattr(a, "worker_id", None) == worker_id]
        total = len(assignments)
        completed = sum(1 for a in assignments if getattr(a, "status", None) == AssignmentStatus.COMPLETED)
        failed = sum(1 for a in assignments if getattr(a, "status", None) == AssignmentStatus.FAILED)
        pending = sum(1 for a in assignments if getattr(a, "status", None) == AssignmentStatus.PENDING)
        running = sum(1 for a in assignments if getattr(a, "status", None) == AssignmentStatus.RUNNING)
        durations: list[float] = []
        for a in assignments:
            ca = getattr(a, "completed_at", None)
            aa = getattr(a, "assigned_at", None)
            if ca is not None and aa is not None:
                try:
                    durations.append((ca - aa).total_seconds() * 1000)
                except Exception:
                    pass
        avg_duration = round(sum(durations) / len(durations), 2) if durations else 0.0
        active = self._registry.active_count(worker_id) if hasattr(self._registry, "active_count") else 0
        maxc = getattr(worker, "max_concurrent_runs", 1) or 1
        utilization_pct = round(active / maxc * 100, 2) if maxc else 0.0

        return {
            "worker_id": worker_id,
            "name": getattr(worker, "name", worker_id),
            "worker_type": getattr(worker, "worker_type", WorkerType.AGENT).value if hasattr(getattr(worker, "worker_type", ""), "value") else str(getattr(worker, "worker_type", "")),
            "tenant_id": tenant_id,
            "total_assignments": total,
            "completed_assignments": completed,
            "failed_assignments": failed,
            "pending_assignments": pending,
            "running_assignments": running,
            "completion_rate": round(completed / total, 4) if total else 0.0,
            "failure_rate": round(failed / total, 4) if total else 0.0,
            "avg_duration_ms": avg_duration,
            "active_count": active,
            "max_concurrent": maxc,
            "utilization_pct": utilization_pct,
        }


def total_capacity_hint(workers: list[Any]) -> int:
    return sum(getattr(w, "max_concurrent_runs", 0) or 0 for w in workers)


__all__ = ["WorkforceAnalyticsService"]
