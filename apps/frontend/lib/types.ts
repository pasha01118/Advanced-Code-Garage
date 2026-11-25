import type { components } from "@acg/contract";

export type AuthMeOut = components["schemas"]["AuthMeOut"];
export type SwarmResponse = components["schemas"]["AgentSwarmResponse"];
// The contract types system_mode as a string with a pattern; these are the only
// modes the API accepts.
export type ExecutionMode = "Autonomous" | "AI-Man" | "Manual";
export type ProjectInitRequest = components["schemas"]["ProjectInitRequest"];
export type ProjectInitResponse = components["schemas"]["ProjectOut"];
export type ProjectStatus = components["schemas"]["ProjectOut"];
export type ProjectOut = components["schemas"]["ProjectOut"];
export type ProjectListOut = components["schemas"]["ProjectListOut"];

export type ProviderCatalogEntry = components["schemas"]["ProviderCatalogEntry"];
export type ProviderCatalogListOut = components["schemas"]["ProviderCatalogListOut"];
export type AIKeyStatus = components["schemas"]["AIKeyStatus"];
export type AIKeyStatusListOut = components["schemas"]["AIKeyStatusListOut"];
export type AIModelInfo = components["schemas"]["AIModelInfo"];
export type AIModelListOut = components["schemas"]["AIModelListOut"];
export type AIValidateOut = components["schemas"]["AIValidateOut"];
export type AISaveKeyRequest = components["schemas"]["AISaveKeyRequest"];
export type AIDeleteOut = components["schemas"]["AIDeleteOut"];
export type AdminBootstrapRequest = components["schemas"]["AdminBootstrapRequest"];
export type AdminBootstrapOut = components["schemas"]["AdminBootstrapOut"];
export type AdminForgotPasswordRequest = components["schemas"]["AdminForgotPasswordRequest"];
export type AdminForgotPasswordOut = components["schemas"]["AdminForgotPasswordOut"];
export type AppStateOut = components["schemas"]["AppStateOut"];
export type SetAppStateRequest = components["schemas"]["SetAppStateRequest"];
export type SetToggleRequest = components["schemas"]["SetToggleRequest"];
export type ProviderUsageOut = components["schemas"]["ProviderUsageOut"];
export type ProviderUsageListOut = components["schemas"]["ProviderUsageListOut"];
export type SentinelEventOut = components["schemas"]["SentinelEventOut"];
export type SentinelDiscussionEntryOut = components["schemas"]["SentinelDiscussionEntryOut"];
export type SentinelSnapshotOut = components["schemas"]["SentinelSnapshotOut"];
export type RunSentinelOut = components["schemas"]["RunSentinelOut"];
export type UserRowOut = components["schemas"]["UserRowOut"];
export type UserListOut = components["schemas"]["UserListOut"];
export type SuspendUserRequest = components["schemas"]["SuspendUserRequest"];
export type UpdateAccountRequest = components["schemas"]["UpdateAccountRequest"];
export type UpdateAccountOut = components["schemas"]["UpdateAccountOut"];

// Agent log frames are hand-written in the backend; the contract does not
// expose a schema for them.
export interface LogEntry {
  timestamp?: string | null;
  level: string;
  agent: string;
  message: string;
  project_id?: string | null;
}