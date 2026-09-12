import React from 'react';

export default function MetricCard({ title, value, subtitle, icon: Icon, trend, trendType = 'neutral', badgeText, badgeColor = 'indigo' }) {
  const getBadgeStyle = () => {
    switch (badgeColor) {
      case 'rose':
      case 'critical':
        return 'bg-rose-500/10 text-rose-400 border-rose-500/30';
      case 'amber':
      case 'high':
        return 'bg-amber-500/10 text-amber-400 border-amber-500/30';
      case 'yellow':
      case 'medium':
        return 'bg-yellow-500/10 text-yellow-400 border-yellow-500/30';
      case 'emerald':
      case 'low':
        return 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30';
      default:
        return 'bg-indigo-500/10 text-indigo-400 border-indigo-500/30';
    }
  };

  return (
    <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 shadow-lg relative overflow-hidden transition-all hover:border-slate-700">
      <div className="flex items-start justify-between">
        <div className="space-y-1">
          <p className="text-xs font-medium text-slate-400 font-mono tracking-wider uppercase">{title}</p>
          <div className="flex items-baseline space-x-2">
            <h3 className="text-2xl font-bold text-slate-100 tracking-tight">{value}</h3>
            {trend && (
              <span className={`text-xs font-mono font-medium ${
                trendType === 'positive' ? 'text-emerald-400' : trendType === 'negative' ? 'text-rose-400' : 'text-slate-400'
              }`}>
                {trend}
              </span>
            )}
          </div>
          {subtitle && <p className="text-xs text-slate-400">{subtitle}</p>}
        </div>

        <div className="flex flex-col items-end space-y-2">
          {Icon && (
            <div className="w-10 h-10 rounded-lg bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400">
              <Icon className="w-5 h-5" />
            </div>
          )}
          {badgeText && (
            <span className={`text-[10px] font-mono px-2 py-0.5 rounded border ${getBadgeStyle()}`}>
              {badgeText}
            </span>
          )}
        </div>
      </div>
    </div>
  );
}
