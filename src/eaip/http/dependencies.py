from __future__ import annotations

from typing import Annotated, Any

from fastapi import Depends, HTTPException, Request
from starlette.status import HTTP_401_UNAUTHORIZED

from eaip.auth.auth_providers import AuthenticationService


async def get_current_user(request: Request) -> dict[str, Any]:
    auth: AuthenticationService = request.app.state.lifecycle.platform.container.resolve(
        AuthenticationService
    )
    token = _extract_token(request)
    user = await auth.get_current_user(token)
    if user is None:
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
    return user


CurrentUser = Annotated[dict[str, Any], Depends(get_current_user)]


async def get_tenant_id(user: CurrentUser) -> str:
    """Extract tenant_id (organization_id) from the current user.

    Honors the authenticated identity's tenant claim so every router that
    depends on this resolves the SAME tenant as claim-based routers
    (e.g. kgraph) — one tenant resolution rule across the API.
    """
    return (
        user.get("organization_id")
        or user.get("tenant_id")
        or user.get("tenant")
        or "default"
    )


def _extract_token(request: Request) -> str:
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        return auth_header[7:]
    cookie = request.cookies.get("eaip_session", "")
    if cookie:
        return cookie
    raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="Missing or invalid session")
