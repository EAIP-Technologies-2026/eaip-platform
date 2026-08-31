"""Tests for datacatalog domain events."""

from __future__ import annotations

from eaip.datacatalog.events import AssetRegistered, AssetRemoved, AssetUpdated
from eaip.events.event import DomainEvent


class TestAssetRegistered:
    def test_event_type(self) -> None:
        event = AssetRegistered(asset_id="a1", name="users", asset_type="table", source_id="s1")
        assert event.event_type == "eaip.datacatalog.asset.registered"
        assert isinstance(event, DomainEvent)

    def test_fields(self) -> None:
        event = AssetRegistered(asset_id="a1", name="users", asset_type="table", source_id="s1")
        assert event.asset_id == "a1"
        assert event.name == "users"
        assert event.asset_type == "table"
        assert event.source_id == "s1"


class TestAssetUpdated:
    def test_event_type(self) -> None:
        event = AssetUpdated(asset_id="a1", name="users", changes={"description": "updated"})
        assert event.event_type == "eaip.datacatalog.asset.updated"
        assert isinstance(event, DomainEvent)

    def test_fields(self) -> None:
        event = AssetUpdated(asset_id="a1", name="users", changes={"name": "renamed"})
        assert event.asset_id == "a1"
        assert event.name == "users"
        assert event.changes == {"name": "renamed"}


class TestAssetRemoved:
    def test_event_type(self) -> None:
        event = AssetRemoved(asset_id="a1", name="users")
        assert event.event_type == "eaip.datacatalog.asset.removed"
        assert isinstance(event, DomainEvent)

    def test_fields(self) -> None:
        event = AssetRemoved(asset_id="a1", name="users", reason="deprecated")
        assert event.asset_id == "a1"
        assert event.name == "users"
        assert event.reason == "deprecated"

    def test_default_reason(self) -> None:
        event = AssetRemoved(asset_id="a1", name="users")
        assert event.reason == ""


class TestAllEventsAreDomainEvents:
    def test_all_inherit_domain_event(self) -> None:
        assert issubclass(AssetRegistered, DomainEvent)
        assert issubclass(AssetUpdated, DomainEvent)
        assert issubclass(AssetRemoved, DomainEvent)
