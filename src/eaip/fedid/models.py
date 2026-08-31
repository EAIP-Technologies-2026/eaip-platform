"""Data models for federated identity and SSO."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class IdpType(StrEnum):
    """Types of identity providers."""

    SAML = "saml"
    OIDC = "oidc"
    OAUTH2 = "oauth2"
    LDAP = "ldap"
    AZURE_AD = "azure_ad"


class SSOStatus(StrEnum):
    """Status of an SSO session."""

    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"


class IdentityProvider(BaseModel):
    """A federated identity provider."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    idp_type: IdpType
    issuer_url: str = Field(default="")
    client_id: str = Field(default="")
    enabled: bool = Field(default=True)
    metadata: dict[str, Any] = Field(default_factory=dict)


class FederatedUser(BaseModel):
    """A user with federated identity."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    external_id: str
    idp_id: str
    email: str = Field(default="")
    display_name: str = Field(default="")
    linked_at: datetime = Field(default_factory=utc_now)
    metadata: dict[str, Any] = Field(default_factory=dict)


class SSOSession(BaseModel):
    """An active SSO session."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    user_id: str
    idp_id: str
    status: SSOStatus = Field(default=SSOStatus.ACTIVE)
    token: str = Field(default="")
    refresh_token: str = Field(default="")
    created_at: datetime = Field(default_factory=utc_now)
    expires_at: datetime
    metadata: dict[str, Any] = Field(default_factory=dict)


class FederationConfig(BaseModel):
    """Configuration for the federated identity provider."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    session_ttl_seconds: int = Field(default=3600, ge=60)
    enable_refresh: bool = Field(default=True)
    max_sessions_per_user: int = Field(default=10, ge=1)
    default_idp: str = Field(default="")
    enable_token_exchange: bool = Field(default=True)


__all__ = [
    "FederatedUser",
    "FederationConfig",
    "IdentityProvider",
    "IdpType",
    "SSOSession",
    "SSOStatus",
]
