import React, { useState, useEffect } from 'react';
import { useOutletContext, Link } from 'react-router-dom';
import {
  ShieldCheck,
  ShieldAlert,
  Database,
  HardDrive,
  FolderKanban,
  ScrollText,
  CheckCircle2,
  AlertTriangle,
  AlertCircle,
  Clock,
  ArrowRight,
  FileSearch,
  FileText,
  Download,
  Activity,
  Layers,
  User,
  RefreshCw,
} from 'lucide-react';
import api from '../api/client';
import StatusBadge from '../components/layout/StatusBadge';

export default function Dashboard() {
  const { health, isRefreshing: healthRefreshing, refreshHealth } = useOutletContext();
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [downloadingCaseId, setDownloadingCaseId] = useState(null);

  const loadStats = async () => {
    setLoading(true);
    try {
      const data = await api.getDashboardStats();
      setStats(data);
      setError(null);
    } catch (err) {
      setError(`Failed to retrieve dashboard statistics: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadStats();
  }, []);

  const handleDownloadPdf = async (caseId, caseNumber) => {
    setDownloadingCaseId(caseId);
    try {
      await api.downloadReportPdf(caseId, caseNumber, 'Lead Forensic Examiner');
    } catch (err) {
      alert(`Report download error: ${err.message}`);
    } finally {
      setDownloadingCaseId(null);
    }
  };

  const formatBytes = (bytes) => {
    if (!bytes || bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const getPriorityVariant = (priority) => {
    switch (priority) {
      case 'CRITICAL': return 'rose';
      case 'HIGH': return 'rose';
      case 'MEDIUM': return 'amber';
      case 'LOW': return 'sky';
      default: return 'slate';
    }
  };

  const getStatusVariant = (status) => {
    switch (status) {
      case 'OPEN': return 'sky';
      case 'IN_PROGRESS': return 'amber';
      case 'UNDER_REVIEW': return 'amber';
      case 'CLOSED': return 'emerald';
      case 'ARCHIVED': return 'slate';
      default: return 'slate';
    }
  };

  return (
    <div className="max-w-7xl mx-auto space-y-8">
      {/* Header Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-6 border-b border-slate-800/80">
        <div>
          <div className="flex items-center gap-2.5">
            <h1 className="text-xl md:text-2xl font-bold tracking-tight text-slate-100">
              Forensic Investigation Dashboard
            </h1>
            <StatusBadge label="PHASE 4 VERIFIED" variant="emerald" />
          </div>
          <p className="text-sm text-slate-400 mt-1">
            Real-time telemetry, live case status distributions, cryptographic evidence health, and official PDF exports.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <button
            onClick={() => { refreshHealth(); loadStats(); }}
            disabled={loading}
            className="p-2 text-slate-400 hover:text-slate-200 hover:bg-slate-900 rounded border border-slate-800 transition-colors"
            title="Refresh All Metrics"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin text-sky-400' : ''}`} />
          </button>
          <Link
            to="/cases"
            className="inline-flex items-center gap-2 bg-sky-600 hover:bg-sky-500 text-white text-xs font-semibold px-3.5 py-2 rounded-md transition-colors shadow-sm shadow-sky-600/20"
          >
            <FolderKanban className="w-3.5 h-3.5" />
            <span>Case Management</span>
          </Link>
          <Link
            to="/evidence"
            className="inline-flex items-center gap-2 bg-slate-900 hover:bg-slate-800 text-slate-300 text-xs font-medium px-3.5 py-2 rounded-md border border-slate-800 transition-colors"
          >
            <HardDrive className="w-3.5 h-3.5 text-slate-400" />
            <span>Evidence Vault</span>
          </Link>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-lg bg-rose-500/10 border border-rose-500/20 flex items-center gap-3 text-rose-300 text-xs">
          <AlertCircle className="w-4 h-4 text-rose-400 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Real Statistics Metric Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Cases Metric */}
        <div className="bg-[#0f1624] border border-slate-800/80 rounded-lg p-5 space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono text-slate-400 uppercase tracking-wider">Investigation Cases</span>
            <FolderKanban className="w-4 h-4 text-sky-400" />
          </div>
          <div>
            <div className="text-2xl font-mono font-bold text-slate-100">
              {stats?.total_cases ?? 0}
            </div>
            <div className="text-xs font-mono text-slate-400 mt-1 flex items-center gap-2">
              <span className="text-sky-400 font-semibold">{stats?.cases_by_status?.['OPEN'] || 0} Open</span>
              <span>&bull;</span>
              <span className="text-amber-400 font-semibold">{stats?.cases_by_status?.['IN_PROGRESS'] || 0} Active</span>
            </div>
          </div>
          <div className="pt-2 border-t border-slate-800/60 text-[11px] font-mono text-slate-500 flex justify-between">
            <span>Critical Priority:</span>
            <span className="text-rose-400 font-bold">{stats?.cases_by_priority?.['CRITICAL'] || 0}</span>
          </div>
        </div>

        {/* Evidence Artifacts Metric */}
        <div className="bg-[#0f1624] border border-slate-800/80 rounded-lg p-5 space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono text-slate-400 uppercase tracking-wider">Evidence Ingested</span>
            <HardDrive className="w-4 h-4 text-emerald-400" />
          </div>
          <div>
            <div className="text-2xl font-mono font-bold text-slate-100">
              {stats?.total_evidence ?? 0}
            </div>
            <div className="text-xs font-mono text-emerald-400 mt-1 flex items-center gap-1.5">
              <ShieldCheck className="w-3.5 h-3.5" />
              <span>{stats?.evidence_by_status?.['VERIFIED'] || 0} Verified Untampered</span>
            </div>
          </div>
          <div className="pt-2 border-t border-slate-800/60 text-[11px] font-mono text-slate-500 flex justify-between">
            <span>Vault Volume:</span>
            <span className="text-slate-300">{formatBytes(stats?.total_evidence_bytes || 0)}</span>
          </div>
        </div>

        {/* Security Events Metric */}
        <div className="bg-[#0f1624] border border-slate-800/80 rounded-lg p-5 space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono text-slate-400 uppercase tracking-wider">Correlated Events</span>
            <Activity className="w-4 h-4 text-amber-400" />
          </div>
          <div>
            <div className="text-2xl font-mono font-bold text-slate-100">
              {stats?.total_events ?? 0}
            </div>
            <div className="text-xs font-mono text-slate-400 mt-1 flex items-center gap-2">
              <span className="text-rose-400 font-semibold">{stats?.events_by_severity?.['CRITICAL'] || 0} Critical</span>
              <span>&bull;</span>
              <span className="text-amber-400 font-semibold">{stats?.events_by_severity?.['HIGH'] || 0} High</span>
            </div>
          </div>
          <div className="pt-2 border-t border-slate-800/60 text-[11px] font-mono text-slate-500 flex justify-between">
            <span>Heuristic Rules Flagged:</span>
            <span className="text-sky-400 font-semibold">{stats?.events_by_type?.['SUSPICIOUS_INDICATOR'] || 0}</span>
          </div>
        </div>

        {/* Storage Vault Integrity */}
        <div className="bg-[#0f1624] border border-slate-800/80 rounded-lg p-5 space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono text-slate-400 uppercase tracking-wider">Vault Storage</span>
            <Database className="w-4 h-4 text-sky-400" />
          </div>
          <div>
            <div className="text-2xl font-mono font-bold text-slate-100">
              {stats?.system_status?.free_storage_bytes
                ? `${(stats.system_status.free_storage_bytes / (1024 * 1024 * 1024)).toFixed(1)} GB`
                : 'Isolated'}
            </div>
            <div className="text-xs font-mono text-emerald-400 mt-1 flex items-center gap-1">
              <CheckCircle2 className="w-3 h-3" />
              <span>Read-Only & Protected</span>
            </div>
          </div>
          <div className="pt-2 border-t border-slate-800/60 text-[11px] font-mono text-slate-500 truncate">
            SQLite PRAGMA FK Enforced
          </div>
        </div>
      </div>

      {/* Main Grid: Active Cases & Severity Breakdown */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column (2 spans): Active Investigations Table */}
        <div className="lg:col-span-2 bg-[#0f1624] border border-slate-800/80 rounded-lg p-5 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
            <div className="flex items-center gap-2">
              <FolderKanban className="w-4 h-4 text-sky-400" />
              <h2 className="text-sm font-semibold text-slate-200">
                Active Forensic Investigations
              </h2>
            </div>
            <Link to="/cases" className="text-xs font-mono text-sky-400 hover:text-sky-300 flex items-center gap-1">
              <span>View All Cases</span>
              <ArrowRight className="w-3 h-3" />
            </Link>
          </div>

          {!stats || stats.recent_cases.length === 0 ? (
            <div className="py-12 text-center text-slate-500 font-mono text-xs">
              No investigation cases recorded. Create a case to begin logging artifacts.
            </div>
          ) : (
            <div className="divide-y divide-slate-800/60 font-mono text-xs">
              {stats.recent_cases.map((c) => (
                <div key={c.id} className="py-3.5 flex flex-col sm:flex-row sm:items-center justify-between gap-3 hover:bg-slate-900/30 px-2 rounded transition-colors">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="font-semibold text-sky-400 text-xs">{c.case_number}</span>
                      <StatusBadge label={c.status} variant={getStatusVariant(c.status)} size="xs" />
                      <StatusBadge label={c.priority} variant={getPriorityVariant(c.priority)} size="xs" />
                    </div>
                    <div className="font-sans font-medium text-slate-200 text-xs">{c.title}</div>
                    <div className="text-[11px] text-slate-400 font-sans flex items-center gap-3">
                      <span>Investigator: {c.investigator_name}</span>
                      <span>&bull;</span>
                      <span>Evidence: {c.evidence_count} items</span>
                      <span>&bull;</span>
                      <span>Events: {c.events_count}</span>
                    </div>
                  </div>

                  <div className="flex items-center gap-2 self-end sm:self-center">
                    <button
                      onClick={() => handleDownloadPdf(c.id, c.case_number)}
                      disabled={downloadingCaseId === c.id}
                      className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded bg-slate-900 hover:bg-slate-800 text-sky-400 border border-slate-700/80 transition-colors text-xs font-sans disabled:opacity-50"
                      title="Download Official Forensic PDF Report"
                    >
                      <Download className={`w-3.5 h-3.5 ${downloadingCaseId === c.id ? 'animate-bounce text-sky-300' : ''}`} />
                      <span>{downloadingCaseId === c.id ? 'Compiling PDF...' : 'PDF Report'}</span>
                    </button>
                    <Link
                      to={`/cases`}
                      className="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-sans transition-colors"
                    >
                      Inspect
                    </Link>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Right Column: Severity Distribution & System Diagnostics */}
        <div className="space-y-6">
          {/* Severity Distribution Card */}
          <div className="bg-[#0f1624] border border-slate-800/80 rounded-lg p-5 space-y-4">
            <div className="flex items-center gap-2 border-b border-slate-800/80 pb-3">
              <ShieldAlert className="w-4 h-4 text-amber-400" />
              <h2 className="text-sm font-semibold text-slate-200">
                Event Severity Breakdown
              </h2>
            </div>

            <div className="space-y-2.5 text-xs font-mono">
              <div className="flex items-center justify-between p-2 rounded bg-rose-500/10 border border-rose-500/20">
                <span className="text-rose-300 font-bold">CRITICAL</span>
                <span className="text-rose-200 font-bold">{stats?.events_by_severity?.['CRITICAL'] || 0}</span>
              </div>
              <div className="flex items-center justify-between p-2 rounded bg-rose-500/5 border border-rose-500/10">
                <span className="text-rose-400">HIGH</span>
                <span className="text-rose-300">{stats?.events_by_severity?.['HIGH'] || 0}</span>
              </div>
              <div className="flex items-center justify-between p-2 rounded bg-amber-500/10 border border-amber-500/20">
                <span className="text-amber-300">MEDIUM</span>
                <span className="text-amber-200">{stats?.events_by_severity?.['MEDIUM'] || 0}</span>
              </div>
              <div className="flex items-center justify-between p-2 rounded bg-sky-500/10 border border-sky-500/20">
                <span className="text-sky-300">LOW</span>
                <span className="text-sky-200">{stats?.events_by_severity?.['LOW'] || 0}</span>
              </div>
              <div className="flex items-center justify-between p-2 rounded bg-slate-900 border border-slate-800">
                <span className="text-slate-400">INFORMATIONAL</span>
                <span className="text-slate-300">{stats?.events_by_severity?.['INFO'] || 0}</span>
              </div>
            </div>
          </div>

          {/* Recent Audit Actions Card */}
          <div className="bg-[#0f1624] border border-slate-800/80 rounded-lg p-5 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
              <div className="flex items-center gap-2">
                <ScrollText className="w-4 h-4 text-emerald-400" />
                <h2 className="text-sm font-semibold text-slate-200">
                  Recent Chain-of-Custody Activity
                </h2>
              </div>
              <Link to="/audit" className="text-xs font-mono text-sky-400 hover:text-sky-300">
                Full Log
              </Link>
            </div>

            {!stats || stats.recent_activity.length === 0 ? (
              <p className="text-xs text-slate-500 font-mono">No recent actions logged.</p>
            ) : (
              <div className="space-y-3 font-mono text-xs">
                {stats.recent_activity.map((act) => (
                  <div key={act.id} className="border-l-2 border-sky-500/60 pl-3 space-y-0.5">
                    <div className="flex items-center justify-between text-[11px]">
                      <span className="font-semibold text-slate-200">{act.action}</span>
                      <span className="text-slate-500">
                        {new Date(act.timestamp).toISOString().replace('T', ' ').substring(11, 19)} UTC
                      </span>
                    </div>
                    <div className="text-[11px] text-slate-400 font-sans line-clamp-1">
                      {act.operator}: {act.details || act.target_id}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
