"""Enterprise settings domain models — categories, groups, definitions, values, profiles, etc."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class SettingsCategory(StrEnum):
    """Enumeration of enterprise settings categories."""

    GENERAL = "general"
    SECURITY = "security"
    COMPLIANCE = "compliance"
    INTEGRATION = "integration"
    NOTIFICATIONS = "notifications"
    PERFORMANCE = "performance"
    AUDIT = "audit"
    ACCESSIBILITY = "accessibility"
    LOCALIZATION = "localization"
    ADVANCED = "advanced"


class SettingsScope(StrEnum):
    """Enumeration of settings scopes."""

    GLOBAL = "global"
    TENANT = "tenant"
    ORGANIZATION = "organization"
    WORKSPACE = "workspace"
    USER = "user"


class EnterpriseSettings(BaseModel):
    """A single enterprise setting key-value pair."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    key: str
    value: Any = None
    category: SettingsCategory = SettingsCategory.GENERAL
    scope: SettingsScope = SettingsScope.GLOBAL
    description: str = ""
    tags: tuple[str, ...] = Field(default=())
    version: int = 1
    is_encrypted: bool = False
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    metadata: dict[str, Any] = Field(default_factory=dict)


class SettingsGroup(BaseModel):
    """A logical group of related settings."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    category: SettingsCategory = SettingsCategory.GENERAL
    description: str = ""
    setting_keys: tuple[str, ...] = Field(default=())
    order: int = 0
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    metadata: dict[str, Any] = Field(default_factory=dict)


class SettingsDefinition(BaseModel):
    """Metadata definition for an enterprise setting."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    key: str
    label: str = ""
    description: str = ""
    category: SettingsCategory = SettingsCategory.GENERAL
    scope: SettingsScope = SettingsScope.GLOBAL
    default_value: Any = None
    value_type: str = "string"
    allowed_values: tuple[Any, ...] = Field(default=())
    validation_rules: dict[str, Any] = Field(default_factory=dict)
    is_encrypted: bool = False
    is_required: bool = False
    is_deprecated: bool = False
    tags: tuple[str, ...] = Field(default=())
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    metadata: dict[str, Any] = Field(default_factory=dict)


class SettingsValue(BaseModel):
    """A scoped value for an enterprise setting."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    setting_id: str
    value: Any = None
    scope: SettingsScope = SettingsScope.GLOBAL
    scope_id: str = ""
    version: int = 1
    created_by: str = ""
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    metadata: dict[str, Any] = Field(default_factory=dict)


class SettingsProfile(BaseModel):
    """A named profile containing setting overrides."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    description: str = ""
    is_active: bool = True
    overrides: dict[str, Any] = Field(default_factory=dict)
    tags: tuple[str, ...] = Field(default=())
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    metadata: dict[str, Any] = Field(default_factory=dict)


class SettingsAuditEntry(BaseModel):
    """An audit log entry for a settings change."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    action: str
    entity_type: str = ""
    entity_id: str = ""
    actor: str = ""
    old_value: Any = None
    new_value: Any = None
    timestamp: datetime = Field(default_factory=utc_now)
    metadata: dict[str, Any] = Field(default_factory=dict)


class SettingsValidation(BaseModel):
    """Result of validating a single enterprise setting."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    setting_id: str
    valid: bool = True
    errors: tuple[str, ...] = Field(default=())
    warnings: tuple[str, ...] = Field(default=())
    timestamp: datetime = Field(default_factory=utc_now)
    metadata: dict[str, Any] = Field(default_factory=dict)


class SettingsValidationResult(BaseModel):
    """Aggregated validation result for a setting key."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    setting_key: str
    valid: bool = True
    errors: tuple[str, ...] = Field(default=())
    warnings: tuple[str, ...] = Field(default=())
    duration_ms: float = 0.0
    timestamp: datetime = Field(default_factory=utc_now)


class SettingsExport(BaseModel):
    """Represents an export of enterprise settings."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    format: str = "json"
    categories: tuple[SettingsCategory, ...] = Field(default=())
    settings: dict[str, Any] = Field(default_factory=dict)
    exported_by: str = ""
    exported_at: datetime = Field(default_factory=utc_now)
    metadata: dict[str, Any] = Field(default_factory=dict)


class SettingsImport(BaseModel):
    """Represents an import of enterprise settings."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    format: str = "json"
    settings: dict[str, Any] = Field(default_factory=dict)
    imported_by: str = ""
    import_mode: str = "merge"
    conflicts: tuple[str, ...] = Field(default=())
    imported_at: datetime = Field(default_factory=utc_now)
    metadata: dict[str, Any] = Field(default_factory=dict)


class SettingsHistoryEntry(BaseModel):
    """A historical record of a setting change."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    setting_id: str
    setting_key: str = ""
    old_value: Any = None
    new_value: Any = None
    changed_by: str = ""
    reason: str = ""
    timestamp: datetime = Field(default_factory=utc_now)
    metadata: dict[str, Any] = Field(default_factory=dict)


class SettingsTemplate(BaseModel):
    """A reusable template of setting values."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    description: str = ""
    category: SettingsCategory = SettingsCategory.GENERAL
    settings: dict[str, Any] = Field(default_factory=dict)
    tags: tuple[str, ...] = Field(default=())
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    metadata: dict[str, Any] = Field(default_factory=dict)


class SettingsEnvironmentOverride(BaseModel):
    """An environment-specific override for a setting."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    setting_key: str
    environment: str = ""
    value: Any = None
    created_by: str = ""
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    metadata: dict[str, Any] = Field(default_factory=dict)


class SettingsPermission(BaseModel):
    """Access control permissions for a setting."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    setting_key: str
    role: str = ""
    can_read: bool = True
    can_write: bool = False
    can_delete: bool = False
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    metadata: dict[str, Any] = Field(default_factory=dict)


class SettingsNotification(BaseModel):
    """Notification configuration for a setting event."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    setting_key: str
    event: str = ""
    channel: str = ""
    recipients: tuple[str, ...] = Field(default=())
    enabled: bool = True
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    metadata: dict[str, Any] = Field(default_factory=dict)


class SettingsConfig(BaseModel):
    """Configuration for the enterprise settings module."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    enable_audit: bool = True
    enable_validation: bool = True
    enable_versioning: bool = True
    enable_encryption: bool = False
    cache_ttl_seconds: int = 300
    max_history_entries: int = 100
    auto_apply_templates: bool = False


__all__ = [
    "EnterpriseSettings",
    "SettingsAuditEntry",
    "SettingsCategory",
    "SettingsConfig",
    "SettingsDefinition",
    "SettingsEnvironmentOverride",
    "SettingsExport",
    "SettingsGroup",
    "SettingsHistoryEntry",
    "SettingsImport",
    "SettingsNotification",
    "SettingsPermission",
    "SettingsProfile",
    "SettingsScope",
    "SettingsTemplate",
    "SettingsValidation",
    "SettingsValidationResult",
    "SettingsValue",
]
