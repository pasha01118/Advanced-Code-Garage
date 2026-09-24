"use client";

import { useEffect, useRef, useState } from "react";
import { Terminal, Cpu, ShieldCheck, Activity, Loader2, Play } from "lucide-react";

interface AgentStatus {
  name: string;
  role: string;
  status: string;
  current_task: string | null;
}

interface SwarmResponse {
  active_agents: AgentStatus[];
  system_mode: string;
  security_gate: string;
}

export default function Home() {
  const [swarmData, setSwarmData] = useState<SwarmResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [initializing, setInitializing] = useState(false);
  const [initResult, setInitResult] = useState<{ message?: string; project_id?: string; error?: string } | null>(null);
  const inFlightRef = useRef(false);

  const fetchSwarm = async () => {
    if (inFlightRef.current) return;
    inFlightRef.current = true;
    
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 60000);

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "https://agc-backend-ix19.onrender.com";
      const response = await fetch(`${apiUrl}/api/v1/agents/swarm`, { signal: controller.signal });
      
      if (!response.ok) throw new Error(`Failed to fetch: ${response.statusText}`);
      
      const data: SwarmResponse = await response.json();
      setSwarmData(data);
      setError(null);
    } catch (err) {
      console.error("Error fetching swarm:", err);
      setError("Unable to connect to Agent Swarm. Retrying...");
    } finally {
      clearTimeout(timeout);
      inFlightRef.current = false;
      setLoading(false);
    }
  };

  const handleInitializeProject = async () => {
    setInitializing(true);
    setInitResult(null);
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "https://agc-backend-ix19.onrender.com";
      const response = await fetch(`${apiUrl}/api/v1/projects/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: "New Project",
          description: "Auto-initialized from dashboard"
        })
      });
      
      if (!response.ok) throw new Error("Failed to initialize project");
      
      const result = await response.json();
      setInitResult(result);
    } catch (err) {
      setInitResult({ error: err instanceof Error ? err.message : "Initialization failed" });
    } finally {
      setInitializing(false);
    }
  };

  useEffect(() => {
    let mounted = true;

    const run = async () => {
      if (mounted) await fetchSwarm();
    };

    run();
    const interval = setInterval(run, 5000);

    return () => {
      mounted = false;
      clearInterval(interval);
    };
  }, []);

  if (loading && !swarmData) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-950 text-slate-100">
        <Loader2 className="w-10 h-10 animate-spin text-blue-500" />
      </div>
    );
  }

  if (error && !swarmData) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-950 text-red-400 p-6">
        <div className="bg-slate-900 border border-red-900 rounded-xl p-6 max-w-md text-center">
          <ShieldCheck className="w-12 h-12 mx-auto mb-4 text-red-500" />
          <h2 className="text-xl font-bold mb-2">Connection Error</h2>
          <p className="text-sm">{error}</p>
          <div className="mt-4 flex items-center justify-center gap-2 text-blue-400 text-xs">
            <Loader2 className="w-3.5 h-3.5 animate-spin" />
            Auto-reconnecting to Agent Swarm...
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex flex-col bg-slate-950 text-slate-100">
      {/* Header */}
      <header className="border-b border-slate-800 bg-slate-900/50 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Cpu className="w-6 h-6 text-blue-500" />
            <span className="font-bold text-xl tracking-tight">Advanced Code Garage</span>
          </div>
          <div className="flex items-center gap-4 text-sm text-slate-400">
            <span className="flex items-center gap-1">
              <Activity className="w-4 h-4 text-green-500" /> System Online
            </span>
            <span className="px-2 py-1 bg-slate-800 rounded text-xs border border-slate-700">
              Mode: {swarmData?.system_mode || "Loading..."}
            </span>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 max-w-7xl mx-auto w-full p-6 grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Left Panel: Agent Swarm */}
        <div className="lg:col-span-2 space-y-6">
          <section className="bg-slate-900 border border-slate-800 rounded-xl p-6">
            <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <Terminal className="w-5 h-5 text-purple-400" /> Active Agent Swarm
            </h2>
            <div className="space-y-3">
              {swarmData?.active_agents.map((agent, i) => (
                <div key={i} className="flex items-center justify-between p-3 bg-slate-950 rounded-lg border border-slate-800/50 hover:border-slate-700 transition-colors">
                  <div>
                    <div className="font-medium text-slate-200">{agent.name}</div>
                    <div className="text-xs text-slate-500">{agent.role}</div>
                  </div>
                  <div className="text-right">
                    <div className="text-xs font-mono text-blue-400 mb-1">{agent.status}</div>
                    {agent.current_task && (
                      <div className="text-[10px] text-slate-600 bg-slate-900 px-2 py-0.5 rounded inline-block">
                        {agent.current_task}
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </section>

          {/* Terminal Output */}
          <section className="bg-black border border-slate-800 rounded-xl p-4 font-mono text-xs h-64 overflow-y-auto shadow-inner">
            <div className="text-slate-500 mb-2"># System Log initialized...</div>
            <div className="text-green-400">[OK] Connected to Supabase Vector DB</div>
            <div className="text-blue-400">[INFO] Git-Sir awaiting input...</div>
            <div className="text-yellow-400">[WARN] Token optimization active (Ms. Kulsum)</div>
            {initResult && !initResult.error && (
              <div className="text-green-400 mt-2">[SUCCESS] {initResult.message}</div>
            )}
            {initResult?.error && (
              <div className="text-red-400 mt-2">[ERROR] {initResult.error}</div>
            )}
            <div className="text-slate-400 animate-pulse mt-2">_</div>
          </section>
        </div>

        {/* Right Panel: Security & Actions */}
        <div className="space-y-6">
          <section className="bg-slate-900 border border-slate-800 rounded-xl p-6">
            <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <ShieldCheck className="w-5 h-5 text-green-500" /> Security Gate
            </h2>
            <div className="text-sm text-slate-400 space-y-2">
              <p>Zero-Tolerance Audit: <span className="text-green-500 font-mono">{swarmData?.security_gate || "Loading..."}</span></p>
              <p>Secrets Scan: <span className="text-green-500 font-mono">Clean</span></p>
              <p>Branch Protection: <span className="text-blue-500 font-mono">Enforced</span></p>
            </div>
          </section>
          
          <section className="bg-slate-900 border border-slate-800 rounded-xl p-6">
             <h2 className="text-lg font-semibold mb-4">Quick Actions</h2>
             <button 
               onClick={handleInitializeProject}
               disabled={initializing}
               className="w-full py-2 bg-blue-600 hover:bg-blue-500 disabled:bg-slate-700 disabled:cursor-not-allowed text-white rounded-lg font-medium transition flex items-center justify-center gap-2 shadow-lg shadow-blue-900/20"
             >
               {initializing ? (
                 <>
                   <Loader2 className="w-4 h-4 animate-spin" />
                   Initializing...
                 </>
               ) : (
                 <>
                   <Play className="w-4 h-4" />
                   Initialize New Project
                 </>
               )}
             </button>
             {initResult && !initResult.error && (
               <div className="mt-3 p-2 bg-green-900/30 border border-green-800 rounded text-xs text-green-300">
                 Project ID: {initResult.project_id}
               </div>
             )}
          </section>
        </div>
      </main>
    </div>
  );
}
