"""Tests for :mod:`eaip.exceptions`."""

from __future__ import annotations

import pytest

from eaip.exceptions import (
    ConfigurationError,
    EAIPError,
    ErrorCode,
    ErrorSeverity,
    LifecycleError,
    NotFoundError,
    ValidationError,
)
from eaip.exceptions.domain import (
    DependencyCycleError,
    DuplicateRegistrationError,
    PluginContractViolationError,
)


def test_base_error_carries_code_and_context() -> None:
    err = EAIPError("boom", context={"x": 1})
    assert err.code is ErrorCode.UNKNOWN
    assert err.severity is ErrorSeverity.ERROR
    assert err.context == {"x": 1}


def test_with_context_is_immutable() -> None:
    err = ConfigurationError("nope", context={"a": 1})
    enriched = err.with_context(b=2)
    assert err.context == {"a": 1}
    assert enriched.context == {"a": 1, "b": 2}
    assert err.context is not enriched.context


def test_subclasses_have_default_codes() -> None:
    assert ConfigurationError("x").code is ErrorCode.CONFIGURATION_INVALID
    assert ValidationError("x").code is ErrorCode.VALIDATION_FAILED
    assert NotFoundError("x").code is ErrorCode.NOT_FOUND
    assert LifecycleError("x").code is ErrorCode.LIFECYCLE_FORBIDDEN
    assert DuplicateRegistrationError("x").code is ErrorCode.REGISTRY_DUPLICATE
    assert DependencyCycleError("x").code is ErrorCode.DEPENDENCY_CYCLE
    assert PluginContractViolationError("x").code is ErrorCode.PLUGIN_CONTRACT_VIOLATION


def test_to_dict_is_json_safe() -> None:
    err = ValidationError("bad input", context={"field": "name"})
    payload = err.to_dict()
    assert payload["type"] == "ValidationError"
    assert payload["code"] == ErrorCode.VALIDATION_FAILED.value
    assert payload["context"] == {"field": "name"}
    assert payload["cause"] is None


def test_cause_is_chained() -> None:
    original = RuntimeError("root")
    err = EAIPError("wrapped", cause=original)
    assert err.__cause__ is original


def test_codes_are_unique_and_stable() -> None:
    values = [c.value for c in ErrorCode]
    assert len(values) == len(set(values))
    assert all(v.startswith("EAIP-") for v in values)
