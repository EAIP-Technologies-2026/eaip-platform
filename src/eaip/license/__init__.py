"""License & Entitlement Management — license keys, feature entitlements, usage tracking, enforcement."""

from __future__ import annotations

from eaip.license.enforcement import LicenseEnforcer
from eaip.license.events import (
    FeatureAccessDenied,
    FeatureAccessGranted,
    LicenseActivated,
    LicenseCreated,
    LicenseExpired,
    LicenseRevoked,
    LicenseSuspended,
    LicenseValidated,
    QuotaExceeded,
    QuotaWarning,
    UsageRecorded,
)
from eaip.license.exceptions import (
    FeatureNotEntitledError,
    LicenseError,
    LicenseExpiredError,
    LicenseNotFoundError,
    LicenseRevokedError,
    QuotaExceededError,
    ValidationError,
)
from eaip.license.health import LicenseHealthCheck
from eaip.license.integration import LicenseRuntimeModule
from eaip.license.manager import LicenseManager
from eaip.license.models import (
    FeatureEntitlement,
    License,
    LicenseConfig,
    LicenseStatus,
    LicenseType,
    LicenseValidationResult,
    UsageRecord,
)

__all__ = [
    "FeatureAccessDenied",
    "FeatureAccessGranted",
    "FeatureEntitlement",
    "FeatureNotEntitledError",
    "License",
    "LicenseActivated",
    "LicenseConfig",
    "LicenseCreated",
    "LicenseError",
    "LicenseExpired",
    "LicenseExpiredError",
    "LicenseHealthCheck",
    "LicenseManager",
    "LicenseNotFoundError",
    "LicenseRevoked",
    "LicenseRevokedError",
    "LicenseRuntimeModule",
    "LicenseStatus",
    "LicenseSuspended",
    "LicenseType",
    "LicenseValidated",
    "LicenseValidationResult",
    "QuotaExceeded",
    "QuotaExceededError",
    "QuotaWarning",
    "UsageRecord",
    "UsageRecorded",
    "ValidationError",
]
