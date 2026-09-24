import type { components } from "../generated/api";

// Re-export the full schema namespace so consumers can reach arbitrary models.
export type { components, paths } from "../generated/api";

export type AgentSwarmResponse = components["schemas"]["AgentSwarmResponse"];
export type ProjectInitRequest = components["schemas"]["ProjectInitRequest"];
export type ProjectInitResponse = components["schemas"]["ProjectOut"];
export type ProjectOut = components["schemas"]["ProjectOut"];
export type ProjectListOut = components["schemas"]["ProjectListOut"];
export type ModeUpdateRequest = components["schemas"]["ModeUpdateRequest"];