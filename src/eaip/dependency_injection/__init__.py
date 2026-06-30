"""A small, dependency-free DI container with explicit scopes."""

from __future__ import annotations

from eaip.dependency_injection.container import Container, Provider
from eaip.dependency_injection.scope import Scope

__all__ = ["Container", "Provider", "Scope"]
