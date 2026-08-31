"""Health check for the data encryption module."""

from __future__ import annotations

from eaip.dataencrypt.encryptor import DataEncryptionService
from eaip.health.checks import HealthCheck, HealthReport, HealthStatus


class DataEncryptHealthCheck(HealthCheck):
    name: str = "dataencrypt"

    def __init__(
        self,
        encryptor: DataEncryptionService | None = None,
    ) -> None:
        self._encryptor = encryptor or DataEncryptionService()

    async def check(self) -> HealthReport:
        keys = await self._encryptor.list_keys()
        active = [k for k in keys if k.status.value == "active"]
        return HealthReport(
            component=self.name,
            status=HealthStatus.HEALTHY,
            message=f"{len(keys)} key(s), {len(active)} active",
            details={
                "keys_total": len(keys),
                "keys_active": len(active),
                "default_algorithm": self._encryptor.config.default_algorithm.value,
                "key_rotation_days": self._encryptor.config.key_rotation_days,
            },
        )


__all__ = ["DataEncryptHealthCheck"]
