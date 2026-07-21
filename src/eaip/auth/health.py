"""Health check for the token & authentication service."""

from __future__ import annotations

from eaip.auth.tokens import TokenService
from eaip.health.checks import HealthReport, HealthStatus


class AuthHealthCheck:
    name: str = "auth"

    def __init__(self, token_service: TokenService) -> None:
        self._token_service = token_service

    async def check(self) -> HealthReport:
        error_details: list[str] = []
        tokens = await self._token_service.list_tokens()
        active = [t for t in tokens if t.status.value == "active"]

        if not tokens:
            error_details.append("No tokens in store")

        status = HealthStatus.HEALTHY
        if error_details:
            status = HealthStatus.DEGRADED

        return HealthReport(
            component="auth",
            status=status,
            message="; ".join(error_details)
            if error_details
            else "Token & authentication service is operational",
            details={
                "tokens_total": len(tokens),
                "tokens_active": len(active),
                "token_config_issuer": self._token_service.config.issuer,
                "signing_algorithm": self._token_service.config.signing_algorithm,
                "enable_revocation": self._token_service.config.enable_revocation,
            },
        )


__all__ = ["AuthHealthCheck"]
