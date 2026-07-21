"""Tests for notification template service."""

from __future__ import annotations

import pytest

from eaip.notifications.events import TemplateCreated, TemplateUpdated
from eaip.notifications.exceptions import TemplateNotFoundError
from eaip.notifications.models import NotificationChannel, NotificationTemplate
from eaip.notifications.templates import TemplateService


class TestTemplateService:
    @pytest.fixture
    def service(self) -> TemplateService:
        return TemplateService()

    def test_create(self, service: TemplateService) -> None:
        t = service.create("t1", "Welcome", NotificationChannel.EMAIL, "Hello {{name}}")
        assert t.id == "t1"
        assert t.name == "Welcome"
        assert t.subject_template == "Hello {{name}}"

    def test_create_emits_event(self, service: TemplateService) -> None:
        service.create("t1", "Welcome", NotificationChannel.EMAIL, "Hi")
        events = service.drain_events()
        assert len(events) == 1
        assert isinstance(events[0], TemplateCreated)
        assert events[0].template_id == "t1"

    def test_get(self, service: TemplateService) -> None:
        service.create("t1", "Welcome", NotificationChannel.EMAIL, "Hi")
        t = service.get("t1")
        assert t is not None
        assert t.name == "Welcome"

    def test_get_missing(self, service: TemplateService) -> None:
        t = service.get("nonexistent")
        assert t is None

    def test_list(self, service: TemplateService) -> None:
        service.create("t1", "A", NotificationChannel.EMAIL, "Hi")
        service.create("t2", "B", NotificationChannel.SMS, "Hello")
        templates = service.list_templates()
        assert len(templates) == 2

    def test_update(self, service: TemplateService) -> None:
        service.create("t1", "Welcome", NotificationChannel.EMAIL, "Hello {{name}}")
        t = service.update("t1", name="Greeting", subject_template="Hi {{name}}")
        assert t.name == "Greeting"
        assert t.subject_template == "Hi {{name}}"

    def test_update_emits_event(self, service: TemplateService) -> None:
        service.create("t1", "Welcome", NotificationChannel.EMAIL, "Hi")
        service.drain_events()
        service.update("t1", name="Greeting")
        events = service.drain_events()
        assert len(events) == 1
        assert isinstance(events[0], TemplateUpdated)

    def test_update_missing(self, service: TemplateService) -> None:
        with pytest.raises(TemplateNotFoundError):
            service.update("nonexistent", name="New")

    def test_delete(self, service: TemplateService) -> None:
        service.create("t1", "Welcome", NotificationChannel.EMAIL, "Hi")
        assert service.delete("t1") is True
        assert service.get("t1") is None

    def test_delete_missing(self, service: TemplateService) -> None:
        assert service.delete("nonexistent") is False

    def test_render(self, service: TemplateService) -> None:
        t = NotificationTemplate(
            id="t1",
            name="Welcome",
            channel=NotificationChannel.EMAIL,
            subject_template="Hello {{name}}",
            body_template="Welcome {{name}}!",
        )
        subject, body = service.render(t, {"name": "Alice"})
        assert subject == "Hello Alice"
        assert body == "Welcome Alice!"

    def test_render_missing_variable(self, service: TemplateService) -> None:
        t = NotificationTemplate(
            id="t1",
            name="Test",
            channel=NotificationChannel.EMAIL,
            subject_template="{{greeting}} {{name}}",
        )
        subject, _ = service.render(t, {"name": "Bob"})
        assert subject == "{{greeting}} Bob"

    def test_validate_valid(self, service: TemplateService) -> None:
        t = NotificationTemplate(
            id="t1",
            name="Welcome",
            channel=NotificationChannel.EMAIL,
            subject_template="Hi",
            variables=("name", "email"),
        )
        errors = service.validate(t)
        assert len(errors) == 0

    def test_validate_missing_subject(self, service: TemplateService) -> None:
        t = NotificationTemplate(
            id="t1",
            name="N",
            channel=NotificationChannel.EMAIL,
            subject_template="",
        )
        errors = service.validate(t)
        assert "subject_template is required" in errors

    def test_validate_invalid_variable(self, service: TemplateService) -> None:
        t = NotificationTemplate(
            id="t1",
            name="N",
            channel=NotificationChannel.EMAIL,
            subject_template="Hi",
            variables=("1invalid",),
        )
        errors = service.validate(t)
        assert any("1invalid" in e for e in errors)
