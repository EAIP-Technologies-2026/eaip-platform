"""Domain events raised by the organization package."""

from __future__ import annotations

from datetime import datetime
from typing import Any, ClassVar

from pydantic import Field

from eaip.events.event import DomainEvent


class OrganizationCreated(DomainEvent):
    event_type: ClassVar[str] = "eaip.organization.created"

    org_id: str
    name: str
    slug: str
    org_type: str = "other"


class OrganizationUpdated(DomainEvent):
    event_type: ClassVar[str] = "eaip.organization.updated"

    org_id: str
    changes: dict[str, Any] = Field(default_factory=dict)


class OrganizationDeleted(DomainEvent):
    event_type: ClassVar[str] = "eaip.organization.deleted"

    org_id: str
    reason: str = ""


class OrganizationActivated(DomainEvent):
    event_type: ClassVar[str] = "eaip.organization.activated"

    org_id: str


class OrganizationDeactivated(DomainEvent):
    event_type: ClassVar[str] = "eaip.organization.deactivated"

    org_id: str
    reason: str = ""


class OrganizationArchived(DomainEvent):
    event_type: ClassVar[str] = "eaip.organization.archived"

    org_id: str
    reason: str = ""


class OrganizationUnitAdded(DomainEvent):
    event_type: ClassVar[str] = "eaip.organization.unit_added"

    org_id: str
    unit_id: str
    name: str
    parent_unit_id: str | None = None


class OrganizationUnitMoved(DomainEvent):
    event_type: ClassVar[str] = "eaip.organization.unit_moved"

    org_id: str
    unit_id: str
    previous_parent_id: str | None = None
    new_parent_id: str | None = None


class OrganizationUnitRemoved(DomainEvent):
    event_type: ClassVar[str] = "eaip.organization.unit_removed"

    org_id: str
    unit_id: str


class OrganizationMemberAdded(DomainEvent):
    event_type: ClassVar[str] = "eaip.organization.member_added"

    org_id: str
    member_id: str
    user_id: str
    email: str
    role: str = "member"


class OrganizationMemberRemoved(DomainEvent):
    event_type: ClassVar[str] = "eaip.organization.member_removed"

    org_id: str
    member_id: str
    user_id: str


class OrganizationMemberRoleChanged(DomainEvent):
    event_type: ClassVar[str] = "eaip.organization.member_role_changed"

    org_id: str
    member_id: str
    user_id: str
    previous_role: str
    new_role: str


class OrganizationSettingsUpdated(DomainEvent):
    event_type: ClassVar[str] = "eaip.organization.settings_updated"

    org_id: str
    changes: dict[str, Any] = Field(default_factory=dict)


class OrganizationPolicyCreated(DomainEvent):
    event_type: ClassVar[str] = "eaip.organization.policy_created"

    org_id: str
    policy_id: str
    name: str
    policy_type: str


class OrganizationPolicyUpdated(DomainEvent):
    event_type: ClassVar[str] = "eaip.organization.policy_updated"

    org_id: str
    policy_id: str
    changes: dict[str, Any] = Field(default_factory=dict)


class OrganizationDomainsVerified(DomainEvent):
    event_type: ClassVar[str] = "eaip.organization.domains_verified"

    org_id: str
    domain_ids: tuple[str, ...] = Field(default=())


class OrganizationSubscriptionsUpdated(DomainEvent):
    event_type: ClassVar[str] = "eaip.organization.subscriptions_updated"

    org_id: str
    subscription_id: str
    plan: str
    status: str


class OrganizationReportGenerated(DomainEvent):
    event_type: ClassVar[str] = "eaip.organization.report_generated"

    org_id: str
    report_id: str
    report_type: str
    period_start: datetime
    period_end: datetime


class OrganizationAuditLogged(DomainEvent):
    event_type: ClassVar[str] = "eaip.organization.audit_logged"

    org_id: str
    entry_id: str
    actor_id: str
    action: str
    resource_type: str
    resource_id: str
