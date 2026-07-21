"""Tests for :mod:`eaip.tenants.events`."""

from __future__ import annotations

from datetime import datetime

import pytest

from eaip.events.event import DomainEvent
from eaip.tenants.events import (
    InvoiceCreated,
    InvoicePaid,
    QuotaExceeded,
    QuotaWarning,
    TenantActivated,
    TenantClosed,
    TenantCreated,
    TenantSuspended,
    TenantUpdated,
    UserAdded,
    UserRemoved,
)


class TestTenantEvents:
    def test_tenant_created(self) -> None:
        event = TenantCreated(tenant_id="t-1", name="Acme", slug="acme")
        assert event.event_type == "eaip.tenants.tenant_created"
        assert isinstance(event, DomainEvent)
        assert event.tenant_id == "t-1"
        assert event.name == "Acme"
        assert event.plan == "free"

    def test_tenant_updated(self) -> None:
        event = TenantUpdated(tenant_id="t-1", changes={"name": "New"})
        assert event.event_type == "eaip.tenants.tenant_updated"
        assert event.changes == {"name": "New"}

    def test_tenant_suspended(self) -> None:
        event = TenantSuspended(tenant_id="t-1", reason="payment_overdue")
        assert event.event_type == "eaip.tenants.tenant_suspended"
        assert event.reason == "payment_overdue"

    def test_tenant_activated(self) -> None:
        event = TenantActivated(tenant_id="t-1")
        assert event.event_type == "eaip.tenants.tenant_activated"

    def test_tenant_closed(self) -> None:
        event = TenantClosed(tenant_id="t-1", reason="manual")
        assert event.event_type == "eaip.tenants.tenant_closed"
        assert event.reason == "manual"

    def test_user_added(self) -> None:
        event = UserAdded(tenant_id="t-1", user_id="u-1", email="a@b.com")
        assert event.event_type == "eaip.tenants.user_added"
        assert event.email == "a@b.com"

    def test_user_removed(self) -> None:
        event = UserRemoved(tenant_id="t-1", user_id="u-1")
        assert event.event_type == "eaip.tenants.user_removed"

    def test_quota_exceeded(self) -> None:
        event = QuotaExceeded(
            tenant_id="t-1", resource_type="agents", hard_limit=10, current_usage=12
        )
        assert event.event_type == "eaip.tenants.quota_exceeded"
        assert event.hard_limit == 10
        assert event.current_usage == 12

    def test_quota_warning(self) -> None:
        event = QuotaWarning(tenant_id="t-1", resource_type="agents", soft_limit=8, current_usage=9)
        assert event.event_type == "eaip.tenants.quota_warning"
        assert event.soft_limit == 8

    def test_invoice_created(self) -> None:
        now = datetime(2025, 1, 1)
        event = InvoiceCreated(
            invoice_id="inv-1", tenant_id="t-1", period_start=now, period_end=now, amount=100.0
        )
        assert event.event_type == "eaip.tenants.invoice_created"
        assert event.amount == 100.0

    def test_invoice_paid(self) -> None:
        event = InvoicePaid(invoice_id="inv-1", tenant_id="t-1", amount=100.0)
        assert event.event_type == "eaip.tenants.invoice_paid"
        assert event.amount == 100.0

    def test_events_are_frozen(self) -> None:
        event = TenantCreated(tenant_id="t-1", name="N", slug="n")
        with pytest.raises(ValueError):
            event.tenant_id = "other"

    def test_events_have_occurred_at(self) -> None:
        event = TenantCreated(tenant_id="t-1", name="N", slug="n")
        assert isinstance(event.occurred_at, datetime)

    def test_tenant_created_default_plan(self) -> None:
        event = TenantCreated(tenant_id="t-1", name="N", slug="n")
        assert event.plan == "free"

    def test_tenant_suspended_default_reason(self) -> None:
        event = TenantSuspended(tenant_id="t-1")
        assert event.reason == ""
