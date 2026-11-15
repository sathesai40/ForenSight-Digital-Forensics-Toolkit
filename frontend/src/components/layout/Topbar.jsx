import React, { useState, useEffect } from 'react';
import { Activity, Clock, ShieldCheck, AlertCircle, RefreshCw, Server } from 'lucide-react';
import StatusBadge from './StatusBadge';

export default function Topbar({ health, isRefreshing, onRefreshHealth, connectionError }) {
  const [utcTime, setUtcTime] = useState('');

  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      // Format as ISO UTC: YYYY-MM-DD HH:mm:ss UTC
      const iso = now.toISOString().replace('T', ' ').substring(0, 19) + ' UTC';
      setUtcTime(iso);
    };
    updateTime();
    const interval = setInterval(updateTime, 1000);
    return () => clearInterval(interval);
  }, []);

  const isOnline = health?.database_connected && !connectionError;

  return (
    <header className="h-16 border-b border-slate-800/80 bg-[#090d16]/95 backdrop-blur px-6 flex items-center justify-between z-10">
      {/* Left: Case workspace context & mission title */}
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2">
          <span className="text-xs font-mono text-slate-500 uppercase tracking-wider">Session:</span>
          <span className="text-xs font-mono font-medium text-slate-200 bg-slate-900/80 border border-slate-800 px-2 py-0.5 rounded">
            FORENSIC WORKBENCH
          </span>
        </div>
        <div className="hidden md:flex items-center gap-1.5 text-xs text-slate-400 font-mono">
          <span className="text-slate-600">/</span>
          <span>PHASE 1 CORE ENGINE</span>
        </div>
      </div>

      {/* Right: Telemetry Indicators */}
      <div className="flex items-center gap-4">
        {/* UTC Clock */}
        <div className="hidden sm:flex items-center gap-2 font-mono text-xs text-slate-300 bg-slate-900/60 border border-slate-800/80 px-2.5 py-1 rounded">
          <Clock className="w-3.5 h-3.5 text-sky-400" />
          <span>{utcTime || 'SYNCHRONIZING...'}</span>
        </div>

        {/* Backend / Health Status Pill */}
        {isOnline ? (
          <div className="flex items-center gap-2 bg-emerald-500/10 border border-emerald-500/25 px-2.5 py-1 rounded">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
            </span>
            <span className="text-[11px] font-mono font-medium text-emerald-400">
              CORE ONLINE
            </span>
          </div>
        ) : (
          <div className="flex items-center gap-2 bg-rose-500/10 border border-rose-500/25 px-2.5 py-1 rounded">
            <AlertCircle className="w-3.5 h-3.5 text-rose-400" />
            <span className="text-[11px] font-mono font-medium text-rose-400">
              BACKEND OFFLINE
            </span>
          </div>
        )}

        {/* Manual Telemetry Refresh Button */}
        <button
          onClick={onRefreshHealth}
          disabled={isRefreshing}
          title="Refresh Backend Telemetry & Diagnostic Health"
          className="p-1.5 text-slate-400 hover:text-slate-200 hover:bg-slate-800/80 rounded border border-slate-800/80 transition-colors disabled:opacity-50"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${isRefreshing ? 'animate-spin text-sky-400' : ''}`} />
        </button>
      </div>
    </header>
  );
}
