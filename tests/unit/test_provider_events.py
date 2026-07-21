from __future__ import annotations

from eaip.events.event import DomainEvent
from eaip.providers.events import (
    ProviderModelDiscovered,
    ProviderRegistered,
    ProviderRequestCompleted,
    ProviderRequestFailed,
    ProviderRequestStarted,
    ProviderStatusChanged,
    ProviderUnregistered,
)


class TestProviderEvents:
    def test_provider_registered(self) -> None:
        evt = ProviderRegistered(
            provider_name="ollama", provider_type="ollama", default_model="llama3"
        )
        assert evt.event_type == "eaip.provider.registered"
        assert isinstance(evt, DomainEvent)
        assert evt.provider_name == "ollama"

    def test_provider_unregistered(self) -> None:
        evt = ProviderUnregistered(provider_name="ollama")
        assert evt.event_type == "eaip.provider.unregistered"

    def test_provider_status_changed(self) -> None:
        evt = ProviderStatusChanged(
            provider_name="ollama", previous_status="unavailable", current_status="available"
        )
        assert evt.current_status == "available"

    def test_provider_request_started(self) -> None:
        evt = ProviderRequestStarted(provider_name="ollama", model="llama3", stream=False)
        assert evt.stream is False

    def test_provider_request_completed(self) -> None:
        evt = ProviderRequestCompleted(
            provider_name="ollama", model="llama3", duration_ms=150.0, finish_reason="stop"
        )
        assert evt.duration_ms == 150.0

    def test_provider_request_failed(self) -> None:
        evt = ProviderRequestFailed(provider_name="ollama", model="llama3", error="timeout")
        assert "timeout" in evt.error

    def test_provider_model_discovered(self) -> None:
        evt = ProviderModelDiscovered(provider_name="ollama", model_id="llama3")
        assert evt.model_id == "llama3"
