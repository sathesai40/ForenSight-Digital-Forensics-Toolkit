import React, { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import {
  FolderKanban,
  Plus,
  RefreshCw,
  Clock,
  User,
  ShieldAlert,
  Search,
  ExternalLink,
  CheckCircle2,
  AlertCircle,
  Download,
  HardDrive,
  FileSearch,
  Filter,
  SlidersHorizontal,
  Edit3,
} from 'lucide-react';
import api from '../api/client';
import StatusBadge from '../components/layout/StatusBadge';

export default function Cases() {
  const navigate = useNavigate();
  const [cases, setCases] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Filters
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [priorityFilter, setPriorityFilter] = useState('');

  // Creation modal state
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [newCaseData, setNewCaseData] = useState({
    title: '',
    description: '',
    investigator_name: 'Lead Examiner',
    lead_analyst: '',
    priority: 'MEDIUM',
  });

  // Selected case for detailed inspection & status update modal
  const [selectedCase, setSelectedCase] = useState(null);
  const [updatingStatus, setUpdatingStatus] = useState(false);
  const [downloadingReport, setDownloadingReport] = useState(false);

  const loadCases = async () => {
    setLoading(true);
    try {
      const params = {};
      if (statusFilter) params.status_filter = statusFilter;
      if (priorityFilter) params.priority_filter = priorityFilter;
      const data = await api.getCases(params);
      setCases(data);
      setError(null);
    } catch (err) {
      setError(`Failed to retrieve cases: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadCases();
  }, [statusFilter, priorityFilter]);

  const handleCreateCase = async (e) => {
    e.preventDefault();
    if (!newCaseData.title || !newCaseData.investigator_name) return;
    setSubmitting(true);
    try {
      await api.createCase(newCaseData);
      setShowCreateModal(false);
      setNewCaseData({
        title: '',
        description: '',
        investigator_name: 'Lead Examiner',
        lead_analyst: '',
        priority: 'MEDIUM',
      });
      await loadCases();
    } catch (err) {
      alert(`Error creating case: ${err.message}`);
    } finally {
      setSubmitting(false);
    }
  };

  const handleUpdateCaseStatus = async (newStatus) => {
    if (!selectedCase) return;
    setUpdatingStatus(true);
    try {
      const updated = await api.updateCase(selectedCase.id, { status: newStatus }, 'Lead Examiner');
      setSelectedCase(updated);
      setCases((prev) => prev.map((c) => (c.id === updated.id ? updated : c)));
    } catch (err) {
      alert(`Error updating case status: ${err.message}`);
    } finally {
      setUpdatingStatus(false);
    }
  };

  const handleUpdateCasePriority = async (newPriority) => {
    if (!selectedCase) return;
    setUpdatingStatus(true);
    try {
      const updated = await api.updateCase(selectedCase.id, { priority: newPriority }, 'Lead Examiner');
      setSelectedCase(updated);
      setCases((prev) => prev.map((c) => (c.id === updated.id ? updated : c)));
    } catch (err) {
      alert(`Error updating case priority: ${err.message}`);
    } finally {
      setUpdatingStatus(false);
    }
  };

  const handleDownloadPdf = async (caseId, caseNumber) => {
    setDownloadingReport(true);
    try {
      await api.downloadReportPdf(caseId, caseNumber, 'Lead Forensic Examiner');
    } catch (err) {
      alert(`PDF download failed: ${err.message}`);
    } finally {
      setDownloadingReport(false);
    }
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

  const filteredCases = cases.filter((c) => {
    if (!searchQuery) return true;
    const q = searchQuery.toLowerCase();
    return (
      c.case_number.toLowerCase().includes(q) ||
      c.title.toLowerCase().includes(q) ||
      c.investigator_name.toLowerCase().includes(q)
    );
  });

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-slate-800/80">
        <div>
          <div className="flex items-center gap-2.5">
            <h1 className="text-xl font-bold tracking-tight text-slate-100">
              Investigation Case Management
            </h1>
            <span className="text-xs font-mono text-slate-400 bg-slate-900 border border-slate-800 px-2 py-0.5 rounded">
              {filteredCases.length} Cases
            </span>
          </div>
          <p className="text-sm text-slate-400 mt-1">
            Maintain case files, track evidentiary scope, transition lifecycle statuses, and generate court-ready PDF reports.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={loadCases}
            disabled={loading}
            className="p-2 text-slate-400 hover:text-slate-200 hover:bg-slate-900 rounded border border-slate-800 transition-colors"
            title="Refresh Cases"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin text-sky-400' : ''}`} />
          </button>

          <button
            onClick={() => setShowCreateModal(true)}
            className="inline-flex items-center gap-2 bg-sky-600 hover:bg-sky-500 text-white text-xs font-semibold px-3.5 py-2 rounded-md transition-colors shadow-sm shadow-sky-600/20"
          >
            <Plus className="w-4 h-4" />
            <span>New Case File</span>
          </button>
        </div>
      </div>

      {/* Search & Filter Toolbar */}
      <div className="bg-[#0f1624] border border-slate-800/80 rounded-lg p-3.5 flex flex-wrap items-center justify-between gap-4 text-xs font-mono">
        <div className="flex items-center gap-2 flex-1 min-w-[240px] max-w-md">
          <Search className="w-4 h-4 text-slate-500" />
          <input
            type="text"
            placeholder="Search by case number, title, or analyst..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-slate-900 border border-slate-800 rounded px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-sky-500 font-sans"
          />
        </div>

        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5 text-slate-400">
            <span>Status:</span>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="bg-slate-900 border border-slate-800 text-slate-200 rounded px-2.5 py-1 text-xs focus:outline-none focus:border-sky-500"
            >
              <option value="">All Statuses</option>
              <option value="OPEN">OPEN</option>
              <option value="IN_PROGRESS">IN PROGRESS</option>
              <option value="UNDER_REVIEW">UNDER REVIEW</option>
              <option value="CLOSED">CLOSED</option>
              <option value="ARCHIVED">ARCHIVED</option>
            </select>
          </div>

          <div className="flex items-center gap-1.5 text-slate-400">
            <span>Priority:</span>
            <select
              value={priorityFilter}
              onChange={(e) => setPriorityFilter(e.target.value)}
              className="bg-slate-900 border border-slate-800 text-slate-200 rounded px-2.5 py-1 text-xs focus:outline-none focus:border-sky-500"
            >
              <option value="">All Priorities</option>
              <option value="CRITICAL">CRITICAL</option>
              <option value="HIGH">HIGH</option>
              <option value="MEDIUM">MEDIUM</option>
              <option value="LOW">LOW</option>
            </select>
          </div>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-lg bg-rose-500/10 border border-rose-500/20 flex items-center gap-3 text-rose-300 text-xs">
          <AlertCircle className="w-4 h-4 text-rose-400 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Cases Grid */}
      {loading ? (
        <div className="py-16 text-center text-slate-500 font-mono text-xs">
          Loading investigation case files...
        </div>
      ) : filteredCases.length === 0 ? (
        <div className="py-16 px-6 text-center border border-dashed border-slate-800 rounded-lg bg-slate-900/20 max-w-xl mx-auto space-y-4">
          <FolderKanban className="w-10 h-10 text-slate-600 mx-auto" />
          <h3 className="text-sm font-semibold text-slate-200">No Cases Found</h3>
          <p className="text-xs text-slate-400 max-w-sm mx-auto">
            No investigation cases match the active search criteria or filters.
          </p>
          <button
            onClick={() => { setSearchQuery(''); setStatusFilter(''); setPriorityFilter(''); }}
            className="text-xs text-sky-400 hover:text-sky-300 underline font-mono"
          >
            Clear Search & Filters
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredCases.map((c) => (
            <div
              key={c.id}
              className="bg-[#0f1624] border border-slate-800/80 hover:border-slate-700 rounded-lg p-5 flex flex-col justify-between space-y-4 transition-colors shadow-sm"
            >
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="font-mono text-xs font-semibold text-sky-400 bg-sky-500/10 border border-sky-500/20 px-2 py-0.5 rounded">
                    {c.case_number}
                  </span>
                  <div className="flex items-center gap-1.5">
                    <StatusBadge label={c.status} variant={getStatusVariant(c.status)} size="xs" />
                    <StatusBadge label={c.priority} variant={getPriorityVariant(c.priority)} size="xs" />
                  </div>
                </div>

                <div>
                  <h3 className="text-sm font-semibold text-slate-100 line-clamp-1">{c.title}</h3>
                  <p className="text-xs text-slate-400 mt-1 line-clamp-2">
                    {c.description || 'No case description provided.'}
                  </p>
                </div>
              </div>

              <div className="space-y-3 pt-3 border-t border-slate-800/60">
                <div className="text-[11px] font-mono text-slate-400 space-y-1">
                  <div className="flex items-center justify-between">
                    <span className="text-slate-500 flex items-center gap-1">
                      <User className="w-3 h-3 text-slate-400" /> Lead:
                    </span>
                    <span className="text-slate-200">{c.investigator_name}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-slate-500">Evidence / Events:</span>
                    <span className="text-slate-300">{c.evidence_count} artifacts &bull; {c.events_count} events</span>
                  </div>
                </div>

                {/* Quick actions */}
                <div className="flex items-center justify-between pt-2 border-t border-slate-800/40">
                  <button
                    onClick={() => setSelectedCase(c)}
                    className="text-xs font-sans text-sky-400 hover:text-sky-300 font-medium"
                  >
                    View Details & Edit
                  </button>

                  <button
                    onClick={() => handleDownloadPdf(c.id, c.case_number)}
                    className="p-1.5 rounded bg-slate-900 hover:bg-slate-800 text-slate-300 hover:text-sky-300 border border-slate-800 transition-colors"
                    title="Download Official Forensic PDF Report"
                  >
                    <Download className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Case Details Drawer / Modal */}
      {selectedCase && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 backdrop-blur-xs p-4">
          <div className="bg-[#0f1624] border border-slate-700 rounded-lg max-w-2xl w-full p-6 space-y-5 shadow-2xl max-h-[90vh] overflow-y-auto">
            {/* Header */}
            <div className="flex items-start justify-between pb-3 border-b border-slate-800">
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-mono font-bold text-sky-400 bg-sky-500/10 border border-sky-500/20 px-2 py-0.5 rounded">
                    {selectedCase.case_number}
                  </span>
                  <StatusBadge label={selectedCase.status} variant={getStatusVariant(selectedCase.status)} size="xs" />
                  <StatusBadge label={selectedCase.priority} variant={getPriorityVariant(selectedCase.priority)} size="xs" />
                </div>
                <h2 className="text-base font-bold text-slate-100 font-sans">{selectedCase.title}</h2>
              </div>
              <button
                onClick={() => setSelectedCase(null)}
                className="text-slate-400 hover:text-slate-200 font-mono text-sm"
              >
                ✕
              </button>
            </div>

            {/* Scope / Description */}
            <div className="space-y-1 text-xs">
              <span className="text-slate-400 font-mono text-[11px] uppercase">Incident Hypothesis & Background</span>
              <p className="p-3 bg-slate-900/60 rounded border border-slate-800/80 text-slate-300 leading-relaxed font-sans">
                {selectedCase.description || 'No detailed background provided.'}
              </p>
            </div>

            {/* Lifecycle Status & Priority State Transitions */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs font-mono">
              <div className="p-3.5 bg-slate-900/60 rounded border border-slate-800 space-y-2">
                <span className="text-slate-400 block text-[11px] uppercase">Lifecycle Status Transition</span>
                <div className="flex flex-wrap gap-1.5">
                  {['OPEN', 'IN_PROGRESS', 'UNDER_REVIEW', 'CLOSED', 'ARCHIVED'].map((st) => (
                    <button
                      key={st}
                      disabled={updatingStatus || selectedCase.status === st}
                      onClick={() => handleUpdateCaseStatus(st)}
                      className={`px-2 py-1 rounded text-[11px] transition-colors ${
                        selectedCase.status === st
                          ? 'bg-sky-600 text-white font-bold'
                          : 'bg-slate-800 text-slate-400 hover:text-slate-200'
                      }`}
                    >
                      {st}
                    </button>
                  ))}
                </div>
              </div>

              <div className="p-3.5 bg-slate-900/60 rounded border border-slate-800 space-y-2">
                <span className="text-slate-400 block text-[11px] uppercase">Case Priority Transition</span>
                <div className="flex flex-wrap gap-1.5">
                  {['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'].map((pr) => (
                    <button
                      key={pr}
                      disabled={updatingStatus || selectedCase.priority === pr}
                      onClick={() => handleUpdateCasePriority(pr)}
                      className={`px-2 py-1 rounded text-[11px] transition-colors ${
                        selectedCase.priority === pr
                          ? 'bg-rose-600 text-white font-bold'
                          : 'bg-slate-800 text-slate-400 hover:text-slate-200'
                      }`}
                    >
                      {pr}
                    </button>
                  ))}
                </div>
              </div>
            </div>

            {/* Metrics & Assignments */}
            <div className="grid grid-cols-3 gap-3 text-xs font-mono text-center">
              <div className="p-3 bg-slate-900/40 rounded border border-slate-800/80">
                <span className="text-slate-500 block text-[10px]">EVIDENCE ITEMS</span>
                <span className="text-base font-bold text-slate-100">{selectedCase.evidence_count}</span>
              </div>
              <div className="p-3 bg-slate-900/40 rounded border border-slate-800/80">
                <span className="text-slate-500 block text-[10px]">SECURITY EVENTS</span>
                <span className="text-base font-bold text-slate-100">{selectedCase.events_count}</span>
              </div>
              <div className="p-3 bg-slate-900/40 rounded border border-slate-800/80">
                <span className="text-slate-500 block text-[10px]">OPENED (UTC)</span>
                <span className="text-xs font-semibold text-slate-300">
                  {new Date(selectedCase.created_at).toISOString().substring(0, 10)}
                </span>
              </div>
            </div>

            {/* Quick module navigation buttons */}
            <div className="space-y-2 pt-2 border-t border-slate-800">
              <span className="text-[11px] font-mono uppercase text-slate-400">Forensic Module Shortcuts</span>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs font-sans">
                <Link
                  to="/evidence"
                  className="p-2.5 rounded bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-300 hover:text-sky-300 flex items-center justify-center gap-1.5 transition-colors"
                >
                  <HardDrive className="w-3.5 h-3.5 text-emerald-400" />
                  <span>Evidence Vault</span>
                </Link>
                <Link
                  to="/logs"
                  className="p-2.5 rounded bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-300 hover:text-sky-300 flex items-center justify-center gap-1.5 transition-colors"
                >
                  <FileSearch className="w-3.5 h-3.5 text-amber-400" />
                  <span>Log Analysis</span>
                </Link>
                <Link
                  to="/timeline"
                  className="p-2.5 rounded bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-300 hover:text-sky-300 flex items-center justify-center gap-1.5 transition-colors"
                >
                  <Clock className="w-3.5 h-3.5 text-sky-400" />
                  <span>Event Timeline</span>
                </Link>
                <button
                  onClick={() => handleDownloadPdf(selectedCase.id, selectedCase.case_number)}
                  disabled={downloadingReport}
                  className="p-2.5 rounded bg-sky-600 hover:bg-sky-500 text-white flex items-center justify-center gap-1.5 transition-colors disabled:opacity-50"
                >
                  <Download className={`w-3.5 h-3.5 ${downloadingReport ? 'animate-bounce' : ''}`} />
                  <span>{downloadingReport ? 'Generating...' : 'Export PDF'}</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Create Case Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 backdrop-blur-xs p-4">
          <div className="bg-[#0f1624] border border-slate-700 rounded-lg max-w-lg w-full p-6 space-y-5 shadow-2xl">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <h2 className="text-base font-semibold text-slate-100 flex items-center gap-2">
                <FolderKanban className="w-4 h-4 text-sky-400" />
                <span>Initialize New Forensic Investigation Case</span>
              </h2>
              <button
                onClick={() => setShowCreateModal(false)}
                className="text-slate-400 hover:text-slate-200 font-mono text-sm"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleCreateCase} className="space-y-4 text-xs">
              <div className="space-y-1">
                <label className="block text-slate-300 font-medium">Case Title *</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Operation Aegis: Data Center Intrusion"
                  value={newCaseData.title}
                  onChange={(e) => setNewCaseData({ ...newCaseData, title: e.target.value })}
                  className="w-full px-3 py-2 bg-slate-900 border border-slate-800 rounded text-slate-100 focus:outline-none focus:border-sky-500 font-sans"
                />
              </div>

              <div className="space-y-1">
                <label className="block text-slate-300 font-medium">Incident Summary / Scope</label>
                <textarea
                  rows={3}
                  placeholder="Initial breach telemetry, affected systems, compromised credentials..."
                  value={newCaseData.description}
                  onChange={(e) => setNewCaseData({ ...newCaseData, description: e.target.value })}
                  className="w-full px-3 py-2 bg-slate-900 border border-slate-800 rounded text-slate-100 focus:outline-none focus:border-sky-500 font-sans"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1">
                  <label className="block text-slate-300 font-medium">Lead Examiner *</label>
                  <input
                    type="text"
                    required
                    value={newCaseData.investigator_name}
                    onChange={(e) => setNewCaseData({ ...newCaseData, investigator_name: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-900 border border-slate-800 rounded text-slate-100 focus:outline-none focus:border-sky-500 font-sans"
                  />
                </div>

                <div className="space-y-1">
                  <label className="block text-slate-300 font-medium">Priority Level</label>
                  <select
                    value={newCaseData.priority}
                    onChange={(e) => setNewCaseData({ ...newCaseData, priority: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-900 border border-slate-800 rounded text-slate-100 focus:outline-none focus:border-sky-500 font-sans"
                  >
                    <option value="LOW">LOW</option>
                    <option value="MEDIUM">MEDIUM</option>
                    <option value="HIGH">HIGH</option>
                    <option value="CRITICAL">CRITICAL</option>
                  </select>
                </div>
              </div>

              <div className="pt-4 border-t border-slate-800 flex items-center justify-end gap-3">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="px-4 py-2 bg-slate-900 hover:bg-slate-800 text-slate-300 rounded border border-slate-800 transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="px-4 py-2 bg-sky-600 hover:bg-sky-500 text-white font-medium rounded transition-colors disabled:opacity-50"
                >
                  {submitting ? 'Creating Case...' : 'Create Case File & Audit'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
