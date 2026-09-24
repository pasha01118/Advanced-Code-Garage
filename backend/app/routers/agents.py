from fastapi import APIRouter
from app.schemas.agent import AgentSwarmResponse, AgentStatus
from pydantic import BaseModel
from typing import Literal
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/api/v1/agents", tags=["Agents"])

VALID_MODES = ("Autonomous", "AI-Man", "Manual")

class ModeUpdateRequest(BaseModel):
    mode: Literal["Autonomous", "AI-Man", "Manual"]

ai_state = {"system_mode": "AI-Man"}

def _agent(name, role, status, task):
    return AgentStatus(name=name, role=role, status=status, current_task=task)

@router.get("/swarm", response_model=AgentSwarmResponse)
async def get_agent_swarm():
    """Returns the current status of the agent team."""
    agents = [
        _agent("Mr. Ravish Kumar", "Research Lead", "Analyzing Market...", "Market Mapping"),
        _agent("Mr. Arman Ali Khan", "Full Stack Arch", "Idle", None),
        _agent("Mr. Sadath Ali Khan", "Security Auditor", "Monitoring...", "Zero-Tolerance Scan"),
        _agent("Ms. Kulsum", "Token Economist", "Optimizing Context", "Compression"),
    ]
    return AgentSwarmResponse(active_agents=agents, system_mode=ai_state["system_mode"])

@router.post("/mode")
async def set_execution_mode(req: ModeUpdateRequest):
    """Switches the swarm execution mode (Autonomous / AI-Man / Manual)."""
    ai_state["system_mode"] = req.mode
    return JSONResponse({"system_mode": ai_state["system_mode"], "status": "updated"})