import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  Shield,
  FolderKanban,
  HardDrive,
  Clock,
  FileSearch,
  ScrollText,
  Settings,
  Database,
  Lock,
} from 'lucide-react';

const NAV_ITEMS = [
  { path: '/', label: 'Overview', icon: Shield },
  { path: '/cases', label: 'Investigation Cases', icon: FolderKanban },
  { path: '/evidence', label: 'Evidence Vault', icon: HardDrive },
  { path: '/timeline', label: 'Event Timeline', icon: Clock },
  { path: '/logs', label: 'Log Analysis', icon: FileSearch },
  { path: '/audit', label: 'Audit Trail', icon: ScrollText },
  { path: '/settings', label: 'Configuration', icon: Settings },
];

export default function Sidebar({ health }) {
  return (
    <aside className="w-64 flex-shrink-0 flex flex-col border-r border-slate-800/80 bg-[#090d16] select-none">
      {/* Brand Header */}
      <div className="h-16 flex items-center px-5 border-b border-slate-800/80 gap-3">
        <div className="w-9 h-9 rounded-lg bg-sky-500/10 border border-sky-500/20 flex items-center justify-center text-sky-400 shadow-sm shadow-sky-500/10">
          <Shield className="w-5 h-5 stroke-[2.2]" />
        </div>
        <div className="flex flex-col">
          <div className="flex items-center gap-1.5">
            <span className="font-semibold text-sm tracking-wider text-slate-100 uppercase">ForenSight</span>
            <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-sky-500/10 text-sky-400 border border-sky-500/20">
              v0.1
            </span>
          </div>
          <span className="text-[11px] text-slate-500 font-mono tracking-tight">Forensics Toolkit</span>
        </div>
      </div>

      {/* Navigation Links */}
      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
        <div className="px-3 pb-2 text-[10px] font-mono uppercase tracking-wider text-slate-500">
          Forensic Modules
        </div>
        {NAV_ITEMS.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.path}
              to={item.path}
              end={item.path === '/'}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2 rounded-md text-xs font-medium transition-colors ${
                  isActive
                    ? 'bg-sky-500/15 text-sky-300 border border-sky-500/30'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/60 border border-transparent'
                }`
              }
            >
              <Icon className="w-4 h-4 flex-shrink-0" />
              <span>{item.label}</span>
            </NavLink>
          );
        })}
      </nav>

      {/* Forensic System Integrity Footer */}
      <div className="p-3 border-t border-slate-800/80 bg-[#070b12]">
        <div className="rounded-md border border-slate-800/80 bg-slate-900/40 p-2.5 space-y-2">
          <div className="flex items-center justify-between text-[11px]">
            <span className="text-slate-500 flex items-center gap-1.5 font-mono">
              <Database className="w-3 h-3 text-sky-400" /> Storage
            </span>
            <span className="text-slate-300 font-mono text-[10px]">
              {health?.diagnostics?.database || 'SQLite (WAL)'}
            </span>
          </div>
          <div className="flex items-center justify-between text-[11px]">
            <span className="text-slate-500 flex items-center gap-1.5 font-mono">
              <Lock className="w-3 h-3 text-emerald-400" /> Integrity
            </span>
            <span className="text-emerald-400 font-mono text-[10px]">SHA-256 Validated</span>
          </div>
          <div className="pt-1.5 border-t border-slate-800/60 flex items-center justify-between text-[10px] font-mono text-slate-500">
            <span>MODE:</span>
            <span className="text-sky-400 font-semibold">AUTHORIZED EXAMINER</span>
          </div>
        </div>
      </div>
    </aside>
  );
}
