import React, { useState, useEffect } from 'react';
import { Activity, ShieldCheck, Database, Server } from 'lucide-react';
import { getHealthStatus } from '../api/health';

export default function Header() {
  const [health, setHealth] = useState({ status: 'checking', app: 'SupplyChain AI' });

  useEffect(() => {
    let isMounted = true;
    const checkHealth = async () => {
      try {
        const data = await getHealthStatus();
        if (isMounted) setHealth(data);
      } catch (err) {
        if (isMounted) setHealth({ status: 'offline', app: 'SupplyChain AI' });
      }
    };

    checkHealth();
    const interval = setInterval(checkHealth, 15000);
    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, []);

  const isOnline = health.status === 'ok' || health.status === 'healthy';

  return (
    <header className="h-16 bg-slate-900 border-b border-slate-800 px-6 flex items-center justify-between sticky top-0 z-30 shadow-md">
      <div className="flex items-center space-x-3">
        <div className="w-9 h-9 rounded-lg bg-indigo-600 flex items-center justify-center text-white font-bold text-lg shadow-lg shadow-indigo-500/20">
          <Activity className="w-5 h-5" />
        </div>
        <div>
          <h1 className="font-semibold text-slate-100 text-lg tracking-tight flex items-center gap-2">
            SupplyChain AI
            <span className="text-xs bg-indigo-950 text-indigo-400 border border-indigo-800/60 px-2 py-0.5 rounded-full font-mono font-normal">
              v1.0.0
            </span>
          </h1>
          <p className="text-xs text-slate-400">Agentic Decision-Support Copilot</p>
        </div>
      </div>

      <div className="flex items-center space-x-4 text-xs font-mono">
        <div className="flex items-center space-x-2 px-3 py-1.5 rounded-md bg-slate-800/80 border border-slate-700/60">
          <Server className="w-3.5 h-3.5 text-slate-400" />
          <span className="text-slate-400">API Status:</span>
          <span className={`flex items-center gap-1.5 font-semibold ${
            isOnline ? 'text-emerald-400' : 'text-rose-400'
          }`}>
            <span className={`w-2 h-2 rounded-full ${
              isOnline ? 'bg-emerald-400 animate-pulse' : 'bg-rose-400'
            }`} />
            {isOnline ? 'ONLINE' : 'BACKEND OFFLINE'}
          </span>
        </div>

        <div className="hidden md:flex items-center space-x-2 px-3 py-1.5 rounded-md bg-slate-800/80 border border-slate-700/60 text-slate-300">
          <Database className="w-3.5 h-3.5 text-indigo-400" />
          <span>PostgreSQL + Vector</span>
        </div>

        <div className="hidden lg:flex items-center space-x-2 px-3 py-1.5 rounded-md bg-slate-800/80 border border-slate-700/60 text-slate-300">
          <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
          <span>Guardrails Active</span>
        </div>
      </div>
    </header>
  );
}
