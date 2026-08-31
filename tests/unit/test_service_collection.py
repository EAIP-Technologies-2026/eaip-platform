"""Tests for ServiceCollection."""

from __future__ import annotations

from eaip.dependency_injection.scope import Scope
from eaip.services.collection import ServiceCollection
from eaip.services.descriptors import ServiceLifetime

# ---------------------------------------------------------------------------
# Stub types
# ---------------------------------------------------------------------------


class IEngine:
    pass


class Engine(IEngine):
    pass


class ElectricEngine(Engine):
    pass


class Logger:
    def __init__(self) -> None:
        self.messages: list[str] = []


class TestServiceCollection:
    def test_empty_collection(self):
        services = ServiceCollection()
        assert services.count == 0
        assert services.descriptors == []

    def test_add_singleton_default_impl(self):
        services = ServiceCollection()
        services.add_singleton(IEngine)
        desc = services.get_descriptor(IEngine)
        assert desc is not None
        assert desc.lifetime is ServiceLifetime.SINGLETON
        assert desc.implementation_type is IEngine

    def test_add_singleton_with_impl(self):
        services = ServiceCollection()
        services.add_singleton(IEngine, Engine)
        desc = services.get_descriptor(IEngine)
        assert desc is not None
        assert desc.implementation_type is Engine

    def test_add_scoped(self):
        services = ServiceCollection()
        services.add_scoped(IEngine, Engine)
        desc = services.get_descriptor(IEngine)
        assert desc is not None
        assert desc.lifetime is ServiceLifetime.SCOPED

    def test_add_transient(self):
        services = ServiceCollection()
        services.add_transient(IEngine)
        desc = services.get_descriptor(IEngine)
        assert desc.lifetime is ServiceLifetime.TRANSIENT

    def test_add_instance(self):
        services = ServiceCollection()
        engine = Engine()
        services.add_instance(IEngine, engine)
        desc = services.get_descriptor(IEngine)
        assert desc is not None
        assert desc.instance is engine
        assert desc.lifetime is ServiceLifetime.SINGLETON

    def test_add_factory(self):
        services = ServiceCollection()
        services.add_factory(IEngine, lambda _c: Engine(), lifetime=ServiceLifetime.TRANSIENT)
        desc = services.get_descriptor(IEngine)
        assert desc is not None
        assert desc.factory is not None
        assert desc.lifetime is ServiceLifetime.TRANSIENT

    def test_has(self):
        services = ServiceCollection()
        services.add_singleton(IEngine)
        assert services.has(IEngine)
        assert not services.has(Logger)

    def test_get_descriptor_returns_none_for_missing(self):
        services = ServiceCollection()
        assert services.get_descriptor(IEngine) is None

    def test_add_collection_merges(self):
        s1 = ServiceCollection()
        s1.add_singleton(IEngine, Engine)

        s2 = ServiceCollection()
        s2.add_singleton(Logger)

        s1.add_collection(s2)
        assert s1.has(IEngine)
        assert s1.has(Logger)
        assert s1.count == 2

    def test_add_collection_overwrites(self):
        s1 = ServiceCollection()
        s1.add_singleton(IEngine, Engine)

        s2 = ServiceCollection()
        s2.add_singleton(IEngine, ElectricEngine)

        s1.add_collection(s2)
        desc = s1.get_descriptor(IEngine)
        assert desc is not None
        assert desc.implementation_type is ElectricEngine

    def test_build_container_singleton(self):
        services = ServiceCollection()
        services.add_singleton(Logger)
        container = services.build_container()
        logger1 = container.resolve(Logger)
        logger2 = container.resolve(Logger)
        assert logger1 is logger2

    def test_build_container_transient(self):
        services = ServiceCollection()
        services.add_transient(Logger)
        container = services.build_container()
        logger1 = container.resolve(Logger)
        logger2 = container.resolve(Logger)
        assert logger1 is not logger2

    def test_build_container_instance(self):
        services = ServiceCollection()
        engine = Engine()
        services.add_instance(IEngine, engine)
        container = services.build_container()
        resolved = container.resolve(IEngine)
        assert resolved is engine

    def test_build_container_factory(self):
        services = ServiceCollection()
        services.add_factory(IEngine, lambda _c: ElectricEngine())
        container = services.build_container()
        resolved = container.resolve(IEngine)
        assert isinstance(resolved, ElectricEngine)

    def test_build_container_scope_mapping(self):
        services = ServiceCollection()
        services.add_scoped(Logger)
        container = services.build_container()
        # Scoped in a root container behaves like singleton
        logger1 = container.resolve(Logger)
        logger2 = container.resolve(Logger)
        assert logger1 is logger2

    def test_descriptors_returns_all(self):
        services = ServiceCollection()
        services.add_singleton(IEngine)
        services.add_singleton(Logger)
        assert len(services.descriptors) == 2

    def test_add_returns_self_for_chaining(self):
        services = ServiceCollection()
        result = services.add_singleton(IEngine)
        assert result is services

    def test_service_lifetime_to_scope(self):
        assert ServiceLifetime.SINGLETON.to_scope() is Scope.SINGLETON
        assert ServiceLifetime.SCOPED.to_scope() is Scope.SCOPED
        assert ServiceLifetime.TRANSIENT.to_scope() is Scope.TRANSIENT
