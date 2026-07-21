"""HTTP Request Router — route management, request matching, middleware dispatch."""

from __future__ import annotations

from eaip.httprouter.events import (
    RequestRouted,
    RouteDeactivated,
    RouteRegistered,
    RouteUpdated,
)
from eaip.httprouter.exceptions import (
    RouteNotFoundError,
    RouterError,
)
from eaip.httprouter.health import HTTPRouterHealthCheck
from eaip.httprouter.integration import HTTPRouterRuntimeModule
from eaip.httprouter.models import Route, RouteMatch, RouterConfig
from eaip.httprouter.router import HTTPRequestRouter

__all__ = [
    "HTTPRequestRouter",
    "HTTPRouterHealthCheck",
    "HTTPRouterRuntimeModule",
    "RequestRouted",
    "Route",
    "RouteDeactivated",
    "RouteMatch",
    "RouteNotFoundError",
    "RouteRegistered",
    "RouteUpdated",
    "RouterConfig",
    "RouterError",
]
