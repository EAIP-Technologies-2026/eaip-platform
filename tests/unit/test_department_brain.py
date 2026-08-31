"""Tests for DepartmentBrain."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from eaip.brain.access import BrainAccessManager, BrainSubject
from eaip.brain.department_brain import DepartmentBrain, DepartmentBrainConfig
from eaip.brain.enterprise_brain import EnterpriseBrain
from eaip.brain.events import BrainSyncCompleted, DepartmentBrainQueryExecuted
from eaip.brain.exceptions import BrainAccessDeniedError, BrainQueryError
from eaip.brain.models import BrainQuery, BrainResult


class TestDepartmentBrainInit:
    def test_department_id_property(self) -> None:
        enterprise = EnterpriseBrain()
        brain = DepartmentBrain(department_id="engineering", enterprise=enterprise)
        assert brain.department_id == "engineering"

    def test_enterprise_property(self) -> None:
        enterprise = EnterpriseBrain()
        brain = DepartmentBrain(department_id="eng", enterprise=enterprise)
        assert brain.enterprise is enterprise

    def test_default_config(self) -> None:
        enterprise = EnterpriseBrain()
        brain = DepartmentBrain(department_id="hr", enterprise=enterprise)
        assert brain.config.top_k is None
        assert brain.config.collections == ()

    def test_custom_config(self) -> None:
        enterprise = EnterpriseBrain()
        config = DepartmentBrainConfig(top_k=5, collections=("hr_docs",))
        brain = DepartmentBrain(department_id="hr", enterprise=enterprise, config=config)
        assert brain.config.top_k == 5
        assert brain.config.collections == ("hr_docs",)


class TestDepartmentBrainQuery:
    @pytest.mark.asyncio
    async def test_query_scopes_collections_to_department(self) -> None:
        enterprise = EnterpriseBrain()
        brain = DepartmentBrain(department_id="finance", enterprise=enterprise)
        result = await brain.query(BrainQuery(query="budget"))
        assert result.query == "budget"

    def test_query_injects_department_filter(self) -> None:
        enterprise = EnterpriseBrain()
        brain = DepartmentBrain(department_id="eng", enterprise=enterprise)
        scoped = brain._build_scoped_query(BrainQuery(query="deploy"))
        assert "department_id" in scoped.filters
        assert scoped.filters["department_id"] == "eng"

    @pytest.mark.asyncio
    async def test_query_with_top_k_override(self) -> None:
        config = DepartmentBrainConfig(top_k=3)
        enterprise = EnterpriseBrain()
        brain = DepartmentBrain(department_id="eng", enterprise=enterprise, config=config)
        scoped = brain._build_scoped_query(BrainQuery(query="test", top_k=10))
        assert scoped.top_k == 3

    @pytest.mark.asyncio
    async def test_query_disables_sources_via_config(self) -> None:
        config = DepartmentBrainConfig(include_memory=False, include_context=False)
        enterprise = EnterpriseBrain()
        brain = DepartmentBrain(department_id="eng", enterprise=enterprise, config=config)
        scoped = brain._build_scoped_query(BrainQuery(query="test"))
        assert scoped.include_memory is False
        assert scoped.include_context is False
        assert scoped.include_knowledge is True

    @pytest.mark.asyncio
    async def test_query_returns_brain_result(self) -> None:
        enterprise = EnterpriseBrain()
        brain = DepartmentBrain(department_id="research", enterprise=enterprise)
        result = await brain.query(BrainQuery(query="innovation"))
        assert isinstance(result, BrainResult)
        assert result.query == "innovation"

    @pytest.mark.asyncio
    async def test_query_uses_department_collections_not_default(self) -> None:
        config = DepartmentBrainConfig(collections=("eng_docs", "eng_wiki"))
        enterprise = EnterpriseBrain()
        brain = DepartmentBrain(department_id="eng", enterprise=enterprise, config=config)
        scoped = brain._build_scoped_query(BrainQuery(query="test"))
        assert scoped.collection_names == ("eng_docs", "eng_wiki")

    @pytest.mark.asyncio
    async def test_query_uses_department_id_as_default_collection(self) -> None:
        enterprise = EnterpriseBrain()
        brain = DepartmentBrain(department_id="eng", enterprise=enterprise)
        scoped = brain._build_scoped_query(BrainQuery(query="test"))
        assert scoped.collection_names == ("eng",)

    @pytest.mark.asyncio
    async def test_query_publishes_event(self) -> None:
        events: list[object] = []
        enterprise = EnterpriseBrain()
        brain = DepartmentBrain(
            department_id="eng",
            enterprise=enterprise,
            event_publisher=events.append,
        )
        await brain.query(BrainQuery(query="test"))
        assert len(events) == 1
        ev = events[0]
        assert isinstance(ev, DepartmentBrainQueryExecuted)
        assert ev.department_id == "eng"
        assert ev.query == "test"

    @pytest.mark.asyncio
    async def test_query_access_denied_raises(self) -> None:
        subject = BrainSubject(subject_id="alice", roles=("viewer",))
        policy_engine = MagicMock()
        decision = MagicMock()
        decision.effect = MagicMock(value="deny")
        from eaip.policy.models import PolicyEffect

        decision.effect = PolicyEffect.DENY
        decision.explanation = "No access"
        policy_engine.evaluate.return_value = decision
        access_manager = BrainAccessManager(policy_engine=policy_engine)
        enterprise = EnterpriseBrain()
        brain = DepartmentBrain(
            department_id="eng",
            enterprise=enterprise,
            access_manager=access_manager,
        )
        with pytest.raises(BrainAccessDeniedError):
            await brain.query(BrainQuery(query="secret"), subject=subject)

    @pytest.mark.asyncio
    async def test_query_enterprise_error_propagates(self) -> None:
        mock_engine = AsyncMock()
        mock_engine.search.side_effect = RuntimeError("downstream failure")
        enterprise = EnterpriseBrain(knowledge_engine=mock_engine)
        brain = DepartmentBrain(department_id="eng", enterprise=enterprise)
        with pytest.raises(BrainQueryError):
            await brain.query(BrainQuery(query="test", include_memory=False, include_context=False))


class TestDepartmentBrainSync:
    @pytest.mark.asyncio
    async def test_sync_from_enterprise_returns_count(self) -> None:
        enterprise = EnterpriseBrain()
        brain = DepartmentBrain(department_id="eng", enterprise=enterprise)
        count = await brain.sync_from_enterprise()
        assert count == 0

    @pytest.mark.asyncio
    async def test_sync_from_enterprise_publishes_event(self) -> None:
        events: list[object] = []
        enterprise = EnterpriseBrain()
        brain = DepartmentBrain(
            department_id="eng",
            enterprise=enterprise,
            event_publisher=events.append,
        )
        await brain.sync_from_enterprise()
        assert len(events) == 1
        ev = events[0]
        assert isinstance(ev, BrainSyncCompleted)
        assert ev.department_id == "eng"
        assert ev.synced_count == 0


class TestDepartmentBrainConfigModel:
    def test_frozen(self) -> None:
        cfg = DepartmentBrainConfig(top_k=5)
        with pytest.raises((ValueError, TypeError)):
            cfg.top_k = 10

    def test_extra_forbidden(self) -> None:
        with pytest.raises((ValueError, TypeError)):
            DepartmentBrainConfig(invalid_field="x")  # type: ignore[call-arg]
