import asyncio
import json
from typing import Annotated

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPAuthorizationCredentials

from app.core.auth import require_authenticated, require_user
from app.core.event_bus import bus

router = APIRouter()

HEARTBEAT_SECONDS = 15.0

AuthenticatedUser = Annotated[dict, Depends(require_authenticated)]


async def _token_still_valid(token: str | None) -> bool:
    if not token:
        # Auth was overridden in local/tests; the connection was authorized.
        return True
    try:
        await require_user(HTTPAuthorizationCredentials(scheme="Bearer", credentials=token))
        return True
    except Exception:
        return False


async def log_stream(owner_id: str, token: str | None = None):
    queue = await bus.subscribe()
    try:
        while True:
            try:
                event = await asyncio.wait_for(queue.get(), timeout=HEARTBEAT_SECONDS)
            except asyncio.TimeoutError:
                if not await _token_still_valid(token):
                    break
                yield ": keepalive\n\n"
                continue
            # The bus is process-global; never expose another user's project logs.
            if event.get("owner_id") != owner_id:
                continue
            yield f"data: {json.dumps(event)}\n\n"
    finally:
        await bus.unsubscribe(queue)


@router.get("/stream")
async def stream_logs(request: Request, user: AuthenticatedUser) -> StreamingResponse:
    header = request.headers.get("authorization", "")
    token = header[7:].strip() if header.lower().startswith("bearer ") else None
    return StreamingResponse(
        log_stream(user.get("sub"), token),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/")
async def get_latest_logs(user: AuthenticatedUser) -> dict:
    return {"note": "Use /stream for real-time"}
