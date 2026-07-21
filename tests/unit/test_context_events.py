"""Tests for context domain events."""

from __future__ import annotations

from eaip.context.events import (
    ContextAssembled,
    ContextCompressed,
    ContextEvent,
    PromptCreated,
    PromptVersioned,
)


class TestContextEvents:
    def test_context_event_base(self) -> None:
        assert ContextEvent.event_type == "eaip.context.event"

    def test_prompt_created(self) -> None:
        event = PromptCreated(
            prompt_id="p1",
            name="test",
            version="1.0.0",
        )
        assert event.event_type == "eaip.context.prompt.created"
        assert event.prompt_id == "p1"
        assert event.name == "test"
        assert event.version == "1.0.0"

    def test_prompt_versioned(self) -> None:
        event = PromptVersioned(
            prompt_id="p1",
            version="2.0.0",
            author="alice",
        )
        assert event.event_type == "eaip.context.prompt.versioned"
        assert event.prompt_id == "p1"
        assert event.version == "2.0.0"
        assert event.author == "alice"

    def test_context_assembled(self) -> None:
        event = ContextAssembled(
            document_count=5,
            total_tokens=1024,
            duration_ms=150.0,
        )
        assert event.event_type == "eaip.context.assembled"
        assert event.document_count == 5
        assert event.total_tokens == 1024
        assert event.duration_ms == 150.0

    def test_context_compressed(self) -> None:
        event = ContextCompressed(
            original_tokens=2048,
            compressed_tokens=512,
            strategy="extractive",
            ratio=0.25,
        )
        assert event.event_type == "eaip.context.compressed"
        assert event.original_tokens == 2048
        assert event.compressed_tokens == 512
        assert event.strategy == "extractive"
        assert event.ratio == 0.25

    def test_events_are_frozen(self) -> None:
        event = PromptCreated(prompt_id="p1", name="test", version="1.0.0")
        try:
            event.prompt_id = "p2"  # type: ignore[misc]
            raise AssertionError()
        except Exception:
            pass

    def test_occurred_at_is_set(self) -> None:
        event = PromptCreated(prompt_id="p1", name="test", version="1.0.0")
        assert event.occurred_at is not None
