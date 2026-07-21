"""Tests for alertcorr domain events."""

from __future__ import annotations

from eaip.alertcorr.events import AlertDeduplicated, AlertGrouped, AlertSuppressed
from eaip.events.event import DomainEvent


class TestAlertGrouped:
    def test_event_type(self) -> None:
        event = AlertGrouped(group_id="g1", rule_id="r1", alert_ids=("a1", "a2"))
        assert event.event_type == "eaip.alertcorr.alert.grouped"
        assert isinstance(event, DomainEvent)

    def test_fields(self) -> None:
        event = AlertGrouped(group_id="g1", rule_id="r1", alert_ids=("a1", "a2"))
        assert event.group_id == "g1"
        assert event.rule_id == "r1"
        assert event.alert_ids == ("a1", "a2")


class TestAlertDeduplicated:
    def test_event_type(self) -> None:
        event = AlertDeduplicated(alert_id="a2", original_alert_id="a1", fingerprint="fp1")
        assert event.event_type == "eaip.alertcorr.alert.deduplicated"
        assert isinstance(event, DomainEvent)

    def test_fields(self) -> None:
        event = AlertDeduplicated(alert_id="a2", original_alert_id="a1", fingerprint="fp1")
        assert event.alert_id == "a2"
        assert event.original_alert_id == "a1"
        assert event.fingerprint == "fp1"


class TestAlertSuppressed:
    def test_event_type(self) -> None:
        event = AlertSuppressed(alert_id="a1", rule_id="r1", reason="low priority", details={})
        assert event.event_type == "eaip.alertcorr.alert.suppressed"
        assert isinstance(event, DomainEvent)

    def test_fields(self) -> None:
        event = AlertSuppressed(
            alert_id="a1", rule_id="r1", reason="suppressed by rule", details={"rule": "info"}
        )
        assert event.alert_id == "a1"
        assert event.rule_id == "r1"
        assert event.reason == "suppressed by rule"
        assert event.details == {"rule": "info"}


class TestAllEventsAreDomainEvents:
    def test_all_inherit_domain_event(self) -> None:
        assert issubclass(AlertGrouped, DomainEvent)
        assert issubclass(AlertDeduplicated, DomainEvent)
        assert issubclass(AlertSuppressed, DomainEvent)
