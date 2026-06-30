"""Tests for :mod:`eaip.core` (feature flags + shutdown signal)."""

from __future__ import annotations

import asyncio

import pytest

from eaip.core import FeatureFlag, FeatureFlagRegistry, ShutdownSignal


def test_feature_flag_defaults_and_overrides() -> None:
    reg = FeatureFlagRegistry()
    reg.define(FeatureFlag(name="alpha", default=False))
    reg.define(FeatureFlag(name="beta", default=True))
    assert not reg.is_enabled("alpha")
    assert reg.is_enabled("beta")

    reg.apply_overrides(enabled=("alpha",), disabled=("beta",))
    assert reg.is_enabled("alpha")
    assert not reg.is_enabled("beta")


def test_unknown_flag_defaults_to_false() -> None:
    assert not FeatureFlagRegistry().is_enabled("ghost")


def test_known_returns_sorted_names() -> None:
    reg = FeatureFlagRegistry()
    reg.define(FeatureFlag(name="b"))
    reg.define(FeatureFlag(name="a"))
    assert reg.known() == ["a", "b"]


@pytest.mark.asyncio
async def test_shutdown_signal_blocks_until_set() -> None:
    sig = ShutdownSignal()
    assert not sig.is_set()

    async def trigger_later() -> None:
        await asyncio.sleep(0.01)
        sig.trigger()

    await asyncio.gather(sig.wait(), trigger_later())
    assert sig.is_set()
