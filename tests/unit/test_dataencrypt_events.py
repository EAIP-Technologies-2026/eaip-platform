"""Tests for :mod:`eaip.dataencrypt.events`."""

from __future__ import annotations

import pytest

from eaip.dataencrypt.events import DataDecrypted, DataEncrypted, KeyRotated
from eaip.events.event import DomainEvent


class TestDataEncrypted:
    def test_defaults(self) -> None:
        e = DataEncrypted(payload_ref="blob://data", algorithm="aes256", key_id="k1")
        assert isinstance(e, DomainEvent)
        assert e.event_type == "eaip.dataencrypt.data.encrypted"
        assert e.payload_ref == "blob://data"

    def test_frozen(self) -> None:
        e = DataEncrypted(payload_ref="p", algorithm="a", key_id="k")
        with pytest.raises((ValueError, TypeError)):
            e.payload_ref = "new"  # type: ignore[misc]


class TestDataDecrypted:
    def test_defaults(self) -> None:
        e = DataDecrypted(payload_ref="blob://data", algorithm="aes256", key_id="k1")
        assert e.event_type == "eaip.dataencrypt.data.decrypted"


class TestKeyRotated:
    def test_defaults(self) -> None:
        e = KeyRotated(key_id="k1", key_name="master", new_algorithm="rsa4096")
        assert e.event_type == "eaip.dataencrypt.key.rotated"
        assert e.new_algorithm == "rsa4096"


class TestAllEvents:
    def test_all_have_unique_event_types(self) -> None:
        events = [DataEncrypted, DataDecrypted, KeyRotated]
        types = [e.event_type for e in events]
        assert len(types) == len(set(types))

    def test_all_are_domain_events(self) -> None:
        events = [
            DataEncrypted(payload_ref="p", algorithm="a", key_id="k"),
            DataDecrypted(payload_ref="p", algorithm="a", key_id="k"),
            KeyRotated(key_id="k", key_name="n", new_algorithm="r"),
        ]
        for e in events:
            assert isinstance(e, DomainEvent), f"{type(e).__name__} is not a DomainEvent"
