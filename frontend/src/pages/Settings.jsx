import React from 'react';
import { useOutletContext } from 'react-router-dom';
import { Settings as SettingsIcon, Database, Shield, Globe, HardDrive, Key, RefreshCw } from 'lucide-react';
import StatusBadge from '../components/layout/StatusBadge';

export default function Settings() {
  const { health, isRefreshing, refreshHealth } = useOutletContext();

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-slate-800/80">
        <div>
          <div className="flex items-center gap-2.5">
            <h1 className="text-xl font-bold tracking-tight text-slate-100">
              System Configuration & Environment
            </h1>
            <StatusBadge label="READ-ONLY CONFIG" variant="slate" />
          </div>
          <p className="text-sm text-slate-400 mt-1">
            Active forensic workbench environment variables, storage mounts, and network boundaries.
          </p>
        </div>

        <button
          onClick={refreshHealth}
          disabled={isRefreshing}
          className="inline-flex items-center gap-2 px-3 py-2 bg-slate-900 hover:bg-slate-800 text-slate-300 text-xs font-mono rounded border border-slate-800 transition-colors"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${isRefreshing ? 'animate-spin text-sky-400' : ''}`} />
          <span>Reload Environment Diagnostics</span>
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Core Storage Mounts */}
        <div className="bg-[#0f1624] border border-slate-800/80 rounded-lg p-5 space-y-4">
          <div className="flex items-center gap-2 text-sky-400 border-b border-slate-800/80 pb-3">
            <Database className="w-4 h-4" />
            <h2 className="text-sm font-semibold text-slate-200">Storage & Database Mounts</h2>
          </div>

          <div className="space-y-3 text-xs font-mono">
            <div>
              <span className="text-slate-500 block text-[11px]">SQLITE_DATABASE_PATH</span>
              <span className="text-slate-200 break-all">
                {health?.diagnostics?.database_path || './data/forensight.db'}
              </span>
            </div>

            <div>
              <span className="text-slate-500 block text-[11px]">EVIDENCE_VAULT_DIR</span>
              <span className="text-slate-200 break-all">
                {health?.diagnostics?.vault_path || './data/vault'}
              </span>
            </div>

            <div>
              <span className="text-slate-500 block text-[11px]">STORAGE_INTEGRITY</span>
              <span className="text-emerald-400">
                {health?.vault_ready ? 'Writable & Isolated' : 'Validating...'}
              </span>
            </div>
          </div>
        </div>

        {/* Security & Network Policies */}
        <div className="bg-[#0f1624] border border-slate-800/80 rounded-lg p-5 space-y-4">
          <div className="flex items-center gap-2 text-emerald-400 border-b border-slate-800/80 pb-3">
            <Shield className="w-4 h-4" />
            <h2 className="text-sm font-semibold text-slate-200">Security & Isolation Policies</h2>
          </div>

          <div className="space-y-3 text-xs font-mono">
            <div>
              <span className="text-slate-500 block text-[11px]">ENVIRONMENT_MODE</span>
              <span className="text-sky-300 uppercase">
                {health?.environment || 'development'}
              </span>
            </div>

            <div>
              <span className="text-slate-500 block text-[11px]">ALLOWED_CORS_ORIGINS</span>
              <span className="text-slate-200">
                http://localhost:5173, http://127.0.0.1:5173
              </span>
            </div>

            <div>
              <span className="text-slate-500 block text-[11px]">TIMESTAMP_STANDARD</span>
              <span className="text-emerald-400">
                ISO 8601 UTC (Strict Enforced)
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
