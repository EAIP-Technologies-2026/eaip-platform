"""Data encryption domain models — keys, requests, results, config."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class EncryptionAlgorithm(StrEnum):
    AES256 = "aes256"
    RSA4096 = "rsa4096"


class KeyStatus(StrEnum):
    ACTIVE = "active"
    DEACTIVATED = "deactivated"
    COMPROMISED = "compromised"


class EncryptionKey(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    algorithm: EncryptionAlgorithm
    key_length: int = Field(default=256)
    status: KeyStatus = Field(default=KeyStatus.ACTIVE)
    created_at: datetime = Field(default_factory=datetime.now)


class EncryptionRequest(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    payload_ref: str
    algorithm: EncryptionAlgorithm
    mode: str = Field(default="CBC")
    key_id: str


class EncryptionResult(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    request_id: str
    encrypted_ref: str = Field(default="")
    algorithm: EncryptionAlgorithm
    key_id: str
    duration_ms: float = Field(default=0.0)


class EncryptionConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    default_algorithm: EncryptionAlgorithm = Field(default=EncryptionAlgorithm.AES256)
    key_rotation_days: int = Field(default=90)
    max_encryption_retries: int = Field(default=3)


__all__ = [
    "EncryptionAlgorithm",
    "EncryptionConfig",
    "EncryptionKey",
    "EncryptionRequest",
    "EncryptionResult",
    "KeyStatus",
]
