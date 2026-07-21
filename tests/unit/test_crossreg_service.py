"""Tests for :mod:`eaip.crossreg.replicator`."""

from __future__ import annotations

import pytest

from eaip.crossreg.exceptions import RuleNotFoundError
from eaip.crossreg.models import ReplicationRule
from eaip.crossreg.replicator import CrossRegionReplicator


@pytest.fixture
def replicator() -> CrossRegionReplicator:
    return CrossRegionReplicator()


class TestCrossRegionReplicator:
    @pytest.mark.asyncio
    async def test_create_rule(self, replicator: CrossRegionReplicator) -> None:
        r = ReplicationRule(
            id="r1",
            name="US-EU",
            source_region="us-east",
            target_region="eu-west",
            resource_type="blob",
        )
        result = await replicator.create_rule(r)
        assert result.id == "r1"

    @pytest.mark.asyncio
    async def test_list_rules_empty(self, replicator: CrossRegionReplicator) -> None:
        assert await replicator.list_rules() == []

    @pytest.mark.asyncio
    async def test_get_rule_found(self, replicator: CrossRegionReplicator) -> None:
        r = ReplicationRule(
            id="r1",
            name="US-EU",
            source_region="us-east",
            target_region="eu-west",
            resource_type="blob",
        )
        await replicator.create_rule(r)
        found = await replicator.get_rule("r1")
        assert found is not None
        assert found.name == "US-EU"

    @pytest.mark.asyncio
    async def test_get_rule_not_found(self, replicator: CrossRegionReplicator) -> None:
        found = await replicator.get_rule("nonexistent")
        assert found is None

    @pytest.mark.asyncio
    async def test_update_rule(self, replicator: CrossRegionReplicator) -> None:
        r = ReplicationRule(
            id="r1",
            name="US-EU",
            source_region="us-east",
            target_region="eu-west",
            resource_type="blob",
        )
        await replicator.create_rule(r)
        updated = await replicator.update_rule("r1", {"enabled": False})
        assert updated.enabled is False

    @pytest.mark.asyncio
    async def test_update_rule_not_found(self, replicator: CrossRegionReplicator) -> None:
        with pytest.raises(RuleNotFoundError):
            await replicator.update_rule("nonexistent", {"enabled": False})

    @pytest.mark.asyncio
    async def test_start_replication(self, replicator: CrossRegionReplicator) -> None:
        r = ReplicationRule(
            id="r1",
            name="US-EU",
            source_region="us-east",
            target_region="eu-west",
            resource_type="blob",
        )
        await replicator.create_rule(r)
        status = await replicator.start_replication("r1")
        assert status.status == "running"

    @pytest.mark.asyncio
    async def test_start_replication_not_found(self, replicator: CrossRegionReplicator) -> None:
        with pytest.raises(RuleNotFoundError):
            await replicator.start_replication("nonexistent")

    @pytest.mark.asyncio
    async def test_get_status(self, replicator: CrossRegionReplicator) -> None:
        r = ReplicationRule(
            id="r1",
            name="US-EU",
            source_region="us-east",
            target_region="eu-west",
            resource_type="blob",
        )
        await replicator.create_rule(r)
        await replicator.start_replication("r1")
        status = await replicator.get_status("r1")
        assert status is not None

    @pytest.mark.asyncio
    async def test_get_status_not_found(self, replicator: CrossRegionReplicator) -> None:
        status = await replicator.get_status("nonexistent")
        assert status is None

    @pytest.mark.asyncio
    async def test_list_statuses(self, replicator: CrossRegionReplicator) -> None:
        r = ReplicationRule(
            id="r1",
            name="US-EU",
            source_region="us-east",
            target_region="eu-west",
            resource_type="blob",
        )
        await replicator.create_rule(r)
        await replicator.start_replication("r1")
        statuses = await replicator.list_statuses()
        assert len(statuses) == 1
