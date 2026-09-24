import asyncio
import json

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from app.core.event_bus import bus

router = APIRouter()

HEARTBEAT_SECONDS = 15.0


async def log_stream():
    queue = await bus.subscribe()
    try:
        while True:
            try:
                event = await asyncio.wait_for(queue.get(), timeout=HEARTBEAT_SECONDS)
            except asyncio.TimeoutError:
                yield ": keepalive\n\n"
                continue
            yield f"data: {json.dumps(event)}\n\n"
    finally:
        await bus.unsubscribe(queue)


@router.get("/stream")
async def stream_logs(request: Request) -> StreamingResponse:
    return StreamingResponse(
        log_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/")
async def get_latest_logs() -> dict:
    return {"note": "Use /stream for real-time"}