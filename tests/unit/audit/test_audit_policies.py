"""Tests for AuditPolicyService."""

from __future__ import annotations

import pytest

from eaip.audit.exceptions import PolicyNotFoundError
from eaip.audit.models import ActorType, AuditEvent, AuditPolicy, RetentionAction, RetentionRule
from eaip.audit.policies import AuditPolicyService


class TestAuditPolicyService:
    def test_create_policy(self) -> None:
        service = AuditPolicyService()
        policy = AuditPolicy(id="p1", name="Test Policy")
        result = service.create_policy(policy)
        assert result.id == "p1"

    def test_get_policy(self) -> None:
        service = AuditPolicyService()
        policy = AuditPolicy(id="p1", name="Test Policy")
        service.create_policy(policy)
        result = service.get_policy("p1")
        assert result.name == "Test Policy"

    def test_get_policy_not_found(self) -> None:
        service = AuditPolicyService()
        with pytest.raises(PolicyNotFoundError):
            service.get_policy("nonexistent")

    def test_update_policy(self) -> None:
        service = AuditPolicyService()
        policy = AuditPolicy(id="p1", name="Original", retention_days=90)
        service.create_policy(policy)
        updated = service.update_policy("p1", name="Updated", retention_days=365)
        assert updated.name == "Updated"
        assert updated.retention_days == 365

    def test_update_policy_not_found(self) -> None:
        service = AuditPolicyService()
        with pytest.raises(PolicyNotFoundError):
            service.update_policy("nonexistent", name="Test")

    def test_delete_policy(self) -> None:
        service = AuditPolicyService()
        policy = AuditPolicy(id="p1", name="Test Policy")
        service.create_policy(policy)
        service.delete_policy("p1")
        with pytest.raises(PolicyNotFoundError):
            service.get_policy("p1")

    def test_delete_policy_not_found(self) -> None:
        service = AuditPolicyService()
        with pytest.raises(PolicyNotFoundError):
            service.delete_policy("nonexistent")

    def test_list_policies(self) -> None:
        service = AuditPolicyService()
        assert service.list_policies() == []
        service.create_policy(AuditPolicy(id="p1", name="P1"))
        service.create_policy(AuditPolicy(id="p2", name="P2"))
        assert len(service.list_policies()) == 2

    async def test_evaluate_policy_no_match(self) -> None:
        service = AuditPolicyService()
        policy = AuditPolicy(id="p1", name="P1", event_types=("data.update",))
        service.create_policy(policy)
        event = AuditEvent(
            id="e1",
            event_type="user.login",
            actor_id="u1",
            actor_type=ActorType.USER,
            action="login",
            resource_type="session",
            resource_id="s1",
        )
        actions = await service.evaluate_policy(event)
        assert actions == []

    async def test_evaluate_policy_notify(self) -> None:
        service = AuditPolicyService()
        policy = AuditPolicy(
            id="p1",
            name="P1",
            event_types=("data.update",),
            notify_on_events=("data.update",),
        )
        service.create_policy(policy)
        event = AuditEvent(
            id="e1",
            event_type="data.update",
            actor_id="u1",
            actor_type=ActorType.USER,
            action="update",
            resource_type="doc",
            resource_id="d1",
        )
        actions = await service.evaluate_policy(event)
        assert actions == ["notify:P1"]

    async def test_evaluate_policy_disabled(self) -> None:
        service = AuditPolicyService()
        policy = AuditPolicy(
            id="p1",
            name="P1",
            event_types=("data.update",),
            notify_on_events=("data.update",),
            enabled=False,
        )
        service.create_policy(policy)
        event = AuditEvent(
            id="e1",
            event_type="data.update",
            actor_id="u1",
            actor_type=ActorType.USER,
            action="update",
            resource_type="doc",
            resource_id="d1",
        )
        actions = await service.evaluate_policy(event)
        assert actions == []

    def test_add_retention_rule(self) -> None:
        service = AuditPolicyService()
        rule = RetentionRule(
            id="r1",
            name="Logs",
            data_type="logs",
            retention_period_days=90,
            action_on_expiry=RetentionAction.DELETE,
        )
        result = service.add_retention_rule(rule)
        assert result.id == "r1"

    async def test_check_retention_default(self) -> None:
        service = AuditPolicyService()
        days = await service.check_retention("unknown_type")
        assert days == 90

    async def test_check_retention_custom(self) -> None:
        service = AuditPolicyService()
        rule = RetentionRule(
            id="r1",
            name="Logs",
            data_type="logs",
            retention_period_days=365,
            action_on_expiry=RetentionAction.ARCHIVE,
        )
        service.add_retention_rule(rule)
        days = await service.check_retention("logs")
        assert days == 365

    async def test_apply_retention(self) -> None:
        service = AuditPolicyService()
        rule = RetentionRule(
            id="r1",
            name="Logs",
            data_type="logs",
            retention_period_days=90,
            action_on_expiry=RetentionAction.DELETE,
        )
        service.add_retention_rule(rule)
        results = await service.apply_retention()
        assert "r1" in results
