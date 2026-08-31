from __future__ import annotations

import asyncio

from eaip.providers.integration import ProviderRuntimeModule
from eaip.providers.models import ModelCapability, ModelFeature, ProviderInstance


class _MockHealth:
    def __init__(self) -> None:
        self._checks: dict = {}

    def register(self, check) -> None:
        self._checks[check.name] = check

    def registered(self) -> list[str]:
        return sorted(self._checks)


class _MockCapabilities:
    def __init__(self) -> None:
        self._caps: list = []

    def register(self, cap) -> None:
        self._caps.append(cap)


class _MockPlatform:
    def __init__(self) -> None:
        self._health = _MockHealth()
        self._capabilities = _MockCapabilities()

    @property
    def health(self):
        return self._health

    @property
    def capabilities(self):
        return self._capabilities

    @property
    def events(self):
        return None


class _MockKernel:
    def __init__(self) -> None:
        self._platform = _MockPlatform()

    @property
    def platform(self):
        return self._platform


class TestProviderRuntimeModule:
    def test_start_stop_lifecycle(self) -> None:
        registry = type(
            "reg",
            (object,),
            {"all": lambda self: [], "register": lambda self, *a: None, "__len__": lambda self: 0},
        )()
        module = ProviderRuntimeModule(registry=registry)
        kernel = _MockKernel()
        asyncio.run(module.start(kernel))
        assert module.startup_duration >= 0
        assert module.selector is not None
        asyncio.run(module.stop(kernel))

    def test_registers_capabilities(self) -> None:
        mc = ModelCapability(
            model_id="llama3",
            provider="ollama",
            features=(ModelFeature.CHAT, ModelFeature.STREAMING),
        )
        inst = ProviderInstance(
            name="ollama",
            provider_type="ollama",
            endpoint="http://localhost:11434",
            default_model="llama3",
            models=(mc,),
        )
        registry = type(
            "reg",
            (object,),
            {
                "all": lambda self: [inst],
                "register": lambda self, i, **kw: None,
                "__len__": lambda self: 1,
            },
        )()
        module = ProviderRuntimeModule(registry=registry)
        kernel = _MockKernel()
        asyncio.run(module.start(kernel))
        caps = kernel.platform._capabilities._caps
        assert len(caps) == 1
        assert caps[0].name == "provider:ollama:llama3"

    def test_selector_raises_before_start(self) -> None:
        module = ProviderRuntimeModule()
        try:
            _ = module.selector
            raise AssertionError("expected RuntimeError")
        except RuntimeError:
            pass

    def test_registers_health_check(self) -> None:
        module = ProviderRuntimeModule()
        kernel = _MockKernel()
        asyncio.run(module.start(kernel))
        assert "providers" in kernel.platform.health.registered()
        asyncio.run(module.stop(kernel))
