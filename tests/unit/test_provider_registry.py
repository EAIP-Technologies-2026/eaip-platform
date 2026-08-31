from __future__ import annotations

from eaip.exceptions.domain import DuplicateRegistrationError, NotFoundError
from eaip.providers.models import ProviderInstance
from eaip.providers.registry import ProviderRegistry
from eaip.registry.registry import RegistryChange, RegistryEvent


def _inst(name: str = "ollama") -> ProviderInstance:
    return ProviderInstance(name=name, provider_type="ollama", endpoint="http://localhost:11434")


class TestProviderRegistry:
    def test_register_and_get(self) -> None:
        reg = ProviderRegistry()
        inst = _inst()
        reg.register(inst)
        assert reg.get("ollama") == inst

    def test_duplicate_raises(self) -> None:
        reg = ProviderRegistry()
        reg.register(_inst())
        try:
            reg.register(_inst())
            raise AssertionError()
        except DuplicateRegistrationError:
            pass

    def test_replace(self) -> None:
        reg = ProviderRegistry()
        reg.register(_inst())
        newer = ProviderInstance(
            name="ollama", provider_type="ollama", endpoint="http://other:11434"
        )
        reg.register(newer, replace=True)
        assert reg.get("ollama").endpoint == "http://other:11434"

    def test_get_missing_raises(self) -> None:
        reg = ProviderRegistry()
        try:
            reg.get("nonexistent")
            raise AssertionError()
        except NotFoundError:
            pass

    def test_try_get(self) -> None:
        reg = ProviderRegistry()
        assert reg.try_get("nonexistent") is None
        reg.register(_inst("p1"))
        assert reg.try_get("p1") is not None

    def test_unregister(self) -> None:
        reg = ProviderRegistry()
        reg.register(_inst("p1"))
        assert reg.unregister("p1") is True
        assert reg.unregister("p1") is False

    def test_all_and_available(self) -> None:
        reg = ProviderRegistry()
        from eaip.providers.models import ProviderStatus

        reg.register(_inst("p1"))
        reg.register(
            ProviderInstance(
                name="p2", provider_type="x", endpoint="x", status=ProviderStatus.AVAILABLE
            )
        )
        assert len(reg.all()) == 2
        assert len(reg.available()) == 1

    def test_clear(self) -> None:
        reg = ProviderRegistry()
        reg.register(_inst("p1"))
        reg.clear()
        assert len(reg) == 0

    def test_len_and_contains(self) -> None:
        reg = ProviderRegistry()
        assert len(reg) == 0
        reg.register(_inst("p1"))
        assert len(reg) == 1
        assert "p1" in reg

    def test_observer_on_register(self) -> None:
        reg = ProviderRegistry()
        changes: list[RegistryChange[ProviderInstance]] = []
        reg.observe(changes.append)
        reg.register(_inst("p1"))
        assert len(changes) == 1
        assert changes[0].event is RegistryEvent.REGISTERED

    def test_observer_on_unregister(self) -> None:
        reg = ProviderRegistry()
        reg.register(_inst("p1"))
        changes: list[RegistryChange[ProviderInstance]] = []
        reg.observe(changes.append)
        reg.unregister("p1")
        assert len(changes) == 1
        assert changes[0].event is RegistryEvent.UNREGISTERED
