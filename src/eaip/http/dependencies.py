from __future__ import annotations

from typing import Any

from fastapi import HTTPException, Request
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


def _extract_token(request: Request) -> str:
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        return auth_header[7:]
    cookie = request.cookies.get("eaip_session", "")
    if cookie:
        return cookie
    raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="Missing or invalid session")
