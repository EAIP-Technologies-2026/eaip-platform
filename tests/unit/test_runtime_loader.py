"""Unit tests for :mod:`eaip.runtime.loader`."""

from __future__ import annotations

import pytest

from eaip.runtime.exceptions import ModuleLoadError
from eaip.runtime.loader import ModuleLoader
from eaip.runtime.module import BaseRuntimeModule


class _Good(BaseRuntimeModule):
    module_name = "good"

    async def on_start(self, host: object, ctx: object) -> None:  # type: ignore[override]
        pass


class _WithDeps(BaseRuntimeModule):
    module_name = "with-deps"
    module_dependencies = ("good",)

    async def on_start(self, host: object, ctx: object) -> None:  # type: ignore[override]
        pass


class _NotAModule:
    """Deliberately does not satisfy RuntimeModule protocol."""

    pass


def test_register_valid_module() -> None:
    loader = ModuleLoader()
    loader.register(_Good())
    assert "good" in loader
    assert len(loader) == 1


def test_register_module_with_deps() -> None:
    loader = ModuleLoader()
    loader.register(_Good())
    loader.register(_WithDeps())
    assert len(loader) == 2


def test_names_are_sorted() -> None:
    loader = ModuleLoader()
    loader.register(_Good())
    loader.register(_WithDeps())
    assert loader.names() == ["good", "with-deps"]


def test_get_returns_module() -> None:
    loader = ModuleLoader()
    m = _Good()
    loader.register(m)
    assert loader.get("good") is m


def test_get_returns_none_for_unknown() -> None:
    loader = ModuleLoader()
    assert loader.get("nope") is None


def test_duplicate_name_raises() -> None:
    loader = ModuleLoader()
    loader.register(_Good())
    with pytest.raises(ModuleLoadError):
        loader.register(_Good())


def test_non_module_raises() -> None:
    loader = ModuleLoader()
    with pytest.raises(ModuleLoadError, match="protocol"):
        loader.register(_NotAModule())  # type: ignore[arg-type]


def test_empty_name_raises() -> None:
    class _EmptyNameModule:
        """Satisfies RuntimeModule protocol but returns empty name."""

        @property
        def name(self) -> str:
            return ""

        @property
        def dependencies(self) -> tuple[str, ...]:
            return ()

        async def on_start(self, host: object, ctx: object) -> None:
            pass

        async def on_stop(self, host: object, ctx: object) -> None:
            pass

    loader = ModuleLoader()
    with pytest.raises(ModuleLoadError, match="non-empty"):
        loader.register(_EmptyNameModule())  # type: ignore[arg-type]


def test_unregister_existing_returns_true() -> None:
    loader = ModuleLoader()
    loader.register(_Good())
    assert loader.unregister("good") is True
    assert "good" not in loader


def test_unregister_missing_returns_false() -> None:
    loader = ModuleLoader()
    assert loader.unregister("nope") is False


def test_all_returns_registration_order() -> None:
    loader = ModuleLoader()
    g = _Good()
    w = _WithDeps()
    loader.register(g)
    loader.register(w)
    assert loader.all() == [g, w]


def test_len_and_contains() -> None:
    loader = ModuleLoader()
    assert len(loader) == 0
    loader.register(_Good())
    assert len(loader) == 1
    assert "good" in loader
    assert "other" not in loader
