import type {
  ExecutionMode,
  LogEntry,
  ProjectInitRequest,
  ProjectInitResponse,
  ProjectStatus,
  SwarmResponse,
} from "./types";

const API_BASE = (process.env.NEXT_PUBLIC_API_URL || "/api").replace(/\/+$/, "");

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, init);
  if (!res.ok) {
    throw new Error(`${res.status} ${res.statusText}`);
  }
  return res.json() as Promise<T>;
}

export function getSwarm(): Promise<SwarmResponse> {
  return request<SwarmResponse>("/v1/agents/swarm");
}

export function setExecutionMode(mode: ExecutionMode): Promise<{ system_mode: ExecutionMode; status: string }> {
  return request("/v1/agents/mode", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ mode }),
  });
}

export function initializeProject(body: ProjectInitRequest): Promise<ProjectInitResponse> {
  return request("/v1/projects/", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

export function getProjectStatus(projectId: string): Promise<ProjectStatus> {
  return request(`/v1/projects/${projectId}`);
}

export function getLogsStreamUrl(): string {
  return `${API_BASE}/v1/logs/stream`;
}

export function parseLogEvent(raw: string): LogEntry | null {
  if (!raw) return null;
  try {
    return JSON.parse(raw) as LogEntry;
  } catch {
    return null;
  }
}