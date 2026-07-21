"""Tests for TemplateEngine service."""

from __future__ import annotations

import pytest

from eaip.etemplate.engine import TemplateEngine
from eaip.etemplate.exceptions import TemplateNotFoundError, TemplateRenderError
from eaip.etemplate.models import (
    TemplateDefinition,
    TemplateEngineConfig,
    TemplateFormat,
    TemplateVariable,
)


class TestTemplateEngine:
    @pytest.fixture
    def engine(self) -> TemplateEngine:
        return TemplateEngine()

    @pytest.fixture
    def text_template(self) -> TemplateDefinition:
        return TemplateDefinition(
            id="t1",
            name="Greeting",
            content="Hello, $name!",
            format=TemplateFormat.TEXT,
            variables=(TemplateVariable(name="name", required=True),),
        )

    class TestRegisterTemplate:
        async def test_register(
            self, engine: TemplateEngine, text_template: TemplateDefinition
        ) -> None:
            result = await engine.register_template(text_template)
            assert result.id == "t1"
            assert result.name == "Greeting"

        async def test_list(
            self, engine: TemplateEngine, text_template: TemplateDefinition
        ) -> None:
            await engine.register_template(text_template)
            templates = await engine.list_templates()
            assert len(templates) == 1

    class TestGetTemplate:
        async def test_get(self, engine: TemplateEngine, text_template: TemplateDefinition) -> None:
            await engine.register_template(text_template)
            template = await engine.get_template("t1")
            assert template.name == "Greeting"

        async def test_get_not_found(self, engine: TemplateEngine) -> None:
            with pytest.raises(TemplateNotFoundError):
                await engine.get_template("nonexistent")

    class TestRenderTemplate:
        async def test_render_text(
            self, engine: TemplateEngine, text_template: TemplateDefinition
        ) -> None:
            await engine.register_template(text_template)
            result = await engine.render_template("t1", {"name": "World"})
            assert result.content == "Hello, World!"
            assert result.format == TemplateFormat.TEXT

        async def test_render_missing_required_variable(
            self, engine: TemplateEngine, text_template: TemplateDefinition
        ) -> None:
            await engine.register_template(text_template)
            with pytest.raises(TemplateRenderError):
                await engine.render_template("t1")

        async def test_render_with_default(self, engine: TemplateEngine) -> None:
            template = TemplateDefinition(
                id="t2",
                name="With Default",
                content="Hello, $name!",
                format=TemplateFormat.TEXT,
                variables=(TemplateVariable(name="name", default="Guest"),),
            )
            await engine.register_template(template)
            result = await engine.render_template("t2")
            assert result.content == "Hello, Guest!"

    class TestValidateTemplate:
        async def test_valid_json(self, engine: TemplateEngine) -> None:
            template = TemplateDefinition(
                id="j1", name="JSON", content='{"key": "value"}', format=TemplateFormat.JSON
            )
            assert await engine.validate_template(template) is True

        async def test_invalid_json(self, engine: TemplateEngine) -> None:
            template = TemplateDefinition(
                id="j2", name="Bad JSON", content="{invalid}", format=TemplateFormat.JSON
            )
            assert await engine.validate_template(template) is False

        async def test_valid_yaml(self, engine: TemplateEngine) -> None:
            template = TemplateDefinition(
                id="y1", name="YAML", content="key: value", format=TemplateFormat.YAML
            )
            assert await engine.validate_template(template) is True

    class TestUpdateTemplate:
        async def test_update(
            self, engine: TemplateEngine, text_template: TemplateDefinition
        ) -> None:
            await engine.register_template(text_template)
            updated = await engine.update_template("t1", name="New Name")
            assert updated.name == "New Name"

        async def test_update_not_found(self, engine: TemplateEngine) -> None:
            with pytest.raises(TemplateNotFoundError):
                await engine.update_template("nonexistent", name="X")

    class TestConfig:
        def test_default_config(self) -> None:
            e = TemplateEngine()
            assert e.config.max_template_size == 1048576
            assert e.config.cache_enabled is True

        def test_custom_config(self) -> None:
            config = TemplateEngineConfig(max_template_size=512, cache_enabled=False)
            e = TemplateEngine(config=config)
            assert e.config.max_template_size == 512
            assert e.config.cache_enabled is False
