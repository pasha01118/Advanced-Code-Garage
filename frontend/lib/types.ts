export type ExecutionMode = "Autonomous" | "AI-Man" | "Manual";

export interface AgentStatus {
  name: string;
  role: string;
  status: string;
  current_task: string | null;
}

export interface SwarmResponse {
  active_agents: AgentStatus[];
  system_mode: ExecutionMode;
  security_gate: string;
}

export interface LogEntry {
  timestamp: string;
  level: string;
  agent: string;
  message: string;
}

export interface ProjectInitRequest {
  name: string;
  description?: string;
  repo_url?: string;
}

export interface ProjectInitResponse {
  status: string;
  project_id: string;
  name: string;
  message: string;
  agents_assigned: string[];
}

export interface ProjectStatus {
  project_id: string;
  status: string;
  progress: number;
  current_agent: string;
  task: string;
}