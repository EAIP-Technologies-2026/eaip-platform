"""Tests for :mod:`eaip.features.manager`."""

from __future__ import annotations

import pytest

from eaip.features.events import (
    FlagCreated,
    FlagDisabled,
    FlagEnabled,
    FlagRolloutChanged,
    FlagUpdated,
)
from eaip.features.exceptions import FlagNotFoundError
from eaip.features.manager import FeatureManager
from eaip.features.models import FeatureFlag, Operator, TargetingRule


@pytest.mark.asyncio
class TestFeatureManager:
    async def test_create_flag(self) -> None:
        mgr = FeatureManager()
        flag = await mgr.create_flag(id="f1", name="Test", key="test-flag")
        assert isinstance(flag, FeatureFlag)
        assert flag.id == "f1"

    async def test_create_flag_emits_event(self) -> None:
        events: list[object] = []
        mgr = FeatureManager(event_callback=events.append)
        await mgr.create_flag(id="f1", name="Test", key="test-flag", enabled=True)
        assert len(events) == 1
        assert isinstance(events[0], FlagCreated)

    async def test_get_flag(self) -> None:
        mgr = FeatureManager()
        await mgr.create_flag(id="f1", name="Test", key="test-flag")
        flag = await mgr.get_flag("f1")
        assert flag.name == "Test"

    async def test_get_flag_not_found(self) -> None:
        mgr = FeatureManager()
        with pytest.raises(FlagNotFoundError):
            await mgr.get_flag("nonexistent")

    async def test_update_flag_name(self) -> None:
        mgr = FeatureManager()
        await mgr.create_flag(id="f1", name="Old", key="test-flag")
        updated = await mgr.update_flag("f1", name="New")
        assert updated.name == "New"

    async def test_update_flag_emits_updated_event(self) -> None:
        events: list[object] = []
        mgr = FeatureManager(event_callback=events.append)
        await mgr.create_flag(id="f1", name="Old", key="test-flag")
        await mgr.update_flag("f1", name="New")
        assert any(isinstance(e, FlagUpdated) for e in events)

    async def test_update_flag_emits_enabled_event(self) -> None:
        events: list[object] = []
        mgr = FeatureManager(event_callback=events.append)
        await mgr.create_flag(id="f1", name="Test", key="test-flag", enabled=False)
        await mgr.update_flag("f1", enabled=True)
        assert any(isinstance(e, FlagEnabled) for e in events)

    async def test_update_flag_emits_disabled_event(self) -> None:
        events: list[object] = []
        mgr = FeatureManager(event_callback=events.append)
        await mgr.create_flag(id="f1", name="Test", key="test-flag", enabled=True)
        await mgr.update_flag("f1", enabled=False)
        assert any(isinstance(e, FlagDisabled) for e in events)

    async def test_update_flag_emits_rollout_changed_event(self) -> None:
        events: list[object] = []
        mgr = FeatureManager(event_callback=events.append)
        await mgr.create_flag(
            id="f1",
            name="Test",
            key="test-flag",
            enabled=True,
            rollout_percentage=10,
        )
        await mgr.update_flag("f1", rollout_percentage=50)
        assert any(isinstance(e, FlagRolloutChanged) for e in events)

    async def test_delete_flag(self) -> None:
        mgr = FeatureManager()
        await mgr.create_flag(id="f1", name="Test", key="test-flag")
        await mgr.delete_flag("f1")
        assert await mgr.list_flags() == []

    async def test_delete_flag_not_found(self) -> None:
        mgr = FeatureManager()
        with pytest.raises(FlagNotFoundError):
            await mgr.delete_flag("nonexistent")

    async def test_list_flags(self) -> None:
        mgr = FeatureManager()
        await mgr.create_flag(id="f1", name="A", key="a")
        await mgr.create_flag(id="f2", name="B", key="b")
        flags = await mgr.list_flags()
        assert len(flags) == 2

    async def test_is_enabled_false_when_disabled(self) -> None:
        mgr = FeatureManager()
        await mgr.create_flag(id="f1", name="Test", key="test-flag", enabled=False)
        assert await mgr.is_enabled("f1", "user-1") is False

    async def test_is_enabled_true_when_100_percent(self) -> None:
        mgr = FeatureManager()
        await mgr.create_flag(
            id="f1",
            name="Test",
            key="test-flag",
            enabled=True,
            rollout_percentage=100,
        )
        assert await mgr.is_enabled("f1", "user-1") is True

    async def test_is_enabled_false_when_0_percent(self) -> None:
        mgr = FeatureManager()
        await mgr.create_flag(
            id="f1",
            name="Test",
            key="test-flag",
            enabled=True,
            rollout_percentage=0,
        )
        assert await mgr.is_enabled("f1", "user-1") is False

    async def test_is_enabled_false_without_entity(self) -> None:
        mgr = FeatureManager()
        await mgr.create_flag(
            id="f1",
            name="Test",
            key="test-flag",
            enabled=True,
            rollout_percentage=50,
        )
        assert await mgr.is_enabled("f1") is False

    async def test_is_enabled_honors_targeting_rules(self) -> None:
        mgr = FeatureManager()
        rules = (
            TargetingRule(id="r1", attribute="region", operator=Operator.IN, values=("us-east",)),
        )
        await mgr.create_flag(
            id="f1",
            name="Test",
            key="test-flag",
            enabled=True,
            rollout_percentage=0,
            targeting_rules=rules,
        )
        assert await mgr.is_enabled("f1", "us-east") is True
        assert await mgr.is_enabled("f1", "eu-west") is False

    async def test_get_flag_value_returns_variant(self) -> None:
        mgr = FeatureManager()
        await mgr.create_flag(
            id="f1",
            name="Test",
            key="test-flag",
            enabled=True,
            rollout_percentage=100,
            variants={"red": "Red Theme", "blue": "Blue Theme"},
        )
        value = await mgr.get_flag_value("f1", "user-1")
        assert value in ("Red Theme", "Blue Theme")

    async def test_get_flag_value_returns_on_when_no_variants(self) -> None:
        mgr = FeatureManager()
        await mgr.create_flag(
            id="f1",
            name="Test",
            key="test-flag",
            enabled=True,
            rollout_percentage=100,
        )
        value = await mgr.get_flag_value("f1", "user-1")
        assert value == "on"

    async def test_get_flag_value_none_when_disabled(self) -> None:
        mgr = FeatureManager()
        await mgr.create_flag(id="f1", name="Test", key="test-flag", enabled=False)
        value = await mgr.get_flag_value("f1", "user-1")
        assert value is None

    async def test_evaluate_targeting_rules(self) -> None:
        mgr = FeatureManager()
        rules = (TargetingRule(id="r1", attribute="country", operator=Operator.EQ, values=("US",)),)
        await mgr.create_flag(
            id="f1",
            name="Test",
            key="test-flag",
            enabled=True,
            rollout_percentage=0,
            targeting_rules=rules,
        )
        assert await mgr.evaluate_targeting_rules("f1", "US") is True
        assert await mgr.evaluate_targeting_rules("f1", "CA") is False

    async def test_list_flags_by_tags(self) -> None:
        mgr = FeatureManager()
        await mgr.create_flag(id="f1", name="A", key="a", tags=("frontend",))
        await mgr.create_flag(id="f2", name="B", key="b", tags=("backend",))
        await mgr.create_flag(id="f3", name="C", key="c", tags=("frontend", "experiment"))
        result = await mgr.list_flags_by_tags({"frontend"})
        assert len(result) == 2

    async def test_set_event_callback(self) -> None:
        events: list[object] = []
        mgr = FeatureManager()
        mgr.set_event_callback(events.append)
        await mgr.create_flag(id="f1", name="Test", key="test-flag")
        assert len(events) == 1
