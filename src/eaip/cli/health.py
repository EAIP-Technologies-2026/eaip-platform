"""Health check for the foundation CLI."""

from __future__ import annotations

from eaip.health.checks import HealthCheck, HealthReport, HealthStatus


class CliHealthCheck(HealthCheck):
    """Health check that reports registered command count."""

    name: str = "eaip.cli"

    def __init__(self, registered_commands: int = 0) -> None:
        """Initialize with the number of registered commands."""
        self._registered_commands = registered_commands

    @property
    def registered_commands(self) -> int:
        """Return the number of registered commands."""
        return self._registered_commands

    @registered_commands.setter
    def registered_commands(self, value: int) -> None:
        """Set the number of registered commands."""
        self._registered_commands = value

    async def check(self) -> HealthReport:
        """Run the health check and return a HealthReport."""
        details = {"registered_commands": self._registered_commands}
        if self._registered_commands == 0:
            return HealthReport(
                component="Cli",
                status=HealthStatus.DEGRADED,
                details=details,
                message="no commands registered",
            )
        return HealthReport(
            component="Cli",
            status=HealthStatus.HEALTHY,
            details=details,
        )


__all__ = ["CliHealthCheck"]
