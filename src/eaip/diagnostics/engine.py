"""Diagnostics engine — run diagnostic checks across subsystems."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from eaip.diagnostics.events import DiagnosticsCheckCompleted
from eaip.logging.context import get_logger
from eaip.shared.time import utc_now


class ProbeStatus(StrEnum):
    PASS = "pass"
    WARN = "warn"
    FAIL = "fail"


class ProbeResult:
    def __init__(
        self,
        probe_id: str,
        status: ProbeStatus,
        message: str = "",
        details: dict[str, Any] | None = None,
    ) -> None:
        self.probe_id = probe_id
        self.status = status
        self.message = message
        self.details = details or {}
        self.timestamp = utc_now()


class HealthProbe:
    def __init__(self, probe_id: str, name: str, check_fn: Any, interval_seconds: int = 60) -> None:
        self.probe_id = probe_id
        self.name = name
        self.check_fn = check_fn
        self.interval_seconds = interval_seconds
        self.last_run: datetime | None = None


class Incident:
    def __init__(
        self, incident_id: str, probe_id: str, message: str, severity: str = "warning"
    ) -> None:
        self.incident_id = incident_id
        self.probe_id = probe_id
        self.message = message
        self.severity = severity
        self.created_at = utc_now()
        self.resolved_at: datetime | None = None
        self.is_resolved: bool = False
        self.resolution: str = ""


class DiagnosticsEngine:
    def __init__(self, event_bus: Any = None) -> None:
        self._probes: dict[str, HealthProbe] = {}
        self._results: list[ProbeResult] = []
        self._incidents: list[Incident] = []
        self._event_bus = event_bus
        self._log = get_logger("eaip.diagnostics.engine")

    def register_probe(self, probe: HealthProbe) -> None:
        self._probes[probe.probe_id] = probe

    def unregister_probe(self, probe_id: str) -> bool:
        return self._probes.pop(probe_id, None) is not None

    def get_probe(self, probe_id: str) -> HealthProbe | None:
        return self._probes.get(probe_id)

    def list_probes(self) -> list[HealthProbe]:
        return list(self._probes.values())

    async def run_probe(self, probe_id: str) -> ProbeResult:
        probe = self._probes.get(probe_id)
        if probe is None:
            msg = f"Probe {probe_id!r} not found"
            raise ProbeExecutionError(msg)
        try:
            if asyncio.iscoroutinefunction(probe.check_fn):
                result = await probe.check_fn()
            else:
                result = probe.check_fn()
            status = ProbeStatus.PASS if result else ProbeStatus.FAIL
            message = str(result) if isinstance(result, str) else ("pass" if result else "fail")
        except Exception as exc:
            status = ProbeStatus.FAIL
            message = str(exc)

        probe_result = ProbeResult(probe_id=probe_id, status=status, message=message)
        probe.last_run = utc_now()
        self._results.append(probe_result)

        if status == ProbeStatus.FAIL:
            incident_id = f"inc-{len(self._incidents) + 1}"
            incident = Incident(incident_id=incident_id, probe_id=probe_id, message=message)
            self._incidents.append(incident)

        self._publish_event(
            DiagnosticsCheckCompleted(probe_id=probe_id, status=status.value, message=message)
        )
        return probe_result

    async def run_all_probes(self) -> list[ProbeResult]:
        results: list[ProbeResult] = []
        for probe_id in self._probes:
            result = await self.run_probe(probe_id)
            results.append(result)
        return results

    def get_results(self, limit: int = 100) -> list[ProbeResult]:
        return self._results[-limit:]

    def get_incidents(self, unresolved_only: bool = False) -> list[Incident]:
        if unresolved_only:
            return [i for i in self._incidents if not i.is_resolved]
        return list(self._incidents)

    def resolve_incident(self, incident_id: str, resolution: str = "") -> bool:
        for incident in self._incidents:
            if incident.incident_id == incident_id:
                incident.is_resolved = True
                incident.resolved_at = utc_now()
                incident.resolution = resolution
                return True
        return False

    def _publish_event(self, event: Any) -> None:
        if self._event_bus is not None:
            import asyncio

            try:
                asyncio.ensure_future(self._event_bus.publish(event))
            except Exception:
                pass


import asyncio

from eaip.diagnostics.exceptions import ProbeExecutionError

__all__ = [
    "DiagnosticsEngine",
    "HealthProbe",
    "Incident",
    "ProbeResult",
    "ProbeStatus",
]
