import React from 'react';
import { AlertTriangle, RefreshCw, ShieldCheck } from 'lucide-react';

export default function ErrorMessage({ error, onRetry, title = "Request Failed" }) {
  const isRateLimit = error?.status === 429 || error?.code === 'RATE_LIMIT_EXCEEDED';
  const isNetwork = error?.status === 0 || error?.code === 'NETWORK_ERROR';
  const isGuardrail = error?.message?.includes('blocked') || error?.message?.includes('Guardrail');

  return (
    <div className="rounded-xl bg-slate-900 border border-rose-500/30 p-6 text-center space-y-4 max-w-lg mx-auto shadow-xl">
      <div className="w-12 h-12 rounded-full bg-rose-500/10 border border-rose-500/30 flex items-center justify-center text-rose-400 mx-auto">
        {isGuardrail ? <ShieldCheck className="w-6 h-6" /> : <AlertTriangle className="w-6 h-6" />}
      </div>

      <div className="space-y-1">
        <h4 className="text-base font-semibold text-slate-100">{title}</h4>
        <p className="text-xs text-slate-400 leading-relaxed">
          {isRateLimit
            ? "Request limit exceeded. Rate limiter requires a temporary cooldown period."
            : isNetwork
            ? "Unable to reach FastAPI backend service. Verify backend is running at http://localhost:8000."
            : error?.message || "An unexpected error occurred while fetching data."}
        </p>
      </div>

      {onRetry && (
        <button
          onClick={onRetry}
          className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold transition-all shadow-md"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          <span>Try Again</span>
        </button>
      )}
    </div>
  );
}
