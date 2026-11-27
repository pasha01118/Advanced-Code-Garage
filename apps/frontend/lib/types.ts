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

export type PreferencesOut = components["schemas"]["PreferencesOut"];
// Literal aliases are inlined by Pydantic, so derive the unions from the
// generated response instead of referencing non-existent named schemas.
export type Theme = NonNullable<PreferencesOut["theme"]>;
export type Accent = NonNullable<PreferencesOut["accent"]>;
export type Density = NonNullable<PreferencesOut["density"]>;
export type UpdatePreferencesRequest = components["schemas"]["UpdatePreferencesRequest"];
export type SnippetOut = components["schemas"]["SnippetOut"];
export type SnippetListOut = components["schemas"]["SnippetListOut"];
export type SnippetCreateRequest = components["schemas"]["SnippetCreateRequest"];
export type SnippetUpdateRequest = components["schemas"]["SnippetUpdateRequest"];
export type HistoryEntryOut = components["schemas"]["HistoryEntryOut"];
export type HistoryListOut = components["schemas"]["HistoryListOut"];
export type LogHistoryEntryOut = components["schemas"]["LogHistoryEntryOut"];
export type LogHistoryOut = components["schemas"]["LogHistoryOut"];
export type NotificationOut = components["schemas"]["NotificationOut"];
export type NotificationType = NotificationOut["type"];
export type NotificationListOut = components["schemas"]["NotificationListOut"];
export type NotificationCountsOut = components["schemas"]["NotificationCountsOut"];
export type ProjectTemplateOut = components["schemas"]["ProjectTemplateOut"];
export type ProjectTemplateListOut = components["schemas"]["ProjectTemplateListOut"];
export type ProjectMetaUpdateRequest = components["schemas"]["ProjectMetaUpdateRequest"];
export type BulkProjectRequest = components["schemas"]["BulkProjectRequest"];
export type BulkProjectResultOut = components["schemas"]["BulkProjectResultOut"];
export type SearchResultOut = components["schemas"]["SearchResultOut"];
export type SearchOut = components["schemas"]["SearchOut"];
export type AuditEntryOut = components["schemas"]["AuditEntryOut"];
export type AuditListOut = components["schemas"]["AuditListOut"];
export type MetricPointOut = components["schemas"]["MetricPointOut"];
export type MetricsOverviewOut = components["schemas"]["MetricsOverviewOut"];
export type InstallationOut = components["schemas"]["InstallationOut"];
export type InstallationListOut = components["schemas"]["InstallationListOut"];
export type SyncOut = components["schemas"]["SyncOut"];
export type RepositoryOut = components["schemas"]["RepositoryOut"];
export type RepositoryListOut = components["schemas"]["RepositoryListOut"];
export type SecretScope = components["schemas"]["SecretCreateRequest"]["scope"];
export type SecretCreateRequest = components["schemas"]["SecretCreateRequest"];
export type SecretOut = components["schemas"]["SecretOut"];
export type SecretListOut = components["schemas"]["SecretListOut"];
export type SecretRevokeOut = components["schemas"]["SecretRevokeOut"];
export type SecretAuditOut = components["schemas"]["SecretAuditOut"];
export type SecretAuditListOut = components["schemas"]["SecretAuditListOut"];

// Repository operations + customization
export type RepoConfig = components["schemas"]["RepoConfig"];
export type AgentMode = RepoConfig["agent_mode"];
export type BranchOut = components["schemas"]["BranchOut"];
export type BranchListOut = components["schemas"]["BranchListOut"];
export type TreeEntryOut = components["schemas"]["TreeEntryOut"];
export type TreeListOut = components["schemas"]["TreeListOut"];
export type FileOut = components["schemas"]["FileOut"];
export type FileWriteRequest = components["schemas"]["FileWriteRequest"];
export type CommitOut = components["schemas"]["CommitOut"];
export type PullOut = components["schemas"]["PullOut"];
export type PullListOut = components["schemas"]["PullListOut"];
export type PullCreateRequest = components["schemas"]["PullCreateRequest"];
export type CompareFileOut = components["schemas"]["CompareFileOut"];
export type CompareOut = components["schemas"]["CompareOut"];
export type ConfigOut = components["schemas"]["ConfigOut"];
export type ConfigPreviewOut = components["schemas"]["ConfigPreviewOut"];
export type ConfigPreviewRequest = components["schemas"]["ConfigPreviewRequest"];
export type ConfigApplyRequest = components["schemas"]["ConfigApplyRequest"];
export type TemplateOut = components["schemas"]["TemplateOut"];
export type TemplateListOut = components["schemas"]["TemplateListOut"];
export type RepoAuditOut = components["schemas"]["RepoAuditOut"];
export type RepoAuditListOut = components["schemas"]["RepoAuditListOut"];
export type RepoRoleOut = components["schemas"]["RepoRoleOut"];
export type RepoRoleListOut = components["schemas"]["RepoRoleListOut"];
export type RepoPermissionRequest = components["schemas"]["RepoPermissionRequest"];

// Agent log frames are hand-written in the backend; the contract does not
// expose a schema for them.
export interface LogEntry {
  timestamp?: string | null;
  level: string;
  agent: string;
  message: string;
  project_id?: string | null;
}