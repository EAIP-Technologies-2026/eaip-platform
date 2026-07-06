"""Tests for :mod:`eaip.application.composition`."""

from __future__ import annotations

import pytest

from eaip.application.composition import ApplicationCompositionRoot
from eaip.config.sources import DictSource, EnvSource
from eaip.dependency_injection.container import Container
from eaip.runtime.context import RuntimeContext
from eaip.runtime.module import BaseRuntimeModule
from eaip.settings.core_settings import PlatformSettings


class _TestModule(BaseRuntimeModule):
    module_name = "test-module"

    async def on_start(self, host, ctx: RuntimeContext) -> None:
        pass


class TestApplicationCompositionRootConstruction:
    def test_create(self) -> None:
        root = ApplicationCompositionRoot()
        assert root is not None
        assert root.platform is None
        assert root.kernel is None
        assert root.container is None
        assert not root.is_composed

    def test_config_source_initial_none(self) -> None:
        root = ApplicationCompositionRoot()
        assert root.config_source() is None


class TestApplicationCompositionRootConfigLoading:
    def test_load_config_with_source(self) -> None:
        root = ApplicationCompositionRoot()
        source = DictSource({"core": {"app_name": "test"}})
        root.load_config(source=source)
        assert root.config_source() is source

    def test_load_config_with_raw(self) -> None:
        root = ApplicationCompositionRoot()
        root.load_config(raw={"key": "value"})
        source = root.config_source()
        assert source is not None
        data = source.load()
        assert data["key"] == "value"

    def test_load_config_with_env_default(self) -> None:
        root = ApplicationCompositionRoot()
        root.load_config()
        source = root.config_source()
        assert isinstance(source, EnvSource)
        assert source._prefix == "EAIP_"

    def test_load_config_idempotent(self) -> None:
        root = ApplicationCompositionRoot()
        source1 = DictSource({"a": 1})
        source2 = DictSource({"b": 2})
        root.load_config(source=source1)
        root.load_config(source=source2)
        assert root.config_source() is source2


class TestApplicationCompositionRootPlatformBuilding:
    def test_build_platform_minimal(self) -> None:
        root = ApplicationCompositionRoot()
        platform = root.build_platform(configure_logging=False)
        assert platform is not None
        assert root.platform is platform
        assert root.container is not None
        assert root.is_composed

    def test_build_platform_with_settings(self) -> None:
        root = ApplicationCompositionRoot()
        settings = PlatformSettings()
        platform = root.build_platform(settings=settings, configure_logging=False)
        assert platform is not None
        assert platform.settings is settings

    def test_build_platform_with_container(self) -> None:
        root = ApplicationCompositionRoot()
        container = Container()
        platform = root.build_platform(container=container, configure_logging=False)
        assert platform is not None

    def test_build_platform_twice(self) -> None:
        root = ApplicationCompositionRoot()
        p1 = root.build_platform(configure_logging=False)
        p2 = root.build_platform(configure_logging=False)
        assert p1 is not p2  # each call creates a new platform


class TestApplicationCompositionRootKernelBuilding:
    def test_build_kernel_without_platform_raises(self) -> None:
        root = ApplicationCompositionRoot()
        with pytest.raises(RuntimeError, match="build_platform"):
            root.build_kernel()

    def test_build_kernel_empty(self) -> None:
        root = ApplicationCompositionRoot()
        root.build_platform(configure_logging=False)
        kernel = root.build_kernel()
        assert kernel is not None
        assert root.kernel is kernel

    def test_build_kernel_with_module(self) -> None:
        root = ApplicationCompositionRoot()
        root.build_platform(configure_logging=False)

        module = _TestModule()
        kernel = root.build_kernel(modules=[module])
        assert kernel is not None
        assert "test-module" in kernel.host.module_names


class TestApplicationCompositionRootWiring:
    def test_wire_without_platform_raises(self) -> None:
        root = ApplicationCompositionRoot()
        with pytest.raises(RuntimeError, match="build_platform"):
            root.wire()

    def test_wire_succeeds(self) -> None:
        root = ApplicationCompositionRoot()
        root.build_platform(configure_logging=False)
        root.wire()
        assert root.is_composed


class TestApplicationCompositionRootConvenience:
    def test_create_minimal(self) -> None:
        root = ApplicationCompositionRoot()
        platform, kernel = root.create(configure_logging=False)
        assert platform is not None
        assert kernel is None

    def test_create_with_modules(self) -> None:
        root = ApplicationCompositionRoot()
        module = _TestModule()
        platform, kernel = root.create(
            configure_logging=False,
            modules=[module],
        )
        assert platform is not None
        assert kernel is not None
        assert "test-module" in kernel.host.module_names

    def test_create_with_source(self) -> None:
        root = ApplicationCompositionRoot()
        source = DictSource({"test": "value"})
        platform, _kernel = root.create(source=source, configure_logging=False)
        assert platform is not None
