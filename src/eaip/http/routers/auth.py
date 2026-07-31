from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Request, Response
from starlette.status import HTTP_401_UNAUTHORIZED

from eaip.auth.auth_providers import AuthenticationService
from eaip.auth.models import AuthenticationRequest
from eaip.logging.context import get_logger

router = APIRouter(tags=["auth"])
log = get_logger("eaip.http.routers.auth")


def _get_auth(request: Request) -> AuthenticationService:
    lifecycle = request.app.state.lifecycle
    return lifecycle.platform.container.resolve(AuthenticationService)


def _extract_token(request: Request) -> str:
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        return auth_header[7:]
    cookie = request.cookies.get("eaip_session", "")
    if cookie:
        return cookie
    raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="Missing or invalid session")


def _set_session_cookie(response: Response, token: str) -> None:
    import os

    secure = os.environ.get("EAIP_ENVIRONMENT") == "production"
    response.set_cookie(
        key="eaip_session",
        value=token,
        httponly=True,
        samesite="lax",
        secure=secure,
        max_age=86400,
        path="/",
    )


@router.post("/auth/login")
async def login(request: Request, body: dict[str, Any], response: Response):
    auth = _get_auth(request)
    username = body.get("username", body.get("email", ""))
    password = body.get("password", "")

    if not username or not password:
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="Missing credentials")

    auth_request = AuthenticationRequest(
        id=username,
        provider="mock",
        credentials={"username": username, "password": password},
    )
    result = await auth.authenticate(auth_request)
    if not result.success:
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail=result.error)

    _set_session_cookie(response, result.token)

    return {
        "token": result.token,
        "refresh_token": result.refresh_token,
        "user": {
            "id": result.identity.get("sub", username),
            "name": result.identity.get("name", username),
            "email": result.identity.get("email", f"{username}@example.com"),
            "roles": ["admin", "user"],
        },
    }


@router.post("/auth/logout")
async def logout(request: Request, response: Response, body: dict[str, Any] | None = None):
    auth = _get_auth(request)
    token = ""
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]
    cookie = request.cookies.get("eaip_session", "")
    if cookie:
        token = cookie
    if token:
        await auth.logout(token)
    response.delete_cookie("eaip_session", path="/")
    return {"status": "ok"}


@router.post("/auth/refresh")
async def refresh(request: Request, body: dict[str, Any]):
    auth = _get_auth(request)
    refresh_token = body.get("refresh_token", "")
    if not refresh_token:
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="Missing refresh_token")

    token_service = auth.token_service
    try:
        new_access, new_refresh = await token_service.refresh_token(refresh_token)
        access_str = await token_service.get_token_string(new_access.id) or ""
        return {
            "token": access_str,
            "refresh_token": new_refresh.id,
        }
    except Exception as e:
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail=str(e))


@router.get("/users/me")
async def get_current_user(request: Request):
    auth = _get_auth(request)
    token = _extract_token(request)
    user = await auth.get_current_user(token)
    if user is None:
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

    return {
        "id": user.get("sub", ""),
        "name": user.get("name", user.get("sub", "")),
        "email": user.get("email", ""),
        "roles": ["admin", "user"],
    }


@router.get("/auth/me")
async def auth_me(request: Request):
    auth = _get_auth(request)
    token = _extract_token(request)
    user = await auth.get_current_user(token)
    if user is None:
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

    return {
        "user": {
            "id": user.get("sub", ""),
            "name": user.get("name", user.get("sub", "")),
            "email": user.get("email", ""),
            "roles": ["admin", "user"],
        }
    }


@router.put("/users/me")
async def update_current_user(request: Request, body: dict[str, Any]):
    auth = _get_auth(request)
    token = _extract_token(request)
    user = await auth.get_current_user(token)
    if user is None:
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

    return {
        "id": user.get("sub", ""),
        "name": body.get("name", user.get("name", user.get("sub", ""))),
        "email": body.get("email", user.get("email", "")),
        "roles": ["admin", "user"],
    }
