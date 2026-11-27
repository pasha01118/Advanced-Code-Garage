"use client";

import { authHeaders } from "./api";

export interface SSEHandlers {
  onMessage: (data: string) => void;
  onOpen?: () => void;
  onDisconnect?: () => void;
}

const INITIAL_RETRY_MS = 500;
const MAX_RETRY_MS = 15000;

function dispatchFrame(frame: string, onMessage: (data: string) => void): void {
  const dataLines: string[] = [];
  for (const line of frame.split("\n")) {
    // Comments (including ": keepalive") carry no payload.
    if (!line || line.startsWith(":")) continue;
    if (line.startsWith("data:")) {
      dataLines.push(line.slice("data:".length).replace(/^ /, ""));
    }
  }
  if (dataLines.length > 0) onMessage(dataLines.join("\n"));
}

/**
 * Subscribe to an authenticated text/event-stream endpoint.
 *
 * EventSource cannot send an Authorization header, so this uses fetch and the
 * current Supabase access token. Returns an unsubscribe function that aborts
 * the in-flight request and stops reconnects.
 */
export function subscribeSSE(url: string, handlers: SSEHandlers): () => void {
  let stopped = false;
  let disconnected = false;
  let retryMs = INITIAL_RETRY_MS;
  let retryTimer: ReturnType<typeof setTimeout> | undefined;
  let controller: AbortController | undefined;

  const markDisconnected = () => {
    if (disconnected) return;
    disconnected = true;
    handlers.onDisconnect?.();
  };

  const scheduleReconnect = () => {
    if (stopped || retryTimer) return;
    markDisconnected();
    retryTimer = setTimeout(() => {
      retryTimer = undefined;
      void connect();
    }, retryMs);
    retryMs = Math.min(retryMs * 2, MAX_RETRY_MS);
  };

  const connect = async () => {
    if (stopped) return;
    const current = new AbortController();
    controller = current;

    try {
      const headers = await authHeaders();
      if (stopped || current.signal.aborted) return;
      const res = await fetch(url, {
        headers: {
          ...headers,
          Accept: "text/event-stream",
        },
        signal: current.signal,
        cache: "no-store",
      });
      if (res.status === 401 || res.status === 403) {
        // Retrying with a rejected session would loop forever.
        stopped = true;
        markDisconnected();
        return;
      }
      if (!res.ok || !res.body) throw new Error(`SSE failed: ${res.status}`);

      disconnected = false;
      retryMs = INITIAL_RETRY_MS;
      handlers.onOpen?.();

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (!stopped && !current.signal.aborted) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer = (buffer + decoder.decode(value, { stream: true })).replace(/\r\n/g, "\n");

        let boundary = buffer.indexOf("\n\n");
        while (boundary !== -1) {
          const frame = buffer.slice(0, boundary);
          buffer = buffer.slice(boundary + 2);
          dispatchFrame(frame, handlers.onMessage);
          boundary = buffer.indexOf("\n\n");
        }
      }
    } catch {
      // Aborts are expected on unsubscribe; everything else retries.
    }
    if (!stopped) scheduleReconnect();
  };

  void connect();

  return () => {
    stopped = true;
    if (retryTimer) clearTimeout(retryTimer);
    controller?.abort();
    markDisconnected();
  };
}
