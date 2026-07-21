"""Tests for change log service domain events."""

from __future__ import annotations

import pydantic
import pytest

from eaip.changelogsvc.events import ChangeBatchProcessed, ChangeRecorded


class TestChangeRecorded:
    def test_create(self) -> None:
        event = ChangeRecorded(
            entry_id="e1", resource_id="r1", resource_type="vm", action="created"
        )
        assert event.entry_id == "e1"
        assert event.resource_id == "r1"
        assert event.resource_type == "vm"
        assert event.action == "created"
        assert event.event_type == "eaip.changelogsvc.change_recorded"

    def test_frozen(self) -> None:
        event = ChangeRecorded(
            entry_id="e1", resource_id="r1", resource_type="vm", action="created"
        )
        with pytest.raises(pydantic.ValidationError):
            event.entry_id = "e2"  # type: ignore[misc]


class TestChangeBatchProcessed:
    def test_create(self) -> None:
        event = ChangeBatchProcessed(batch_size=10, success_count=10, failure_count=0)
        assert event.batch_size == 10
        assert event.success_count == 10
        assert event.failure_count == 0
        assert event.event_type == "eaip.changelogsvc.change_batch_processed"
