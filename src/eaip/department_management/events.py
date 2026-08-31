"""Domain events raised by the department management package."""

from __future__ import annotations

from typing import Any, ClassVar

from pydantic import Field

from eaip.events.event import DomainEvent


class DepartmentCreated(DomainEvent):
    """Published when a new department is created."""

    event_type: ClassVar[str] = "eaip.department_management.department_created"

    department_id: str
    name: str
    parent_id: str | None = None
    created_by: str = "system"


class DepartmentUpdated(DomainEvent):
    """Published when a department is updated."""

    event_type: ClassVar[str] = "eaip.department_management.department_updated"

    department_id: str
    changes: dict[str, Any] = Field(default_factory=dict)
    updated_by: str = "system"


class DepartmentDeleted(DomainEvent):
    """Published when a department is deleted."""

    event_type: ClassVar[str] = "eaip.department_management.department_deleted"

    department_id: str
    deleted_by: str = "system"


class DepartmentActivated(DomainEvent):
    """Published when a department is activated."""

    event_type: ClassVar[str] = "eaip.department_management.department_activated"

    department_id: str
    activated_by: str = "system"


class DepartmentDeactivated(DomainEvent):
    """Published when a department is deactivated."""

    event_type: ClassVar[str] = "eaip.department_management.department_deactivated"

    department_id: str
    deactivated_by: str = "system"


class DepartmentMerged(DomainEvent):
    """Published when two departments are merged."""

    event_type: ClassVar[str] = "eaip.department_management.department_merged"

    source_department_id: str
    target_department_id: str
    merged_by: str = "system"


class DepartmentSplit(DomainEvent):
    """Published when a department is split into two."""

    event_type: ClassVar[str] = "eaip.department_management.department_split"

    source_department_id: str
    new_department_id: str
    split_by: str = "system"


class DepartmentHierarchyChanged(DomainEvent):
    """Published when a department's position in the hierarchy changes."""

    event_type: ClassVar[str] = "eaip.department_management.department_hierarchy_changed"

    department_id: str
    old_parent_id: str | None = None
    new_parent_id: str | None = None
    changed_by: str = "system"


class DepartmentMemberAdded(DomainEvent):
    """Published when a member is added to a department."""

    event_type: ClassVar[str] = "eaip.department_management.department_member_added"

    department_id: str
    user_id: str
    role: str = "member"
    added_by: str = "system"


class DepartmentMemberRemoved(DomainEvent):
    """Published when a member is removed from a department."""

    event_type: ClassVar[str] = "eaip.department_management.department_member_removed"

    department_id: str
    user_id: str
    removed_by: str = "system"


class DepartmentMemberRoleChanged(DomainEvent):
    """Published when a member's role within a department changes."""

    event_type: ClassVar[str] = "eaip.department_management.department_member_role_changed"

    department_id: str
    user_id: str
    old_role: str
    new_role: str
    changed_by: str = "system"


class DepartmentBudgetUpdated(DomainEvent):
    """Published when a department's budget is updated."""

    event_type: ClassVar[str] = "eaip.department_management.department_budget_updated"

    budget_id: str
    department_id: str
    fiscal_year: str
    old_total: float = 0.0
    new_total: float = 0.0
    updated_by: str = "system"


class DepartmentResourceAllocated(DomainEvent):
    """Published when a resource is allocated to a department."""

    event_type: ClassVar[str] = "eaip.department_management.department_resource_allocated"

    resource_id: str
    department_id: str
    resource_type: str
    name: str
    allocated_by: str = "system"


class DepartmentResourceReleased(DomainEvent):
    """Published when a resource is released from a department."""

    event_type: ClassVar[str] = "eaip.department_management.department_resource_released"

    resource_id: str
    department_id: str
    released_by: str = "system"


class DepartmentReportGenerated(DomainEvent):
    """Published when a department report is generated."""

    event_type: ClassVar[str] = "eaip.department_management.department_report_generated"

    report_id: str
    department_id: str
    report_type: str
    generated_by: str = "system"


class DepartmentSettingsUpdated(DomainEvent):
    """Published when department settings are updated."""

    event_type: ClassVar[str] = "eaip.department_management.department_settings_updated"

    department_id: str
    changes: dict[str, Any] = Field(default_factory=dict)
    updated_by: str = "system"


class DepartmentAuditLogged(DomainEvent):
    """Published when an audit entry is logged for a department."""

    event_type: ClassVar[str] = "eaip.department_management.department_audit_logged"

    entry_id: str
    department_id: str
    action: str
    actor_id: str
