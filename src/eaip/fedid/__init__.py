"""Federated Identity & SSO Provider — manage identity providers, SSO sessions, and token exchange."""

from __future__ import annotations

from eaip.fedid.events import (
    IdentityLinked,
    SSOSessionCreated,
    UserAuthenticated,
)
from eaip.fedid.exceptions import (
    AuthenticationFailedError,
    FederationError,
    ProviderNotFoundError,
)
from eaip.fedid.health import FederatedIdentityHealthCheck
from eaip.fedid.integration import FederatedIdentityRuntimeModule
from eaip.fedid.models import (
    FederatedUser,
    FederationConfig,
    IdentityProvider,
    SSOSession,
)
from eaip.fedid.provider import FederatedIdentityProvider

__all__ = [
    "AuthenticationFailedError",
    "FederatedIdentityHealthCheck",
    "FederatedIdentityProvider",
    "FederatedIdentityRuntimeModule",
    "FederatedUser",
    "FederationConfig",
    "FederationError",
    "IdentityLinked",
    "IdentityProvider",
    "ProviderNotFoundError",
    "SSOSession",
    "SSOSessionCreated",
    "UserAuthenticated",
]
