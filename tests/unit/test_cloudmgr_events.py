"""Tests for cloudmgr domain events."""

from __future__ import annotations

from eaip.cloudmgr.events import CostCompared, ProviderRegistered, ResourceDiscovered
from eaip.events.event import DomainEvent


class TestProviderRegistered:
    def test_event_type(self) -> None:
        event = ProviderRegistered(provider_id="aws1", name="AWS", provider_type="aws")
        assert event.event_type == "eaip.cloudmgr.provider.registered"
        assert isinstance(event, DomainEvent)

    def test_fields(self) -> None:
        event = ProviderRegistered(provider_id="aws1", name="AWS", provider_type="aws")
        assert event.provider_id == "aws1"
        assert event.name == "AWS"
        assert event.provider_type == "aws"


class TestResourceDiscovered:
    def test_event_type(self) -> None:
        event = ResourceDiscovered(
            resource_id="r1", provider_id="aws1", resource_type="ec2", name="web"
        )
        assert event.event_type == "eaip.cloudmgr.resource.discovered"
        assert isinstance(event, DomainEvent)

    def test_fields(self) -> None:
        event = ResourceDiscovered(
            resource_id="r1", provider_id="aws1", resource_type="ec2", name="web"
        )
        assert event.resource_id == "r1"
        assert event.provider_id == "aws1"
        assert event.resource_type == "ec2"
        assert event.name == "web"


class TestCostCompared:
    def test_event_type(self) -> None:
        event = CostCompared(estimate_id="ce1", resource_type="ec2", estimates={"aws": 1.5})
        assert event.event_type == "eaip.cloudmgr.cost.compared"
        assert isinstance(event, DomainEvent)

    def test_fields(self) -> None:
        event = CostCompared(
            estimate_id="ce1", resource_type="ec2", estimates={"aws": 1.5, "gcp": 1.2}
        )
        assert event.estimate_id == "ce1"
        assert event.resource_type == "ec2"
        assert event.estimates == {"aws": 1.5, "gcp": 1.2}


class TestAllEventsAreDomainEvents:
    def test_all_inherit_domain_event(self) -> None:
        assert issubclass(ProviderRegistered, DomainEvent)
        assert issubclass(ResourceDiscovered, DomainEvent)
        assert issubclass(CostCompared, DomainEvent)
