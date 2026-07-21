"""Floating License Manager — license pool allocation, lease management, vendor-granted floating licenses."""

from __future__ import annotations

from eaip.floatlicense.events import (
    LicenseCheckedIn,
    LicenseCheckedOut,
    LicenseExhausted,
)
from eaip.floatlicense.exceptions import (
    LicenseMgrError,
    PoolNotFoundError,
)
from eaip.floatlicense.health import FloatLicenseHealthCheck
from eaip.floatlicense.integration import FloatLicenseRuntimeModule
from eaip.floatlicense.manager import FloatingLicenseManager
from eaip.floatlicense.models import (
    LeaseStatus,
    LicenseConfig,
    LicenseLease,
    LicensePool,
)

__all__ = [
    "FloatLicenseHealthCheck",
    "FloatLicenseRuntimeModule",
    "FloatingLicenseManager",
    "LeaseStatus",
    "LicenseCheckedIn",
    "LicenseCheckedOut",
    "LicenseConfig",
    "LicenseExhausted",
    "LicenseLease",
    "LicenseMgrError",
    "LicensePool",
    "PoolNotFoundError",
]
