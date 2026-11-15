import React, { useState, useEffect } from 'react';
import {
  Clock,
  HardDrive,
  ShieldCheck,
  ShieldAlert,
  Terminal,
  Filter,
  ArrowUpDown,
  Search,
  AlertCircle,
  FileText,
  User,
  Hash,
  Globe,
  Download,
} from 'lucide-react';
import api from '../api/client';
import StatusBadge from '../components/layout/StatusBadge';

export default function Timeline() {
  const [cases, setCases] = useState([]);
  const [selectedCaseId, setSelectedCaseId] = useState('');
  const [timelineEvents, setTimelineEvents] = useState([]);
  const [totalEvents, setTotalEvents] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [downloadingReport, setDownloadingReport] = useState(false);

  // Filter states
  const [order, setOrder] = useState('asc'); // 'asc' or 'desc'
  const [selectedCategory, setSelectedCategory] = useState('');
  const [selectedSeverity, setSelectedSeverity] = useState('');

  // Load cases on mount
  useEffect(() => {
    async function loadCases() {
      try {
        const data = await api.getCases();
        setCases(data);
        if (data.length > 0 && !selectedCaseId) {
          setSelectedCaseId(data[0].id.toString());
        }
      } catch (err) {
        setError(`Failed to load investigation cases: ${err.message}`);
      }
    }
    loadCases();
  }, []);

  // Load timeline whenever case or filters change
  const loadTimeline = async (caseId, sortOrder, cat, sev) => {
    if (!caseId) {
      setTimelineEvents([]);
      setTotalEvents(0);
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const params = { order: sortOrder };
      if (cat) params.category = cat;
      if (sev) params.severity = sev;

      const data = await api.getTimeline(caseId, params);
      setTimelineEvents(data.timeline || []);
      setTotalEvents(data.total_events || 0);
    } catch (err) {
      setError(`Failed to retrieve timeline events: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadTimeline(selectedCaseId, order, selectedCategory, selectedSeverity);
  }, [selectedCaseId, order, selectedCategory, selectedSeverity]);

  const handleDownloadPdf = async () => {
    if (!selectedCaseId) return;
    const c = cases.find((x) => x.id.toString() === selectedCaseId);
    setDownloadingReport(true);
    try {
      await api.downloadReportPdf(selectedCaseId, c?.case_number || 'Case', 'Lead Forensic Examiner');
    } catch (err) {
      alert(`Report download error: ${err.message}`);
    } finally {
      setDownloadingReport(false);
    }
  };

  const getCategoryIcon = (category) => {
    switch (category) {
      case 'EVIDENCE_ACQUISITION':
        return <HardDrive className="w-4 h-4 text-emerald-400" />;
      case 'INTEGRITY_CHECK':
        return <ShieldCheck className="w-4 h-4 text-sky-400" />;
      case 'ANALYSIS_FINDING':
        return <ShieldAlert className="w-4 h-4 text-rose-400" />;
      default:
        return <Clock className="w-4 h-4 text-slate-400" />;
    }
  };

  const getSeverityVariant = (sev) => {
    switch (sev) {
      case 'CRITICAL': return 'rose';
      case 'HIGH': return 'rose';
      case 'MEDIUM': return 'amber';
      case 'LOW': return 'sky';
      default: return 'slate';
    }
  };

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-slate-800/80">
        <div>
          <div className="flex items-center gap-2.5">
            <h1 className="text-xl font-bold tracking-tight text-slate-100">
              Investigation Chronology & Event Timeline
            </h1>
            <StatusBadge label="STRICT UTC" variant="sky" />
          </div>
          <p className="text-sm text-slate-400 mt-1">
            Correlated sequence of evidence acquisitions, log telemetry, integrity verification, and audit milestones.
          </p>
        </div>

        {/* Case selector & Report button */}
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <span className="text-xs font-mono text-slate-400">Case:</span>
            <select
              value={selectedCaseId}
              onChange={(e) => setSelectedCaseId(e.target.value)}
              className="bg-slate-900 border border-slate-800 text-slate-200 text-xs rounded px-3 py-2 font-mono focus:outline-none focus:border-sky-500"
            >
              {cases.length === 0 && <option value="">No cases created yet</option>}
              {cases.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.case_number} — {c.title.substring(0, 30)}
                </option>
              ))}
            </select>
          </div>

          <button
            onClick={handleDownloadPdf}
            disabled={!selectedCaseId || downloadingReport}
            className="inline-flex items-center gap-1.5 bg-sky-600 hover:bg-sky-500 text-white text-xs font-semibold px-3 py-2 rounded-md transition-colors shadow-sm shadow-sky-600/20 disabled:opacity-50"
            title="Download Official Forensic PDF Report for this Case"
          >
            <Download className={`w-3.5 h-3.5 ${downloadingReport ? 'animate-bounce' : ''}`} />
            <span>{downloadingReport ? 'Compiling PDF...' : 'Export Timeline Report'}</span>
          </button>
        </div>
      </div>

      {/* Filter toolbar */}
      <div className="bg-[#0f1624] border border-slate-800/80 rounded-lg p-3.5 flex flex-wrap items-center justify-between gap-4 text-xs font-mono">
        <div className="flex flex-wrap items-center gap-3">
          <div className="flex items-center gap-1.5 text-slate-400">
            <Filter className="w-3.5 h-3.5 text-sky-400" />
            <span>Category:</span>
            <select
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
              className="bg-slate-900 border border-slate-800 text-slate-200 rounded px-2.5 py-1 text-xs focus:outline-none focus:border-sky-500"
            >
              <option value="">All Categories</option>
              <option value="EVIDENCE_ACQUISITION">Evidence Acquisition</option>
              <option value="SECURITY_EVENT">Security Event</option>
              <option value="ANALYSIS_FINDING">Analysis Finding</option>
              <option value="INTEGRITY_CHECK">Integrity Check</option>
              <option value="AUDIT_ACTION">Audit Action</option>
            </select>
          </div>

          <div className="flex items-center gap-1.5 text-slate-400">
            <span>Severity:</span>
            <select
              value={selectedSeverity}
              onChange={(e) => setSelectedSeverity(e.target.value)}
              className="bg-slate-900 border border-slate-800 text-slate-200 rounded px-2.5 py-1 text-xs focus:outline-none focus:border-sky-500"
            >
              <option value="">All Severities</option>
              <option value="CRITICAL">CRITICAL</option>
              <option value="HIGH">HIGH</option>
              <option value="MEDIUM">MEDIUM</option>
              <option value="LOW">LOW</option>
              <option value="INFO">INFO</option>
            </select>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => setOrder(order === 'asc' ? 'desc' : 'asc')}
            className="inline-flex items-center gap-1.5 bg-slate-900 hover:bg-slate-800 text-slate-300 px-3 py-1 rounded border border-slate-800 transition-colors"
          >
            <ArrowUpDown className="w-3.5 h-3.5 text-sky-400" />
            <span>{order === 'asc' ? 'Chronological (Oldest First)' : 'Reverse (Newest First)'}</span>
          </button>
          <span className="text-slate-500">|</span>
          <span className="text-slate-400">{timelineEvents.length} Events Listed</span>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-lg bg-rose-500/10 border border-rose-500/20 flex items-center gap-3 text-rose-300 text-xs">
          <AlertCircle className="w-4 h-4 text-rose-400 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Timeline Event Stream */}
      {loading ? (
        <div className="py-16 text-center text-slate-500 font-mono text-xs">
          Correlating chronological timeline in UTC...
        </div>
      ) : timelineEvents.length === 0 ? (
        <div className="py-16 px-6 text-center border border-dashed border-slate-800 rounded-lg bg-slate-900/20 max-w-xl mx-auto space-y-3">
          <Clock className="w-8 h-8 text-slate-600 mx-auto" />
          <h3 className="text-sm font-semibold text-slate-300">Timeline Empty</h3>
          <p className="text-xs text-slate-500 max-w-sm mx-auto">
            No events match the current filter criteria. Upload evidence or ingest security logs in the Evidence Vault and Log Analysis modules to build this case's timeline.
          </p>
        </div>
      ) : (
        <div className="relative border-l border-slate-800/80 ml-4 md:ml-6 space-y-6 pb-6">
          {timelineEvents.map((item, idx) => (
            <div key={item.id} className="relative pl-6 md:pl-8 group">
              {/* Timeline Node Bullet */}
              <div
                className={`absolute -left-2.5 top-1.5 w-5 h-5 rounded-full border flex items-center justify-center bg-[#090d16] ${
                  item.severity === 'CRITICAL'
                    ? 'border-rose-500 text-rose-400 shadow-sm shadow-rose-500/20'
                    : item.severity === 'HIGH'
                    ? 'border-amber-500 text-amber-400 shadow-sm shadow-amber-500/20'
                    : item.category === 'EVIDENCE_ACQUISITION'
                    ? 'border-emerald-500 text-emerald-400 shadow-sm shadow-emerald-500/20'
                    : 'border-slate-700 text-slate-400'
                }`}
              >
                <div className="w-1.5 h-1.5 rounded-full bg-current" />
              </div>

              {/* Event Card */}
              <div className="bg-[#0f1624] border border-slate-800/80 hover:border-slate-700/80 rounded-lg p-4 space-y-3 transition-colors shadow-sm">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-800/60 pb-2.5">
                  <div className="flex items-center gap-2">
                    {getCategoryIcon(item.category)}
                    <h3 className="text-xs font-semibold text-slate-200 font-mono">
                      {item.title}
                    </h3>
                    <StatusBadge
                      label={item.category.replace('_', ' ')}
                      variant="slate"
                      size="xs"
                    />
                  </div>

                  <div className="flex items-center gap-2 font-mono text-[11px]">
                    <StatusBadge
                      label={item.severity}
                      variant={getSeverityVariant(item.severity)}
                      size="xs"
                    />
                    <span className="text-sky-400 flex items-center gap-1">
                      <Clock className="w-3 h-3 text-slate-500" />
                      {new Date(item.timestamp).toISOString().replace('T', ' ').substring(0, 19)} UTC
                    </span>
                  </div>
                </div>

                <p className="text-xs text-slate-300 font-sans leading-relaxed">
                  {item.description}
                </p>

                {/* Additional Forensic Context / Metadata */}
                {item.metadata && Object.keys(item.metadata).length > 0 && (
                  <div className="pt-2 border-t border-slate-800/40 flex flex-wrap items-center gap-3 text-[11px] font-mono text-slate-400">
                    {item.metadata.source_ip && (
                      <span className="flex items-center gap-1 text-slate-300">
                        <Globe className="w-3 h-3 text-slate-500" /> IP: {item.metadata.source_ip}
                      </span>
                    )}
                    {item.metadata.user_account && (
                      <span className="flex items-center gap-1 text-slate-300">
                        <User className="w-3 h-3 text-slate-500" /> User: {item.metadata.user_account}
                      </span>
                    )}
                    {item.metadata.sha256_hash && (
                      <span className="flex items-center gap-1 text-sky-400">
                        <Hash className="w-3 h-3 text-slate-500" /> SHA: {item.metadata.sha256_hash.substring(0, 16)}...
                      </span>
                    )}
                    {item.metadata.indicator_tags && (
                      <span className="text-amber-400">
                        Tags: [{item.metadata.indicator_tags}]
                      </span>
                    )}
                    {item.source && (
                      <span className="text-slate-500">
                        Source: {item.source}
                      </span>
                    )}
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
