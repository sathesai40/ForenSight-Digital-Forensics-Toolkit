import React from 'react';

const VARIANTS = {
  emerald: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
  sky: 'bg-sky-500/10 text-sky-400 border-sky-500/20',
  amber: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
  rose: 'bg-rose-500/10 text-rose-400 border-rose-500/20',
  slate: 'bg-slate-800/60 text-slate-400 border-slate-700/50',
};

export default function StatusBadge({ label, variant = 'slate', dot = true, size = 'sm' }) {
  const colorClass = VARIANTS[variant] || VARIANTS.slate;
  const sizeClass = size === 'xs' ? 'text-[11px] px-2 py-0.5' : 'text-xs px-2.5 py-1';

  return (
    <span className={`inline-flex items-center gap-1.5 font-mono font-medium rounded border ${colorClass} ${sizeClass}`}>
      {dot && (
        <span className="w-1.5 h-1.5 rounded-full bg-current opacity-80" />
      )}
      {label}
    </span>
  );
}
