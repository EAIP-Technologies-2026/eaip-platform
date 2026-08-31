"""Export & reporting domain models — report definitions, jobs, format config, schedule, delivery, and global config."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class ReportDefinition(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    description: str = ""
    source_type: str = "custom"  # analytics / cost / quality / audit / custom
    query_config: dict[str, Any] = Field(default_factory=dict)
    format: str = "csv"  # csv / json / pdf / xlsx
    schedule_cron: str = ""
    recipients: tuple[str, ...] = Field(default=())
    enabled: bool = True
    tags: tuple[str, ...] = Field(default=())
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class ExportJob(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    report_id: str
    status: str = "pending"  # pending / running / completed / failed
    format: str = "csv"
    filters: dict[str, Any] = Field(default_factory=dict)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    duration_ms: int = 0
    file_size_bytes: int = 0
    record_count: int = 0
    error: str = ""
    output_path: str = ""
    delivery_status: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


class FormatConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    csv: dict[str, Any] = Field(
        default_factory=lambda: {"delimiter": ",", "include_headers": True, "encoding": "utf-8"}
    )
    json_format: dict[str, Any] = Field(
        default_factory=lambda: {"indent": 2, "include_schema": False}
    )
    xlsx: dict[str, Any] = Field(
        default_factory=lambda: {"sheet_name": "Export", "freeze_panes": True}
    )
    pdf: dict[str, Any] = Field(
        default_factory=lambda: {"orientation": "landscape", "page_size": "A4"}
    )


class ScheduleConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    cron_expression: str
    timezone: str = "UTC"
    start_date: datetime | None = None
    end_date: datetime | None = None
    max_runs: int = 0


class DeliveryConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    channels: tuple[str, ...] = Field(default=("storage",))
    email_recipients: tuple[str, ...] = Field(default=())
    webhook_url: str = ""
    storage_path: str = ""
    retention_days: int = 30
    compress: bool = False


class ExportConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    max_file_size_bytes: int = 104_857_600  # 100 MB
    default_format: str = "csv"
    temp_directory: str = "/tmp/exports"
    enable_compression: bool = True
    max_concurrent_exports: int = 5
    retention_days: int = 90


__all__ = [
    "DeliveryConfig",
    "ExportConfig",
    "ExportJob",
    "FormatConfig",
    "ReportDefinition",
    "ScheduleConfig",
]
