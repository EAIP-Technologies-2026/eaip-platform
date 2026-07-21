"""Tests for asset inventory domain events."""

from __future__ import annotations

import pytest

from eaip.assetinv.events import AssetDecommissioned, AssetRegistered, AssetUpdated
from eaip.assetinv.models import AssetStatus
from eaip.events.event import DomainEvent


class TestAssetRegistered:
    def test_defaults(self) -> None:
        e = AssetRegistered(asset_id="a1", name="Laptop", asset_type="hardware", department="IT")
        assert e.event_type == "eaip.assetinv.asset.registered"
        assert isinstance(e, DomainEvent)

    def test_with_values(self) -> None:
        e = AssetRegistered(asset_id="a1", name="Laptop", asset_type="hardware", department="IT")
        assert e.asset_id == "a1"
        assert e.name == "Laptop"
        assert e.asset_type == "hardware"

    def test_frozen(self) -> None:
        e = AssetRegistered(asset_id="a1", name="Laptop", asset_type="hardware", department="IT")
        with pytest.raises((ValueError, TypeError)):
            e.asset_id = "a2"  # type: ignore[misc]


class TestAssetUpdated:
    def test_defaults(self) -> None:
        e = AssetUpdated(asset_id="a1")
        assert e.event_type == "eaip.assetinv.asset.updated"
        assert e.changes == {}

    def test_with_values(self) -> None:
        e = AssetUpdated(asset_id="a1", changes={"name": "New Name"})
        assert e.changes == {"name": "New Name"}


class TestAssetDecommissioned:
    def test_defaults(self) -> None:
        e = AssetDecommissioned(asset_id="a1", previous_status=AssetStatus.ACTIVE)
        assert e.event_type == "eaip.assetinv.asset.decommissioned"
        assert e.reason == ""

    def test_with_values(self) -> None:
        e = AssetDecommissioned(
            asset_id="a1", previous_status=AssetStatus.ACTIVE, reason="end of life"
        )
        assert e.previous_status == AssetStatus.ACTIVE
        assert e.reason == "end of life"


class TestEventTypes:
    def test_all_have_unique_event_types(self) -> None:
        events = [AssetRegistered, AssetUpdated, AssetDecommissioned]
        types = [e.event_type for e in events]
        assert len(types) == len(set(types))
