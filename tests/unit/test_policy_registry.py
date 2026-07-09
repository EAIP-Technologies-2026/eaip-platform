from __future__ import annotations

from eaip.exceptions.domain import DuplicateRegistrationError, NotFoundError
from eaip.policy.models import Policy, PolicyRule, PolicyEffect
from eaip.policy.registry import PolicyRegistry
from eaip.registry.registry import RegistryChange, RegistryEvent


def _policy(pid: str = "pol-1", enabled: bool = True) -> Policy:
    return Policy(id=pid, name=pid, enabled=enabled)


class TestPolicyRegistry:
    def test_register_and_get(self) -> None:
        reg = PolicyRegistry()
        p = _policy()
        reg.register(p)
        assert reg.get("pol-1") == p

    def test_duplicate_raises(self) -> None:
        reg = PolicyRegistry()
        reg.register(_policy())
        try:
            reg.register(_policy())
            assert False, "expected DuplicateRegistrationError"
        except DuplicateRegistrationError:
            pass

    def test_replace_duplicate(self) -> None:
        reg = PolicyRegistry()
        reg.register(_policy("pol-1", enabled=True))
        reg.register(_policy("pol-1", enabled=False), replace=True)
        assert reg.get("pol-1").enabled is False

    def test_get_missing_raises(self) -> None:
        reg = PolicyRegistry()
        try:
            reg.get("nonexistent")
            assert False, "expected NotFoundError"
        except NotFoundError:
            pass

    def test_try_get(self) -> None:
        reg = PolicyRegistry()
        assert reg.try_get("nonexistent") is None
        reg.register(_policy("p1"))
        assert reg.try_get("p1") is not None

    def test_unregister(self) -> None:
        reg = PolicyRegistry()
        reg.register(_policy("p1"))
        assert reg.unregister("p1") is True
        assert reg.unregister("p1") is False
        assert len(reg) == 0

    def test_all_and_enabled(self) -> None:
        reg = PolicyRegistry()
        reg.register(_policy("p1", enabled=True))
        reg.register(_policy("p2", enabled=False))
        assert len(reg.all()) == 2
        assert len(reg.enabled()) == 1

    def test_clear(self) -> None:
        reg = PolicyRegistry()
        reg.register(_policy("p1"))
        reg.clear()
        assert len(reg) == 0

    def test_len_and_contains(self) -> None:
        reg = PolicyRegistry()
        assert len(reg) == 0
        assert "p1" not in reg
        reg.register(_policy("p1"))
        assert len(reg) == 1
        assert "p1" in reg

    def test_observer_notified_on_register(self) -> None:
        reg = PolicyRegistry()
        changes: list[RegistryChange[Policy]] = []
        remove = reg.observe(changes.append)
        reg.register(_policy("p1"))
        assert len(changes) == 1
        assert changes[0].event is RegistryEvent.REGISTERED
        assert changes[0].key == "p1"
        remove()

    def test_observer_notified_on_unregister(self) -> None:
        reg = PolicyRegistry()
        changes: list[RegistryChange[Policy]] = []
        reg.register(_policy("p1"))
        reg.observe(changes.append)
        reg.unregister("p1")
        assert len(changes) == 1
        assert changes[0].event is RegistryEvent.UNREGISTERED
