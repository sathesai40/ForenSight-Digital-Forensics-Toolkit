import React from 'react';
import { Link } from 'react-router-dom';
import { ShieldAlert, ArrowLeft } from 'lucide-react';

export default function NotFound() {
  return (
    <div className="py-20 text-center space-y-4 max-w-md mx-auto">
      <div className="w-12 h-12 rounded-full bg-rose-500/10 border border-rose-500/20 text-rose-400 flex items-center justify-center mx-auto">
        <ShieldAlert className="w-6 h-6" />
      </div>
      <h2 className="text-lg font-bold text-slate-100 font-mono">404: ARTIFACT NOT FOUND</h2>
      <p className="text-xs text-slate-400">
        The requested forensic route or resource does not exist in the active workbench scope.
      </p>
      <Link
        to="/"
        className="inline-flex items-center gap-2 text-xs font-mono text-sky-400 hover:text-sky-300 pt-2"
      >
        <ArrowLeft className="w-3.5 h-3.5" />
        <span>Return to Investigation Overview</span>
      </Link>
    </div>
  );
}
