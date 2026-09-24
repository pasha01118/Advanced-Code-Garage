from fastapi import APIRouter
from typing import List, Optional
from pydantic import BaseModel
import datetime

router = APIRouter()

class LogEntry(BaseModel):
    timestamp: str
    level: str
    agent: str
    message: str

# Simulated live logs
LOG_STREAM: List[LogEntry] = [
    LogEntry(timestamp=datetime.datetime.utcnow().isoformat(), level="INFO", agent="Git-Sir", message="Awaiting input..."),
    LogEntry(timestamp=datetime.datetime.utcnow().isoformat(), level="WARN", agent="Ms. Kulsum", message="Token optimization active"),
    LogEntry(timestamp=datetime.datetime.utcnow().isoformat(), level="OK", agent="System", message="Connected to Supabase Vector DB"),
]

@router.get("/")
async def get_logs():
    return {"logs": LOG_STREAM}

@router.post("/")
async def add_log(log_entry: LogEntry):
    LOG_STREAM.append(log_entry)
    return {"status": "logged"}
