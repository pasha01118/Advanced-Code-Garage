from fastapi import APIRouter
from app.schemas.agent import AgentSwarmResponse, AgentStatus

router = APIRouter(prefix="/api/v1/agents", tags=["Agents"])

@router.get("/swarm", response_model=AgentSwarmResponse)
async def get_agent_swarm():
    """Returns the current status of the agent team."""
    agents = [
        AgentStatus(name="Mr. Ravish Kumar", role="Research Lead", status="Analyzing Market...", current_task="Market Mapping"),
        AgentStatus(name="Mr. Arman Ali Khan", role="Full Stack Arch", status="Idle", current_task=None),
        AgentStatus(name="Mr. Sadath Ali Khan", role="Security Auditor", status="Monitoring...", current_task="Zero-Tolerance Scan"),
        AgentStatus(name="Ms. Kulsum", role="Token Economist", status="Optimizing Context", current_task="Compression"),
    ]
    return AgentSwarmResponse(active_agents=agents, system_mode="AI-Man")
