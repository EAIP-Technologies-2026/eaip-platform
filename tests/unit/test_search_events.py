from __future__ import annotations

from eaip.search.events import (
    ProviderRegistered,
    ProviderSearchExecuted,
    ProviderUnregistered,
    SearchExecuted,
    SearchFederated,
)


class TestSearchEvents:
    def test_search_executed(self) -> None:
        event = SearchExecuted(query="test query", provider_name="knowledge", result_count=5, duration_ms=42.0)
        assert event.event_type == "eaip.search.executed"
        assert event.query == "test query"
        assert event.provider_name == "knowledge"
        assert event.result_count == 5
        assert event.duration_ms == 42.0

    def test_search_federated(self) -> None:
        event = SearchFederated(
            query="test",
            sources=("brain", "memory"),
            result_count=10,
            duration_ms=100.0,
        )
        assert event.event_type == "eaip.search.federated"
        assert event.sources == ("brain", "memory")
        assert event.result_count == 10

    def test_provider_search_executed(self) -> None:
        event = ProviderSearchExecuted(
            provider_name="elastic",
            query="test",
            result_count=3,
            duration_ms=50.0,
            error=None,
            metadata={"index": "main"},
        )
        assert event.event_type == "eaip.search.provider.executed"
        assert event.provider_name == "elastic"
        assert event.metadata["index"] == "main"

    def test_provider_search_executed_with_error(self) -> None:
        event = ProviderSearchExecuted(
            provider_name="memory",
            query="test",
            result_count=0,
            duration_ms=5.0,
            error="timeout",
        )
        assert event.error == "timeout"

    def test_provider_registered(self) -> None:
        event = ProviderRegistered(provider_name="qdrant")
        assert event.event_type == "eaip.search.provider.registered"
        assert event.provider_name == "qdrant"

    def test_provider_unregistered(self) -> None:
        event = ProviderUnregistered(provider_name="qdrant")
        assert event.event_type == "eaip.search.provider.unregistered"
        assert event.provider_name == "qdrant"
