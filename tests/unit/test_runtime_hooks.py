"""Unit tests for :mod:`eaip.runtime.hooks`."""

from __future__ import annotations

import pytest

from eaip.runtime.hooks import ObservabilityHooks


def test_no_hooks_is_noop() -> None:
    hooks = ObservabilityHooks()
    # None of these should raise.
    hooks.fire_host_starting()
    hooks.fire_host_running()
    hooks.fire_host_stopping()
    hooks.fire_host_stopped()
    hooks.fire_module_starting(module="x")
    hooks.fire_module_started(module="x")
    hooks.fire_module_stopping(module="x")
    hooks.fire_module_stopped(module="x")
    hooks.fire_module_error(module="x", error="oops")


def test_registered_hook_is_called() -> None:
    called: list[str] = []
    hooks = ObservabilityHooks()
    hooks.on_host_starting(lambda **_kw: called.append("starting"))
    hooks.fire_host_starting()
    assert called == ["starting"]


def test_multiple_hooks_all_called() -> None:
    called: list[int] = []
    hooks = ObservabilityHooks()
    hooks.on_host_running(lambda **_kw: called.append(1))
    hooks.on_host_running(lambda **_kw: called.append(2))
    hooks.fire_host_running()
    assert called == [1, 2]


def test_failing_hook_does_not_propagate() -> None:
    called: list[str] = []
    hooks = ObservabilityHooks()
    hooks.on_module_started(lambda **_kw: (_ for _ in ()).throw(RuntimeError("oops")))
    hooks.on_module_started(lambda **_kw: called.append("second"))
    hooks.fire_module_started(module="m")
    # The second hook must still run.
    assert "second" in called


def test_kwargs_passed_to_hook() -> None:
    received: list[dict[str, object]] = []
    hooks = ObservabilityHooks()
    hooks.on_module_stopping(lambda **kw: received.append(kw))
    hooks.fire_module_stopping(module="x", ctx="ctx-val")
    assert received == [{"module": "x", "ctx": "ctx-val"}]


def test_all_hook_types_are_registered() -> None:
    """Smoke test: register one hook per event type, fire all."""
    fired: list[str] = []
    hooks = ObservabilityHooks()
    for name in [
        "on_host_starting",
        "on_host_running",
        "on_host_stopping",
        "on_host_stopped",
        "on_module_starting",
        "on_module_started",
        "on_module_stopping",
        "on_module_stopped",
        "on_module_error",
    ]:

        def _make_cb(n: str) -> object:
            def _cb(**_kw: object) -> None:
                fired.append(n)

            return _cb

        getattr(hooks, name)(_make_cb(name))

    hooks.fire_host_starting()
    hooks.fire_host_running()
    hooks.fire_host_stopping()
    hooks.fire_host_stopped()
    hooks.fire_module_starting()
    hooks.fire_module_started()
    hooks.fire_module_stopping()
    hooks.fire_module_stopped()
    hooks.fire_module_error()

    assert len(fired) == 9


# ---------------------------------------------------------------------------
# Extension hooks
# ---------------------------------------------------------------------------


def test_define_and_fire_extension_hook() -> None:
    called: list[dict[str, object]] = []
    hooks = ObservabilityHooks()
    hooks.define("my.event")
    hooks.on("my.event", lambda **kw: called.append(kw))
    hooks.fire("my.event", key="val")
    assert called == [{"key": "val"}]


def test_define_duplicate_is_idempotent() -> None:
    hooks = ObservabilityHooks()
    hooks.define("my.event")
    hooks.define("my.event")
    hooks.on("my.event", lambda **kw: None)


def test_define_empty_raises() -> None:
    hooks = ObservabilityHooks()
    with pytest.raises(ValueError, match="non-empty"):
        hooks.define("")


def test_define_builtin_conflict_raises() -> None:
    hooks = ObservabilityHooks()
    with pytest.raises(ValueError, match="built-in"):
        hooks.define("host_starting")


def test_on_unknown_extension_raises() -> None:
    hooks = ObservabilityHooks()
    with pytest.raises(ValueError, match="define"):
        hooks.on("unknown.event", lambda **kw: None)


def test_on_builtin_routes_correctly() -> None:
    called: list[str] = []
    hooks = ObservabilityHooks()
    hooks.on("host_running", lambda **kw: called.append("fired"))
    hooks.fire_host_running()
    assert called == ["fired"]


def test_fire_builtin_routes_correctly() -> None:
    called: list[str] = []
    hooks = ObservabilityHooks()
    hooks.on_host_running(lambda **kw: called.append("fired"))
    hooks.fire("host_running")
    assert called == ["fired"]


def test_undefine_removes_event() -> None:
    hooks = ObservabilityHooks()
    hooks.define("my.event")
    assert hooks.undefine("my.event") is True
    assert hooks.undefine("my.event") is False
    # Firing an undefined event should not raise.
    hooks.fire("my.event")


def test_registered_events_includes_builtin_and_extension() -> None:
    hooks = ObservabilityHooks()
    hooks.define("custom.a")
    hooks.define("custom.b")
    events = hooks.registered_events()
    assert "host_starting" in events
    assert "custom.a" in events
    assert "custom.b" in events
