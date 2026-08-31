"""Tests for :mod:`eaip.apiext.integration`."""

from __future__ import annotations

from typing import Any

from eaip.apiext.integration import ApiExtRuntimeModule


class _MockHealth:
    def __init__(self) -> None:
        self._checks: dict[str, Any] = {}

    def register(self, check: Any) -> None:
        self._checks[check.name] = check


class _MockPlatform:
    def __init__(self) -> None:
        self.health = _MockHealth()


class _MockKernel:
    def __init__(self) -> None:
        self._platform = _MockPlatform()

    @property
    def platform(self) -> _MockPlatform:
        return self._platform


class TestApiExtRuntimeModule:
    async def test_startup_duration_starts_zero(self) -> None:
        module = ApiExtRuntimeModule()
        assert module.startup_duration == 0.0

    async def test_start_registers_health_check(self) -> None:
        module = ApiExtRuntimeModule()
        kernel: Any = _MockKernel()
        await module.start(kernel)
        assert "apiext" in kernel.platform.health._checks

    async def test_start_creates_subcomponents(self) -> None:
        module = ApiExtRuntimeModule()
        assert module.composer is not None
        assert module.cache is not None
        assert module.rate_limit_engine is not None
        assert module.transformer is not None

    async def test_stop_clears_cache(self) -> None:
        module = ApiExtRuntimeModule()
        kernel: Any = _MockKernel()
        await module.start(kernel)
        await module.cache.set("key", {"data": "test"}, ttl=60.0)
        assert await module.cache.get("key") is not None
        await module.stop(kernel)
        assert await module.cache.get("key") is None

    async def test_stop_does_not_raise(self) -> None:
        module = ApiExtRuntimeModule()
        kernel: Any = _MockKernel()
        await module.start(kernel)
        await module.stop(kernel)

    async def test_custom_components(self) -> None:
        from eaip.apiext.caching import ResponseCache
        from eaip.apiext.composition import ApiComposer
        from eaip.apiext.rate_limit_policy import RateLimitPolicyEngine
        from eaip.apiext.transforms import ResponseTransformer

        composer = ApiComposer()
        cache = ResponseCache(max_size=50)
        rl_engine = RateLimitPolicyEngine()
        transformer = ResponseTransformer()

        module = ApiExtRuntimeModule(
            composer=composer,
            cache=cache,
            rate_limit_engine=rl_engine,
            transformer=transformer,
        )
        assert module.composer is composer
        assert module.cache is cache
        assert module.rate_limit_engine is rl_engine
        assert module.transformer is transformer
