"""Shared, zero-dependency primitives used across the entire platform.

The :mod:`eaip.shared` package is the lowest-level layer of the Foundation.
It must **not** depend on any other ``eaip`` subpackage; every other layer is
free to depend on it.

Re-exports the most commonly used primitives so callers can write
``from eaip.shared import Result`` rather than memorising sub-paths.
"""

from __future__ import annotations

from eaip.shared.identifiers import ComponentId, CorrelationId, RunId, Slug
from eaip.shared.repository import InMemoryRepository
from eaip.shared.result import Err, Ok, Result
from eaip.shared.sandbox import safe_exec
from eaip.shared.sentinels import UNSET, UnsetType
from eaip.shared.tenant import (
    TenantAwareRepository,
    TenantContext,
    get_current_tenant,
    set_current_tenant,
)
from eaip.shared.time import Clock, Duration, utc_now
from eaip.shared.types import JSONArray, JSONObject, JSONValue

__all__ = [
    "UNSET",
    "Clock",
    "ComponentId",
    "CorrelationId",
    "Duration",
    "Err",
    "InMemoryRepository",
    "JSONArray",
    "JSONObject",
    "JSONValue",
    "Ok",
    "Result",
    "RunId",
    "Slug",
    "TenantAwareRepository",
    "TenantContext",
    "UnsetType",
    "get_current_tenant",
    "safe_exec",
    "set_current_tenant",
    "utc_now",
]
