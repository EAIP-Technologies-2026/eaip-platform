"""Knowledge permission models — permissions, roles, ACLs, access rules, and audit."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class PermissionLevel(StrEnum):
    """Granular permission levels for knowledge resources."""

    NONE = "none"
    READ = "read"
    WRITE = "write"
    ADMIN = "admin"
    OWNER = "owner"


class KnowledgeAccessScope(StrEnum):
    """Scope of a knowledge access rule."""

    COLLECTION = "collection"
    DOCUMENT = "document"
    CATEGORY = "category"
    GLOBAL = "global"


class KnowledgePermissionConditionOperator(StrEnum):
    """Operators for permission conditions."""

    EQ = "eq"
    NEQ = "neq"
    IN = "in"
    NOT_IN = "not_in"
    GT = "gt"
    GTE = "gte"
    LT = "lt"
    LTE = "lte"
    EXISTS = "exists"
    MATCHES = "matches"


class KnowledgePermission(BaseModel):
    """A permission grant for a specific subject on a specific resource."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    subject_id: str
    resource_id: str
    level: PermissionLevel
    scope: KnowledgeAccessScope = KnowledgeAccessScope.COLLECTION
    conditions: tuple[KnowledgePermissionCondition, ...] = ()
    granted_by: str = ""
    granted_at: datetime = Field(default_factory=utc_now)
    expires_at: datetime | None = None
    metadata: dict[str, str] = {}


class KnowledgeAccessRule(BaseModel):
    """A rule that defines access conditions for knowledge resources."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    scope: KnowledgeAccessScope
    resource_pattern: str = "*"
    allowed_levels: tuple[PermissionLevel, ...] = ()
    conditions: tuple[KnowledgePermissionCondition, ...] = ()
    priority: int = 0
    enabled: bool = True
    description: str = ""


class KnowledgeRole(BaseModel):
    """A named role that aggregates multiple permission levels."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    description: str = ""
    permissions: tuple[KnowledgeResourcePermission, ...] = ()
    metadata: dict[str, str] = {}


class KnowledgeRoleAssignment(BaseModel):
    """Assignment of a role to a subject within a scope."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    role_id: str
    subject_id: str
    scope: KnowledgeAccessScope
    scope_id: str = ""
    assigned_by: str = ""
    assigned_at: datetime = Field(default_factory=utc_now)
    expires_at: datetime | None = None


class KnowledgeResourcePermission(BaseModel):
    """Permission descriptor for a specific resource pattern."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    resource_pattern: str
    level: PermissionLevel
    scope: KnowledgeAccessScope = KnowledgeAccessScope.COLLECTION


class KnowledgePermissionPolicy(BaseModel):
    """A policy document binding rules, roles, and conditions."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    description: str = ""
    rules: tuple[KnowledgeAccessRule, ...] = ()
    roles: tuple[KnowledgeRole, ...] = ()
    default_level: PermissionLevel = PermissionLevel.NONE
    enabled: bool = True
    metadata: dict[str, str] = {}


class KnowledgeAccessAuditEntry(BaseModel):
    """An audit log entry for a permission check or change."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    subject_id: str
    action: str
    resource_id: str
    granted: bool
    level: PermissionLevel
    reason: str = ""
    timestamp: datetime = Field(default_factory=utc_now)
    context: dict[str, Any] = {}


class KnowledgePermissionConfig(BaseModel):
    """Configuration for the knowledge permission subsystem."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    enabled: bool = True
    default_level: PermissionLevel = PermissionLevel.NONE
    audit_enabled: bool = True
    role_based_enabled: bool = True
    acl_enabled: bool = True
    max_cache_seconds: int = 300
    max_rules_per_policy: int = 100


class KnowledgePermissionEvaluation(BaseModel):
    """Result of evaluating a permission request."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    subject_id: str
    resource_id: str
    requested_level: PermissionLevel
    effective_level: PermissionLevel
    granted: bool
    matched_rules: tuple[str, ...] = ()
    matched_roles: tuple[str, ...] = ()
    explanation: str = ""
    evaluated_at: datetime = Field(default_factory=utc_now)


class KnowledgePermissionReport(BaseModel):
    """A report summarising the permission state of the system."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    generated_at: datetime = Field(default_factory=utc_now)
    total_permissions: int = 0
    total_rules: int = 0
    total_roles: int = 0
    total_assignments: int = 0
    summary: dict[str, int] = {}


class KnowledgeResourceAccess(BaseModel):
    """Describes how a subject can access a specific resource."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    subject_id: str
    resource_id: str
    effective_level: PermissionLevel
    source_rules: tuple[str, ...] = ()
    source_roles: tuple[str, ...] = ()
    expires_at: datetime | None = None


class AccessControlList(BaseModel):
    """An access control list for a knowledge resource."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    resource_id: str
    entries: tuple[KnowledgePermission, ...] = ()
    version: int = 1
    updated_at: datetime = Field(default_factory=utc_now)


class KnowledgePermissionCondition(BaseModel):
    """A condition that must be satisfied for a permission to apply."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    attribute: str
    operator: KnowledgePermissionConditionOperator
    value: Any = None


__all__ = [
    "AccessControlList",
    "KnowledgeAccessAuditEntry",
    "KnowledgeAccessRule",
    "KnowledgeAccessScope",
    "KnowledgePermission",
    "KnowledgePermissionCondition",
    "KnowledgePermissionConditionOperator",
    "KnowledgePermissionConfig",
    "KnowledgePermissionEvaluation",
    "KnowledgePermissionPolicy",
    "KnowledgePermissionReport",
    "KnowledgeResourceAccess",
    "KnowledgeResourcePermission",
    "KnowledgeRole",
    "KnowledgeRoleAssignment",
    "PermissionLevel",
]
