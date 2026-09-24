from pydantic import BaseModel, Field
from typing import Optional, List

class AgentStatus(BaseModel):
    name: str
    role: str
    status: str
    current_task: Optional[str] = None

class AgentSwarmResponse(BaseModel):
    active_agents: List[AgentStatus]
    system_mode: str = Field(default="AI-Man", pattern="^(Autonomous|AI-Man|Manual)$")
    security_gate: str = "Active"
