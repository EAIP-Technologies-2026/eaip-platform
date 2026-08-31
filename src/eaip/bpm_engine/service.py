"""BpmService — deploy definitions, manage instance lifecycle, signals, messages, timers."""

from __future__ import annotations

from typing import Any

from eaip.bpm_engine.events import (
    ActivityCompleted,
    ActivityFailed,
    ErrorEventTriggered,
    GatewayEvaluated,
    MessageReceived,
    ProcessCompleted,
    ProcessDeployed,
    ProcessFailed,
    ProcessStarted,
    SignalReceived,
    TimerFired,
)
from eaip.bpm_engine.exceptions import (
    ProcessDefinitionError,
    ProcessInstanceNotFoundError,
    SignalDeliveryError,
)
from eaip.bpm_engine.models import (
    ActivityStatus,
    BpmnProcessDefinition,
    ProcessInstance,
    ProcessStatus,
    ProcessVariable,
)
from eaip.events.bus import EventBus
from eaip.logging.context import get_logger
from eaip.shared.time import utc_now


class BpmService:
    """Central service for deploying and executing BPMN process definitions."""

    def __init__(self, event_bus: EventBus | None = None) -> None:
        self._definitions: dict[str, BpmnProcessDefinition] = {}
        self._instances: dict[str, ProcessInstance] = {}
        self._event_bus = event_bus
        self._log = get_logger("eaip.bpm_engine.service")

    @property
    def definitions(self) -> dict[str, BpmnProcessDefinition]:
        return dict(self._definitions)

    @property
    def instances(self) -> dict[str, ProcessInstance]:
        return dict(self._instances)

    async def deploy(self, definition: BpmnProcessDefinition) -> BpmnProcessDefinition:
        """Deploy a BPMN process definition."""
        if definition.id in self._definitions:
            raise ProcessDefinitionError(
                f"process definition already deployed: {definition.id!r}",
                process_key=definition.key,
            )
        self._definitions[definition.id] = definition
        event = ProcessDeployed(
            process_definition_id=definition.id,
            process_name=definition.name,
            version=definition.version,
            key=definition.key,
        )
        await self._emit(event)
        self._log.info(
            "bpm_engine.process.deployed",
            definition_id=definition.id,
            key=definition.key,
            version=definition.version,
        )
        return definition

    async def start(
        self,
        definition_id: str,
        variables: tuple[ProcessVariable, ...] = (),
        correlation_id: str = "",
    ) -> ProcessInstance:
        """Start a new process instance from a deployed definition."""
        definition = self._definitions.get(definition_id)
        if definition is None:
            raise ProcessDefinitionError(
                f"process definition not found: {definition_id!r}",
                process_key=definition_id,
            )

        instance = ProcessInstance(
            id=f"inst_{definition_id}_{utc_now().timestamp():.0f}",
            process_definition_id=definition_id,
            process_name=definition.name,
            status=ProcessStatus.RUNNING,
            variables=variables,
            active_activity_ids=tuple(
                a.id for a in definition.activities if a.status == ActivityStatus.PENDING
            ),
        )
        self._instances[instance.id] = instance

        event = ProcessStarted(
            process_instance_id=instance.id,
            process_definition_id=definition_id,
            process_name=definition.name,
        )
        await self._emit(event)
        self._log.info(
            "bpm_engine.process.started",
            instance_id=instance.id,
            definition_id=definition_id,
        )
        return instance

    async def signal(
        self,
        process_instance_id: str,
        signal_name: str,
        payload: dict[str, Any] | None = None,
    ) -> ProcessInstance:
        """Deliver a signal to a running process instance."""
        instance = self._get_instance(process_instance_id)
        if instance.status != ProcessStatus.RUNNING:
            raise SignalDeliveryError(
                signal_name,
                f"instance {process_instance_id!r} is not running (status={instance.status})",
            )

        event = SignalReceived(
            process_instance_id=process_instance_id,
            signal_name=signal_name,
            signal_payload=payload or {},
        )
        await self._emit(event)
        return instance

    async def send_message(
        self,
        process_instance_id: str,
        message_name: str,
        payload: dict[str, Any] | None = None,
        correlation_key: str = "",
    ) -> ProcessInstance:
        """Send a message to a running process instance."""
        instance = self._get_instance(process_instance_id)
        event = MessageReceived(
            process_instance_id=process_instance_id,
            message_name=message_name,
            correlation_key=correlation_key,
            message_payload=payload or {},
        )
        await self._emit(event)
        return instance

    async def complete_activity(
        self,
        process_instance_id: str,
        activity_id: str,
        duration_ms: float = 0.0,
    ) -> ProcessInstance:
        """Mark an activity as completed within a process instance."""
        instance = self._get_instance(process_instance_id)
        updated = ProcessInstance(
            id=instance.id,
            process_definition_id=instance.process_definition_id,
            process_name=instance.process_name,
            status=instance.status,
            variables=instance.variables,
            active_activity_ids=tuple(
                aid for aid in instance.active_activity_ids if aid != activity_id
            ),
            completed_activity_ids=(*instance.completed_activity_ids, activity_id),
            started_at=instance.started_at,
            completed_at=instance.completed_at,
            duration_ms=instance.duration_ms if instance.duration_ms else 0.0,
            error_message=instance.error_message,
            correlation_id=instance.correlation_id,
            parent_instance_id=instance.parent_instance_id,
            tags=instance.tags,
            metadata=instance.metadata,
        )
        self._instances[instance.id] = updated

        event = ActivityCompleted(
            process_instance_id=process_instance_id,
            activity_id=activity_id,
            activity_name=activity_id,
            duration_ms=duration_ms,
        )
        await self._emit(event)

        definition = self._definitions.get(instance.process_definition_id)
        total = len(definition.activities) if definition else 0
        if len(updated.completed_activity_ids) >= total > 0:
            await self._complete_process(updated.id)
        return updated

    async def fail_activity(
        self,
        process_instance_id: str,
        activity_id: str,
        error: str,
        attempt: int = 1,
        will_retry: bool = False,
    ) -> ProcessInstance:
        """Mark an activity as failed."""
        instance = self._get_instance(process_instance_id)
        definition = self._definitions.get(instance.process_definition_id)
        activity_name = activity_id
        activity_type = "task"
        if definition:
            for act in definition.activities:
                if act.id == activity_id:
                    activity_name = act.name
                    activity_type = act.type
                    break

        event = ActivityFailed(
            process_instance_id=process_instance_id,
            activity_id=activity_id,
            activity_name=activity_name,
            activity_type=activity_type,
            error=error,
            attempt=attempt,
            will_retry=will_retry,
        )
        await self._emit(event)

        if not will_retry:
            updated = ProcessInstance(
                id=instance.id,
                process_definition_id=instance.process_definition_id,
                process_name=instance.process_name,
                status=ProcessStatus.FAILED,
                variables=instance.variables,
                active_activity_ids=instance.active_activity_ids,
                completed_activity_ids=instance.completed_activity_ids,
                started_at=instance.started_at,
                completed_at=utc_now(),
                duration_ms=(utc_now() - instance.started_at).total_seconds() * 1000.0,
                error_message=error,
                correlation_id=instance.correlation_id,
                parent_instance_id=instance.parent_instance_id,
                tags=instance.tags,
                metadata=instance.metadata,
            )
            self._instances[instance.id] = updated
            await self._emit(
                ProcessFailed(
                    process_instance_id=instance.id,
                    process_definition_id=instance.process_definition_id,
                    process_name=instance.process_name,
                    error=error,
                    failed_activity_id=activity_id,
                )
            )
        return self._instances[instance.id]

    async def evaluate_gateway(
        self,
        process_instance_id: str,
        gateway_id: str,
        selected_flow_id: str,
        condition_result: bool = False,
    ) -> ProcessInstance:
        """Record a gateway evaluation."""
        instance = self._get_instance(process_instance_id)
        definition = self._definitions.get(instance.process_definition_id)
        gateway_name = gateway_id
        gateway_type = "exclusive"
        if definition:
            for gw in definition.gateways:
                if gw.id == gateway_id:
                    gateway_name = gw.name
                    gateway_type = gw.type
                    break

        event = GatewayEvaluated(
            process_instance_id=process_instance_id,
            gateway_id=gateway_id,
            gateway_name=gateway_name,
            gateway_type=gateway_type,
            selected_flow_id=selected_flow_id,
            condition_result=condition_result,
        )
        await self._emit(event)
        return instance

    async def fire_timer(
        self,
        process_instance_id: str,
        activity_id: str,
        timer_name: str,
        duration_seconds: float = 0.0,
    ) -> ProcessInstance:
        """Fire a timer event for a process instance."""
        instance = self._get_instance(process_instance_id)
        event = TimerFired(
            process_instance_id=process_instance_id,
            activity_id=activity_id,
            timer_name=timer_name,
            timer_duration_seconds=duration_seconds,
        )
        await self._emit(event)
        return instance

    async def trigger_error_event(
        self,
        process_instance_id: str,
        error_code: str,
        error_message: str,
        failed_activity_id: str = "",
    ) -> ProcessInstance:
        """Trigger an error boundary event for a process instance."""
        instance = self._get_instance(process_instance_id)
        event = ErrorEventTriggered(
            process_instance_id=process_instance_id,
            error_code=error_code,
            error_message=error_message,
            failed_activity_id=failed_activity_id,
        )
        await self._emit(event)
        return instance

    async def get_instance(self, instance_id: str) -> ProcessInstance:
        """Retrieve a process instance by ID."""
        return self._get_instance(instance_id)

    async def list_instances(self, status: ProcessStatus | None = None) -> list[ProcessInstance]:
        """List all process instances, optionally filtered by status."""
        if status is None:
            return list(self._instances.values())
        return [i for i in self._instances.values() if i.status == status]

    async def list_definitions(self) -> list[BpmnProcessDefinition]:
        """List all deployed process definitions."""
        return list(self._definitions.values())

    async def get_definition(self, definition_id: str) -> BpmnProcessDefinition:
        """Retrieve a process definition by ID."""
        definition = self._definitions.get(definition_id)
        if definition is None:
            raise ProcessDefinitionError(
                f"process definition not found: {definition_id!r}",
                process_key=definition_id,
            )
        return definition

    async def _complete_process(self, instance_id: str) -> None:
        """Mark a process instance as completed."""
        instance = self._instances.get(instance_id)
        if instance is None:
            return
        duration = (utc_now() - instance.started_at).total_seconds() * 1000.0
        updated = ProcessInstance(
            id=instance.id,
            process_definition_id=instance.process_definition_id,
            process_name=instance.process_name,
            status=ProcessStatus.COMPLETED,
            variables=instance.variables,
            active_activity_ids=(),
            completed_activity_ids=instance.completed_activity_ids,
            started_at=instance.started_at,
            completed_at=utc_now(),
            duration_ms=duration,
            error_message=instance.error_message,
            correlation_id=instance.correlation_id,
            parent_instance_id=instance.parent_instance_id,
            tags=instance.tags,
            metadata=instance.metadata,
        )
        self._instances[instance.id] = updated
        event = ProcessCompleted(
            process_instance_id=instance.id,
            process_definition_id=instance.process_definition_id,
            process_name=instance.process_name,
            duration_ms=duration,
            completed_activities=len(updated.completed_activity_ids),
        )
        await self._emit(event)

    def _get_instance(self, instance_id: str) -> ProcessInstance:
        instance = self._instances.get(instance_id)
        if instance is None:
            raise ProcessInstanceNotFoundError(instance_id)
        return instance

    async def _emit(self, event: Any) -> None:
        if self._event_bus is not None:
            await self._event_bus.publish(event)


__all__ = ["BpmService"]
