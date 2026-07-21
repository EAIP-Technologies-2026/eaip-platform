"""Domain events for the data encryption module."""

from __future__ import annotations

from typing import ClassVar

from eaip.events.event import DomainEvent


class DataEncrypted(DomainEvent):
    event_type: ClassVar[str] = "eaip.dataencrypt.data.encrypted"
    payload_ref: str
    algorithm: str
    key_id: str


class DataDecrypted(DomainEvent):
    event_type: ClassVar[str] = "eaip.dataencrypt.data.decrypted"
    payload_ref: str
    algorithm: str
    key_id: str


class KeyRotated(DomainEvent):
    event_type: ClassVar[str] = "eaip.dataencrypt.key.rotated"
    key_id: str
    key_name: str
    new_algorithm: str


__all__ = [
    "DataDecrypted",
    "DataEncrypted",
    "KeyRotated",
]
