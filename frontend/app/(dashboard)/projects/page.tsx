"use client";

import { useState } from "react";
import { FolderGit2, Plus, Loader2, RefreshCw, GitBranch, CheckCircle2, AlertTriangle } from "lucide-react";
import { initializeProject, getProjectStatus } from "@/lib/api";
import type { ProjectInitResponse, ProjectStatus } from "@/lib/types";

interface TrackedProject {
  project_id: string;
  name: string;
  description?: string;
  status: string;
  message: string;
  agents_assigned: string[];
  statusInfo?: ProjectStatus;
  statusError?: boolean;
}

export default function ProjectsPage() {
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [repoUrl, setRepoUrl] = useState("");
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [projects, setProjects] = useState<TrackedProject[]>([]);
  const [checkingId, setCheckingId] = useState<string | null>(null);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;
    setCreating(true);
    setError(null);
    try {
      const result: ProjectInitResponse = await initializeProject({
        name: name.trim(),
        description: description.trim() || undefined,
        repo_url: repoUrl.trim() || undefined,
      });
      setProjects((prev) => [{ ...result, description: description.trim() || undefined }, ...prev]);
      setName("");
      setDescription("");
      setRepoUrl("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to initialize project");
    } finally {
      setCreating(false);
    }
  };

  const handleCheck = async (projectId: string) => {
    setCheckingId(projectId);
    try {
      const status = await getProjectStatus(projectId);
      setProjects((prev) =>
        prev.map((p) => (p.project_id === projectId ? { ...p, statusInfo: status, statusError: false } : p))
      );
    } catch {
      setProjects((prev) =>
        prev.map((p) => (p.project_id === projectId ? { ...p, statusError: true } : p))
      );
    } finally {
      setCheckingId(null);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold flex items-center gap-2">
          <FolderGit2 className="w-6 h-6 text-blue-400" /> Projects
        </h1>
        <p className="text-sm text-slate-500 mt-1">
          Initialize new projects and dispatch the agent swarm.
        </p>
      </div>

      {error && (
        <div className="flex items-center gap-2 p-3 bg-red-950/40 border border-red-800/40 rounded-xl text-sm text-red-300">
          <AlertTriangle className="w-4 h-4" /> {error}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <section className="bg-slate-900 border border-slate-800 rounded-xl p-6 lg:col-span-1 self-start">
          <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <Plus className="w-5 h-5 text-blue-400" /> New Project
          </h2>
          <form onSubmit={handleCreate} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1">Project Name *</label>
              <input
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
                placeholder="e.g. acg-ecommerce"
                className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white placeholder-slate-600 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1">Description</label>
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                rows={3}
                placeholder="What should the swarm build?"
                className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white placeholder-slate-600 focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1">
                Repository URL (optional)
              </label>
              <input
                value={repoUrl}
                onChange={(e) => setRepoUrl(e.target.value)}
                placeholder="https://github.com/..."
                className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white placeholder-slate-600 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <button
              type="submit"
              disabled={creating}
              className="w-full flex items-center justify-center gap-2 py-2.5 bg-blue-600 hover:bg-blue-500 disabled:bg-slate-700 disabled:cursor-not-allowed text-white rounded-lg font-medium transition"
            >
              {creating ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" /> Dispatching Swarm...
                </>
              ) : (
                <>
                  <Plus className="w-4 h-4" /> Initialize Project
                </>
              )}
            </button>
          </form>
        </section>

        <section className="lg:col-span-2 space-y-3">
          <h2 className="text-lg font-semibold flex items-center gap-2">
            <GitBranch className="w-5 h-5 text-purple-400" /> Active Projects
          </h2>
          {projects.length === 0 ? (
            <div className="bg-slate-900 border border-slate-800 border-dashed rounded-xl p-8 text-center text-sm text-slate-500">
              No projects yet. Initialize one to dispatch the agent swarm.
            </div>
          ) : (
            projects.map((project) => (
              <div key={project.project_id} className="bg-slate-900 border border-slate-800 rounded-xl p-5">
                <div className="flex items-start justify-between gap-4">
                  <div className="min-w-0">
                    <div className="font-semibold text-slate-200 truncate">{project.name}</div>
                    <div className="text-xs font-mono text-slate-500 mt-0.5">{project.project_id}</div>
                    {project.description && (
                      <div className="text-sm text-slate-400 mt-1">{project.description}</div>
                    )}
                  </div>
                  <button
                    onClick={() => handleCheck(project.project_id)}
                    disabled={checkingId === project.project_id}
                    className="shrink-0 flex items-center gap-1.5 px-3 py-1.5 bg-slate-800 hover:bg-slate-700 rounded-lg text-xs text-slate-300 transition-colors disabled:opacity-60"
                  >
                    {checkingId === project.project_id ? (
                      <Loader2 className="w-3.5 h-3.5 animate-spin" />
                    ) : (
                      <RefreshCw className="w-3.5 h-3.5" />
                    )}
                    Check Status
                  </button>
                </div>

                <div className="text-xs mt-3 text-slate-500 flex flex-wrap gap-x-4 gap-y-1">
                  <span className="flex items-center gap-1.5">
                    <CheckCircle2 className="w-3.5 h-3.5 text-green-500" />
                    {project.status}
                  </span>
                  <span>Assigned: {project.agents_assigned.join(", ")}</span>
                </div>

                {project.statusInfo && (
                  <div className="mt-4">
                    <div className="flex items-center justify-between text-xs text-slate-400 mb-1.5">
                      <span className="flex items-center gap-1.5">
                        {project.statusInfo.current_agent} — {project.statusInfo.task}
                      </span>
                      <span className="font-mono">{project.statusInfo.progress}%</span>
                    </div>
                    <div className="h-2 bg-slate-800 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-blue-500 rounded-full transition-all"
                        style={{ width: `${project.statusInfo.progress}%` }}
                      />
                    </div>
                  </div>
                )}

                {project.statusError && (
                  <div className="mt-3 text-xs text-red-400">Failed to fetch status. Backend may be waking up.</div>
                )}
              </div>
            ))
          )}
        </section>
      </div>
    </div>
  );
}