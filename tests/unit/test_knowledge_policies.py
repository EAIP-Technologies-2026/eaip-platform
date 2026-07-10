"""Tests for retrieval policies — access control and policy enforcement."""

from __future__ import annotations

import pytest

from eaip.knowledge.models import RetrievedChunk, SourceAttribution
from eaip.knowledge.policies import (
    AccessLevel,
    CollectionAccessPolicy,
    RetrievalPolicy,
    RetrievalPolicyEnforcer,
)


class TestRetrievalPolicy:
    def test_policy_creation(self) -> None:
        policy = RetrievalPolicy(
            policy_id="pol-1",
            name="HR Access",
            collections=("hr",),
            allowed_roles=("hr_manager", "admin"),
            access_level=AccessLevel.READ,
        )
        assert policy.policy_id == "pol-1"
        assert policy.access_level is AccessLevel.READ
        assert "hr_manager" in policy.allowed_roles

    def test_policy_frozen(self) -> None:
        policy = RetrievalPolicy(
            policy_id="p1",
            collections=("default",),
            allowed_roles=("admin",),
        )
        with pytest.raises(Exception):
            policy.allowed_roles = ("user",)  # type: ignore[misc]

    def test_policy_extra_forbid(self) -> None:
        with pytest.raises(Exception):
            RetrievalPolicy(  # type: ignore[call-arg]
                policy_id="p1",
                collections=("default",),
                unknown_field="value",
            )


class TestCollectionAccessPolicy:
    def test_creation(self) -> None:
        cap = CollectionAccessPolicy(
            collection="finance",
            required_roles=("finance_reader",),
            required_groups=("finance_team",),
        )
        assert cap.collection == "finance"
        assert cap.default_access is AccessLevel.DENY

    def test_default_deny(self) -> None:
        cap = CollectionAccessPolicy(collection="secret")
        assert cap.default_access is AccessLevel.DENY


class TestRetrievalPolicyEnforcer:
    def test_add_policy(self) -> None:
        enforcer = RetrievalPolicyEnforcer()
        policy = RetrievalPolicy(
            policy_id="p1",
            collections=("hr",),
            allowed_roles=("hr_user",),
        )
        enforcer.add_policy(policy)
        assert len(enforcer._policies) == 1

    def test_add_collection_policy(self) -> None:
        enforcer = RetrievalPolicyEnforcer()
        cp = CollectionAccessPolicy(collection="finance", required_roles=("fin_role",))
        enforcer.add_collection_policy(cp)
        assert "finance" in enforcer._collection_policies

    @pytest.mark.asyncio
    async def test_check_access_allowed_by_role(self) -> None:
        enforcer = RetrievalPolicyEnforcer()
        enforcer.add_policy(RetrievalPolicy(
            policy_id="p1",
            collections=("hr",),
            allowed_roles=("hr_manager",),
        ))

        result = await enforcer.check_access("hr", roles=["hr_manager"])
        assert result is True

    @pytest.mark.asyncio
    async def test_check_access_denied(self) -> None:
        enforcer = RetrievalPolicyEnforcer()
        enforcer.add_policy(RetrievalPolicy(
            policy_id="p1",
            collections=("hr",),
            allowed_roles=("hr_manager",),
            access_level=AccessLevel.DENY,
        ))

        result = await enforcer.check_access("hr", roles=["hr_manager"])
        assert result is False

    @pytest.mark.asyncio
    async def test_check_access_denied_by_default(self) -> None:
        enforcer = RetrievalPolicyEnforcer()
        enforcer.add_collection_policy(CollectionAccessPolicy(
            collection="secret",
            required_roles=("admin",),
        ))

        result = await enforcer.check_access("secret", roles=["user"])
        assert result is False

    @pytest.mark.asyncio
    async def test_check_access_no_policies_allows(self) -> None:
        enforcer = RetrievalPolicyEnforcer()
        result = await enforcer.check_access("any", roles=["user"])
        assert result is True

    @pytest.mark.asyncio
    async def test_filter_results(self) -> None:
        enforcer = RetrievalPolicyEnforcer()
        enforcer.add_policy(RetrievalPolicy(
            policy_id="p1",
            collections=("restricted",),
            allowed_roles=("admin",),
        ))

        chunks = [
            RetrievedChunk(
                chunk_id="c1", document_id="d1", collection="restricted",
                content="Secret", score=0.9,
                attribution=SourceAttribution(document_id="d1", collection="restricted", score=0.9),
            ),
            RetrievedChunk(
                chunk_id="c2", document_id="d2", collection="public",
                content="Open", score=0.8,
                attribution=SourceAttribution(document_id="d2", collection="public", score=0.8),
            ),
        ]

        filtered = await enforcer.filter_results(chunks, roles=["user"])
        assert len(filtered) == 1
        assert filtered[0].collection == "public"

    @pytest.mark.asyncio
    async def test_filter_results_admin(self) -> None:
        enforcer = RetrievalPolicyEnforcer()
        enforcer.add_policy(RetrievalPolicy(
            policy_id="p1",
            collections=("restricted",),
            allowed_roles=("admin",),
        ))

        chunks = [
            RetrievedChunk(
                chunk_id="c1", document_id="d1", collection="restricted",
                content="Secret", score=0.9,
                attribution=SourceAttribution(document_id="d1", collection="restricted", score=0.9),
            ),
        ]

        filtered = await enforcer.filter_results(chunks, roles=["admin"])
        assert len(filtered) == 1

    @pytest.mark.asyncio
    async def test_filter_results_empty_input(self) -> None:
        enforcer = RetrievalPolicyEnforcer()
        filtered = await enforcer.filter_results([])
        assert filtered == ()

    @pytest.mark.asyncio
    async def test_subject_match(self) -> None:
        enforcer = RetrievalPolicyEnforcer()
        enforcer.add_policy(RetrievalPolicy(
            policy_id="p1",
            collections=("personal",),
            allowed_subjects=("user123",),
        ))

        result = await enforcer.check_access("personal", subject_id="user123")
        assert result is True

    @pytest.mark.asyncio
    async def test_group_match(self) -> None:
        enforcer = RetrievalPolicyEnforcer()
        enforcer.add_policy(RetrievalPolicy(
            policy_id="p1",
            collections=("team_space",),
            allowed_groups=("engineering",),
        ))

        result = await enforcer.check_access("team_space", groups=["engineering"])
        assert result is True
