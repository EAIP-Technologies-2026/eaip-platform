"""Middleware types and implementations for the gateway pipeline."""

from __future__ import annotations

import time
from collections.abc import Awaitable, Callable
from typing import Protocol, runtime_checkable

from eaip.gateway.auth import ApiKeyStore
from eaip.gateway.exceptions import AuthError, RateLimitExceededError
from eaip.gateway.models import ApiRequest, ApiResponse, RateLimitConfig
from eaip.gateway.rate_limiter import RateLimiter
from eaip.logging.context import get_logger

# A handler is the terminal step in the pipeline — it produces a response.
Handler = Callable[[ApiRequest], Awaitable[ApiResponse]]
# The "next" parameter in middleware is a handler that represents the rest of the pipeline.
NextCall = Handler


@runtime_checkable
class Middleware(Protocol):
    """Protocol for gateway middleware.

    Implementations must provide an async ``handle`` method that receives
    the request and a ``next`` callable, and returns an ``ApiResponse``.
    """

    async def handle(self, request: ApiRequest, next_call: NextCall) -> ApiResponse:
        """Process a request, optionally delegating to the next middleware.

        Args:
            request: The incoming API request.
            next_call: The next handler in the pipeline.

        Returns:
            The API response.
        """
        ...


class LoggingMiddleware:
    """Log requests and responses with timing information."""

    def __init__(self) -> None:
        """Initialize the logging middleware."""
        self._log = get_logger("eaip.gateway.middleware.logging")

    async def handle(self, request: ApiRequest, next_call: NextCall) -> ApiResponse:
        """Log the request, delegate, then log the response.

        Args:
            request: The incoming API request.
            next_call: The next handler in the pipeline.

        Returns:
            The API response.
        """
        t0 = time.monotonic()
        self._log.info(
            "gateway.middleware.request_started",
            method=request.method.value,
            path=request.path,
            correlation_id=str(request.correlation_id) if request.correlation_id else None,
        )
        try:
            return await next_call(request)
        finally:
            duration_ms = (time.monotonic() - t0) * 1000
            self._log.info(
                "gateway.middleware.request_completed",
                method=request.method.value,
                path=request.path,
                duration_ms=round(duration_ms, 3),
            )


class MetricsMiddleware:
    """Record basic request metrics (count, duration histogram)."""

    def __init__(self) -> None:
        """Initialize the metrics middleware with zeroed counters."""
        self.request_count: int = 0
        self.durations: list[float] = []

    async def handle(self, request: ApiRequest, next_call: NextCall) -> ApiResponse:
        """Record metrics around the request.

        Args:
            request: The incoming API request.
            next_call: The next handler in the pipeline.

        Returns:
            The API response.
        """
        t0 = time.monotonic()
        try:
            return await next_call(request)
        finally:
            duration_ms = (time.monotonic() - t0) * 1000
            self.request_count += 1
            self.durations.append(duration_ms)


class AuthMiddleware:
    """Validate the API key in the ``Authorization`` header."""

    def __init__(self, key_store: ApiKeyStore) -> None:
        """Initialize the auth middleware with a key store."""
        self._key_store = key_store

    async def handle(self, request: ApiRequest, next_call: NextCall) -> ApiResponse:
        """Validate the ``Authorization`` header.

        Expects a ``Bearer <key_id>:<key>`` format.

        Args:
            request: The incoming API request.
            next_call: The next handler in the pipeline.

        Returns:
            The API response.

        Raises:
            AuthError: If authentication fails.
        """
        auth = request.headers.get("authorization", request.headers.get("Authorization", ""))
        if not auth.startswith("Bearer "):
            raise AuthError("Missing or malformed Authorization header")

        token = auth.removeprefix("Bearer ").strip()
        if ":" not in token:
            raise AuthError("Malformed API key token")

        key_id, _, key = token.partition(":")
        creds = self._key_store.validate_key(key_id, key)

        request = ApiRequest(
            id=request.id,
            method=request.method,
            path=request.path,
            headers=request.headers,
            query_params=request.query_params,
            body=request.body,
            timestamp=request.timestamp,
            correlation_id=request.correlation_id,
            subject_id=creds.name,
        )
        return await next_call(request)


class RateLimitMiddleware:
    """Enforce rate limits per key/subject."""

    def __init__(
        self,
        rate_limiter: RateLimiter,
        default_config: RateLimitConfig | None = None,
    ) -> None:
        """Initialize the rate-limit middleware with a limiter and optional config."""
        self._rate_limiter = rate_limiter
        self._default_config = default_config

    async def handle(self, request: ApiRequest, next_call: NextCall) -> ApiResponse:
        """Check rate limit for the authenticated subject.

        Args:
            request: The incoming API request.
            next_call: The next handler in the pipeline.

        Returns:
            The API response.

        Raises:
            RateLimitExceededError: If the rate limit is exceeded.
        """
        key = request.subject_id or "anonymous"
        config = self._default_config
        if config is not None and not self._rate_limiter.check_limit(key, config):
            raise RateLimitExceededError(
                "Rate limit exceeded",
                context={"subject": key},
            )
        return await next_call(request)


class CorsMiddleware:
    """Handle CORS pre-flight and response headers."""

    def __init__(
        self,
        allowed_origins: tuple[str, ...] = ("*",),
        allowed_methods: tuple[str, ...] = ("GET", "POST", "PUT", "DELETE", "PATCH"),
        allowed_headers: tuple[str, ...] = ("*",),
    ) -> None:
        """Initialize the CORS middleware with allowed origins, methods, and headers."""
        self._allowed_origins = allowed_origins
        self._allowed_methods = allowed_methods
        self._allowed_headers = allowed_headers

    async def handle(self, request: ApiRequest, next_call: NextCall) -> ApiResponse:
        """Add CORS headers and handle pre-flight ``OPTIONS`` requests.

        Args:
            request: The incoming API request.
            next_call: The next handler in the pipeline.

        Returns:
            The API response with CORS headers.
        """
        if request.method.value == "OPTIONS":
            return ApiResponse(
                request_id=request.id,
                status_code=204,
                headers=self._cors_headers(request),
            )

        response = await next_call(request)
        merged = {**response.headers, **self._cors_headers(request)}
        return ApiResponse(
            request_id=response.request_id,
            status_code=response.status_code,
            headers=merged,
            body=response.body,
            duration_ms=response.duration_ms,
        )

    def _cors_headers(self, request: ApiRequest) -> dict[str, str]:
        origin = request.headers.get("origin", request.headers.get("Origin", "*"))
        if "*" not in self._allowed_origins and origin not in self._allowed_origins:
            return {}
        return {
            "Access-Control-Allow-Origin": origin,
            "Access-Control-Allow-Methods": ", ".join(self._allowed_methods),
            "Access-Control-Allow-Headers": ", ".join(self._allowed_headers),
        }


class MiddlewarePipeline:
    """Chain middlewares and run them in order with cleanup in reverse."""

    def __init__(self) -> None:
        """Initialize the pipeline with an empty middleware list."""
        self._middlewares: list[Middleware] = []

    def add(self, middleware: Middleware) -> None:
        """Register a middleware into the pipeline.

        Args:
            middleware: A middleware instance.
        """
        self._middlewares.append(middleware)

    def remove(self, middleware: Middleware) -> None:
        """Remove a previously registered middleware.

        Args:
            middleware: The middleware instance to remove.
        """
        self._middlewares = [m for m in self._middlewares if m is not middleware]

    @property
    def middlewares(self) -> list[Middleware]:
        """Return the list of registered middlewares."""
        return list(self._middlewares)

    async def run(
        self,
        request: ApiRequest,
        handler: Handler,
    ) -> ApiResponse:
        """Run the request through the pipeline.

        Middlewares are invoked in registration order. Each receives the
        request and a ``next`` callable that represents the rest of the
        pipeline, ending with the terminal *handler*.

        Args:
            request: The incoming API request.
            handler: The terminal handler that produces the response.

        Returns:
            The API response.
        """
        chain = self._build_chain(handler)
        return await chain(request)

    def _build_chain(self, handler: Handler) -> Handler:
        chain = handler
        for mw in reversed(self._middlewares):
            mw_instance = mw
            prev = chain

            async def _next(
                req: ApiRequest, m: Middleware = mw_instance, nxt: Handler = prev
            ) -> ApiResponse:
                return await m.handle(req, nxt)

            chain = _next
        return chain


__all__ = [
    "AuthMiddleware",
    "CorsMiddleware",
    "Handler",
    "LoggingMiddleware",
    "MetricsMiddleware",
    "Middleware",
    "MiddlewarePipeline",
    "NextCall",
    "RateLimitMiddleware",
]
