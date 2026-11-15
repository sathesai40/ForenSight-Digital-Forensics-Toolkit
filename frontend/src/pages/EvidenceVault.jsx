import React, { useState, useEffect } from 'react';
import {
  HardDrive,
  UploadCloud,
  CheckCircle2,
  AlertTriangle,
  ShieldCheck,
  ShieldAlert,
  Hash,
  FileCode,
  RefreshCw,
  Search,
  Lock,
  Eye,
  Copy,
  Clock,
  User,
  AlertCircle,
  FileText,
  Download,
} from 'lucide-react';
import api from '../api/client';
import StatusBadge from '../components/layout/StatusBadge';

export default function EvidenceVault() {
  const [cases, setCases] = useState([]);
  const [selectedCaseId, setSelectedCaseId] = useState('');
  const [evidenceList, setEvidenceList] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [downloadingReport, setDownloadingReport] = useState(false);

  // Upload modal state
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [uploadFile, setUploadFile] = useState(null);
  const [investigator, setInvestigator] = useState('Lead Examiner');
  const [custodyNotes, setCustodyNotes] = useState('');
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState(null);

  // Verification state
  const [verifyingId, setVerifyingId] = useState(null);
  const [verificationResult, setVerificationResult] = useState(null);

  // Metadata modal state
  const [inspectEvidenceId, setInspectEvidenceId] = useState(null);
  const [metadataModal, setMetadataModal] = useState(null);
  const [loadingMetadata, setLoadingMetadata] = useState(false);

  // Copy hash feedback
  const [copiedHash, setCopiedHash] = useState(null);

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

  // Load evidence whenever selectedCaseId changes
  useEffect(() => {
    if (!selectedCaseId) {
      setEvidenceList([]);
      setLoading(false);
      return;
    }

    async function loadEvidence() {
      setLoading(true);
      setError(null);
      try {
        const data = await api.getEvidence(selectedCaseId);
        setEvidenceList(data);
      } catch (err) {
        setError(`Failed to load evidence artifacts: ${err.message}`);
      } finally {
        setLoading(false);
      }
    }
    loadEvidence();
  }, [selectedCaseId]);

  const handleUpload = async (e) => {
    e.preventDefault();
    if (!uploadFile || !selectedCaseId) return;

    setUploading(true);
    setUploadError(null);

    const formData = new FormData();
    formData.append('file', uploadFile);
    formData.append('investigator_name', investigator);
    formData.append('chain_of_custody_notes', custodyNotes);

    try {
      const created = await api.uploadEvidence(selectedCaseId, formData);
      setEvidenceList((prev) => [created, ...prev]);
      setShowUploadModal(false);
      setUploadFile(null);
      setCustodyNotes('');
    } catch (err) {
      setUploadError(err.message);
    } finally {
      setUploading(false);
    }
  };

  const handleVerify = async (evidenceId) => {
    setVerifyingId(evidenceId);
    setVerificationResult(null);
    try {
      const res = await api.verifyEvidence(evidenceId, investigator || 'Lead Examiner');
      setVerificationResult(res);
      // Update local record status
      setEvidenceList((prev) =>
        prev.map((item) =>
          item.id === evidenceId
            ? { ...item, integrity_status: res.status === 'MATCH' ? 'VERIFIED' : (res.status === 'MISMATCH' ? 'COMPROMISED' : 'ERROR') }
            : item
        )
      );
    } catch (err) {
      setVerificationResult({
        evidence_id: evidenceId,
        status: 'ERROR',
        detail: err.message,
      });
    } finally {
      setVerifyingId(null);
    }
  };

  const handleInspectMetadata = async (evidenceId) => {
    setInspectEvidenceId(evidenceId);
    setLoadingMetadata(true);
    setMetadataModal(null);
    try {
      const meta = await api.getEvidenceMetadata(evidenceId);
      setMetadataModal(meta);
    } catch (err) {
      alert(`Metadata inspection error: ${err.message}`);
    } finally {
      setLoadingMetadata(false);
    }
  };

  const handleDownloadPdf = async (caseId, caseNumber) => {
    setDownloadingReport(true);
    try {
      await api.downloadReportPdf(caseId, caseNumber, 'Lead Forensic Examiner');
    } catch (err) {
      alert(`Report download error: ${err.message}`);
    } finally {
      setDownloadingReport(false);
    }
  };

  const copyToClipboard = (text, id) => {
    navigator.clipboard.writeText(text);
    setCopiedHash(id);
    setTimeout(() => setCopiedHash(null), 2000);
  };

  const formatBytes = (bytes) => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-slate-800/80">
        <div>
          <div className="flex items-center gap-2.5">
            <h1 className="text-xl font-bold tracking-tight text-slate-100">
              Evidence Vault & Artifact Storage
            </h1>
            <StatusBadge label="PHASE 2 ENGINE" variant="emerald" />
          </div>
          <p className="text-sm text-slate-400 mt-1">
            Read-only storage, automated SHA-256 acquisition hashing, and on-demand cryptographic verification.
          </p>
        </div>

        {/* Case selector & Upload action */}
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
            onClick={() => {
              const c = cases.find((x) => x.id.toString() === selectedCaseId);
              handleDownloadPdf(selectedCaseId, c?.case_number || 'Case');
            }}
            disabled={!selectedCaseId || downloadingReport}
            className="inline-flex items-center gap-1.5 bg-slate-900 hover:bg-slate-800 text-slate-200 border border-slate-700 text-xs font-semibold px-3 py-2 rounded-md transition-colors disabled:opacity-50"
            title="Download Official Forensic PDF Report for this Case"
          >
            <Download className={`w-3.5 h-3.5 text-sky-400 ${downloadingReport ? 'animate-bounce' : ''}`} />
            <span>{downloadingReport ? 'Compiling PDF...' : 'PDF Report'}</span>
          </button>

          <button
            onClick={() => setShowUploadModal(true)}
            disabled={!selectedCaseId}
            className="inline-flex items-center gap-2 bg-sky-600 hover:bg-sky-500 text-white text-xs font-semibold px-3.5 py-2 rounded-md transition-colors shadow-sm shadow-sky-600/20 disabled:opacity-50"
          >
            <UploadCloud className="w-4 h-4" />
            <span>Secure Evidence Upload</span>
          </button>
        </div>
      </div>

      {/* Global error banner */}
      {error && (
        <div className="p-4 rounded-lg bg-rose-500/10 border border-rose-500/20 flex items-center gap-3 text-rose-300 text-xs">
          <AlertCircle className="w-4 h-4 text-rose-400 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Verification Result Banner */}
      {verificationResult && (
        <div
          className={`p-4 rounded-lg border flex items-start justify-between gap-3 text-xs ${
            verificationResult.status === 'MATCH'
              ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300'
              : verificationResult.status === 'MISMATCH'
              ? 'bg-rose-500/15 border-rose-500/40 text-rose-200'
              : 'bg-amber-500/10 border-amber-500/30 text-amber-300'
          }`}
        >
          <div className="flex items-start gap-3">
            {verificationResult.status === 'MATCH' ? (
              <ShieldCheck className="w-5 h-5 text-emerald-400 flex-shrink-0 mt-0.5" />
            ) : verificationResult.status === 'MISMATCH' ? (
              <ShieldAlert className="w-5 h-5 text-rose-400 flex-shrink-0 mt-0.5" />
            ) : (
              <AlertTriangle className="w-5 h-5 text-amber-400 flex-shrink-0 mt-0.5" />
            )}
            <div className="space-y-1 font-mono">
              <div className="font-semibold text-sm">
                INTEGRITY VERIFICATION RESULT: {verificationResult.status}
              </div>
              <p className="text-xs font-sans text-slate-300">{verificationResult.detail}</p>
              {verificationResult.expected_sha256 && (
                <div className="text-[11px] space-y-0.5 pt-1 text-slate-400">
                  <div>Expected:   <span className="text-slate-200">{verificationResult.expected_sha256}</span></div>
                  {verificationResult.calculated_sha256 && (
                    <div>Calculated: <span className={verificationResult.status === 'MATCH' ? 'text-emerald-300' : 'text-rose-400 font-bold'}>{verificationResult.calculated_sha256}</span></div>
                  )}
                </div>
              )}
            </div>
          </div>
          <button
            onClick={() => setVerificationResult(null)}
            className="text-slate-400 hover:text-slate-200 font-mono text-xs px-2"
          >
            ✕
          </button>
        </div>
      )}

      {/* Evidence Table */}
      {loading ? (
        <div className="py-16 text-center text-slate-500 font-mono text-xs">
          Loading evidence records from storage vault...
        </div>
      ) : evidenceList.length === 0 ? (
        <div className="py-16 px-6 text-center border border-dashed border-slate-800 rounded-lg bg-slate-900/20 max-w-xl mx-auto space-y-4">
          <div className="w-12 h-12 rounded-full bg-slate-900 border border-slate-800 flex items-center justify-center mx-auto text-slate-500">
            <HardDrive className="w-6 h-6" />
          </div>
          <div className="space-y-1">
            <h3 className="text-sm font-semibold text-slate-200">No Evidence Uploaded For This Case</h3>
            <p className="text-xs text-slate-400 max-w-sm mx-auto">
              Securely upload disk images, memory captures, or logs into the isolated vault. SHA-256 checksums are calculated immediately during ingestion.
            </p>
          </div>
          <button
            onClick={() => setShowUploadModal(true)}
            disabled={!selectedCaseId}
            className="inline-flex items-center gap-2 bg-sky-600 hover:bg-sky-500 text-white text-xs font-medium px-4 py-2 rounded transition-colors disabled:opacity-50"
          >
            <UploadCloud className="w-3.5 h-3.5" />
            <span>Upload First Artifact</span>
          </button>
        </div>
      ) : (
        <div className="bg-[#0f1624] border border-slate-800/80 rounded-lg overflow-hidden shadow-sm">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-[#0a0f1a] text-slate-400 font-mono text-[11px] uppercase border-b border-slate-800/80">
                <tr>
                  <th className="px-4 py-3">Tag</th>
                  <th className="px-4 py-3">Artifact Filename</th>
                  <th className="px-4 py-3">Size</th>
                  <th className="px-4 py-3">Acquisition SHA-256</th>
                  <th className="px-4 py-3">Status</th>
                  <th className="px-4 py-3">Acquired UTC</th>
                  <th className="px-4 py-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-mono">
                {evidenceList.map((ev) => (
                  <tr key={ev.id} className="hover:bg-slate-900/40 transition-colors">
                    <td className="px-4 py-3 text-sky-400 font-semibold whitespace-nowrap">
                      {ev.evidence_number}
                    </td>
                    <td className="px-4 py-3 text-slate-200">
                      <div className="font-sans font-medium line-clamp-1">{ev.source_filename}</div>
                      <div className="text-[10px] text-slate-500 font-mono">{ev.mime_type}</div>
                    </td>
                    <td className="px-4 py-3 text-slate-300 whitespace-nowrap">
                      {formatBytes(ev.file_size_bytes)}
                    </td>
                    <td className="px-4 py-3 text-slate-300">
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-[11px] text-slate-400">
                          {ev.sha256_hash.substring(0, 12)}...{ev.sha256_hash.substring(56)}
                        </span>
                        <button
                          onClick={() => copyToClipboard(ev.sha256_hash, ev.id)}
                          title="Copy Full SHA-256 Hash"
                          className="text-slate-500 hover:text-slate-300 transition-colors"
                        >
                          <Copy className="w-3.5 h-3.5" />
                        </button>
                        {copiedHash === ev.id && (
                          <span className="text-[10px] text-emerald-400 font-sans">Copied!</span>
                        )}
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <StatusBadge
                        label={ev.integrity_status}
                        variant={
                          ev.integrity_status === 'VERIFIED'
                            ? 'emerald'
                            : ev.integrity_status === 'COMPROMISED'
                            ? 'rose'
                            : 'amber'
                        }
                        size="xs"
                      />
                    </td>
                    <td className="px-4 py-3 text-slate-400 whitespace-nowrap text-[11px]">
                      {new Date(ev.acquired_at).toISOString().replace('T', ' ').substring(0, 16)}
                    </td>
                    <td className="px-4 py-3 text-right whitespace-nowrap space-x-2">
                      <button
                        onClick={() => handleVerify(ev.id)}
                        disabled={verifyingId === ev.id}
                        className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded bg-slate-900 hover:bg-slate-800 text-sky-400 border border-slate-700/80 transition-colors text-xs font-sans disabled:opacity-50"
                        title="Recalculate SHA-256 and verify against acquisition hash"
                      >
                        <ShieldCheck className={`w-3.5 h-3.5 ${verifyingId === ev.id ? 'animate-spin' : ''}`} />
                        <span>{verifyingId === ev.id ? 'Checking...' : 'Verify Hash'}</span>
                      </button>

                      <button
                        onClick={() => handleInspectMetadata(ev.id)}
                        className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded bg-slate-900 hover:bg-slate-800 text-slate-300 border border-slate-700/80 transition-colors text-xs font-sans"
                        title="Inspect file headers, magic signature, and indicators"
                      >
                        <Eye className="w-3.5 h-3.5 text-slate-400" />
                        <span>Inspect</span>
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Upload Evidence Modal */}
      {showUploadModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 backdrop-blur-xs p-4">
          <div className="bg-[#0f1624] border border-slate-700 rounded-lg max-w-lg w-full p-6 space-y-5 shadow-2xl">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <h2 className="text-base font-semibold text-slate-100 flex items-center gap-2">
                <UploadCloud className="w-4 h-4 text-sky-400" />
                <span>Secure Evidence Artifact Ingestion</span>
              </h2>
              <button
                onClick={() => setShowUploadModal(false)}
                className="text-slate-400 hover:text-slate-200 font-mono text-sm"
              >
                ✕
              </button>
            </div>

            {uploadError && (
              <div className="p-3 rounded bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs">
                {uploadError}
              </div>
            )}

            <form onSubmit={handleUpload} className="space-y-4 text-xs">
              <div className="space-y-1">
                <label className="block text-slate-300 font-medium">Select Evidence File *</label>
                <input
                  type="file"
                  required
                  onChange={(e) => setUploadFile(e.target.files[0] || null)}
                  className="w-full px-3 py-2 bg-slate-900 border border-slate-800 rounded text-slate-300 focus:outline-none focus:border-sky-500 font-mono text-xs file:mr-3 file:py-1 file:px-2 file:rounded file:border-0 file:text-xs file:font-semibold file:bg-sky-600 file:text-white hover:file:bg-sky-500"
                />
                <p className="text-[11px] text-slate-500">
                  Upload cap: 25 MB. Original bytes are written directly to vault storage without modification.
                </p>
              </div>

              <div className="space-y-1">
                <label className="block text-slate-300 font-medium">Acquiring Examiner / Specialist *</label>
                <input
                  type="text"
                  required
                  value={investigator}
                  onChange={(e) => setInvestigator(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-900 border border-slate-800 rounded text-slate-100 focus:outline-none focus:border-sky-500 font-sans"
                />
              </div>

              <div className="space-y-1">
                <label className="block text-slate-300 font-medium">Chain of Custody Notes</label>
                <textarea
                  rows={3}
                  value={custodyNotes}
                  onChange={(e) => setCustodyNotes(e.target.value)}
                  placeholder="Device source, acquisition methodology, forensic write blocker used, hardware serial..."
                  className="w-full px-3 py-2 bg-slate-900 border border-slate-800 rounded text-slate-100 focus:outline-none focus:border-sky-500 font-sans"
                />
              </div>

              <div className="pt-4 border-t border-slate-800 flex items-center justify-end gap-3">
                <button
                  type="button"
                  onClick={() => setShowUploadModal(false)}
                  className="px-4 py-2 bg-slate-900 hover:bg-slate-800 text-slate-300 rounded border border-slate-800 transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={uploading || !uploadFile}
                  className="px-4 py-2 bg-sky-600 hover:bg-sky-500 text-white font-medium rounded transition-colors disabled:opacity-50"
                >
                  {uploading ? 'Calculating Hashes & Storing...' : 'Ingest to Vault & Calculate SHA-256'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Metadata Inspection Modal */}
      {metadataModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 backdrop-blur-xs p-4">
          <div className="bg-[#0f1624] border border-slate-700 rounded-lg max-w-2xl w-full p-6 space-y-5 shadow-2xl max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <div className="flex items-center gap-2">
                <FileCode className="w-4 h-4 text-sky-400" />
                <h2 className="text-base font-semibold text-slate-100">
                  Forensic Metadata: {metadataModal.evidence_number}
                </h2>
              </div>
              <button
                onClick={() => setMetadataModal(null)}
                className="text-slate-400 hover:text-slate-200 font-mono text-sm"
              >
                ✕
              </button>
            </div>

            {/* Investigative Indicators Section */}
            <div className="space-y-2">
              <span className="text-xs font-mono uppercase tracking-wider text-slate-400">
                Investigative Indicators (Rule Heuristics)
              </span>
              {metadataModal.investigative_indicators.length === 0 ? (
                <div className="p-3 rounded bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 flex-shrink-0" />
                  <span>No immediate heuristic anomalies detected (extension and magic bytes match).</span>
                </div>
              ) : (
                <div className="space-y-2">
                  {metadataModal.investigative_indicators.map((ind, i) => (
                    <div
                      key={i}
                      className={`p-3 rounded border text-xs space-y-1 ${
                        ind.severity === 'HIGH'
                          ? 'bg-rose-500/10 border-rose-500/30 text-rose-300'
                          : 'bg-amber-500/10 border-amber-500/30 text-amber-300'
                      }`}
                    >
                      <div className="flex items-center justify-between font-mono font-semibold">
                        <span>{ind.rule}</span>
                        <StatusBadge label={ind.severity} variant={ind.severity === 'HIGH' ? 'rose' : 'amber'} size="xs" />
                      </div>
                      <p className="font-sans text-slate-300">{ind.description}</p>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Source Acquisition vs Vault Metadata Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs font-mono">
              {/* Source Metadata */}
              <div className="bg-slate-900/60 border border-slate-800 rounded p-4 space-y-2">
                <span className="text-sky-400 block font-semibold text-[11px] uppercase border-b border-slate-800 pb-1">
                  Source Acquisition Metadata
                </span>
                <div>
                  <span className="text-slate-500 block text-[10px]">ORIGINAL FILENAME</span>
                  <span className="text-slate-200 break-all">{metadataModal.source_metadata.source_filename}</span>
                </div>
                <div>
                  <span className="text-slate-500 block text-[10px]">FILE EXTENSION</span>
                  <span className="text-slate-200">{metadataModal.source_metadata.file_extension || '(none)'}</span>
                </div>
                <div>
                  <span className="text-slate-500 block text-[10px]">DECLARED MIME</span>
                  <span className="text-slate-200">{metadataModal.source_metadata.declared_mime_type}</span>
                </div>
                <div>
                  <span className="text-slate-500 block text-[10px]">ACQUIRED UTC</span>
                  <span className="text-slate-200">{metadataModal.source_metadata.acquisition_timestamp_utc}</span>
                </div>
              </div>

              {/* Vault Storage Metadata */}
              <div className="bg-slate-900/60 border border-slate-800 rounded p-4 space-y-2">
                <span className="text-emerald-400 block font-semibold text-[11px] uppercase border-b border-slate-800 pb-1">
                  Vault Filesystem Metadata
                </span>
                <div>
                  <span className="text-slate-500 block text-[10px]">STORED FILE SIZE</span>
                  <span className="text-slate-200">{formatBytes(metadataModal.vault_storage_metadata.actual_size_bytes)} ({metadataModal.vault_storage_metadata.actual_size_bytes} B)</span>
                </div>
                <div>
                  <span className="text-slate-500 block text-[10px]">MAGIC SIGNATURE</span>
                  <span className="text-slate-200">{metadataModal.signature_analysis.signature_name}</span>
                </div>
                <div>
                  <span className="text-slate-500 block text-[10px]">DETECTED MIME</span>
                  <span className="text-slate-200">{metadataModal.signature_analysis.detected_mime_type}</span>
                </div>
                <div>
                  <span className="text-slate-500 block text-[10px]">VAULT MTIME (UTC)</span>
                  <span className="text-slate-200">{metadataModal.vault_storage_metadata.vault_filesystem_mtime_utc || '—'}</span>
                </div>
              </div>
            </div>

            {/* Cryptographic Hashes */}
            <div className="bg-slate-900/60 border border-slate-800 rounded p-3 text-xs font-mono space-y-1">
              <span className="text-slate-500 block text-[10px]">IMMUTABLE SHA-256 ACQUISITION HASH</span>
              <span className="text-sky-300 break-all select-all">{metadataModal.source_metadata.sha256_hash}</span>
            </div>

            <div className="pt-2 border-t border-slate-800 flex justify-end">
              <button
                onClick={() => setMetadataModal(null)}
                className="px-4 py-1.5 bg-slate-900 hover:bg-slate-800 text-slate-300 rounded border border-slate-800 text-xs font-sans"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
