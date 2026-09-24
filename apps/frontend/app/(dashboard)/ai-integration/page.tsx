"use client";

import { useEffect, useState } from "react";
import {
  Sparkles,
  Loader2,
  KeyRound,
  Trash2,
  RefreshCw,
  ChevronDown,
  ChevronRight,
  ExternalLink,
  PlugZap,
  Server,
  X,
  Layers,
} from "lucide-react";
import {
  deleteAIKey,
  getAICatalog,
  getAIKeyStatuses,
  getAIModels,
  saveAIKey,
  validateAIKey,
} from "@/lib/api";
import type { AIKeyStatus, AIModelInfo, ProviderCatalogEntry } from "@/lib/types";

const MODEL_PREVIEW_LIMIT = 20;

const STATUS_META: Record<
  string,
  { label: string; dot: string; pill: string }
> = {
  active: {
    label: "Connected",
    dot: "bg-green-500 shadow-[0_0_10px_3px_rgba(34,197,94,0.55)] animate-pulse",
    pill: "text-green-400 bg-green-950/40 border border-green-800/50",
  },
  quota: {
    label: "Limit Exhausted",
    dot: "bg-amber-400 shadow-[0_0_10px_3px_rgba(245,158,11,0.55)]",
    pill: "text-amber-300 bg-amber-950/40 border border-amber-800/50",
  },
  error: {
    label: "Disconnected / Error",
    dot: "bg-red-500 shadow-[0_0_10px_3px_rgba(239,68,68,0.55)]",
    pill: "text-red-400 bg-red-950/40 border border-red-800/50",
  },
  untested: {
    label: "Untested",
    dot: "bg-slate-500",
    pill: "text-slate-400 bg-slate-900 border border-slate-700",
  },
};

const NOT_CONFIGURED = {
  label: "Not Configured",
  dot: "bg-slate-700",
  pill: "text-slate-500 bg-slate-900 border border-slate-800",
};

function statusMeta(status: string | undefined, hasKey: boolean) {
  if (hasKey) return STATUS_META[status ?? "untested"] ?? STATUS_META.untested;
  return NOT_CONFIGURED;
}

function contextLabel(n?: number | null): string {
  if (!n) return "";
  return `${Math.round(n / 1000)}K ctx`;
}

function ModelChip({ model }: { model: AIModelInfo }) {
  return (
    <div className="flex items-center gap-2 px-2.5 py-1 bg-slate-950 border border-slate-800 rounded-lg text-[11px] font-mono text-slate-300 hover:border-slate-600 transition-colors">
      <span>{model.id}</span>
      {model.tags?.map((t) => (
        <span
          key={t}
          className="text-[10px] uppercase tracking-wide text-blue-300 bg-blue-950/50 border border-blue-800/40 px-1.5 py-0.5 rounded"
        >
          {t}
        </span>
      ))}
      {contextLabel(model.context_length) && (
        <span className="text-slate-500">{contextLabel(model.context_length)}</span>
      )}
    </div>
  );
}

function OllamaModal({
  url,
  onChange,
  onConnect,
  busy,
}: {
  url: string;
  onChange: (v: string) => void;
  onConnect: () => void;
  busy: boolean;
}) {
  const [open, setOpen] = useState(true);
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
      <div className="w-full max-w-md bg-slate-900 border border-slate-700 rounded-xl p-6">
        <div className="flex items-start justify-between mb-4">
          <div>
            <h3 className="text-lg font-semibold flex items-center gap-2">
              <Server className="w-5 h-5 text-purple-400" /> Connect Ollama
            </h3>
            <p className="text-xs text-slate-500 mt-1">
              Local (http://localhost:11434) or a cloud Ollama endpoint. No API
              key required.
            </p>
          </div>
          <button
            onClick={() => setOpen(false)}
            className="p-1.5 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
        <label className="block text-xs text-slate-400 mb-1.5">Base URL</label>
        <input
          value={url}
          onChange={(e) => onChange(e.target.value)}
          placeholder="http://localhost:11434"
          spellCheck={false}
          className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-purple-500"
        />
        <div className="mt-4 flex gap-2">
          <button
            onClick={onConnect}
            disabled={busy || !url.trim()}
            className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-purple-600 hover:bg-purple-500 disabled:opacity-50 rounded-lg text-sm font-medium transition-colors"
          >
            {busy ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <PlugZap className="w-4 h-4" />
            )}
            {busy ? "Connecting..." : "Connect"}
          </button>
          <button
            onClick={() => setOpen(false)}
            className="px-4 py-2 bg-slate-800 hover:bg-slate-700 rounded-lg text-sm text-slate-300 transition-colors"
          >
            Cancel
          </button>
        </div>
      </div>
    </div>
  );
}

export default function AIIntegrationPage() {
  const [catalog, setCatalog] = useState<ProviderCatalogEntry[]>([]);
  const [statuses, setStatuses] = useState<Record<string, AIKeyStatus>>({});
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);

  const [models, setModels] = useState<Record<string, AIModelInfo[]>>({});
  const [modelsCached, setModelsCached] = useState<Record<string, boolean>>({});
  const [modelsLoading, setModelsLoading] = useState<Record<string, boolean>>({});
  const [expanded, setExpanded] = useState<Record<string, boolean>>({});
  const [showAll, setShowAll] = useState<Record<string, boolean>>({});

  const [keyInputs, setKeyInputs] = useState<Record<string, string>>({});
  const [busy, setBusy] = useState<string | null>(null);
  const [errors, setErrors] = useState<Record<string, string>>({});

  const [ollamaUrl, setOllamaUrl] = useState("http://localhost:11434");
  const [ollamaModal, setOllamaModal] = useState(false);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const [cat, status] = await Promise.all([getAICatalog(), getAIKeyStatuses()]);
        if (cancelled) return;
        setCatalog(cat.providers);
        const map: Record<string, AIKeyStatus> = {};
        for (const entry of status.entries) map[entry.provider] = entry;
        setStatuses(map);
      } catch (err) {
        if (!cancelled) setLoadError(err instanceof Error ? err.message : "Failed to load AI catalog");
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const applyValidation = (result: { provider: string; status: string; message: string; model_count: number; models: AIModelInfo[] }) => {
    setStatuses((prev) => ({
      ...prev,
      [result.provider]: {
        provider: result.provider,
        has_key: true,
        status: result.status,
        message: result.message,
        model_count: result.model_count,
        last_validated_at: new Date().toISOString(),
      },
    }));
    setModels((prev) => ({ ...prev, [result.provider]: result.models }));
    setModelsCached((prev) => ({ ...prev, [result.provider]: false }));
    setExpanded((prev) => ({ ...prev, [result.provider]: true }));
  };

  const connect = async (provider: ProviderCatalogEntry, secret: string) => {
    setBusy(provider.id);
    setErrors((prev) => ({ ...prev, [provider.id]: "" }));
    try {
      const body =
        provider.kind === "ollama"
          ? { provider: provider.id, api_key: undefined, ollama_base_url: secret }
          : { provider: provider.id, api_key: secret, ollama_base_url: undefined };
      const result = await saveAIKey(body);
      applyValidation(result);
      setOllamaModal(false);
    } catch (err) {
      setErrors((prev) => ({ ...prev, [provider.id]: err instanceof Error ? err.message : "Connect failed" }));
    } finally {
      setBusy(null);
    }
  };

  const rerun = async (providerId: string) => {
    setBusy(providerId);
    setErrors((prev) => ({ ...prev, [providerId]: "" }));
    try {
      const result = await validateAIKey(providerId);
      applyValidation(result);
    } catch (err) {
      setErrors((prev) => ({ ...prev, [providerId]: err instanceof Error ? err.message : "Test failed" }));
    } finally {
      setBusy(null);
    }
  };

  const disconnect = async (providerId: string) => {
    setBusy(providerId);
    setErrors((prev) => ({ ...prev, [providerId]: "" }));
    try {
      await deleteAIKey(providerId);
      setStatuses((prev) => {
        const next = { ...prev };
        delete next[providerId];
        return next;
      });
      setModels((prev) => {
        const next = { ...prev };
        delete next[providerId];
        return next;
      });
      setExpanded((prev) => ({ ...prev, [providerId]: false }));
      setKeyInputs((prev) => ({ ...prev, [providerId]: "" }));
    } catch (err) {
      setErrors((prev) => ({ ...prev, [providerId]: err instanceof Error ? err.message : "Disconnect failed" }));
    } finally {
      setBusy(null);
    }
  };

  const toggleModels = async (providerId: string) => {
    if (!expanded[providerId] && !models[providerId]) {
      setModelsLoading((prev) => ({ ...prev, [providerId]: true }));
      try {
        const result = await getAIModels(providerId);
        setModels((prev) => ({ ...prev, [providerId]: result.models }));
        setModelsCached((prev) => ({ ...prev, [providerId]: result.cached }));
      } catch (err) {
        setErrors((prev) => ({ ...prev, [providerId]: err instanceof Error ? err.message : "Failed to load models" }));
      } finally {
        setModelsLoading((prev) => ({ ...prev, [providerId]: false }));
      }
    }
    setExpanded((prev) => ({ ...prev, [providerId]: !prev[providerId] }));
  };

  const connectedCount = Object.values(statuses).filter((s) => s.has_key).length;

  if (loading) {
    return (
      <div className="flex items-center justify-center py-24 text-slate-500">
        <Loader2 className="w-6 h-6 animate-spin text-blue-500" />
      </div>
    );
  }

  if (loadError && catalog.length === 0) {
    return (
      <div className="text-sm text-red-400 bg-red-950/40 border border-red-800/50 px-4 py-3 rounded-lg">
        {loadError}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Sparkles className="w-6 h-6 text-purple-400" /> AI Integration
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Curated free-tier LLM providers. Keys are encrypted server-side and
            auto-activated with a live connectivity check on connect.
          </p>
        </div>
        <div className="text-xs text-slate-400 bg-slate-900 border border-slate-800 px-3 py-1.5 rounded-lg">
          <span className="text-green-400 font-mono">{connectedCount}</span> /{" "}
          <span className="font-mono">{catalog.length}</span> providers connected
        </div>
      </div>

      {loadError && (
        <div className="text-xs text-red-400 bg-red-950/40 border border-red-800/50 px-3 py-2 rounded-lg">
          {loadError}
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {catalog.map((provider) => {
          const st = statuses[provider.id];
          const hasKey = st?.has_key ?? false;
          const meta = statusMeta(st?.status, hasKey);
          const isBusy = busy === provider.id;
          const modelList = models[provider.id] ?? [];
          const isExpanded = !!expanded[provider.id];
          const showCount = showAll[provider.id] ? modelList.length : Math.min(MODEL_PREVIEW_LIMIT, modelList.length);

          return (
            <section
              key={provider.id}
              className="bg-slate-900 border border-slate-800 rounded-xl p-5 flex flex-col"
            >
              <div className="flex items-start gap-3">
                <div className={`mt-2 w-3 h-3 rounded-full shrink-0 ${meta.dot}`} />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <h2 className="font-semibold text-slate-100">{provider.name}</h2>
                    <span className={`text-[10px] px-2 py-0.5 rounded-full border ${meta.pill}`}>
                      {meta.label}
                    </span>
                  </div>
                  <p className="text-xs text-slate-500">{provider.tagline}</p>
                </div>
                {provider.signup_url && (
                  <a
                    href={provider.signup_url}
                    target="_blank"
                    rel="noreferrer"
                    className="text-xs text-blue-400 hover:text-blue-300 flex items-center gap-1 shrink-0 mt-1"
                  >
                    Get key <ExternalLink className="w-3 h-3" />
                  </a>
                )}
              </div>

              <p className="text-xs text-slate-500 leading-relaxed mt-3">
                <span className="text-slate-400 font-medium">Free tier: </span>
                {provider.free_tier}
              </p>

              {errors[provider.id] && (
                <div className="mt-3 text-xs text-red-400 bg-red-950/40 border border-red-800/40 px-3 py-2 rounded-lg">
                  {errors[provider.id]}
                </div>
              )}

              <div className="mt-4 flex-1">
                {!hasKey ? (
                  provider.kind === "ollama" ? (
                    <button
                      onClick={() => setOllamaModal(true)}
                      className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-purple-600 hover:bg-purple-500 disabled:opacity-50 rounded-lg text-sm font-medium transition-colors"
                    >
                      <Server className="w-4 h-4" /> Open Ollama Setup
                    </button>
                  ) : (
                    <div className="flex gap-2">
                      <div className="relative flex-1">
                        <KeyRound className="w-4 h-4 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
                        <input
                          type="password"
                          value={keyInputs[provider.id] ?? ""}
                          onChange={(e) =>
                            setKeyInputs((prev) => ({ ...prev, [provider.id]: e.target.value }))
                          }
                          placeholder={`Paste ${provider.id} API key`}
                          spellCheck={false}
                          className="w-full bg-slate-950 border border-slate-700 rounded-lg pl-9 pr-3 py-2 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                      </div>
                      <button
                        onClick={() => connect(provider, keyInputs[provider.id] ?? "")}
                        disabled={isBusy || !(keyInputs[provider.id] ?? "").trim()}
                        className="flex items-center justify-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 rounded-lg text-sm font-medium transition-colors"
                      >
                        {isBusy ? (
                          <Loader2 className="w-4 h-4 animate-spin" />
                        ) : (
                          <PlugZap className="w-4 h-4" />
                        )}
                        Connect
                      </button>
                    </div>
                  )
                ) : (
                  <div className="text-xs text-slate-400">
                    <p className="break-words">{st?.message || "Connected."}</p>
                    <div className="flex flex-wrap gap-2 mt-3">
                      <button
                        onClick={() => rerun(provider.id)}
                        disabled={isBusy}
                        className="flex items-center gap-1.5 px-3 py-1.5 bg-slate-800 hover:bg-slate-700 disabled:opacity-50 rounded-lg text-xs text-slate-200 transition-colors"
                      >
                        {isBusy ? (
                          <Loader2 className="w-3.5 h-3.5 animate-spin" />
                        ) : (
                          <RefreshCw className="w-3.5 h-3.5" />
                        )}
                        Run test
                      </button>
                      <button
                        onClick={() => toggleModels(provider.id)}
                        disabled={modelsLoading[provider.id]}
                        className="flex items-center gap-1.5 px-3 py-1.5 bg-slate-800 hover:bg-slate-700 disabled:opacity-50 rounded-lg text-xs text-slate-200 transition-colors"
                      >
                        {modelsLoading[provider.id] ? (
                          <Loader2 className="w-3.5 h-3.5 animate-spin" />
                        ) : isExpanded ? (
                          <ChevronDown className="w-3.5 h-3.5" />
                        ) : (
                          <ChevronRight className="w-3.5 h-3.5" />
                        )}
                        <Layers className="w-3.5 h-3.5" />
                        Models ({st?.model_count ?? 0})
                        {isExpanded && modelsCached[provider.id] ? " · cached" : ""}
                      </button>
                      <button
                        onClick={() => disconnect(provider.id)}
                        disabled={isBusy}
                        className="flex items-center gap-1.5 px-3 py-1.5 bg-slate-800 hover:bg-red-950/60 hover:text-red-400 rounded-lg text-xs text-slate-300 transition-colors"
                      >
                        <Trash2 className="w-3.5 h-3.5" /> Disconnect
                      </button>
                    </div>

                    {isExpanded && (
                      <div className="mt-3">
                        {modelList.length === 0 ? (
                          <div className="text-xs text-slate-500">No models returned.</div>
                        ) : (
                          <>
                            <div className="flex flex-wrap gap-1.5">
                              {modelList.slice(0, showCount).map((m) => (
                                <ModelChip key={m.id} model={m} />
                              ))}
                            </div>
                            {modelList.length > MODEL_PREVIEW_LIMIT && (
                              <button
                                onClick={() =>
                                  setShowAll((prev) => ({ ...prev, [provider.id]: !prev[provider.id] }))
                                }
                                className="mt-3 text-xs text-blue-400 hover:text-blue-300 transition-colors"
                              >
                                {showAll[provider.id]
                                  ? "Show fewer"
                                  : `Show all ${modelList.length} models`}
                              </button>
                            )}
                          </>
                        )}
                      </div>
                    )}
                  </div>
                )}
              </div>
            </section>
          );
        })}
      </div>

      {ollamaModal && (
        <OllamaModal
          url={ollamaUrl}
          onChange={setOllamaUrl}
          onConnect={() => {
            const entry = catalog.find((p) => p.id === "ollama");
            if (entry) connect(entry, ollamaUrl);
          }}
          busy={busy === "ollama"}
        />
      )}
    </div>
  );
}