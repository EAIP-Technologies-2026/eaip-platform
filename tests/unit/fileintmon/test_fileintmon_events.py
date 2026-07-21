"""Tests for file integrity monitoring domain events."""

from __future__ import annotations

import pytest

from eaip.events.event import DomainEvent
from eaip.fileintmon.events import BaselineRecorded, IntegrityVerified, IntegrityViolation


class TestBaselineRecorded:
    def test_defaults(self) -> None:
        e = BaselineRecorded(
            file_id="f1",
            path="/etc/config.yml",
            hash_value="abc123",
            algorithm="sha256",
        )
        assert e.event_type == "eaip.fileintmon.baseline.recorded"
        assert isinstance(e, DomainEvent)

    def test_with_values(self) -> None:
        e = BaselineRecorded(
            file_id="f1",
            path="/etc/config.yml",
            hash_value="abc123",
            algorithm="sha256",
        )
        assert e.file_id == "f1"
        assert e.path == "/etc/config.yml"

    def test_frozen(self) -> None:
        e = BaselineRecorded(
            file_id="f1",
            path="/etc/config.yml",
            hash_value="abc123",
            algorithm="sha256",
        )
        with pytest.raises((ValueError, TypeError)):
            e.file_id = "f2"


class TestIntegrityVerified:
    def test_defaults(self) -> None:
        e = IntegrityVerified(file_id="f1", path="/etc/config.yml", hash_matched=True)
        assert e.event_type == "eaip.fileintmon.integrity.verified"
        assert e.hash_matched is True

    def test_with_values(self) -> None:
        e = IntegrityVerified(file_id="f1", path="/etc/config.yml", hash_matched=False)
        assert e.hash_matched is False


class TestIntegrityViolation:
    def test_defaults(self) -> None:
        e = IntegrityViolation(
            file_id="f1",
            path="/etc/config.yml",
            expected_hash="abc",
            actual_hash="def",
            reason="hash_mismatch",
        )
        assert e.event_type == "eaip.fileintmon.integrity.violation"
        assert e.reason == "hash_mismatch"

    def test_with_values(self) -> None:
        e = IntegrityViolation(
            file_id="f1",
            path="/etc/config.yml",
            expected_hash="abc",
            actual_hash="def",
            reason="hash_mismatch",
        )
        assert e.expected_hash == "abc"
        assert e.actual_hash == "def"


class TestEventTypes:
    def test_all_have_unique_event_types(self) -> None:
        events = [BaselineRecorded, IntegrityVerified, IntegrityViolation]
        types = [e.event_type for e in events]
        assert len(types) == len(set(types))
