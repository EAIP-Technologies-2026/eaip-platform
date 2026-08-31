"""Tests for external identity mapping domain events."""

from __future__ import annotations

import pytest

from eaip.events.event import DomainEvent
from eaip.extidmap.events import IdentityMapped, IdentityUnlinked, MappingUpdated


class TestIdentityMapped:
    def test_defaults(self) -> None:
        e = IdentityMapped(local_uid="u1", external_uid="ext-u1", external_idp="azure_ad")
        assert e.event_type == "eaip.extidmap.identity.mapped"
        assert isinstance(e, DomainEvent)

    def test_with_values(self) -> None:
        e = IdentityMapped(local_uid="u1", external_uid="ext-u1", external_idp="azure_ad")
        assert e.local_uid == "u1"
        assert e.external_uid == "ext-u1"
        assert e.external_idp == "azure_ad"

    def test_frozen(self) -> None:
        e = IdentityMapped(local_uid="u1", external_uid="ext-u1", external_idp="azure_ad")
        with pytest.raises((ValueError, TypeError)):
            e.local_uid = "u2"


class TestMappingUpdated:
    def test_defaults(self) -> None:
        e = MappingUpdated(mapping_id="m1", changes={"status": "STALE"})
        assert e.event_type == "eaip.extidmap.mapping.updated"

    def test_with_values(self) -> None:
        e = MappingUpdated(mapping_id="m1", changes={"status": "STALE"})
        assert e.mapping_id == "m1"
        assert e.changes["status"] == "STALE"


class TestIdentityUnlinked:
    def test_defaults(self) -> None:
        e = IdentityUnlinked(mapping_id="m1", local_uid="u1", external_idp="azure_ad")
        assert e.event_type == "eaip.extidmap.identity.unlinked"

    def test_with_values(self) -> None:
        e = IdentityUnlinked(mapping_id="m1", local_uid="u1", external_idp="azure_ad")
        assert e.mapping_id == "m1"
        assert e.external_idp == "azure_ad"


class TestEventTypes:
    def test_all_have_unique_event_types(self) -> None:
        events = [IdentityMapped, MappingUpdated, IdentityUnlinked]
        types = [e.event_type for e in events]
        assert len(types) == len(set(types))
