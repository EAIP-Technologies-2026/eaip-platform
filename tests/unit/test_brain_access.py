"""Tests for BrainAccessManager and BrainSubject."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from eaip.brain.access import BrainAccessManager, BrainSubject
from eaip.brain.events import BrainAccessDenied
from eaip.brain.exceptions import BrainAccessDeniedError
from eaip.brain.models import BrainQuery
from eaip.policy.models import Policy, PolicyDecision, PolicyEffect, PolicyRule


class TestBrainSubject:
    def test_defaults(self) -> None:
        subj = BrainSubject(subject_id="alice")
        assert subj.subject_id == "alice"
        assert subj.roles == ()
        assert subj.attributes == {}

    def test_with_all_fields(self) -> None:
        subj = BrainSubject(
            subject_id="bob",
            roles=("admin", "manager"),
            attributes={"ip": "10.0.0.1"},
        )
        assert subj.subject_id == "bob"
        assert "admin" in subj.roles
        assert subj.attributes["ip"] == "10.0.0.1"

    def test_frozen(self) -> None:
        subj = BrainSubject(subject_id="alice")
        with pytest.raises((ValueError, TypeError)):
            subj.subject_id = "bob"

    def test_extra_forbidden(self) -> None:
        with pytest.raises((ValueError, TypeError)):
            BrainSubject(subject_id="test", unknown="x")  # type: ignore[call-arg]


class TestBrainAccessManagerCheckAccess:
    def test_check_access_enterprise_allowed(self) -> None:
        rule = PolicyRule(
            id="allow-enterprise",
            name="Allow enterprise query",
            effect=PolicyEffect.ALLOW,
            actions=("query",),
            resources=("brain:enterprise",),
        )
        policy = Policy(
            id="p1",
            name="Enterprise access",
            rules=(rule,),
        )
        manager = BrainAccessManager(policies=[policy])
        result = manager.check_access(
            subject_id="alice",
            roles=("user",),
            brain_type="enterprise",
        )
        assert result is True

    def test_check_access_enterprise_denied(self) -> None:
        manager = BrainAccessManager(policies=[])
        result = manager.check_access(
            subject_id="alice",
            roles=("user",),
            brain_type="enterprise",
        )
        assert result is False

    def test_check_access_department_allowed(self) -> None:
        rule = PolicyRule(
            id="allow-eng",
            name="Allow engineering query",
            effect=PolicyEffect.ALLOW,
            actions=("query",),
            resources=("brain:department:engineering",),
        )
        policy = Policy(
            id="p1",
            name="Department access",
            rules=(rule,),
        )
        manager = BrainAccessManager(policies=[policy])
        result = manager.check_access(
            subject_id="bob",
            roles=("engineer",),
            brain_type="department",
            department_id="engineering",
        )
        assert result is True

    def test_check_access_department_denied(self) -> None:
        rule = PolicyRule(
            id="allow-finance",
            name="Allow finance query",
            effect=PolicyEffect.ALLOW,
            actions=("query",),
            resources=("brain:department:finance",),
        )
        policy = Policy(
            id="p1",
            name="Department access",
            rules=(rule,),
        )
        manager = BrainAccessManager(policies=[policy])
        result = manager.check_access(
            subject_id="bob",
            roles=("engineer",),
            brain_type="department",
            department_id="engineering",
        )
        assert result is False

    def test_check_access_role_based(self) -> None:
        rule = PolicyRule(
            id="allow-admin",
            name="Allow admins",
            effect=PolicyEffect.ALLOW,
            subjects=("admin",),
            actions=("query",),
            resources=("*",),
        )
        policy = Policy(
            id="p1",
            name="Admin access",
            rules=(rule,),
        )
        manager = BrainAccessManager(policies=[policy])
        result = manager.check_access(
            subject_id="charlie",
            roles=("admin",),
            brain_type="enterprise",
        )
        assert result is True

    def test_check_access_deny_overrides_allow(self) -> None:
        deny = PolicyRule(
            id="deny-all",
            name="Deny everyone",
            effect=PolicyEffect.DENY,
            subjects=(),
            actions=("*",),
            resources=("*",),
        )
        allow = PolicyRule(
            id="allow-admin",
            name="Allow admins",
            effect=PolicyEffect.ALLOW,
            subjects=("admin",),
            actions=("query",),
            resources=("*",),
        )
        policy = Policy(
            id="p1",
            name="Mixed rules",
            rules=(deny, allow),
        )
        manager = BrainAccessManager(policies=[policy])
        result = manager.check_access(
            subject_id="admin_user",
            roles=("admin",),
            brain_type="enterprise",
        )
        assert result is False


class TestBrainAccessManagerAuthorizeQuery:
    def test_authorize_query_allows(self) -> None:
        rule = PolicyRule(
            id="allow-all",
            name="Allow all",
            effect=PolicyEffect.ALLOW,
            actions=("query",),
            resources=("*",),
        )
        policy = Policy(id="p1", name="Allow all", rules=(rule,))
        manager = BrainAccessManager(policies=[policy])
        subject = BrainSubject(subject_id="alice")
        manager.authorize_query(subject, BrainQuery(query="test"))

    def test_authorize_query_denies_raises(self) -> None:
        manager = BrainAccessManager(policies=[])
        subject = BrainSubject(subject_id="alice")
        with pytest.raises(BrainAccessDeniedError):
            manager.authorize_query(subject, BrainQuery(query="test"))

    def test_authorize_query_department_scoped(self) -> None:
        rule = PolicyRule(
            id="allow-eng",
            name="Allow engineering",
            effect=PolicyEffect.ALLOW,
            actions=("query",),
            resources=("brain:department:engineering",),
        )
        policy = Policy(id="p1", name="Eng access", rules=(rule,))
        manager = BrainAccessManager(policies=[policy])
        subject = BrainSubject(subject_id="alice")
        manager.authorize_query(
            subject, BrainQuery(query="test"), department_id="engineering"
        )

    def test_authorize_query_department_denied(self) -> None:
        rule = PolicyRule(
            id="allow-finance",
            name="Allow finance",
            effect=PolicyEffect.ALLOW,
            actions=("query",),
            resources=("brain:department:finance",),
        )
        policy = Policy(id="p1", name="Finance access", rules=(rule,))
        manager = BrainAccessManager(policies=[policy])
        subject = BrainSubject(subject_id="alice")
        with pytest.raises(BrainAccessDeniedError):
            manager.authorize_query(
                subject, BrainQuery(query="test"), department_id="engineering"
            )

    def test_authorize_query_publishes_event_on_deny(self) -> None:
        events: list[object] = []
        manager = BrainAccessManager(policies=[], event_publisher=events.append)
        subject = BrainSubject(subject_id="alice")
        with pytest.raises(BrainAccessDeniedError):
            manager.authorize_query(subject, BrainQuery(query="test"))
        assert len(events) == 1
        ev = events[0]
        assert isinstance(ev, BrainAccessDenied)
        assert ev.subject_id == "alice"
        assert ev.brain_type == "enterprise"
        assert "deny" in ev.reason.lower()

    def test_authorize_query_with_empty_policies_denies(self) -> None:
        manager = BrainAccessManager()
        subject = BrainSubject(subject_id="bob", roles=("user",))
        with pytest.raises(BrainAccessDeniedError):
            manager.authorize_query(subject, BrainQuery(query="test"))
