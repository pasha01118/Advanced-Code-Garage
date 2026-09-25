import type {
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
} from "./types";
import { supabase } from "./supabaseClient";

const API_BASE = (process.env.NEXT_PUBLIC_API_URL || "/api").replace(/\/+$/, "");

function apiUrl(path: string): string {
  const base = API_BASE.endsWith("/api") ? API_BASE : `${API_BASE}/api`;
  return `${base}${path}`;
}

async function authHeaders(): Promise<Record<string, string>> {
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
  return `${API_BASE}/v1/admin/sentinel/stream`;
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