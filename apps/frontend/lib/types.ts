import type { components } from "@acg/contract";

export type SwarmResponse = components["schemas"]["AgentSwarmResponse"];
export type ExecutionMode = SwarmResponse["system_mode"];
export type ProjectInitRequest = components["schemas"]["ProjectInitRequest"];
export type ProjectInitResponse = components["schemas"]["ProjectOut"];
export type ProjectStatus = components["schemas"]["ProjectOut"];
export type ProjectOut = components["schemas"]["ProjectOut"];

export type ProviderCatalogEntry = components["schemas"]["ProviderCatalogEntry"];
export type ProviderCatalogListOut = components["schemas"]["ProviderCatalogListOut"];
export type AIKeyStatus = components["schemas"]["AIKeyStatus"];
export type AIKeyStatusListOut = components["schemas"]["AIKeyStatusListOut"];
export type AIModelInfo = components["schemas"]["AIModelInfo"];
export type AIModelListOut = components["schemas"]["AIModelListOut"];
export type AIValidateOut = components["schemas"]["AIValidateOut"];
export type AISaveKeyRequest = components["schemas"]["AISaveKeyRequest"];
export type AIDeleteOut = components["schemas"]["AIDeleteOut"];

export interface LogEntry {
  timestamp?: string;
  level: string;
  agent: string;
  message: string;
  project_id?: string | null;
}