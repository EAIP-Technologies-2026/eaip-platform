"""Tests for :mod:`eaip.features.rollout`."""

from __future__ import annotations

import pytest

from eaip.features.exceptions import FlagNotEnabledError, InvalidRolloutError
from eaip.features.manager import FeatureManager
from eaip.features.rollout import RolloutManager


@pytest.mark.asyncio
class TestRolloutManager:
    async def test_gradual_rollout(self) -> None:
        mgr = FeatureManager()
        await mgr.create_flag(id="f1", name="Test", key="test-flag", enabled=True)
        rm = RolloutManager(mgr)
        status = await rm.gradual_rollout("f1", 50)
        assert status["current_percentage"] == 50

    async def test_gradual_rollout_invalid_percentage(self) -> None:
        mgr = FeatureManager()
        await mgr.create_flag(id="f1", name="Test", key="test-flag", enabled=True)
        rm = RolloutManager(mgr)
        with pytest.raises(InvalidRolloutError):
            await rm.gradual_rollout("f1", 150)

    async def test_gradual_rollout_disabled_flag(self) -> None:
        mgr = FeatureManager()
        await mgr.create_flag(id="f1", name="Test", key="test-flag", enabled=False)
        rm = RolloutManager(mgr)
        with pytest.raises(FlagNotEnabledError):
            await rm.gradual_rollout("f1", 50)

    async def test_ramp_up(self) -> None:
        mgr = FeatureManager()
        await mgr.create_flag(
            id="f1",
            name="Test",
            key="test-flag",
            enabled=True,
            rollout_percentage=20,
        )
        rm = RolloutManager(mgr)
        status = await rm.ramp_up("f1", 30)
        assert status["current_percentage"] == 50

    async def test_ramp_up_caps_at_100(self) -> None:
        mgr = FeatureManager()
        await mgr.create_flag(
            id="f1",
            name="Test",
            key="test-flag",
            enabled=True,
            rollout_percentage=80,
        )
        rm = RolloutManager(mgr)
        status = await rm.ramp_up("f1", 50)
        assert status["current_percentage"] == 100

    async def test_ramp_up_disabled_flag(self) -> None:
        mgr = FeatureManager()
        await mgr.create_flag(id="f1", name="Test", key="test-flag", enabled=False)
        rm = RolloutManager(mgr)
        with pytest.raises(FlagNotEnabledError):
            await rm.ramp_up("f1", 10)

    async def test_ramp_up_invalid_step(self) -> None:
        mgr = FeatureManager()
        await mgr.create_flag(id="f1", name="Test", key="test-flag", enabled=True)
        rm = RolloutManager(mgr)
        with pytest.raises(InvalidRolloutError):
            await rm.ramp_up("f1", -5)

    async def test_rollback(self) -> None:
        mgr = FeatureManager()
        await mgr.create_flag(
            id="f1",
            name="Test",
            key="test-flag",
            enabled=True,
            rollout_percentage=50,
        )
        rm = RolloutManager(mgr)
        status = await rm.rollback("f1")
        assert status["current_percentage"] == 0
        assert status["rolled_back"] is True
        flag = await mgr.get_flag("f1")
        assert flag.enabled is False

    async def test_get_rollout_status(self) -> None:
        mgr = FeatureManager()
        await mgr.create_flag(
            id="f1",
            name="Test",
            key="test-flag",
            enabled=True,
            rollout_percentage=30,
        )
        rm = RolloutManager(mgr)
        status = await rm.get_rollout_status("f1")
        assert status is not None
        assert status["has_active_rollout"] is False

    async def test_get_rollout_status_after_gradual(self) -> None:
        mgr = FeatureManager()
        await mgr.create_flag(id="f1", name="Test", key="test-flag", enabled=True)
        rm = RolloutManager(mgr)
        await rm.gradual_rollout("f1", 50)
        status = await rm.get_rollout_status("f1")
        assert status["has_active_rollout"] is True

    async def test_get_rollout_status_nonexistent_flag(self) -> None:
        mgr = FeatureManager()
        rm = RolloutManager(mgr)
        status = await rm.get_rollout_status("nonexistent")
        assert status is None

    async def test_schedule_rollout(self) -> None:
        mgr = FeatureManager()
        rm = RolloutManager(mgr)
        schedule = {
            "steps": [
                {"percentage": 10, "after_seconds": 60},
                {"percentage": 50, "after_seconds": 300},
                {"percentage": 100, "after_seconds": 600},
            ],
        }
        result = await rm.schedule_rollout("f1", schedule)
        assert result["scheduled"] is True
        assert result["steps"] == 3

    async def test_schedule_rollout_invalid(self) -> None:
        mgr = FeatureManager()
        rm = RolloutManager(mgr)
        with pytest.raises(InvalidRolloutError):
            await rm.schedule_rollout("f1", {"invalid": True})
