from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Annotated, Literal

from app.core.auth import require_authenticated
from app.schemas.agent import AgentStatus, AgentSwarmResponse
from app.services.mode import ModeService
from app.services.ops_state import require_service

router = APIRouter(prefix="/api/v1/agents", tags=["Agents"])

VALID_MODES = ("Autonomous", "AI-Man", "Manual")


class ModeUpdateRequest(BaseModel):
    mode: Literal["Autonomous", "AI-Man", "Manual"]


def get_mode_service() -> ModeService:
    return ModeService()


AuthenticatedUser = Annotated[dict, Depends(require_authenticated)]


ROSTER = [
    AgentStatus(name="Mr. Ravish Kumar", role="Research Lead", status="Analyzing Market...", current_task="Market Mapping"),
    AgentStatus(name="Mr. Arman Ali Khan", role="Full Stack Arch", status="Idle", current_task=None),
    AgentStatus(name="Mr. Sadath Ali Khan", role="Security Auditor", status="Monitoring...", current_task="Zero-Tolerance Scan"),
    AgentStatus(name="Ms. Kulsum", role="Token Economist", status="Optimizing Context", current_task="Compression"),
]


@router.get("/swarm", response_model=AgentSwarmResponse, dependencies=[Depends(require_service("swarm"))])
async def get_agent_swarm(mode_service: ModeService = Depends(get_mode_service)) -> AgentSwarmResponse:
    """Returns the current status of the agent team with the persistent mode."""
    system_mode = await mode_service.get()
    return AgentSwarmResponse(active_agents=ROSTER, system_mode=system_mode)


@router.post("/mode", dependencies=[Depends(require_service("swarm"))])
async def set_execution_mode(
    req: ModeUpdateRequest,
    user: AuthenticatedUser,
    mode_service: ModeService = Depends(get_mode_service),
) -> JSONResponse:
    """Switches the swarm execution mode (Autonomous / AI-Man / Manual)."""
    actor = user.get("email") or user.get("sub") or "authenticated"
    updated = await mode_service.set(req.mode, actor=actor)
    return JSONResponse({"system_mode": updated, "status": "updated"})