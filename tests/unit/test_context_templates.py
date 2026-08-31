"""Tests for PromptManager."""

from __future__ import annotations

from eaip.context.exceptions import (
    PromptNotFoundError,
    TemplatePolicyError,
    TemplateRenderError,
)
from eaip.context.models import PromptTemplate
from eaip.context.registry import PromptRegistry
from eaip.context.templates import PromptManager


class TestPromptManager:
    def test_create_template(self) -> None:
        mgr = PromptManager()
        tpl = mgr.create_template(
            template_id="greeting",
            name="Greeting",
            content="Hello {name}!",
            variables=("name",),
        )
        assert tpl.template_id == "greeting"
        assert tpl.variables == ("name",)

    def test_create_template_auto_detect_vars(self) -> None:
        mgr = PromptManager()
        tpl = mgr.create_template(
            template_id="auto",
            name="Auto",
            content="{a} and {b} and {a}",
        )
        assert "a" in tpl.variables
        assert "b" in tpl.variables
        assert len(tpl.variables) == 2

    def test_render(self) -> None:
        mgr = PromptManager()
        mgr.create_template(
            template_id="render_test",
            name="Render Test",
            content="Hello {name}, you are {age} years old",
            variables=("name", "age"),
        )
        result = mgr.render("render_test", {"name": "Alice", "age": "30"})
        assert result == "Hello Alice, you are 30 years old"

    def test_render_missing_variable(self) -> None:
        mgr = PromptManager()
        mgr.create_template(
            template_id="missing",
            name="Missing",
            content="{a} and {b}",
            variables=("a", "b"),
        )
        try:
            mgr.render("missing", {"a": "only"})
            raise AssertionError()
        except TemplateRenderError:
            pass

    def test_render_template_not_found(self) -> None:
        mgr = PromptManager()
        try:
            mgr.render("nonexistent", {})
            raise AssertionError()
        except PromptNotFoundError:
            pass

    def test_create_template_empty_content(self) -> None:
        mgr = PromptManager()
        try:
            mgr.create_template(
                template_id="empty",
                name="Empty",
                content="   ",
            )
            raise AssertionError()
        except TemplateRenderError:
            pass

    def test_create_template_undeclared_variables(self) -> None:
        mgr = PromptManager()
        try:
            mgr.create_template(
                template_id="undeclared",
                name="Undeclared",
                content="{a} and {b}",
                variables=("a",),
            )
            raise AssertionError()
        except TemplateRenderError:
            pass

    def test_create_template_unused_variables(self) -> None:
        mgr = PromptManager()
        try:
            mgr.create_template(
                template_id="unused",
                name="Unused",
                content="{a}",
                variables=("a", "b"),
            )
            raise AssertionError()
        except TemplateRenderError:
            pass

    def test_create_version(self) -> None:
        mgr = PromptManager()
        mgr.create_template(
            template_id="ver",
            name="Versioned",
            content="v1 content",
        )
        pv = mgr.create_version(
            template_id="ver",
            content="v2 content",
            version="2.0.0",
            change_log="Updated content",
            author="bob",
        )
        assert pv.version == "2.0.0"
        assert pv.content == "v2 content"
        assert pv.author == "bob"

        rendered = mgr.render("ver", {})
        assert rendered == "v2 content"

    def test_create_version_not_set_current(self) -> None:
        mgr = PromptManager()
        mgr.create_template(
            template_id="ver2",
            name="Ver2",
            content="v1 content",
        )
        mgr.create_version(
            template_id="ver2",
            content="v2 content",
            version="2.0.0",
            set_current=False,
        )
        rendered = mgr.render("ver2", {})
        assert rendered == "v1 content"

    def test_get_current_version(self) -> None:
        mgr = PromptManager()
        mgr.create_template(
            template_id="cv",
            name="Current Version",
            content="first",
            version="1.0.0",
        )
        assert mgr.get_current_version("cv") == "1.0.0"

    def test_policy_check_passes(self) -> None:
        def no_empty_name(tpl: PromptTemplate) -> None:
            if not tpl.name.strip():
                raise TemplatePolicyError("Name must not be empty")

        mgr = PromptManager(policies=[no_empty_name])
        tpl = mgr.create_template(
            template_id="policy_ok",
            name="OK",
            content="hello",
        )
        assert tpl.template_id == "policy_ok"

    def test_policy_check_fails(self) -> None:
        def reject_all(_tpl: PromptTemplate) -> None:
            raise TemplatePolicyError("Rejected by policy")

        mgr = PromptManager(policies=[reject_all])
        try:
            mgr.create_template(
                template_id="policy_fail",
                name="Fail",
                content="test",
            )
            raise AssertionError()
        except TemplatePolicyError:
            pass

    def test_add_policy(self) -> None:
        mgr = PromptManager()
        calls: list[str] = []

        def track(tpl: PromptTemplate) -> None:
            calls.append(tpl.template_id)

        mgr.add_policy(track)
        mgr.create_template(
            template_id="tracked",
            name="Tracked",
            content="test",
        )
        assert "tracked" in calls

    def test_registry_property(self) -> None:
        reg = PromptRegistry()
        mgr = PromptManager(registry=reg)
        assert mgr.registry is reg

    def test_event_published_on_create(self) -> None:
        events: list[object] = []

        def publisher(event: object) -> None:
            events.append(event)

        mgr = PromptManager(event_publisher=publisher)
        mgr.create_template(
            template_id="evt1",
            name="Event Test",
            content="test",
        )
        assert len(events) == 1
        assert events[0].prompt_id == "evt1"

    def test_event_published_on_version(self) -> None:
        events: list[object] = []

        def publisher(event: object) -> None:
            events.append(event)

        mgr = PromptManager(event_publisher=publisher)
        mgr.create_template(
            template_id="evt2",
            name="Version Event",
            content="v1",
        )
        mgr.create_version(
            template_id="evt2",
            content="v2",
            version="2.0.0",
        )
        assert len(events) == 2
        assert events[1].prompt_id == "evt2"
        assert events[1].version == "2.0.0"
