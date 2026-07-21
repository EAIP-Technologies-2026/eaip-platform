"""Data encryption service — encrypt and decrypt payloads."""

from __future__ import annotations

from eaip.dataencrypt.encryptor import DataEncryptionService
from eaip.dataencrypt.events import (
    DataDecrypted,
    DataEncrypted,
    KeyRotated,
)
from eaip.dataencrypt.exceptions import (
    EncryptionError,
    KeyNotFoundError,
)
from eaip.dataencrypt.health import DataEncryptHealthCheck
from eaip.dataencrypt.integration import DataEncryptRuntimeModule
from eaip.dataencrypt.models import (
    EncryptionConfig,
    EncryptionKey,
    EncryptionRequest,
    EncryptionResult,
)

__all__ = [
    "DataDecrypted",
    "DataEncryptHealthCheck",
    "DataEncryptRuntimeModule",
    "DataEncrypted",
    "DataEncryptionService",
    "EncryptionConfig",
    "EncryptionError",
    "EncryptionKey",
    "EncryptionRequest",
    "EncryptionResult",
    "KeyNotFoundError",
    "KeyRotated",
]
