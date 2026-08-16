from __future__ import annotations

import asyncio
import json
import uuid
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from eaip.events.bus import EventBus, Subscription
from eaip.events.event import DomainEvent
from eaip.logging.context import get_logger
from eaip.ws.connection_manager import ConnectionManager
from eaip.ws.models import WebSocketConnection
from eaip.ws.push_service import PushService

router = APIRouter(tags=["websocket"])
log = get_logger("eaip.http.routers.websocket")


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    from eaip.auth.auth_providers import AuthenticationService
    
    # We must accept the socket to read headers/params or we can check before accepting.
    # Actually, we should check token first.
    token = websocket.query_params.get("token") or websocket.headers.get("Authorization", "").replace("Bearer ", "") or websocket.cookies.get("eaip_session")
    
    if not token:
        await websocket.close(code=1008, reason="Unauthorized")
        log.warning("websocket.rejected_missing_token")
        return

    await websocket.accept()
    log.info("websocket.connected")
    
    lifecycle = websocket.app.state.lifecycle
    
    auth_service: AuthenticationService | None = None
    try:
        auth_service = lifecycle.platform.container.resolve(AuthenticationService)
    except Exception:
        pass
        
    user = None
    if auth_service:
        user = await auth_service.get_current_user(token)
        if not user:
            await websocket.close(code=1008, reason="Unauthorized")
            log.warning("websocket.rejected_invalid_token")
            return

    lifecycle = websocket.app.state.lifecycle
    event_bus: EventBus = lifecycle.platform.events
    push_service: PushService | None = None
    conn_mgr: ConnectionManager | None = None

    try:
        push_service = lifecycle.platform.container.try_resolve(PushService)
    except Exception:
        pass
    try:
        conn_mgr = lifecycle.platform.container.try_resolve(ConnectionManager)
    except Exception:
        pass

    connection_id = f"ws-{uuid.uuid4().hex[:12]}"
    subscribed_channels: set[str] = set()
    running = True

    def socket_send(data: str) -> None:
        if running:
            try:
                asyncio.ensure_future(websocket.send_text(data))
            except Exception:
                pass

    # Register with push service for active delivery
    if push_service:
        push_service.register_socket(connection_id, socket_send)

    user_id = user.get("id", "anonymous") if user else "anonymous"
    tenant_id = user.get("tenant_id", "default") if user else "default"

    # Register with connection manager
    if conn_mgr:
        ws_conn = WebSocketConnection(
            id=connection_id,
            channel="global",
            user_id=user_id,
            metadata={
                "remote_addr": websocket.client.host if websocket.client else "unknown",
                "tenant_id": tenant_id
            },
        )
        conn_mgr.register(ws_conn)

    async def event_listener(event: DomainEvent) -> None:
        if not running:
            return
        try:
            module = type(event).__module__
            if "agents" in module:
                event_channel = "agent"
            elif "workflow" in module:
                event_channel = "workflow"
            elif "mission" in module:
                event_channel = "mission"
            elif "knowledge" in module:
                event_channel = "knowledge"
            elif "auth" in module:
                event_channel = "auth"
            else:
                event_channel = "system"

            if (
                subscribed_channels
                and event_channel not in subscribed_channels
                and "all" not in subscribed_channels
            ):
                return

            data = {
                "event_type": type(event).__name__,
                "event_data": event.model_dump() if hasattr(event, "model_dump") else str(event),
            }
            await websocket.send_json({"channel": event_channel, "data": data})
        except Exception:
            pass

    sub: Subscription[DomainEvent] | None = None
    try:
        sub = event_bus.subscribe(DomainEvent, event_listener)
        log.info("websocket.subscribed_event_bus")
    except Exception as e:
        log.warning("websocket.subscribe_failed", error=str(e))

    async def heartbeat():
        while running:
            try:
                await asyncio.sleep(30)
                if conn_mgr:
                    try:
                        conn_mgr.heartbeat(connection_id)
                    except Exception:
                        pass
                await websocket.send_json({"type": "heartbeat"})
            except Exception:
                break

    hb_task = asyncio.create_task(heartbeat())

    try:
        while running:
            try:
                raw = await asyncio.wait_for(websocket.receive_text(), timeout=60)
            except TimeoutError:
                continue

            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                continue

            msg_type = msg.get("type", "")

            if msg_type == "subscribe":
                channel = msg.get("channel", "")
                if channel:
                    subscribed_channels.add(channel)
                    await websocket.send_json({"type": "subscribed", "channel": channel})
                    log.info("websocket.subscribed", channel=channel)

            elif msg_type == "unsubscribe":
                channel = msg.get("channel", "")
                subscribed_channels.discard(channel)

            elif msg_type == "ping":
                if conn_mgr:
                    try:
                        conn_mgr.heartbeat(connection_id)
                    except Exception:
                        pass
                await websocket.send_json({"type": "pong"})

            elif msg_type == "emit":
                channel = msg.get("channel", "")
                data = msg.get("data", {})

                if push_service:
                    await push_service.push(channel, "message", data)

                class WsEmitEvent(DomainEvent):
                    event_type: str = "websocket.emit"
                    channel: str = channel
                    data: dict[str, Any] = data

                try:
                    await event_bus.publish(WsEmitEvent(channel=channel, data=data))
                except Exception:
                    pass

    except WebSocketDisconnect:
        log.info("websocket.disconnected")
    finally:
        running = False
        hb_task.cancel()
        if push_service:
            push_service.unregister_socket(connection_id)
        if conn_mgr:
            try:
                conn_mgr.unregister(connection_id)
            except Exception:
                pass
        if sub is not None:
            try:
                event_bus.unsubscribe(sub)
            except Exception:
                pass
