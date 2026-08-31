"""SlaService — CRUD for definitions, monitor lifecycle, and SLA evaluation."""

from __future__ import annotations

from eaip.logging.context import get_logger
from eaip.shared.time import utc_now
from eaip.sla_engine.events import (
    SlaPolicyEvaluated,
)
from eaip.sla_engine.exceptions import (
    SlaDefinitionNotFoundError,
    SlaMonitorNotFoundError,
)
from eaip.sla_engine.models import SlaDefinition, SlaMonitor, SlaStatus, SlaViolation


class SlaService:
    """Central service for managing SLA definitions, monitors, and evaluations."""

    def __init__(self) -> None:
        self._definitions: dict[str, SlaDefinition] = {}
        self._monitors: dict[str, SlaMonitor] = {}
        self._violations: dict[str, SlaViolation] = {}
        self._log = get_logger("eaip.sla_engine.service")

    # -- definitions -----------------------------------------------------------

    async def create_definition(self, definition: SlaDefinition) -> SlaDefinition:
        self._definitions[definition.id] = definition
        self._log.info("sla.definition.created", definition_id=definition.id, name=definition.name)
        return definition

    async def get_definition(self, definition_id: str) -> SlaDefinition:
        definition = self._definitions.get(definition_id)
        if definition is None:
            raise SlaDefinitionNotFoundError(definition_id)
        return definition

    async def update_definition(self, definition_id: str, **updates: object) -> SlaDefinition:
        current = await self.get_definition(definition_id)
        updated = current.model_copy(update=updates)
        self._definitions[definition_id] = updated
        self._log.info("sla.definition.updated", definition_id=definition_id)
        return updated

    async def delete_definition(self, definition_id: str) -> None:
        if definition_id not in self._definitions:
            raise SlaDefinitionNotFoundError(definition_id)
        del self._definitions[definition_id]
        self._log.info("sla.definition.deleted", definition_id=definition_id)

    async def list_definitions(self) -> list[SlaDefinition]:
        return list(self._definitions.values())

    # -- monitors --------------------------------------------------------------

    async def start_monitor(self, definition_id: str) -> SlaMonitor:
        await self.get_definition(definition_id)
        monitor = SlaMonitor(
            id=f"mon_{definition_id}_{int(utc_now().timestamp())}",
            definition_id=definition_id,
            status=SlaStatus.ACTIVE,
            started_at=utc_now(),
        )
        self._monitors[monitor.id] = monitor
        self._log.info("sla.monitor.started", monitor_id=monitor.id, definition_id=definition_id)
        return monitor

    async def stop_monitor(self, monitor_id: str) -> SlaMonitor:
        monitor = self._monitors.get(monitor_id)
        if monitor is None:
            raise SlaMonitorNotFoundError(monitor_id)
        updated = monitor.model_copy(
            update={"status": SlaStatus.COMPLETED, "completed_at": utc_now()}
        )
        self._monitors[monitor_id] = updated
        self._log.info("sla.monitor.completed", monitor_id=monitor_id)
        return updated

    async def get_monitor(self, monitor_id: str) -> SlaMonitor:
        monitor = self._monitors.get(monitor_id)
        if monitor is None:
            raise SlaMonitorNotFoundError(monitor_id)
        return monitor

    async def list_monitors(self, definition_id: str | None = None) -> list[SlaMonitor]:
        if definition_id is not None:
            return [m for m in self._monitors.values() if m.definition_id == definition_id]
        return list(self._monitors.values())

    # -- evaluation ------------------------------------------------------------

    async def evaluate_sla(self, definition_id: str, current_value: float) -> SlaPolicyEvaluated:
        definition = await self.get_definition(definition_id)
        policy = definition.policy
        monitors = [
            m
            for m in self._monitors.values()
            if m.definition_id == definition_id
            and m.status in (SlaStatus.ACTIVE, SlaStatus.WARNING)
        ]
        if not monitors:
            raise SlaMonitorNotFoundError(f"no active monitor for definition {definition_id!r}")

        monitor = monitors[0]
        breach = policy.breach_threshold > 0 and current_value > policy.breach_threshold
        warning = policy.warning_threshold > 0 and current_value > policy.warning_threshold

        violation_ids: list[str] = []
        if breach:
            violation = await self._log_violation(
                definition_id,
                definition.name,
                definition.target_metric,
                current_value,
                definition.target_value,
                severity="breach",
            )
            violation_ids.append(violation.id)
            updated = monitor.model_copy(
                update={
                    "status": SlaStatus.BREACHED,
                    "current_value": current_value,
                    "last_evaluated": utc_now(),
                }
            )
            self._monitors[monitor.id] = updated
        elif warning:
            violation = await self._log_violation(
                definition_id,
                definition.name,
                definition.target_metric,
                current_value,
                policy.warning_threshold,
                severity="warning",
            )
            violation_ids.append(violation.id)
            updated = monitor.model_copy(
                update={
                    "status": SlaStatus.WARNING,
                    "current_value": current_value,
                    "last_evaluated": utc_now(),
                }
            )
            self._monitors[monitor.id] = updated
        else:
            updated = monitor.model_copy(
                update={"current_value": current_value, "last_evaluated": utc_now()}
            )
            self._monitors[monitor.id] = updated

        return SlaPolicyEvaluated(
            definition_id=definition_id,
            definition_name=definition.name,
            monitor_id=monitor.id,
            current_value=current_value,
            breach_detected=breach,
            warning_detected=warning,
            violation_ids=tuple(violation_ids),
        )

    # -- violations ------------------------------------------------------------

    async def _log_violation(
        self,
        definition_id: str,
        definition_name: str,
        metric: str,
        actual_value: float,
        threshold: float,
        severity: str = "warning",
    ) -> SlaViolation:
        violation = SlaViolation(
            id=f"viol_{definition_id}_{int(utc_now().timestamp())}",
            definition_id=definition_id,
            definition_name=definition_name,
            metric=metric,
            actual_value=actual_value,
            threshold=threshold,
            severity=severity,
            message=f"{severity}: {metric} = {actual_value} (threshold {threshold})",
        )
        self._violations[violation.id] = violation
        self._log.info(
            "sla.violation.logged", violation_id=violation.id, definition_id=definition_id
        )
        return violation

    async def get_violations(self, definition_id: str | None = None) -> list[SlaViolation]:
        if definition_id is not None:
            return [v for v in self._violations.values() if v.definition_id == definition_id]
        return list(self._violations.values())


__all__ = ["SlaService"]
