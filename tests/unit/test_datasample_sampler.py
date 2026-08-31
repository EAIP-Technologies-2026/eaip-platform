"""Tests for :mod:`eaip.datasample.sampler`."""

from __future__ import annotations

import pytest

from eaip.datasample.models import SampleDefinition, SamplingStrategy
from eaip.datasample.sampler import DataSamplingService


class TestDataSamplingService:
    @pytest.fixture
    def service(self) -> DataSamplingService:
        return DataSamplingService()

    @pytest.fixture
    def sample_def(self) -> SampleDefinition:
        return SampleDefinition(
            id="d1",
            name="User Sample",
            source="users",
            strategy=SamplingStrategy.RANDOM,
            sample_size=100,
        )

    async def test_create_and_get_definition(
        self, service: DataSamplingService, sample_def: SampleDefinition
    ) -> None:
        created = await service.create_definition(sample_def)
        assert created.id == "d1"
        fetched = await service.get_definition("d1")
        assert fetched.name == "User Sample"

    async def test_get_definition_not_found(self, service: DataSamplingService) -> None:
        with pytest.raises(Exception):
            await service.get_definition("nonexistent")

    async def test_update_definition(
        self, service: DataSamplingService, sample_def: SampleDefinition
    ) -> None:
        await service.create_definition(sample_def)
        updated = await service.update_definition("d1", sample_size=500, enabled=False)
        assert updated.sample_size == 500
        assert updated.enabled is False

    async def test_delete_definition(
        self, service: DataSamplingService, sample_def: SampleDefinition
    ) -> None:
        await service.create_definition(sample_def)
        await service.delete_definition("d1")
        with pytest.raises(Exception):
            await service.get_definition("d1")

    async def test_list_definitions(self, service: DataSamplingService) -> None:
        d1 = SampleDefinition(id="d1", name="D1", source="s1", strategy=SamplingStrategy.RANDOM)
        d2 = SampleDefinition(
            id="d2", name="D2", source="s2", strategy=SamplingStrategy.STRATIFIED, enabled=False
        )
        await service.create_definition(d1)
        await service.create_definition(d2)
        all_defs = await service.list_definitions()
        assert len(all_defs) == 2
        enabled = await service.list_definitions(enabled_only=True)
        assert len(enabled) == 1

    async def test_execute_sample(
        self, service: DataSamplingService, sample_def: SampleDefinition
    ) -> None:
        await service.create_definition(sample_def)
        result = await service.execute_sample("d1")
        assert result.definition_id == "d1"
        assert result.sampled_records > 0
        assert result.status.value == "completed"
