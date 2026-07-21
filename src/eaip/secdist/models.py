"""Pydantic models for the secrets distribution service."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class DistributionTarget(BaseModel):
    """A target that can receive distributed secrets."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str = Field(description="Unique identifier for this target")
    endpoint: str = Field(description="Endpoint URL for the target")
    protocol: str = Field(description="Protocol to use (e.g. http, grpc)")
    auth_method: str = Field(description="Authentication method (e.g. token, mTLS, api_key)")


class SecretPackage(BaseModel):
    """A secret payload ready for distribution."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str = Field(description="Unique identifier for the secret package")
    name: str = Field(description="Human-readable name of the secret")
    targets: tuple[str, ...] = Field(
        default=(), description="Target IDs this secret is distributed to"
    )
    encrypted: bool = Field(default=True, description="Whether the secret payload is encrypted")
    ttl_seconds: int = Field(default=3600, ge=1, description="Time-to-live in seconds")
    created_at: datetime = Field(default_factory=utc_now, description="When the secret was created")
    expires_at: datetime | None = Field(default=None, description="When the secret expires")


class DistributionResult(BaseModel):
    """Result of a secret distribution attempt."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    package_id: str = Field(description="ID of the secret package")
    target_id: str = Field(description="ID of the distribution target")
    success: bool = Field(description="Whether distribution succeeded")
    delivered_at: datetime = Field(
        default_factory=utc_now, description="When delivery was attempted"
    )
    error_message: str = Field(default="", description="Error message if distribution failed")


class DistributorConfig(BaseModel):
    """Configuration for the secret distributor."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    max_retries: int = Field(default=3, ge=0, description="Maximum retry attempts per distribution")
    retry_delay_seconds: int = Field(default=5, ge=1, description="Delay between retries")
    default_ttl_seconds: int = Field(default=3600, ge=1, description="Default TTL for secrets")
    enable_encryption: bool = Field(default=True, description="Whether to encrypt secrets at rest")
    history_retention_days: int = Field(
        default=30, ge=1, description="Days to retain distribution history"
    )


__all__ = [
    "DistributionResult",
    "DistributionTarget",
    "DistributorConfig",
    "SecretPackage",
]
