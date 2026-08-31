"""BPMN domain models - process definitions, instances, activities, gateways, flows."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class ProcessStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMED_OUT = "timed_out"


class ActivityType(StrEnum):
    TASK = "task"
    SERVICE_TASK = "service_task"
    USER_TASK = "user_task"
    SUB_PROCESS = "sub_process"
    CALL_ACTIVITY = "call_activity"
    SCRIPT_TASK = "script_task"
    BUSINESS_RULE_TASK = "business_rule_task"
    MANUAL_TASK = "manual_task"
    RECEIVE_TASK = "receive_task"
    SEND_TASK = "send_task"


class ActivityStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    TIMED_OUT = "timed_out"


class GatewayType(StrEnum):
    EXCLUSIVE = "exclusive"
    PARALLEL = "parallel"
    INCLUSIVE = "inclusive"


class SequenceFlowCondition(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    expression: str
    label: str = ""


class SequenceFlow(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    source_id: str
    target_id: str
    condition: SequenceFlowCondition | None = None
    label: str = ""


class ProcessVariable(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str
    value: Any = None
    type: str = "string"


class Activity(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    type: ActivityType = ActivityType.TASK
    status: ActivityStatus = ActivityStatus.PENDING
    documentations: str = ""
    implementation: str = ""
    loop_characteristic: str = ""
    default_sequence_flow_id: str = ""
    input_params: dict[str, Any] = Field(default_factory=dict)
    output_params: dict[str, Any] = Field(default_factory=dict)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    duration_ms: float = 0.0
    retry_count: int = 0
    error_message: str = ""


class Gateway(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    type: GatewayType
    default_flow_id: str = ""


class ExclusiveGateway(Gateway):
    model_config = ConfigDict(frozen=True, extra="forbid")

    type: GatewayType = GatewayType.EXCLUSIVE


class ParallelGateway(Gateway):
    model_config = ConfigDict(frozen=True, extra="forbid")

    type: GatewayType = GatewayType.PARALLEL


class InclusiveGateway(Gateway):
    model_config = ConfigDict(frozen=True, extra="forbid")

    type: GatewayType = GatewayType.INCLUSIVE


class BpmnProcessDefinition(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    key: str
    version: int = 1
    description: str = ""
    activities: tuple[Activity, ...] = Field(default_factory=tuple)
    gateways: tuple[Gateway, ...] = Field(default_factory=tuple)
    sequence_flows: tuple[SequenceFlow, ...] = Field(default_factory=tuple)
    variables: tuple[ProcessVariable, ...] = Field(default_factory=tuple)
    is_executable: bool = True
    target_namespace: str = ""
    documentation: str = ""
    tags: tuple[str, ...] = Field(default_factory=tuple)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ProcessInstance(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    process_definition_id: str
    process_name: str = ""
    status: ProcessStatus = ProcessStatus.PENDING
    variables: tuple[ProcessVariable, ...] = Field(default_factory=tuple)
    active_activity_ids: tuple[str, ...] = Field(default_factory=tuple)
    completed_activity_ids: tuple[str, ...] = Field(default_factory=tuple)
    started_at: datetime = Field(default_factory=utc_now)
    completed_at: datetime | None = None
    duration_ms: float = 0.0
    error_message: str = ""
    correlation_id: str = ""
    parent_instance_id: str = ""
    tags: tuple[str, ...] = Field(default_factory=tuple)
    metadata: dict[str, Any] = Field(default_factory=dict)


__all__ = [
    "Activity",
    "ActivityStatus",
    "ActivityType",
    "BpmnProcessDefinition",
    "ExclusiveGateway",
    "Gateway",
    "GatewayType",
    "InclusiveGateway",
    "ParallelGateway",
    "ProcessInstance",
    "ProcessStatus",
    "ProcessVariable",
    "SequenceFlow",
    "SequenceFlowCondition",
]
