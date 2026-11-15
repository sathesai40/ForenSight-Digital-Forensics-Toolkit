import React, { useState, useEffect } from 'react';
import {
  FileSearch,
  UploadCloud,
  Terminal,
  ShieldAlert,
  AlertTriangle,
  CheckCircle2,
  AlertCircle,
  FileText,
  User,
  Clock,
  Layers,
  ArrowRight,
} from 'lucide-react';
import api from '../api/client';
import StatusBadge from '../components/layout/StatusBadge';

const SAMPLE_BENCHMARK = `2026-11-15T01:14:02.000Z host-sec01 sshd[14221]: Failed password for invalid user root from 198.51.100.42 port 54312 ssh2
2026-11-15T01:14:05.000Z host-sec01 sshd[14223]: Failed password for invalid user admin from 198.51.100.42 port 54314 ssh2
2026-11-15T01:14:09.000Z host-sec01 sshd[14225]: Failed password for invalid user analyst from 198.51.100.42 port 54316 ssh2
2026-11-15T01:15:22.000Z host-sec01 sshd[14230]: Accepted publickey for forensic_user from 192.0.2.15 port 55102 ssh2: RSA SHA256:7f8e...
2026-11-15T01:16:01.000Z host-sec01 sudo: forensic_user : TTY=pts/0 ; PWD=/home/forensic_user ; USER=root ; COMMAND=/bin/journalctl -u ssh`;

export default function LogAnalysis() {
  const [cases, setCases] = useState([]);
  const [selectedCaseId, setSelectedCaseId] = useState('');
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Ingestion form state
  const [logInputType, setLogInputType] = useState('text'); // 'text' or 'file'
  const [rawText, setRawText] = useState('');
  const [uploadFile, setUploadFile] = useState(null);
  const [operator, setOperator] = useState('Forensic Analyst');
  const [analyzing, setAnalyzing] = useState(false);
  const [analysisSummary, setAnalysisSummary] = useState(null);

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

  // Load existing case security events
  const loadCaseEvents = async (caseId) => {
    if (!caseId) {
      setEvents([]);
      setLoading(false);
      return;
    }
    setLoading(true);
    try {
      const data = await api.getCaseEvents(caseId);
      setEvents(data);
      setError(null);
    } catch (err) {
      setError(`Failed to retrieve case events: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadCaseEvents(selectedCaseId);
  }, [selectedCaseId]);

  const handleAnalyze = async (e) => {
    e.preventDefault();
    if (!selectedCaseId) return;

    setAnalyzing(true);
    setAnalysisSummary(null);
    setError(null);

    const formData = new FormData();
    formData.append('operator', operator);

    if (logInputType === 'file' && uploadFile) {
      formData.append('file', uploadFile);
    } else if (rawText) {
      formData.append('content', rawText);
    } else {
      setError('Please provide log text or select a log file to analyze.');
      setAnalyzing(false);
      return;
    }

    try {
      const result = await api.analyzeLogs(selectedCaseId, formData);
      setAnalysisSummary(result);
      setRawText('');
      setUploadFile(null);
      await loadCaseEvents(selectedCaseId);
    } catch (err) {
      setError(`Log analysis error: ${err.message}`);
    } finally {
      setAnalyzing(false);
    }
  };

  const loadBenchmark = () => {
    setLogInputType('text');
    setRawText(SAMPLE_BENCHMARK);
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
              Security Log Analyzer & Indicator Engine
            </h1>
            <StatusBadge label="RULE DETECTOR" variant="emerald" />
          </div>
          <p className="text-sm text-slate-400 mt-1">
            Ingest auth logs, syslog streams, and CSV tables. Flag brute-force bursts and suspicious credential transitions.
          </p>
        </div>

        {/* Case selector */}
        <div className="flex items-center gap-2">
          <span className="text-xs font-mono text-slate-400">Case:</span>
          <select
            value={selectedCaseId}
            onChange={(e) => setSelectedCaseId(e.target.value)}
            className="bg-slate-900 border border-slate-800 text-slate-200 text-xs rounded px-3 py-2 font-mono focus:outline-none focus:border-sky-500"
          >
            {cases.length === 0 && <option value="">No cases available</option>}
            {cases.map((c) => (
              <option key={c.id} value={c.id}>
                {c.case_number} — {c.title.substring(0, 30)}
              </option>
            ))}
          </select>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-lg bg-rose-500/10 border border-rose-500/20 flex items-center gap-3 text-rose-300 text-xs">
          <AlertCircle className="w-4 h-4 text-rose-400 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Log Ingestion Box */}
      <div className="bg-[#0f1624] border border-slate-800/80 rounded-lg p-5 space-y-4">
        <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
          <div className="flex items-center gap-2">
            <Terminal className="w-4 h-4 text-sky-400" />
            <h2 className="text-sm font-semibold text-slate-200">
              Ingest & Analyze Security Log Stream
            </h2>
          </div>
          <button
            type="button"
            onClick={loadBenchmark}
            className="text-xs font-mono text-sky-400 hover:text-sky-300 underline"
          >
            Insert Synthetic Auth.log Benchmark
          </button>
        </div>

        <form onSubmit={handleAnalyze} className="space-y-4 text-xs">
          {/* Input mode tabs */}
          <div className="flex items-center gap-2 border-b border-slate-800/60 pb-2">
            <button
              type="button"
              onClick={() => setLogInputType('text')}
              className={`px-3 py-1 rounded text-xs font-mono transition-colors ${
                logInputType === 'text'
                  ? 'bg-sky-500/15 text-sky-300 border border-sky-500/30'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Direct Text / Syslog Stream
            </button>
            <button
              type="button"
              onClick={() => setLogInputType('file')}
              className={`px-3 py-1 rounded text-xs font-mono transition-colors ${
                logInputType === 'file'
                  ? 'bg-sky-500/15 text-sky-300 border border-sky-500/30'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Upload Log / CSV File
            </button>
          </div>

          {logInputType === 'text' ? (
            <div className="space-y-1">
              <textarea
                rows={5}
                value={rawText}
                onChange={(e) => setRawText(e.target.value)}
                placeholder="Paste auth.log lines or CSV entries with timestamps..."
                className="w-full px-3 py-2 bg-slate-900 border border-slate-800 rounded text-slate-200 font-mono text-xs focus:outline-none focus:border-sky-500"
              />
              <p className="text-[11px] text-slate-500">
                Supports standard SSH/Syslog auth lines or CSV formatted tables with timestamp, event_type, source_ip, and description.
              </p>
            </div>
          ) : (
            <div className="space-y-1">
              <input
                type="file"
                accept=".log,.csv,.txt"
                onChange={(e) => setUploadFile(e.target.files[0] || null)}
                className="w-full px-3 py-2 bg-slate-900 border border-slate-800 rounded text-slate-300 font-mono text-xs focus:outline-none focus:border-sky-500 file:mr-3 file:py-1 file:px-2 file:rounded file:border-0 file:text-xs file:font-semibold file:bg-sky-600 file:text-white hover:file:bg-sky-500"
              />
            </div>
          )}

          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pt-2">
            <div className="flex items-center gap-2">
              <label className="text-slate-400 font-mono text-xs">Analyst:</label>
              <input
                type="text"
                value={operator}
                onChange={(e) => setOperator(e.target.value)}
                className="px-2.5 py-1 bg-slate-900 border border-slate-800 rounded text-slate-200 text-xs font-sans"
              />
            </div>

            <button
              type="submit"
              disabled={analyzing || (!rawText && !uploadFile) || !selectedCaseId}
              className="inline-flex items-center gap-2 bg-sky-600 hover:bg-sky-500 text-white text-xs font-semibold px-4 py-2 rounded transition-colors disabled:opacity-50"
            >
              <FileSearch className="w-3.5 h-3.5" />
              <span>{analyzing ? 'Executing Forensic Rules...' : 'Analyze Logs & Detect Indicators'}</span>
            </button>
          </div>
        </form>
      </div>

      {/* Analysis Outcome Summary Banner */}
      {analysisSummary && (
        <div className="p-4 rounded-lg bg-[#0f1624] border border-sky-500/30 space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-sky-400 font-semibold text-xs">
              <CheckCircle2 className="w-4 h-4" />
              <span>LOG ANALYSIS COMPLETE: {analysisSummary.total_parsed} Events Processed, {analysisSummary.indicators_detected} Findings Detected</span>
            </div>
            <button
              onClick={() => setAnalysisSummary(null)}
              className="text-slate-400 hover:text-slate-200 text-xs font-mono"
            >
              ✕
            </button>
          </div>

          {analysisSummary.findings.length > 0 ? (
            <div className="space-y-2">
              {analysisSummary.findings.map((finding, idx) => (
                <div
                  key={idx}
                  className={`p-3 rounded border text-xs space-y-1 ${
                    finding.severity === 'CRITICAL'
                      ? 'bg-rose-500/15 border-rose-500/40 text-rose-200'
                      : 'bg-amber-500/10 border-amber-500/30 text-amber-200'
                  }`}
                >
                  <div className="flex items-center justify-between font-mono font-bold">
                    <span>{finding.rule}</span>
                    <StatusBadge label={finding.severity} variant={finding.severity === 'CRITICAL' ? 'rose' : 'amber'} size="xs" />
                  </div>
                  <p className="font-sans text-slate-300">{finding.description}</p>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-xs text-slate-400">
              All parsed events fell within baseline parameters. No brute-force or privilege escalation thresholds breached.
            </p>
          )}
        </div>
      )}

      {/* Normalized Security Events Table */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <h2 className="text-sm font-semibold text-slate-200">
              Normalized Security Events & Telemetry
            </h2>
            <span className="text-xs font-mono text-slate-500 bg-slate-900 border border-slate-800 px-2 py-0.5 rounded">
              {events.length} Recorded
            </span>
          </div>
        </div>

        {loading ? (
          <div className="py-16 text-center text-slate-500 font-mono text-xs">
            Querying SQLite security events...
          </div>
        ) : events.length === 0 ? (
          <div className="py-16 px-6 text-center border border-dashed border-slate-800 rounded-lg bg-slate-900/20 max-w-xl mx-auto space-y-3">
            <FileSearch className="w-8 h-8 text-slate-600 mx-auto" />
            <h3 className="text-sm font-semibold text-slate-300">No Security Events Extracted</h3>
            <p className="text-xs text-slate-500 max-w-sm mx-auto">
              Import a security log or load the synthetic benchmark above to extract normalized security events and rule-based indicators.
            </p>
          </div>
        ) : (
          <div className="bg-[#0f1624] border border-slate-800/80 rounded-lg overflow-hidden shadow-sm">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-[#0a0f1a] text-slate-400 font-mono text-[11px] uppercase border-b border-slate-800/80">
                  <tr>
                    <th className="px-4 py-3">Timestamp (UTC)</th>
                    <th className="px-4 py-3">Event Type</th>
                    <th className="px-4 py-3">Severity</th>
                    <th className="px-4 py-3">Source IP</th>
                    <th className="px-4 py-3">User</th>
                    <th className="px-4 py-3">Description</th>
                    <th className="px-4 py-3">Indicator Tags</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 font-mono">
                  {events.map((ev) => (
                    <tr key={ev.id} className="hover:bg-slate-900/40 transition-colors">
                      <td className="px-4 py-3 text-slate-400 whitespace-nowrap text-[11px]">
                        {new Date(ev.timestamp).toISOString().replace('T', ' ').substring(0, 19)}
                      </td>
                      <td className="px-4 py-3 text-sky-300 font-semibold">
                        {ev.event_type}
                      </td>
                      <td className="px-4 py-3">
                        <StatusBadge
                          label={ev.severity}
                          variant={getSeverityVariant(ev.severity)}
                          size="xs"
                        />
                      </td>
                      <td className="px-4 py-3 text-slate-300">
                        {ev.source_ip || '—'}
                      </td>
                      <td className="px-4 py-3 text-slate-200">
                        {ev.user_account || '—'}
                      </td>
                      <td className="px-4 py-3 text-slate-300 font-sans max-w-md truncate" title={ev.description}>
                        {ev.description}
                      </td>
                      <td className="px-4 py-3 text-slate-400 text-[11px]">
                        {ev.indicator_tags || '—'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
