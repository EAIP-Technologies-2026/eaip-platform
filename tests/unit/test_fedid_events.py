"""Tests for fedid domain events."""

from __future__ import annotations

from eaip.events.event import DomainEvent
from eaip.fedid.events import IdentityLinked, SSOSessionCreated, UserAuthenticated


class TestUserAuthenticated:
    def test_event_type(self) -> None:
        event = UserAuthenticated(user_id="u1", idp_id="azure1", external_id="ext-1")
        assert event.event_type == "eaip.fedid.user.authenticated"
        assert isinstance(event, DomainEvent)

    def test_fields(self) -> None:
        event = UserAuthenticated(user_id="u1", idp_id="azure1", external_id="ext-1", method="saml")
        assert event.user_id == "u1"
        assert event.idp_id == "azure1"
        assert event.external_id == "ext-1"
        assert event.method == "saml"

    def test_default_method(self) -> None:
        event = UserAuthenticated(user_id="u1", idp_id="azure1", external_id="ext-1")
        assert event.method == ""


class TestSSOSessionCreated:
    def test_event_type(self) -> None:
        event = SSOSessionCreated(session_id="s1", user_id="u1", idp_id="azure1", ttl_seconds=3600)
        assert event.event_type == "eaip.fedid.sso.session.created"
        assert isinstance(event, DomainEvent)

    def test_fields(self) -> None:
        event = SSOSessionCreated(session_id="s1", user_id="u1", idp_id="azure1", ttl_seconds=7200)
        assert event.session_id == "s1"
        assert event.user_id == "u1"
        assert event.idp_id == "azure1"
        assert event.ttl_seconds == 7200


class TestIdentityLinked:
    def test_event_type(self) -> None:
        event = IdentityLinked(user_id="u1", idp_id="azure1", external_id="ext-1", details={})
        assert event.event_type == "eaip.fedid.identity.linked"
        assert isinstance(event, DomainEvent)

    def test_fields(self) -> None:
        event = IdentityLinked(
            user_id="u1", idp_id="azure1", external_id="ext-1", details={"provider": "Azure AD"}
        )
        assert event.user_id == "u1"
        assert event.idp_id == "azure1"
        assert event.external_id == "ext-1"
        assert event.details == {"provider": "Azure AD"}


class TestAllEventsAreDomainEvents:
    def test_all_inherit_domain_event(self) -> None:
        assert issubclass(UserAuthenticated, DomainEvent)
        assert issubclass(SSOSessionCreated, DomainEvent)
        assert issubclass(IdentityLinked, DomainEvent)
