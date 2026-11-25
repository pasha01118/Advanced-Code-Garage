import type {
  AuthMeOut,
  AdminBootstrapOut,
  AdminBootstrapRequest,
  AdminForgotPasswordOut,
  AdminForgotPasswordRequest,
  AIDeleteOut,
  AIModelListOut,
  AIKeyStatusListOut,
  AIValidateOut,
  AISaveKeyRequest,
  AppStateOut,
  SetAppStateRequest,
  ProviderUsageListOut,
  ExecutionMode,
  LogEntry,
  ProjectInitRequest,
  ProjectInitResponse,
  ProjectListOut,
  ProjectStatus,
  ProviderCatalogListOut,
  RunSentinelOut,
  SwarmResponse,
  SentinelSnapshotOut,
  SentinelEventOut,
  SentinelDiscussionEntryOut,
  UserListOut,
  UpdateAccountRequest,
  UpdateAccountOut,
  PreferencesOut,
  UpdatePreferencesRequest,
  SnippetOut,
  SnippetListOut,
  SnippetCreateRequest,
  SnippetUpdateRequest,
  HistoryListOut,
  LogHistoryOut,
  NotificationOut,
  NotificationListOut,
  NotificationCountsOut,
  ProjectTemplateListOut,
  ProjectMetaUpdateRequest,
  BulkProjectRequest,
  BulkProjectResultOut,
  SearchOut,
  AuditListOut,
  MetricsOverviewOut,
} from "./types";
import { supabase } from "./supabaseClient";

const API_BASE = (process.env.NEXT_PUBLIC_API_URL || "/api").replace(/\/+$/, "");

function apiUrl(path: string): string {
  const base = API_BASE.endsWith("/api") ? API_BASE : `${API_BASE}/api`;
  return `${base}${path}`;
}

// SSE endpoints live under the same /api base as REST calls.
export function streamUrl(path: string): string {
  return apiUrl(path);
}

export async function authHeaders(): Promise<Record<string, string>> {
  if (!supabase) return {};
  try {
    const { data } = await supabase.auth.getSession();
    const token = data.session?.access_token;
    return token ? { Authorization: `Bearer ${token}` } : {};
  } catch {
    return {};
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(apiUrl(path), init);
  if (!res.ok) {
    let detail = `${res.status} ${res.statusText}`;
    try {
      const body = (await res.json()) as { detail?: unknown };
      if (typeof body.detail === "string") detail = body.detail;
      else if (Array.isArray(body.detail) && body.detail.length > 0) {
        const first = body.detail[0] as { msg?: string };
        if (first?.msg) detail = first.msg;
      }
    } catch {
      // ignore non-JSON error bodies
    }
    throw new Error(detail);
  }
  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

async function requestAuthed<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers: Record<string, string> = {
    ...(init.headers as Record<string, string> | undefined),
    ...(await authHeaders()),
  };
  return request<T>(path, { ...init, headers });
}

export function getSwarm(): Promise<SwarmResponse> {
  return request<SwarmResponse>("/v1/agents/swarm");
}

export function setExecutionMode(mode: ExecutionMode): Promise<{ system_mode: ExecutionMode; status: string }> {
  return requestAuthed("/v1/agents/mode", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ mode }),
  });
}

export function initializeProject(body: ProjectInitRequest): Promise<ProjectInitResponse> {
  return requestAuthed("/v1/projects/", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

export interface ProjectFilters {
  status?: string;
  tag?: string;
  search?: string;
  limit?: number;
}

function queryString(values: object): string {
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(values)) {
    if (value !== undefined && value !== null && value !== "") params.set(key, String(value));
  }
  const encoded = params.toString();
  return encoded ? `?${encoded}` : "";
}

export function listProjects(filters: ProjectFilters = {}): Promise<ProjectListOut> {
  return requestAuthed(`/v1/projects/${queryString(filters)}`);
}

export function getProjectStatus(projectId: string): Promise<ProjectStatus> {
  return requestAuthed(`/v1/projects/${encodeURIComponent(projectId)}`);
}

export function getLogsStreamUrl(): string {
  return streamUrl("/v1/logs/stream");
}

export function parseLogEvent(raw: string): LogEntry | null {
  if (!raw) return null;
  try {
    return JSON.parse(raw) as LogEntry;
  } catch {
    return null;
  }
}

// -- AI Integration ----------------------------------------------------------

export function getAICatalog(): Promise<ProviderCatalogListOut> {
  return requestAuthed("/v1/ai/catalog");
}

export function getAIKeyStatuses(): Promise<AIKeyStatusListOut> {
  return requestAuthed("/v1/ai/keys");
}

export function saveAIKey(payload: AISaveKeyRequest): Promise<AIValidateOut> {
  return requestAuthed("/v1/ai/keys", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export function validateAIKey(provider: string): Promise<AIValidateOut> {
  return requestAuthed(`/v1/ai/keys/${encodeURIComponent(provider)}/validate`, {
    method: "POST",
  });
}

export function getAIModels(provider: string): Promise<AIModelListOut> {
  return requestAuthed(`/v1/ai/keys/${encodeURIComponent(provider)}/models`);
}

export function deleteAIKey(provider: string): Promise<AIDeleteOut> {
  return requestAuthed(`/v1/ai/keys/${encodeURIComponent(provider)}`, {
    method: "DELETE",
  });
}

export function getAuthMe(): Promise<AuthMeOut> {
  return requestAuthed("/v1/auth/me");
}

// -- Admin bootstrap (first-run sign-up, no confirmation email) -------------

export function bootstrapAdmin(payload: AdminBootstrapRequest): Promise<AdminBootstrapOut> {
  return request("/v1/auth/bootstrap", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export function adminForgotPassword(payload: AdminForgotPasswordRequest): Promise<AdminForgotPasswordOut> {
  return request("/v1/auth/admin/forgot-password", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

// -- Admin Panel --------------------------------------------------------------

export function getAppState(): Promise<AppStateOut> {
  return requestAuthed("/v1/admin/state");
}

export function setAppState(payload: SetAppStateRequest): Promise<AppStateOut> {
  return requestAuthed("/v1/admin/state", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export function setToggle(name: string, enabled: boolean): Promise<AppStateOut> {
  return requestAuthed(`/v1/admin/toggles/${encodeURIComponent(name)}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ enabled }),
  });
}

export function getProviderUsage(): Promise<ProviderUsageListOut> {
  return requestAuthed("/v1/admin/providers/usage");
}

export function getSentinelEvents(): Promise<SentinelEventOut[]> {
  return requestAuthed("/v1/admin/sentinel/events");
}

export function getSentinelDiscussion(): Promise<SentinelDiscussionEntryOut[]> {
  return requestAuthed("/v1/admin/sentinel/discussion");
}

export function getSentinelSnapshot(): Promise<SentinelSnapshotOut> {
  return requestAuthed("/v1/admin/sentinel/snapshot");
}

export function runSentinel(): Promise<RunSentinelOut> {
  return requestAuthed("/v1/admin/sentinel/run", { method: "POST" });
}

export function getSentinelStreamUrl(): string {
  return streamUrl("/v1/admin/sentinel/stream");
}

export function listUsers(): Promise<UserListOut> {
  return requestAuthed("/v1/admin/users");
}

export function suspendUser(userId: string, durationMinutes: number): Promise<{ user_id: string; suspended: boolean; duration_minutes: number }> {
  return requestAuthed(`/v1/admin/users/${encodeURIComponent(userId)}/suspend`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ duration_minutes: durationMinutes }),
  });
}

export function reactivateUser(userId: string): Promise<{ user_id: string; suspended: boolean }> {
  return requestAuthed(`/v1/admin/users/${encodeURIComponent(userId)}/reactivate`, { method: "POST" });
}

export function updateAdminAccount(payload: UpdateAccountRequest): Promise<UpdateAccountOut> {
  return requestAuthed("/v1/admin/account", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

// -- Preferences --------------------------------------------------------------

export function getPreferences(): Promise<PreferencesOut> {
  return requestAuthed("/v1/preferences/");
}

export function updatePreferences(payload: UpdatePreferencesRequest): Promise<PreferencesOut> {
  return requestAuthed("/v1/preferences/", {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

// -- Terminal power tools -----------------------------------------------------

export function listSnippets(): Promise<SnippetListOut> {
  return requestAuthed("/v1/terminal/snippets");
}

export function createSnippet(payload: SnippetCreateRequest): Promise<SnippetOut> {
  return requestAuthed("/v1/terminal/snippets", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export function updateSnippet(id: string, payload: SnippetUpdateRequest): Promise<SnippetOut> {
  return requestAuthed(`/v1/terminal/snippets/${encodeURIComponent(id)}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export function deleteSnippet(id: string): Promise<void> {
  return requestAuthed(`/v1/terminal/snippets/${encodeURIComponent(id)}`, { method: "DELETE" });
}

export function listCommandHistory(limit = 100): Promise<HistoryListOut> {
  return requestAuthed(`/v1/terminal/history${queryString({ limit })}`);
}

export function addCommandHistory(command: string): Promise<{ id: string; saved: boolean }> {
  return requestAuthed("/v1/terminal/history", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ command }),
  });
}

export function clearCommandHistory(): Promise<void> {
  return requestAuthed("/v1/terminal/history", { method: "DELETE" });
}

export function getLogHistory(filters: {
  limit?: number;
  level?: string;
  search?: string;
} = {}): Promise<LogHistoryOut> {
  return requestAuthed(`/v1/terminal/logs${queryString(filters)}`);
}

// -- Notifications ------------------------------------------------------------

export function listNotifications(unreadOnly = false, limit = 100): Promise<NotificationListOut> {
  return requestAuthed(`/v1/notifications/${queryString({ unread_only: unreadOnly, limit })}`);
}

export function getNotificationCounts(): Promise<NotificationCountsOut> {
  return requestAuthed("/v1/notifications/counts");
}

export function markNotificationRead(id: string): Promise<NotificationOut> {
  return requestAuthed(`/v1/notifications/${encodeURIComponent(id)}/read`, { method: "POST" });
}

export function markAllNotificationsRead(): Promise<{ updated: number }> {
  return requestAuthed("/v1/notifications/read-all", { method: "POST" });
}

export function deleteNotification(id: string): Promise<void> {
  return requestAuthed(`/v1/notifications/${encodeURIComponent(id)}`, { method: "DELETE" });
}

export function clearNotifications(): Promise<void> {
  return requestAuthed("/v1/notifications/", { method: "DELETE" });
}

// -- Workspace upgrade APIs ---------------------------------------------------

export function searchWorkspace(q: string): Promise<SearchOut> {
  return requestAuthed(`/v1/workspace/search${queryString({ q })}`);
}

export function listProjectTemplates(): Promise<ProjectTemplateListOut> {
  return requestAuthed("/v1/workspace/templates");
}

export function getWorkspaceMetrics(): Promise<MetricsOverviewOut> {
  return requestAuthed("/v1/workspace/metrics");
}

export function getAuditLog(filters: {
  all_users?: boolean;
  limit?: number;
  action?: string;
  since?: string;
} = {}): Promise<AuditListOut> {
  return requestAuthed(`/v1/workspace/audit${queryString(filters)}`);
}

export function updateProjectMeta(id: string, payload: ProjectMetaUpdateRequest): Promise<{ id: string; updated: boolean }> {
  return requestAuthed(`/v1/workspace/projects/${encodeURIComponent(id)}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export function bulkProjectAction(payload: BulkProjectRequest): Promise<BulkProjectResultOut> {
  return requestAuthed("/v1/workspace/projects/bulk", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}