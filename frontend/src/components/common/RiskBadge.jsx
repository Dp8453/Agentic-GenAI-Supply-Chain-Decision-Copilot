import React from 'react';
import { AlertTriangle, AlertOctagon, CheckCircle2, Info } from 'lucide-react';

export default function RiskBadge({ level = 'LOW', score = null, size = 'normal' }) {
  const normalizedLevel = (level || 'LOW').toUpperCase();

  const getStyle = () => {
    switch (normalizedLevel) {
      case 'CRITICAL':
        return {
          bg: 'bg-rose-950/80 text-rose-300 border-rose-600/50',
          dot: 'bg-rose-400',
          icon: AlertOctagon,
        };
      case 'HIGH':
        return {
          bg: 'bg-amber-950/80 text-amber-300 border-amber-600/50',
          dot: 'bg-amber-400',
          icon: AlertTriangle,
        };
      case 'MEDIUM':
        return {
          bg: 'bg-yellow-950/80 text-yellow-300 border-yellow-600/50',
          dot: 'bg-yellow-400',
          icon: Info,
        };
      case 'LOW':
      default:
        return {
          bg: 'bg-emerald-950/80 text-emerald-300 border-emerald-600/50',
          dot: 'bg-emerald-400',
          icon: CheckCircle2,
        };
    }
  };

  const style = getStyle();
  const Icon = style.icon;

  const isSmall = size === 'small';

  return (
    <span className={`inline-flex items-center gap-1.5 font-mono rounded-full border font-semibold ${style.bg} ${
      isSmall ? 'px-2 py-0.5 text-[10px]' : 'px-2.5 py-1 text-xs'
    }`}>
      <span className={`rounded-full ${style.dot} ${isSmall ? 'w-1.5 h-1.5' : 'w-2 h-2 animate-pulse'}`} />
      <Icon className={isSmall ? 'w-3 h-3' : 'w-3.5 h-3.5'} />
      <span>{normalizedLevel}</span>
      {score !== null && score !== undefined && (
        <span className="opacity-75 font-normal ml-0.5">({score})</span>
      )}
    </span>
  );
}
