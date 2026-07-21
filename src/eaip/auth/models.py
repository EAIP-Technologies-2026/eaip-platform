"""Token & authentication domain models — tokens, configs, requests, results, identity providers."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class TokenStatus(StrEnum):
    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"
    SUSPENDED = "suspended"


class TokenType(StrEnum):
    ACCESS = "access"
    REFRESH = "refresh"
    API = "api"
    SERVICE = "service"


class ProviderType(StrEnum):
    OAUTH2 = "oauth2"
    OIDC = "oidc"
    LDAP = "ldap"
    SAML = "saml"
    LOCAL = "local"


class AuthToken(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    type: TokenType
    issuer: str
    subject: str
    audience: tuple[str, ...] = Field(default=())
    claims: dict[str, Any] = Field(default_factory=dict)
    issued_at: datetime = Field(default_factory=utc_now)
    expires_at: datetime
    not_before: datetime | None = None
    token_hash: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    status: TokenStatus = TokenStatus.ACTIVE


class TokenConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    access_token_ttl_seconds: int = 900
    refresh_token_ttl_seconds: int = 86_400
    issuer: str = "eaip"
    audience: tuple[str, ...] = Field(default=("eaip",))
    signing_algorithm: str = "HS256"
    secret_key_ref: str = "eaip-auth-secret"
    enable_refresh_rotation: bool = True
    enable_revocation: bool = True


class AuthenticationRequest(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    provider: str
    credentials: dict[str, Any] = Field(default_factory=dict)
    client_id: str = ""
    redirect_uri: str = ""
    scope: tuple[str, ...] = Field(default=())
    metadata: dict[str, Any] = Field(default_factory=dict)


class AuthenticationResult(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    success: bool
    token: str = ""
    refresh_token: str = ""
    identity: dict[str, Any] = Field(default_factory=dict)
    claims: dict[str, Any] = Field(default_factory=dict)
    error: str = ""
    provider: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)


class IdentityProvider(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    type: ProviderType
    config: dict[str, Any] = Field(default_factory=dict)
    enabled: bool = True
    priority: int = 0
    metadata: dict[str, Any] = Field(default_factory=dict)


__all__ = [
    "AuthToken",
    "AuthenticationRequest",
    "AuthenticationResult",
    "IdentityProvider",
    "ProviderType",
    "TokenConfig",
    "TokenStatus",
    "TokenType",
]
