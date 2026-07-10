"""Internal API gateway/middleware layer for the EAIP platform.

Provides endpoint registration, middleware pipeline (auth, rate limiting,
logging, metrics), request/response wrapping, and integration with existing
platform components.
"""

from __future__ import annotations

from eaip.gateway.auth import ApiKeyStore
from eaip.gateway.events import (
    ApiRequestProcessed,
    EndpointRegistered,
    EndpointUnregistered,
)
from eaip.gateway.exceptions import (
    AuthError,
    EndpointNotFoundError,
    GatewayError,
    RateLimitExceededError,
)
from eaip.gateway.health import GatewayHealthCheck
from eaip.gateway.integration import GatewayRuntimeModule
from eaip.gateway.middleware import (
    AuthMiddleware,
    CorsMiddleware,
    LoggingMiddleware,
    MetricsMiddleware,
    Middleware,
    MiddlewarePipeline,
    RateLimitMiddleware,
)
from eaip.gateway.models import (
    ApiKeyCredentials,
    ApiRequest,
    ApiResponse,
    Endpoint,
    HttpMethod,
    RateLimitConfig,
)
from eaip.gateway.router import ApiRouter

__all__ = [
    "ApiKeyCredentials",
    "ApiKeyStore",
    "ApiRequest",
    "ApiRequestProcessed",
    "ApiResponse",
    "ApiRouter",
    "AuthError",
    "AuthMiddleware",
    "CorsMiddleware",
    "Endpoint",
    "EndpointNotFoundError",
    "EndpointRegistered",
    "EndpointUnregistered",
    "GatewayError",
    "GatewayHealthCheck",
    "GatewayRuntimeModule",
    "HttpMethod",
    "LoggingMiddleware",
    "MetricsMiddleware",
    "Middleware",
    "MiddlewarePipeline",
    "RateLimitConfig",
    "RateLimitExceededError",
    "RateLimitMiddleware",
]
