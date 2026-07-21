"""Import/Export domain models — config, jobs, results, mappings, schedules, and transforms."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class ImportJobStatus(StrEnum):
    PENDING = "pending"
    VALIDATING = "validating"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ExportJobStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ExportFormat(StrEnum):
    CSV = "csv"
    JSON = "json"
    XLSX = "xlsx"
    PARQUET = "parquet"
    XML = "xml"


class ImportExportConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    max_file_size_bytes: int = 524_288_000
    allowed_formats: tuple[str, ...] = Field(default=("csv", "json", "xlsx", "parquet"))
    temp_directory: str = "/tmp/import_export"
    enable_validation: bool = True
    max_concurrent_jobs: int = 5
    retention_days: int = 90
    notify_on_completion: bool = True


class ImportJob(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    filename: str
    source: str = ""
    status: ImportJobStatus = ImportJobStatus.PENDING
    format: str = "csv"
    mapping_id: str = ""
    total_records: int = 0
    processed_records: int = 0
    failed_records: int = 0
    error: str = ""
    started_at: datetime | None = None
    completed_at: datetime | None = None
    duration_ms: int = 0
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)


class ImportResult(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    job_id: str
    success: bool = True
    total_records: int = 0
    imported_records: int = 0
    skipped_records: int = 0
    failed_records: int = 0
    errors: tuple[str, ...] = Field(default=())
    duration_ms: int = 0
    completed_at: datetime = Field(default_factory=utc_now)


class ImportRecord(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    job_id: str
    row_number: int = 0
    data: dict[str, Any] = Field(default_factory=dict)
    valid: bool = True
    errors: tuple[str, ...] = Field(default=())
    processed_at: datetime | None = None


class ExportJob(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    query_id: str = ""
    status: ExportJobStatus = ExportJobStatus.PENDING
    format: ExportFormat = ExportFormat.CSV
    filters: dict[str, Any] = Field(default_factory=dict)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    duration_ms: int = 0
    file_size_bytes: int = 0
    record_count: int = 0
    error: str = ""
    output_path: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)


class ExportResult(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    job_id: str
    success: bool = True
    format: ExportFormat = ExportFormat.CSV
    record_count: int = 0
    file_size_bytes: int = 0
    output_path: str = ""
    duration_ms: int = 0
    errors: tuple[str, ...] = Field(default=())
    completed_at: datetime = Field(default_factory=utc_now)


class FieldMapping(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    source_field: str
    target_field: str
    transform: str = ""
    default_value: str = ""
    required: bool = False


class ImportExportMapping(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    description: str = ""
    source_format: str = ""
    target_format: str = ""
    field_mappings: tuple[FieldMapping, ...] = Field(default=())
    options: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class ImportExportValidation(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    job_id: str
    valid: bool = True
    schema_errors: tuple[str, ...] = Field(default=())
    field_errors: tuple[str, ...] = Field(default=())
    warnings: tuple[str, ...] = Field(default=())
    validated_records: int = 0
    duration_ms: int = 0
    validated_at: datetime = Field(default_factory=utc_now)


class ImportExportSchedule(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    description: str = ""
    job_type: str = "import"
    cron_expression: str
    timezone: str = "UTC"
    mapping_id: str = ""
    config: dict[str, Any] = Field(default_factory=dict)
    enabled: bool = True
    last_run: datetime | None = None
    next_run: datetime | None = None
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class ImportExportMetrics(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    total_imports: int = 0
    successful_imports: int = 0
    failed_imports: int = 0
    total_exports: int = 0
    successful_exports: int = 0
    failed_exports: int = 0
    total_records_imported: int = 0
    total_records_exported: int = 0
    avg_import_duration_ms: float = 0.0
    avg_export_duration_ms: float = 0.0
    period_start: datetime | None = None
    period_end: datetime | None = None


class ImportExportReport(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    description: str = ""
    metrics: ImportExportMetrics = Field(default_factory=ImportExportMetrics)
    recent_jobs: tuple[dict[str, Any], ...] = Field(default=())
    generated_at: datetime = Field(default_factory=utc_now)


class ImportExportAuditEntry(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    action: str
    entity_type: str
    entity_id: str
    user: str = ""
    details: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=utc_now)


class DataTransform(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str
    description: str = ""
    transform_type: str = "custom"
    config: dict[str, Any] = Field(default_factory=dict)


class TransformConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    enabled: bool = True
    transforms: tuple[DataTransform, ...] = Field(default=())
    max_transform_steps: int = 10
    error_handling: str = "skip"


__all__ = [
    "DataTransform",
    "ExportFormat",
    "ExportJob",
    "ExportJobStatus",
    "ExportResult",
    "FieldMapping",
    "ImportExportAuditEntry",
    "ImportExportConfig",
    "ImportExportMapping",
    "ImportExportMetrics",
    "ImportExportReport",
    "ImportExportSchedule",
    "ImportExportValidation",
    "ImportJob",
    "ImportJobStatus",
    "ImportRecord",
    "ImportResult",
    "TransformConfig",
]
