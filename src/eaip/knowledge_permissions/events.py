"""Knowledge permission domain events."""

from __future__ import annotations

from typing import Any, ClassVar

from pydantic import Field

from eaip.events.event import DomainEvent
from eaip.knowledge_permissions.models import (
    KnowledgeAccessAuditEntry,
    KnowledgeAccessRule,
    KnowledgePermission,
    KnowledgePermissionEvaluation,
    KnowledgePermissionPolicy,
    KnowledgePermissionReport,
    KnowledgeResourceAccess,
    KnowledgeRole,
    KnowledgeRoleAssignment,
)


class KnowledgePermissionCreated(DomainEvent):
    """Published when a new permission is created."""

    event_type: ClassVar[str] = "eaip.knowledge_permissions.permission.created"

    permission: KnowledgePermission


class KnowledgePermissionUpdated(DomainEvent):
    """Published when an existing permission is updated."""

    event_type: ClassVar[str] = "eaip.knowledge_permissions.permission.updated"

    permission_id: str
    changes: dict[str, Any] = Field(default_factory=dict)


class KnowledgePermissionDeleted(DomainEvent):
    """Published when a permission is deleted."""

    event_type: ClassVar[str] = "eaip.knowledge_permissions.permission.deleted"

    permission_id: str


class KnowledgePermissionGranted(DomainEvent):
    """Published when access is successfully granted."""

    event_type: ClassVar[str] = "eaip.knowledge_permissions.permission.granted"

    subject_id: str
    resource_id: str
    level: str
    access: KnowledgeResourceAccess


class KnowledgePermissionRevoked(DomainEvent):
    """Published when a permission is revoked."""

    event_type: ClassVar[str] = "eaip.knowledge_permissions.permission.revoked"

    subject_id: str
    resource_id: str
    permission_id: str
    reason: str = ""


class KnowledgeRoleCreated(DomainEvent):
    """Published when a new role is created."""

    event_type: ClassVar[str] = "eaip.knowledge_permissions.role.created"

    role: KnowledgeRole


class KnowledgeRoleUpdated(DomainEvent):
    """Published when an existing role is updated."""

    event_type: ClassVar[str] = "eaip.knowledge_permissions.role.updated"

    role_id: str
    changes: dict[str, Any] = Field(default_factory=dict)


class KnowledgeRoleDeleted(DomainEvent):
    """Published when a role is deleted."""

    event_type: ClassVar[str] = "eaip.knowledge_permissions.role.deleted"

    role_id: str


class KnowledgeRoleAssigned(DomainEvent):
    """Published when a role is assigned to a subject."""

    event_type: ClassVar[str] = "eaip.knowledge_permissions.role.assigned"

    assignment: KnowledgeRoleAssignment


class KnowledgeRoleUnassigned(DomainEvent):
    """Published when a role is unassigned from a subject."""

    event_type: ClassVar[str] = "eaip.knowledge_permissions.role.unassigned"

    assignment_id: str
    role_id: str
    subject_id: str


class KnowledgeAccessRuleCreated(DomainEvent):
    """Published when a new access rule is created."""

    event_type: ClassVar[str] = "eaip.knowledge_permissions.access_rule.created"

    rule: KnowledgeAccessRule


class KnowledgeAccessRuleEvaluated(DomainEvent):
    """Published when an access rule is evaluated."""

    event_type: ClassVar[str] = "eaip.knowledge_permissions.access_rule.evaluated"

    rule_id: str
    subject_id: str
    resource_id: str
    matched: bool


class KnowledgeAccessGranted(DomainEvent):
    """Published when access is granted to a knowledge resource."""

    event_type: ClassVar[str] = "eaip.knowledge_permissions.access.granted"

    subject_id: str
    resource_id: str
    level: str
    evaluation: KnowledgePermissionEvaluation


class KnowledgeAccessDenied(DomainEvent):
    """Published when access is denied to a knowledge resource."""

    event_type: ClassVar[str] = "eaip.knowledge_permissions.access.denied"

    subject_id: str
    resource_id: str
    requested_level: str
    evaluation: KnowledgePermissionEvaluation


class KnowledgePermissionAuditLogged(DomainEvent):
    """Published when an audit entry is logged."""

    event_type: ClassVar[str] = "eaip.knowledge_permissions.audit.logged"

    entry: KnowledgeAccessAuditEntry


class KnowledgePermissionPolicyUpdated(DomainEvent):
    """Published when a permission policy is updated."""

    event_type: ClassVar[str] = "eaip.knowledge_permissions.policy.updated"

    policy: KnowledgePermissionPolicy


class KnowledgePermissionReportGenerated(DomainEvent):
    """Published when a permission report is generated."""

    event_type: ClassVar[str] = "eaip.knowledge_permissions.report.generated"

    report: KnowledgePermissionReport


__all__ = [
    "KnowledgeAccessDenied",
    "KnowledgeAccessGranted",
    "KnowledgeAccessRuleCreated",
    "KnowledgeAccessRuleEvaluated",
    "KnowledgePermissionAuditLogged",
    "KnowledgePermissionCreated",
    "KnowledgePermissionDeleted",
    "KnowledgePermissionGranted",
    "KnowledgePermissionPolicyUpdated",
    "KnowledgePermissionReportGenerated",
    "KnowledgePermissionRevoked",
    "KnowledgePermissionUpdated",
    "KnowledgeRoleAssigned",
    "KnowledgeRoleCreated",
    "KnowledgeRoleDeleted",
    "KnowledgeRoleUnassigned",
    "KnowledgeRoleUpdated",
]
