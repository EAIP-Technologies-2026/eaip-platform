"""Tests for PromptRegistry."""

from __future__ import annotations

from eaip.context.exceptions import PromptNotFoundError
from eaip.context.models import PromptTemplate, PromptVersion
from eaip.context.registry import PromptRegistry


class _T:
    @staticmethod
    def make(tid: str = "t1", version: str = "1.0.0") -> PromptTemplate:
        return PromptTemplate(
            template_id=tid,
            name=tid,
            content=f"Template {tid}",
            version=version,
        )


class TestPromptRegistry:
    def test_register_and_get(self) -> None:
        reg = PromptRegistry()
        tpl = _T.make("test_prompt")
        reg.register(tpl)
        retrieved = reg.get("test_prompt")
        assert retrieved.template_id == "test_prompt"
        assert retrieved.content == "Template test_prompt"

    def test_get_not_found(self) -> None:
        reg = PromptRegistry()
        try:
            reg.get("nonexistent")
            assert False
        except PromptNotFoundError:
            pass

    def test_get_entry(self) -> None:
        reg = PromptRegistry()
        tpl = _T.make("e1")
        reg.register(tpl)
        entry = reg.get_entry("e1")
        assert entry.prompt_id == "e1"
        assert entry.current_version == "1.0.0"

    def test_register_creates_entry(self) -> None:
        reg = PromptRegistry()
        tpl = _T.make("e2", "2.0.0")
        entry = reg.register(tpl)
        assert entry.prompt_id == "e2"
        assert entry.current_version == "2.0.0"
        assert len(entry.versions) == 1

    def test_add_version(self) -> None:
        reg = PromptRegistry()
        reg.register(_T.make("v1"))
        v2 = PromptVersion(version="2.0.0", content="v2 content", change_log="update")
        reg.add_version("v1", v2)
        retrieved = reg.get_version("v1", "2.0.0")
        assert retrieved.version == "2.0.0"
        assert retrieved.content == "v2 content"
        assert retrieved.change_log == "update"

    def test_add_version_sets_current(self) -> None:
        reg = PromptRegistry()
        reg.register(_T.make("cur", "1.0.0"))
        v2 = PromptVersion(version="2.0.0", content="new")
        reg.add_version("cur", v2, set_current=True)
        entry = reg.get_entry("cur")
        assert entry.current_version == "2.0.0"

    def test_add_version_does_not_set_current(self) -> None:
        reg = PromptRegistry()
        reg.register(_T.make("cur2", "1.0.0"))
        v2 = PromptVersion(version="2.0.0", content="new")
        reg.add_version("cur2", v2, set_current=False)
        entry = reg.get_entry("cur2")
        assert entry.current_version == "1.0.0"

    def test_get_version_not_found(self) -> None:
        reg = PromptRegistry()
        reg.register(_T.make("nf"))
        try:
            reg.get_version("nf", "99.0.0")
            assert False
        except PromptNotFoundError:
            pass

    def test_list_prompts(self) -> None:
        reg = PromptRegistry()
        reg.register(_T.make("a"))
        reg.register(_T.make("b"))
        reg.register(_T.make("c"))
        assert len(reg.list_prompts()) == 3

    def test_list_versions(self) -> None:
        reg = PromptRegistry()
        reg.register(_T.make("lv", "1.0.0"))
        reg.add_version("lv", PromptVersion(version="2.0.0", content="v2"))
        reg.add_version("lv", PromptVersion(version="3.0.0", content="v3"))
        versions = reg.list_versions("lv")
        assert len(versions) == 3

    def test_remove(self) -> None:
        reg = PromptRegistry()
        reg.register(_T.make("rm"))
        assert reg.remove("rm") is True
        assert reg.remove("rm") is False
        assert reg.count == 0

    def test_clear(self) -> None:
        reg = PromptRegistry()
        reg.register(_T.make("a"))
        reg.register(_T.make("b"))
        reg.clear()
        assert reg.count == 0

    def test_observer_notification(self) -> None:
        reg = PromptRegistry()
        events: list[tuple[str, str]] = []

        def on_event(event_type: str, payload: dict) -> None:
            events.append((event_type, payload.get("prompt_id", "")))

        reg.attach("test_obs", on_event)
        reg.register(_T.make("obs1"))

        assert len(events) == 1
        assert events[0] == ("registered", "obs1")

        reg.detach("test_obs")
        reg.register(_T.make("obs2"))
        assert len(events) == 1

    def test_observer_failure_isolation(self) -> None:
        reg = PromptRegistry()

        def failing(_event_type: str, _payload: dict) -> None:
            raise ValueError("observer error")

        reg.attach("failing", failing)
        reg.register(_T.make("iso"))
        assert reg.count == 1

    async def test_health(self) -> None:
        reg = PromptRegistry()
        reg.register(_T.make("h1"))
        result = await reg.health()
        assert result["status"] == "healthy"
        assert result["prompts"] == 1
