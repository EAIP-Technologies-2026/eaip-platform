"""Tests for ServiceProvider."""

from __future__ import annotations

import pytest

from eaip.dependency_injection.container import Container
from eaip.exceptions.domain import NotFoundError
from eaip.services.provider import ServiceProvider


class IEngine:
    pass


class Engine(IEngine):
    pass


class TestServiceProvider:
    def setup_method(self) -> None:
        self._container = Container()
        self._provider = ServiceProvider(self._container)

    def test_get_service_returns_none_for_unknown(self):
        result = self._provider.get_service(IEngine)
        assert result is None

    def test_get_service_returns_instance(self):
        self._container.register(IEngine, Engine)
        result = self._provider.get_service(IEngine)
        assert isinstance(result, Engine)

    def test_get_required_service_returns_instance(self):
        self._container.register(IEngine, Engine)
        result = self._provider.get_required_service(IEngine)
        assert isinstance(result, Engine)

    def test_get_required_service_raises_for_unknown(self):
        with pytest.raises(NotFoundError, match="IEngine"):
            self._provider.get_required_service(IEngine)

    def test_has_service_returns_true_for_registered(self):
        self._container.register(IEngine, Engine)
        assert self._provider.has_service(IEngine)

    def test_has_service_returns_false_for_unregistered(self):
        assert not self._provider.has_service(IEngine)

    def test_container_property(self):
        assert self._provider.container is self._container
