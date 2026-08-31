"""Tests for :mod:`eaip.datasample.models`."""

from __future__ import annotations

import pytest

from eaip.datasample.models import (
    SampleDefinition,
    SampleResult,
    SampleStatus,
    SamplingConfig,
    SamplingStrategy,
)


class TestSampleDefinition:
    def test_defaults(self) -> None:
        d = SampleDefinition(
            id="d1", name="User Sample", source="users", strategy=SamplingStrategy.RANDOM
        )
        assert d.id == "d1"
        assert d.sample_size == 100
        assert d.sample_percentage == 10.0
        assert d.filters == {}
        assert d.enabled is True

    def test_with_all_fields(self) -> None:
        d = SampleDefinition(
            id="d2",
            name="Stratified",
            source="orders",
            strategy=SamplingStrategy.STRATIFIED,
            sample_size=500,
            sample_percentage=25.0,
            filters={"status": "active"},
            enabled=False,
        )
        assert d.strategy is SamplingStrategy.STRATIFIED
        assert d.sample_size == 500
        assert d.filters["status"] == "active"
        assert d.enabled is False

    def test_frozen(self) -> None:
        d = SampleDefinition(id="d1", name="N", source="s", strategy=SamplingStrategy.RANDOM)
        with pytest.raises((ValueError, TypeError)):
            d.name = "new"  # type: ignore[misc]

    def test_strategy_values(self) -> None:
        assert SamplingStrategy.RANDOM.value == "random"
        assert SamplingStrategy.STRATIFIED.value == "stratified"
        assert SamplingStrategy.SEQUENTIAL.value == "sequential"


class TestSampleResult:
    def test_defaults(self) -> None:
        r = SampleResult(id="r1", definition_id="d1")
        assert r.sampled_records == 0
        assert r.total_records == 0
        assert r.status is SampleStatus.PENDING

    def test_with_data(self) -> None:
        r = SampleResult(
            id="r2",
            definition_id="d1",
            sampled_records=100,
            total_records=1000,
            status=SampleStatus.COMPLETED,
        )
        assert r.sampled_records == 100
        assert r.status is SampleStatus.COMPLETED

    def test_frozen(self) -> None:
        r = SampleResult(id="r1", definition_id="d")
        with pytest.raises((ValueError, TypeError)):
            r.definition_id = "new"  # type: ignore[misc]

    def test_status_values(self) -> None:
        assert SampleStatus.PENDING.value == "pending"
        assert SampleStatus.COMPLETED.value == "completed"
        assert SampleStatus.FAILED.value == "failed"


class TestSamplingConfig:
    def test_defaults(self) -> None:
        c = SamplingConfig()
        assert c.max_sample_size == 10000
        assert c.default_strategy is SamplingStrategy.RANDOM
        assert c.enable_audit_logging is True

    def test_custom_values(self) -> None:
        c = SamplingConfig(
            max_sample_size=5000,
            default_strategy=SamplingStrategy.STRATIFIED,
            enable_audit_logging=False,
        )
        assert c.max_sample_size == 5000
        assert c.default_strategy is SamplingStrategy.STRATIFIED

    def test_frozen(self) -> None:
        c = SamplingConfig()
        with pytest.raises((ValueError, TypeError)):
            c.max_sample_size = 10  # type: ignore[misc]
