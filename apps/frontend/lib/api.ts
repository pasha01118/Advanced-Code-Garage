import type {
  AIDeleteOut,
  AIModelListOut,
  AIKeyStatusListOut,
  AIValidateOut,
  AISaveKeyRequest,
  ExecutionMode,
  LogEntry,
  ProjectInitRequest,
  ProjectInitResponse,
  ProjectStatus,
  ProviderCatalogListOut,
  SwarmResponse,
} from "./types";
import { supabase } from "./supabaseClient";

const API_BASE = (process.env.NEXT_PUBLIC_API_URL || "/api").replace(/\/+$/, "");

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
  const res = await fetch(`${API_BASE}${path}`, init);
  if (!res.ok) {
    let detail = `${res.status} ${res.statusText}`;
    try {
      const body = (await res.json()) as { detail?: unknown };
      if (typeof body.detail === "string") detail = body.detail;
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