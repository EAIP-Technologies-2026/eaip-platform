"""Runtime integration — DataEncryptRuntimeModule for the EAIP kernel."""

from __future__ import annotations

from typing import TYPE_CHECKING

from eaip.capabilities.capability import Capability, CapabilityStatus
from eaip.dataencrypt.encryptor import DataEncryptionService
from eaip.dataencrypt.health import DataEncryptHealthCheck
from eaip.dataencrypt.models import EncryptionConfig

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel

from eaip.logging.context import get_logger

logger = get_logger("eaip.dataencrypt.integration")


class DataEncryptRuntimeModule:
    name: str = "dataencrypt"

    def __init__(
        self,
        config: EncryptionConfig | None = None,
        encryptor: DataEncryptionService | None = None,
    ) -> None:
        self._config = config or EncryptionConfig()
        self._encryptor = encryptor or DataEncryptionService(config=self._config)
        self._health_check = DataEncryptHealthCheck(encryptor=self._encryptor)

    async def start(self, kernel: RuntimeKernel) -> None:
        platform = kernel.platform
        capability = Capability(
            name="eaip.dataencrypt",
            title="Data Encryption Service",
            description="Encrypt and decrypt payloads using AES-256 and RSA-4096",
            version="0.1.0",
            status=CapabilityStatus.ENABLED,
            tags=("dataencrypt", "encryption", "decryption", "key-management"),
        )
        platform.capabilities.register(capability)
        platform.health.register(self._health_check)
        logger.info("dataencrypt_module_started", encryptor_ready=True)

    async def stop(self, kernel: RuntimeKernel) -> None:
        logger.info("dataencrypt_module_stopped")

    @property
    def encryptor(self) -> DataEncryptionService:
        return self._encryptor

    @property
    def health_check(self) -> DataEncryptHealthCheck:
        return self._health_check


__all__ = ["DataEncryptRuntimeModule"]
