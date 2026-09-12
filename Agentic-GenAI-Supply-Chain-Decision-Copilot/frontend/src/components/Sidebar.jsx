import React from 'react';
import { 
  LayoutDashboard, 
  Package, 
  TrendingUp, 
  Users, 
  Bot, 
  SlidersHorizontal,
  ShieldCheck
} from 'lucide-react';

export default function Sidebar({ activeTab, setActiveTab }) {
  const navItems = [
    { id: 'overview', label: 'Overview', icon: LayoutDashboard },
    { id: 'inventory', label: 'Inventory', icon: Package },
    { id: 'forecast', label: 'Forecast', icon: TrendingUp },
    { id: 'suppliers', label: 'Suppliers', icon: Users },
    { id: 'copilot', label: 'AI Copilot', icon: Bot, badge: 'Agentic' },
    { id: 'simulation', label: 'What-If Analysis', icon: SlidersHorizontal },
  ];

  return (
    <aside className="w-64 bg-slate-900/95 border-r border-slate-800 flex flex-col justify-between py-4 shrink-0">
      <div className="space-y-1 px-3">
        <div className="px-3 py-2 text-xs font-semibold uppercase tracking-wider text-slate-500 font-mono flex items-center justify-between">
          <span>Navigation</span>
        </div>
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id)}
              className={`w-full flex items-center justify-between px-3 py-2.5 rounded-lg text-sm font-medium transition-all ${
                isActive
                  ? 'bg-indigo-600/15 text-indigo-400 border border-indigo-500/30 font-semibold shadow-sm'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
              }`}
            >
              <div className="flex items-center space-x-3">
                <Icon className={`w-4 h-4 ${isActive ? 'text-indigo-400' : 'text-slate-400'}`} />
                <span>{item.label}</span>
              </div>
              {item.badge && (
                <span className="text-[10px] bg-indigo-500/20 text-indigo-300 font-mono px-1.5 py-0.5 rounded border border-indigo-500/30">
                  {item.badge}
                </span>
              )}
            </button>
          );
        })}
      </div>

      <div className="px-3 space-y-3">
        <div className="px-3 py-2.5 rounded-lg bg-slate-950/80 border border-slate-800/80 text-xs text-slate-400 font-mono space-y-1.5">
          <div className="text-slate-300 font-semibold flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
            LangGraph Orchestrator
          </div>
          <p className="text-[11px] text-slate-500 leading-tight">
            Supervisor Planner online. Tools: SQL, RAG, XGBoost, Simulation.
          </p>
        </div>

        <div className="px-3 py-2 text-[10px] text-slate-500 font-mono text-center border-t border-slate-800/60 flex items-center justify-center gap-1">
          <ShieldCheck className="w-3 h-3 text-emerald-500" />
          <span>Security Guardrails v1.0</span>
        </div>
      </div>
    </aside>
  );
}
