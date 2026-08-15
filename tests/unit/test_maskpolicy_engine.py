"""Tests for :mod:`eaip.maskpolicy.engine`."""

from __future__ import annotations

import pytest

from eaip.maskpolicy.engine import MaskingPolicyEngine
from eaip.maskpolicy.models import MaskingPolicy, PolicyStatus


class TestMaskingPolicyEngine:
    @pytest.fixture
    def engine(self) -> MaskingPolicyEngine:
        return MaskingPolicyEngine()

    @pytest.fixture
    def sample_policy(self) -> MaskingPolicy:
        return MaskingPolicy(
            id="p1",
            name="PCI Policy",
            environment="prod",
            status=PolicyStatus.DRAFT,
        )

    async def test_create_and_get_policy(
        self, engine: MaskingPolicyEngine, sample_policy: MaskingPolicy
    ) -> None:
        created = await engine.create_policy(sample_policy)
        assert created.id == "p1"
        fetched = await engine.get_policy("p1")
        assert fetched.name == "PCI Policy"

    async def test_get_policy_not_found(self, engine: MaskingPolicyEngine) -> None:
        with pytest.raises(Exception):
            await engine.get_policy("nonexistent")

    async def test_update_policy(
        self, engine: MaskingPolicyEngine, sample_policy: MaskingPolicy
    ) -> None:
        await engine.create_policy(sample_policy)
        updated = await engine.update_policy("p1", name="Updated PCI", environment="staging")
        assert updated.name == "Updated PCI"
        assert updated.environment == "staging"

    async def test_delete_policy(
        self, engine: MaskingPolicyEngine, sample_policy: MaskingPolicy
    ) -> None:
        await engine.create_policy(sample_policy)
        await engine.delete_policy("p1")
        with pytest.raises(Exception):
            await engine.get_policy("p1")

    async def test_list_policies(self, engine: MaskingPolicyEngine) -> None:
        p1 = MaskingPolicy(id="p1", name="P1", environment="prod")
        p2 = MaskingPolicy(id="p2", name="P2", environment="dev")
        await engine.create_policy(p1)
        await engine.create_policy(p2)
        policies = await engine.list_policies()
        assert len(policies) == 2

    async def test_apply_policy(
        self, engine: MaskingPolicyEngine, sample_policy: MaskingPolicy
    ) -> None:
        await engine.create_policy(sample_policy)
        applied = await engine.apply_policy("p1")
        assert applied.status is PolicyStatus.ACTIVE

    async def test_archive_policy(
        self, engine: MaskingPolicyEngine, sample_policy: MaskingPolicy
    ) -> None:
        await engine.create_policy(sample_policy)
        archived = await engine.archive_policy("p1")
        assert archived.status is PolicyStatus.ARCHIVED
