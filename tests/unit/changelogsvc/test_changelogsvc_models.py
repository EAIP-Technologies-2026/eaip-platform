"""Tests for change log service Pydantic models."""

from __future__ import annotations

from datetime import datetime

import pytest
from pydantic import ValidationError

from eaip.changelogsvc.models import ChangeAction, ChangeEntry, ChangeLogConfig, ChangeQuery


class TestChangeEntry:
    def test_default_values(self) -> None:
        entry = ChangeEntry(
            id="e1",
            resource_id="r1",
            resource_type="vm",
            action=ChangeAction.CREATED,
            changed_by="alice",
        )
        assert entry.id == "e1"
        assert entry.resource_id == "r1"
        assert entry.resource_type == "vm"
        assert entry.action == ChangeAction.CREATED
        assert entry.changed_by == "alice"
        assert isinstance(entry.changed_at, datetime)

    def test_frozen(self) -> None:
        entry = ChangeEntry(
            id="e1",
            resource_id="r1",
            resource_type="vm",
            action=ChangeAction.CREATED,
            changed_by="alice",
        )
        with pytest.raises(ValidationError):
            entry.id = "e2"  # type: ignore[misc]

    def test_extra_forbidden(self) -> None:
        with pytest.raises(ValidationError):
            ChangeEntry(
                id="e1",
                resource_id="r1",
                resource_type="vm",
                action=ChangeAction.CREATED,
                changed_by="alice",
                unknown="x",
            )  # type: ignore[call-arg]

    def test_action_enum(self) -> None:
        for action in ChangeAction:
            entry = ChangeEntry(
                id="e1", resource_id="r1", resource_type="vm", action=action, changed_by="alice"
            )
            assert entry.action == action


class TestChangeQuery:
    def test_default_values(self) -> None:
        q = ChangeQuery()
        assert q.limit == 100
        assert q.offset == 0
        assert q.resource_id is None

    def test_extra_forbidden(self) -> None:
        with pytest.raises(ValidationError):
            ChangeQuery(unknown=True)  # type: ignore[call-arg]


class TestChangeLogConfig:
    def test_default_values(self) -> None:
        cfg = ChangeLogConfig()
        assert cfg.retention_days == 90
        assert cfg.max_batch_size == 1000
        assert cfg.enable_compression is False
        assert cfg.storage_backend == "memory"

    def test_extra_forbidden(self) -> None:
        with pytest.raises(ValidationError):
            ChangeLogConfig(unknown=True)  # type: ignore[call-arg]

    def test_custom_values(self) -> None:
        cfg = ChangeLogConfig(
            retention_days=30,
            max_batch_size=500,
            enable_compression=True,
            storage_backend="postgres",
        )
        assert cfg.retention_days == 30
        assert cfg.storage_backend == "postgres"
