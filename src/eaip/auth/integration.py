"""Runtime module integration for the token & authentication service."""

from __future__ import annotations

from typing import TYPE_CHECKING

from eaip.auth.auth_providers import AuthenticationService
from eaip.auth.health import AuthHealthCheck
from eaip.auth.models import TokenConfig
from eaip.auth.tokens import TokenService
from eaip.capabilities.capability import Capability, CapabilityStatus
from eaip.logging.context import get_logger

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel


class AuthRuntimeModule:
    name: str = "auth"

    def __init__(
        self,
        config: TokenConfig | None = None,
        token_service: TokenService | None = None,
        auth_service: AuthenticationService | None = None,
    ) -> None:
        self._config = config or TokenConfig()
        self._token_service = token_service or TokenService(config=self._config)
        self._auth_service = auth_service or AuthenticationService(
            token_service=self._token_service
        )
        self._log = get_logger("eaip.auth.integration")

    @property
    def token_service(self) -> TokenService:
        return self._token_service

    @property
    def auth_service(self) -> AuthenticationService:
        return self._auth_service

    async def start(self, kernel: RuntimeKernel) -> None:
        self._log.info("auth.module.starting")
        platform = kernel.platform
        capability = Capability(
            name="eaip.auth",
            title="Token & Authentication Service",
            description="JWT management, token lifecycle, authentication provider abstraction, and identity store",
            version="0.1.0",
            status=CapabilityStatus.ENABLED,
            tags=("auth", "tokens", "jwt", "authentication", "identity"),
        )
        platform.capabilities.register(capability)
        platform.health.register(AuthHealthCheck(token_service=self._token_service))
        self._log.info("auth.module.started")

    async def stop(self, kernel: RuntimeKernel) -> None:
        self._log.info("auth.module.stopping")


__all__ = ["AuthRuntimeModule"]
