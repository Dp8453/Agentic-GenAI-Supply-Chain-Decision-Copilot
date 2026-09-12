import React from 'react';

export default function LoadingSkeleton({ type = 'table', count = 3 }) {
  if (type === 'cards') {
    return (
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 animate-pulse">
        {Array.from({ length: count }).map((_, i) => (
          <div key={i} className="h-28 rounded-xl bg-slate-900 border border-slate-800 p-4 space-y-3">
            <div className="h-3 w-1/2 bg-slate-800 rounded" />
            <div className="h-6 w-3/4 bg-slate-800 rounded" />
            <div className="h-3 w-1/3 bg-slate-800 rounded" />
          </div>
        ))}
      </div>
    );
  }

  if (type === 'chart') {
    return (
      <div className="h-64 rounded-xl bg-slate-900 border border-slate-800 p-6 flex items-center justify-center animate-pulse">
        <div className="space-y-4 w-full">
          <div className="h-4 w-1/4 bg-slate-800 rounded" />
          <div className="h-40 w-full bg-slate-800/60 rounded" />
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-3 animate-pulse">
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} className="h-12 rounded-lg bg-slate-900 border border-slate-800/80 w-full" />
      ))}
    </div>
  );
}
