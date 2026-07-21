"""Domain events raised by the tenants package."""

from __future__ import annotations

from datetime import datetime
from typing import Any, ClassVar

from pydantic import Field

from eaip.events.event import DomainEvent


class TenantCreated(DomainEvent):
    event_type: ClassVar[str] = "eaip.tenants.tenant_created"

    tenant_id: str
    name: str
    slug: str
    plan: str = "free"


class TenantUpdated(DomainEvent):
    event_type: ClassVar[str] = "eaip.tenants.tenant_updated"

    tenant_id: str
    changes: dict[str, Any] = Field(default_factory=dict)


class TenantSuspended(DomainEvent):
    event_type: ClassVar[str] = "eaip.tenants.tenant_suspended"

    tenant_id: str
    reason: str = ""


class TenantActivated(DomainEvent):
    event_type: ClassVar[str] = "eaip.tenants.tenant_activated"

    tenant_id: str


class TenantClosed(DomainEvent):
    event_type: ClassVar[str] = "eaip.tenants.tenant_closed"

    tenant_id: str
    reason: str = ""


class UserAdded(DomainEvent):
    event_type: ClassVar[str] = "eaip.tenants.user_added"

    tenant_id: str
    user_id: str
    email: str


class UserRemoved(DomainEvent):
    event_type: ClassVar[str] = "eaip.tenants.user_removed"

    tenant_id: str
    user_id: str


class QuotaExceeded(DomainEvent):
    event_type: ClassVar[str] = "eaip.tenants.quota_exceeded"

    tenant_id: str
    resource_type: str
    hard_limit: int
    current_usage: int


class QuotaWarning(DomainEvent):
    event_type: ClassVar[str] = "eaip.tenants.quota_warning"

    tenant_id: str
    resource_type: str
    soft_limit: int
    current_usage: int


class InvoiceCreated(DomainEvent):
    event_type: ClassVar[str] = "eaip.tenants.invoice_created"

    invoice_id: str
    tenant_id: str
    period_start: datetime
    period_end: datetime
    amount: float


class InvoicePaid(DomainEvent):
    event_type: ClassVar[str] = "eaip.tenants.invoice_paid"

    invoice_id: str
    tenant_id: str
    amount: float
