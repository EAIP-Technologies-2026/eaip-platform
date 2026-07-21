"""Token & Authentication Service — JWT management, token lifecycle, and authentication provider abstraction."""

from __future__ import annotations

from eaip.auth.auth_providers import AuthenticationService, MockIdentityProvider
from eaip.auth.events import (
    AuthenticationFailed,
    AuthenticationSucceeded,
    ProviderRegistered,
    ProviderUnregistered,
    TokenCreated,
    TokenExpired,
    TokenRefreshed,
    TokenRevoked,
    TokenValidated,
)
from eaip.auth.exceptions import (
    AuthenticationError,
    AuthError,
    ProviderAlreadyRegisteredError,
    ProviderNotFoundError,
    TokenExpiredError,
    TokenInvalidError,
    TokenRevokedError,
)
from eaip.auth.health import AuthHealthCheck
from eaip.auth.integration import AuthRuntimeModule
from eaip.auth.models import (
    AuthenticationRequest,
    AuthenticationResult,
    AuthToken,
    IdentityProvider,
    ProviderType,
    TokenConfig,
    TokenStatus,
    TokenType,
)
from eaip.auth.tokens import TokenService

__all__ = [
    "AuthError",
    "AuthHealthCheck",
    "AuthRuntimeModule",
    "AuthToken",
    "AuthenticationError",
    "AuthenticationFailed",
    "AuthenticationRequest",
    "AuthenticationResult",
    "AuthenticationService",
    "AuthenticationSucceeded",
    "IdentityProvider",
    "MockIdentityProvider",
    "ProviderAlreadyRegisteredError",
    "ProviderNotFoundError",
    "ProviderRegistered",
    "ProviderType",
    "ProviderUnregistered",
    "TokenConfig",
    "TokenCreated",
    "TokenExpired",
    "TokenExpiredError",
    "TokenInvalidError",
    "TokenRefreshed",
    "TokenRevoked",
    "TokenRevokedError",
    "TokenService",
    "TokenStatus",
    "TokenType",
    "TokenValidated",
]
