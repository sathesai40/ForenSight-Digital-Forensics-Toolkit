import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Shell from './components/layout/Shell';
import Dashboard from './pages/Dashboard';
import Cases from './pages/Cases';
import EvidenceVault from './pages/EvidenceVault';
import Timeline from './pages/Timeline';
import LogAnalysis from './pages/LogAnalysis';
import AuditTrail from './pages/AuditTrail';
import Settings from './pages/Settings';
import NotFound from './pages/NotFound';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Shell />}>
          <Route index element={<Dashboard />} />
          <Route path="cases" element={<Cases />} />
          <Route path="evidence" element={<EvidenceVault />} />
          <Route path="timeline" element={<Timeline />} />
          <Route path="logs" element={<LogAnalysis />} />
          <Route path="audit" element={<AuditTrail />} />
          <Route path="settings" element={<Settings />} />
          <Route path="*" element={<NotFound />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
