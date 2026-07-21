"""Health check for the credential rotator."""

from __future__ import annotations

from eaip.credrot.rotator import CredentialRotator
from eaip.health.checks import HealthReport, HealthStatus


class CredRotHealthCheck:
    name: str = "credrot"

    def __init__(self, rotator: CredentialRotator) -> None:
        self._rotator = rotator

    async def check(self) -> HealthReport:
        details: dict[str, object] = {}
        try:
            credentials = await self._rotator.list_credentials()
            details["credential_count"] = len(credentials)
            active = [c for c in credentials if c.status.value == "active"]
            rotating = [c for c in credentials if c.status.value == "rotating"]
            details["active_count"] = len(active)
            details["rotating_count"] = len(rotating)
        except Exception as exc:
            return HealthReport(
                component=self.name,
                status=HealthStatus.UNHEALTHY,
                message=f"Credential rotator unavailable: {exc}",
                details={"error": str(exc)},
            )

        status = HealthStatus.HEALTHY
        messages: list[str] = []
        if (
            details.get("rotating_count", 0)
            and isinstance(details["rotating_count"], int)
            and details["rotating_count"] > 0
        ):
            status = HealthStatus.DEGRADED
            messages.append(f"{details['rotating_count']} credential(s) rotating")

        return HealthReport(
            component=self.name,
            status=status,
            message="; ".join(messages) if messages else "Credential rotator healthy",
            details=details,
        )
