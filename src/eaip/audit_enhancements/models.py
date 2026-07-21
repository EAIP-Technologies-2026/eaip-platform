"""Domain models for audit enhancements — correlation, enrichment, aggregation, alerts, and streaming."""  # noqa: E501

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class EnhancementType(StrEnum):
    CORRELATION = "correlation"
    ENRICHMENT = "enrichment"
    AGGREGATION = "aggregation"
    ALERT = "alert"
    STREAM = "stream"


class AuditAlertSeverity(StrEnum):
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AuditCorrelationRule(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    source_event_types: tuple[str, ...] = Field(default=())
    target_event_types: tuple[str, ...] = Field(default=())
    correlation_field: str = ""
    window_seconds: int = 300
    enabled: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)


class AuditAggregationRule(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    event_type: str = ""
    group_by_fields: tuple[str, ...] = Field(default=())
    window_seconds: int = 60
    threshold: int = 1
    enabled: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)


class AuditEnrichmentRule(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    event_types: tuple[str, ...] = Field(default=())
    enrichment_providers: tuple[str, ...] = Field(default=())
    field_mappings: dict[str, str] = Field(default_factory=dict)
    enabled: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)


class AuditAlertRule(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    event_type: str = ""
    condition_expression: str = ""
    severity: AuditAlertSeverity = AuditAlertSeverity.INFO
    notification_targets: tuple[str, ...] = Field(default=())
    throttle_seconds: int = 0
    enabled: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)


class AuditNotificationTarget(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    target_type: str = ""
    address: str = ""
    enabled: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)


class AuditStreamConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    event_types: tuple[str, ...] = Field(default=())
    batch_size: int = 100
    flush_interval_seconds: int = 10
    destination: str = ""
    enabled: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)


class AuditRetentionRule(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    event_types: tuple[str, ...] = Field(default=())
    retention_days: int = 90
    max_records: int = 0
    enabled: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)


class AuditCorrelationResult(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    rule_id: str
    source_event_ids: tuple[str, ...] = Field(default=())
    target_event_ids: tuple[str, ...] = Field(default=())
    correlation_id: str = ""
    matched_at: datetime = Field(default_factory=utc_now)


class AuditEnrichmentResult(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    rule_id: str
    event_id: str
    provider: str = ""
    enrichment_data: dict[str, Any] = Field(default_factory=dict)
    enriched_at: datetime = Field(default_factory=utc_now)


class AuditAggregationResult(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    rule_id: str
    group_key: str = ""
    count: int = 0
    window_start: datetime = Field(default_factory=utc_now)
    window_end: datetime = Field(default_factory=utc_now)


class AuditEnhancementConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    enabled: bool = True
    correlation_enabled: bool = True
    enrichment_enabled: bool = True
    aggregation_enabled: bool = True
    alerts_enabled: bool = True
    streaming_enabled: bool = True
    max_correlation_window_seconds: int = 600
    default_batch_size: int = 100
    metadata: dict[str, Any] = Field(default_factory=dict)


class AuditEnhancementReport(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    type: EnhancementType
    rules_evaluated: int = 0
    rules_matched: int = 0
    generated_at: datetime = Field(default_factory=utc_now)
    details: dict[str, Any] = Field(default_factory=dict)


__all__ = [
    "AuditAggregationResult",
    "AuditAggregationRule",
    "AuditAlertRule",
    "AuditAlertSeverity",
    "AuditCorrelationResult",
    "AuditCorrelationRule",
    "AuditEnhancementConfig",
    "AuditEnhancementReport",
    "AuditEnrichmentResult",
    "AuditEnrichmentRule",
    "AuditNotificationTarget",
    "AuditRetentionRule",
    "AuditStreamConfig",
    "EnhancementType",
]
