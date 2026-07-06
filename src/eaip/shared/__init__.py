"""Shared, zero-dependency primitives used across the entire platform.

The :mod:`eaip.shared` package is the lowest-level layer of the Foundation.
It must **not** depend on any other ``eaip`` subpackage; every other layer is
free to depend on it.

Re-exports the most commonly used primitives so callers can write
``from eaip.shared import Result`` rather than memorising sub-paths.
"""

from __future__ import annotations

from eaip.shared.identifiers import ComponentId, CorrelationId, RunId, Slug
from eaip.shared.result import Err, Ok, Result
from eaip.shared.sentinels import UNSET, UnsetType
from eaip.shared.time import Clock, Duration, utc_now
from eaip.shared.types import JSONArray, JSONObject, JSONValue

__all__ = [
    # identifiers
    "ComponentId",
    "CorrelationId",
    "RunId",
    "Slug",
    # result
    "Err",
    "Ok",
    "Result",
    # sentinels
    "UNSET",
    "UnsetType",
    # time
    "Clock",
    "Duration",
    "utc_now",
    # types
    "JSONArray",
    "JSONObject",
    "JSONValue",
]
