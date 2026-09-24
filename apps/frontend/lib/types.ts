import type { components } from "@acg/contract";

export type SwarmResponse = components["schemas"]["AgentSwarmResponse"];
export type ExecutionMode = SwarmResponse["system_mode"];
export type ProjectInitRequest = components["schemas"]["ProjectInitRequest"];
export type ProjectInitResponse = components["schemas"]["ProjectOut"];
export type ProjectStatus = components["schemas"]["ProjectOut"];
export type ProjectOut = components["schemas"]["ProjectOut"];

export interface LogEntry {
  timestamp?: string;
  level: string;
  agent: string;
  message: string;
  project_id?: string | null;
}