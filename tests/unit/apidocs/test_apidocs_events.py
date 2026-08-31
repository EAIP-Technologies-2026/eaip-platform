"""Tests for API Documentation domain events."""

from __future__ import annotations

from eaip.apidocs.events import (
    ApiDocsEvent,
    ChangelogCreated,
    DocGenerated,
    DocPublished,
    EndpointDocRegistered,
)
from eaip.events.event import DomainEvent


class TestBaseEvent:
    def test_all_events_are_domain_events(self) -> None:
        assert issubclass(DocGenerated, DomainEvent)
        assert issubclass(DocPublished, DomainEvent)
        assert issubclass(ChangelogCreated, DomainEvent)
        assert issubclass(EndpointDocRegistered, DomainEvent)

    def test_event_type_values(self) -> None:
        assert DocGenerated.event_type == "eaip.apidocs.doc.generated"
        assert DocPublished.event_type == "eaip.apidocs.doc.published"
        assert ChangelogCreated.event_type == "eaip.apidocs.changelog.created"
        assert EndpointDocRegistered.event_type == "eaip.apidocs.endpoint.registered"


class TestDocGenerated:
    def test_fields(self) -> None:
        evt = DocGenerated(doc_id="d1", source_version="1.0.0", format="openapi_json")
        assert evt.doc_id == "d1"
        assert evt.format == "openapi_json"


class TestDocPublished:
    def test_fields(self) -> None:
        evt = DocPublished(doc_id="d1", source_version="1.0.0", format="markdown")
        assert evt.format == "markdown"


class TestChangelogCreated:
    def test_fields(self) -> None:
        evt = ChangelogCreated(changelog_id="cl_1", version="1.1.0", change_count=3)
        assert evt.change_count == 3


class TestEndpointDocRegistered:
    def test_fields(self) -> None:
        evt = EndpointDocRegistered(endpoint_id="ep_1", endpoint_path="/users", method="GET")
        assert evt.endpoint_path == "/users"
        assert evt.method == "GET"


class TestUnion:
    def test_union_type(self) -> None:
        evt: ApiDocsEvent = DocGenerated(doc_id="d1", source_version="1", format="json")
        assert isinstance(evt, DocGenerated)
