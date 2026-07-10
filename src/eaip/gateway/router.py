"""API router — endpoint registry and request dispatch."""

from __future__ import annotations

import time

from eaip.gateway.events import (
    ApiRequestProcessed,
    EndpointRegistered,
    EndpointUnregistered,
)
from eaip.gateway.exceptions import EndpointNotFoundError
from eaip.gateway.middleware import MiddlewarePipeline
from eaip.gateway.models import ApiRequest, ApiResponse, Endpoint, HttpMethod
from eaip.logging.context import get_logger


class ApiRouter:
    """Registers API endpoints and dispatches requests through a middleware pipeline.

    Usage::

        router = ApiRouter()
        router.register_endpoint(Endpoint(...))
        response = await router.dispatch(request)
    """

    def __init__(self, pipeline: MiddlewarePipeline | None = None) -> None:
        """Initialize the router with an empty endpoint map."""
        self._endpoints: dict[tuple[str, HttpMethod], Endpoint] = {}
        self._pipeline = pipeline or MiddlewarePipeline()
        self._log = get_logger("eaip.gateway.router")

    @property
    def pipeline(self) -> MiddlewarePipeline:
        """Return the middleware pipeline."""
        return self._pipeline

    def register_endpoint(self, endpoint: Endpoint) -> None:
        """Register an endpoint.

        Args:
            endpoint: The endpoint to register.
        """
        key = (endpoint.path, endpoint.method)
        self._endpoints[key] = endpoint
        self._log.info(
            "gateway.router.endpoint.registered",
            path=endpoint.path,
            method=endpoint.method.value,
        )
        EndpointRegistered(path=endpoint.path, method=endpoint.method.value)

    def unregister_endpoint(self, path: str, method: HttpMethod) -> None:
        """Remove a previously registered endpoint.

        Args:
            path: The endpoint path.
            method: The HTTP method.
        """
        key = (path, method)
        old = self._endpoints.pop(key, None)
        if old is not None:
            self._log.info(
                "gateway.router.endpoint.unregistered",
                path=path,
                method=method.value,
            )
            EndpointUnregistered(path=path, method=method.value)

    def get_endpoint(self, path: str, method: HttpMethod) -> Endpoint | None:
        """Look up a registered endpoint by path and method.

        Args:
            path: The endpoint path.
            method: The HTTP method.

        Returns:
            The matching endpoint, or ``None``.
        """
        return self._endpoints.get((path, method))

    def list_endpoints(self) -> list[Endpoint]:
        """Return all registered endpoints (for discovery)."""
        return list(self._endpoints.values())

    async def dispatch(self, request: ApiRequest) -> ApiResponse:
        """Find the handler for *request* and invoke the middleware pipeline.

        Args:
            request: The incoming API request.

        Returns:
            The API response after pipeline processing.
        """
        t0 = time.monotonic()

        endpoint = self.get_endpoint(request.path, request.method)
        if endpoint is None:
            raise EndpointNotFoundError(
                f"No endpoint registered for {request.method} {request.path}",
                context={
                    "path": request.path,
                    "method": request.method.value,
                },
            )

        async def handler(req: ApiRequest) -> ApiResponse:
            result = await endpoint.handler(req)
            if isinstance(result, ApiResponse):
                return result
            return ApiResponse(
                request_id=req.id,
                status_code=200,
                body=result,
            )

        response = await self._pipeline.run(request, handler)

        duration_ms = (time.monotonic() - t0) * 1000
        response = ApiResponse(
            request_id=response.request_id,
            status_code=response.status_code,
            headers=response.headers,
            body=response.body,
            duration_ms=duration_ms,
        )

        ApiRequestProcessed(
            request_id=request.id,
            path=request.path,
            method=request.method.value,
            status_code=response.status_code,
            duration_ms=duration_ms,
        )

        return response


__all__ = ["ApiRouter"]
