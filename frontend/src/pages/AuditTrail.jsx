import React, { useState, useEffect } from 'react';
import { ScrollText, RefreshCw, Shield, Clock, User, AlertCircle, FileCheck } from 'lucide-react';
import api from '../api/client';
import StatusBadge from '../components/layout/StatusBadge';

export default function AuditTrail() {
  const [audits, setAudits] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const loadAuditTrail = async () => {
    setLoading(true);
    try {
      const data = await api.getAuditTrail();
      setAudits(data);
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAuditTrail();
  }, []);

  const getActionVariant = (action) => {
    switch (action) {
      case 'CASE_CREATED': return 'emerald';
      case 'EVIDENCE_INGESTED': return 'sky';
      case 'HASH_VERIFIED': return 'emerald';
      case 'INTEGRITY_CHECK_PASSED': return 'emerald';
      case 'EVENT_FLAGGED': return 'amber';
      case 'EVIDENCE_MODIFIED': return 'rose';
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
              Cryptographic Audit Trail
            </h1>
            <span className="text-xs font-mono text-slate-400 bg-slate-900 border border-slate-800 px-2 py-0.5 rounded">
              {audits.length} Records
            </span>
          </div>
          <p className="text-sm text-slate-400 mt-1">
            Immutable, append-only chain of custody records verifying examiner operations and evidence integrity.
          </p>
        </div>

        <button
          onClick={loadAuditTrail}
          disabled={loading}
          className="p-2 text-slate-400 hover:text-slate-200 hover:bg-slate-900 rounded border border-slate-800 transition-colors"
          title="Refresh Audit Trail"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin text-sky-400' : ''}`} />
        </button>
      </div>

      {error && (
        <div className="p-4 rounded-lg bg-rose-500/10 border border-rose-500/20 flex items-center gap-3 text-rose-300 text-xs">
          <AlertCircle className="w-4 h-4 text-rose-400 flex-shrink-0" />
          <span>Failed to load audit logs: {error}</span>
        </div>
      )}

      {loading ? (
        <div className="py-16 text-center text-slate-500 font-mono text-xs">
          Querying immutable audit logs...
        </div>
      ) : audits.length === 0 ? (
        <div className="py-16 px-6 text-center border border-dashed border-slate-800 rounded-lg bg-slate-900/20 max-w-xl mx-auto space-y-3">
          <ScrollText className="w-8 h-8 text-slate-600 mx-auto" />
          <h3 className="text-sm font-semibold text-slate-300">Audit Log Initialized</h3>
          <p className="text-xs text-slate-500 max-w-sm mx-auto">
            Actions like creating cases, accessing evidence, and running diagnostic checks will automatically append non-repudiation audit entries here.
          </p>
        </div>
      ) : (
        <div className="bg-[#0f1624] border border-slate-800/80 rounded-lg overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-[#0a0f1a] text-slate-400 font-mono text-[11px] uppercase border-b border-slate-800/80">
                <tr>
                  <th className="px-4 py-3">Timestamp (UTC)</th>
                  <th className="px-4 py-3">Operator</th>
                  <th className="px-4 py-3">Action</th>
                  <th className="px-4 py-3">Target</th>
                  <th className="px-4 py-3">Details</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-mono">
                {audits.map((item) => (
                  <tr key={item.id} className="hover:bg-slate-900/40 transition-colors">
                    <td className="px-4 py-3 text-slate-400 whitespace-nowrap">
                      {new Date(item.timestamp).toISOString().replace('T', ' ').substring(0, 19)}
                    </td>
                    <td className="px-4 py-3 text-slate-200 flex items-center gap-1.5">
                      <User className="w-3 h-3 text-sky-400" />
                      <span>{item.operator}</span>
                    </td>
                    <td className="px-4 py-3">
                      <StatusBadge
                        label={item.action}
                        variant={getActionVariant(item.action)}
                        size="xs"
                      />
                    </td>
                    <td className="px-4 py-3 text-sky-300">
                      {item.target_type}: {item.target_id}
                    </td>
                    <td className="px-4 py-3 text-slate-300 font-sans max-w-md truncate">
                      {item.details || '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
