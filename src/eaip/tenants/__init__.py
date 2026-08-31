"""Multi-tenant platform — tenant provisioning, isolation, billing, and analytics."""

from __future__ import annotations

from eaip.tenants.billing import BillingService
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
from eaip.tenants.exceptions import (
    BillingError,
    FeatureNotAvailableError,
    TenantError,
    TenantNotFoundError,
    TenantQuotaExceededError,
    TenantSuspendedError,
    UserNotFoundError,
)
from eaip.tenants.health import TenantHealthCheck
from eaip.tenants.integration import TenantRuntimeModule
from eaip.tenants.isolation import TenantIsolationService
from eaip.tenants.manager import TenantManager
from eaip.tenants.models import (
    BillingLineItem,
    BillingRecord,
    CrossTenantReport,
    Tenant,
    TenantConfig,
    TenantQuota,
    TenantUser,
)
from eaip.tenants.reporting import CrossTenantAnalytics

__all__ = [
    "BillingError",
    "BillingLineItem",
    "BillingRecord",
    "BillingService",
    "CrossTenantAnalytics",
    "CrossTenantReport",
    "FeatureNotAvailableError",
    "InvoiceCreated",
    "InvoicePaid",
    "QuotaExceeded",
    "QuotaWarning",
    "Tenant",
    "TenantActivated",
    "TenantClosed",
    "TenantConfig",
    "TenantCreated",
    "TenantError",
    "TenantHealthCheck",
    "TenantIsolationService",
    "TenantManager",
    "TenantNotFoundError",
    "TenantQuota",
    "TenantQuotaExceededError",
    "TenantRuntimeModule",
    "TenantSuspended",
    "TenantSuspendedError",
    "TenantUpdated",
    "TenantUser",
    "UserAdded",
    "UserNotFoundError",
    "UserRemoved",
]
