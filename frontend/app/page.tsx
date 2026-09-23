import { Terminal, Cpu, ShieldCheck, Activity } from "lucide-react";

export default function Home() {
  return (
    <div className="min-h-screen flex flex-col">
      {/* Header */}
      <header className="border-b border-slate-800 bg-slate-900/50 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Cpu className="w-6 h-6 text-blue-500" />
            <span className="font-bold text-xl tracking-tight">Advanced Code Garage</span>
          </div>
          <div className="flex items-center gap-4 text-sm text-slate-400">
            <span className="flex items-center gap-1"><Activity className="w-4 h-4 text-green-500" /> System Online</span>
            <span className="px-2 py-1 bg-slate-800 rounded text-xs">Mode: AI-Man</span>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 max-w-7xl mx-auto w-full p-6 grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Left Panel: Agent Swarm Status */}
        <div className="lg:col-span-2 space-y-6">
          <section className="bg-slate-900 border border-slate-800 rounded-xl p-6">
            <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <Terminal className="w-5 h-5 text-purple-400" /> Active Agent Swarm
            </h2>
            <div className="space-y-3">
              {[
                { name: "Mr. Ravish Kumar", role: "Research Lead", status: "Analyzing Market...", color: "text-blue-400" },
                { name: "Mr. Arman Ali Khan", role: "Full Stack Arch", status: "Idle", color: "text-slate-400" },
                { name: "Mr. Sadath Ali Khan", role: "Security Auditor", status: "Monitoring...", color: "text-red-400" },
                { name: "Ms. Kulsum", role: "Token Economist", status: "Optimizing Context", color: "text-yellow-400" },
              ].map((agent, i) => (
                <div key={i} className="flex items-center justify-between p-3 bg-slate-950 rounded-lg border border-slate-800/50">
                  <div>
                    <div className={`font-medium ${agent.color}`}>{agent.name}</div>
                    <div className="text-xs text-slate-500">{agent.role}</div>
                  </div>
                  <div className="text-xs font-mono text-slate-400">{agent.status}</div>
                </div>
              ))}
            </div>
          </section>

          {/* Terminal Output Mockup */}
          <section className="bg-black border border-slate-800 rounded-xl p-4 font-mono text-xs h-64 overflow-y-auto">
            <div className="text-slate-500 mb-2"># System Log initialized...</div>
            <div className="text-green-400">[OK] Connected to Supabase Vector DB</div>
            <div className="text-blue-400">[INFO] Git-Sir awaiting input...</div>
            <div className="text-slate-400 animate-pulse">_</div>
          </section>
        </div>

        {/* Right Panel: Controls & Stats */}
        <div className="space-y-6">
          <section className="bg-slate-900 border border-slate-800 rounded-xl p-6">
            <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <ShieldCheck className="w-5 h-5 text-green-500" /> Security Gate
            </h2>
            <div className="text-sm text-slate-400 space-y-2">
              <p>Zero-Tolerance Audit: <span className="text-green-500">Active</span></p>
              <p>Secrets Scan: <span className="text-green-500">Clean</span></p>
              <p>Branch Protection: <span className="text-blue-500">Enforced</span></p>
            </div>
          </section>
          
          <section className="bg-slate-900 border border-slate-800 rounded-xl p-6">
             <h2 className="text-lg font-semibold mb-4">Quick Actions</h2>
             <button className="w-full py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg font-medium transition">
               Initialize New Project
             </button>
          </section>
        </div>

      </main>
    </div>
  );
}
