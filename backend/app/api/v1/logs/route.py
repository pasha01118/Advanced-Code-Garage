from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
import asyncio
import json
import datetime
import random

router = APIRouter()

# Simulated log generator
async def log_generator():
    messages = [
        {"level": "INFO", "agent": "System", "msg": "Agent Swarm initialized."},
        {"level": "DEBUG", "agent": "Ms. Kulsum", "msg": "Token budget optimized: 85% efficiency."},
        {"level": "WARN", "agent": "Mr. Sadath", "msg": "High entropy detected in input buffer."},
        {"level": "OK", "agent": "Git-Sir", "msg": "Repository index synced."},
    ]
    
    while True:
        msg = random.choice(messages)
        timestamp = datetime.datetime.utcnow().isoformat()
        payload = {
            "timestamp": timestamp,
            "level": msg["level"],
            "agent": msg["agent"],
            "message": msg["msg"]
        }
        yield f"data: {json.dumps(payload)}\n\n"
        await asyncio.sleep(2)  # Send every 2 seconds

@router.get("/stream")
async def stream_logs(request: Request):
    return StreamingResponse(log_generator(), media_type="text/event-stream")

@router.get("/")
async def get_latest_logs():
    return {"logs": [], "note": "Use /stream for real-time"}
