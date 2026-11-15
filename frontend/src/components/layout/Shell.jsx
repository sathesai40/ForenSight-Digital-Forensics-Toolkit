import React, { useState, useEffect, useCallback } from 'react';
import { Outlet } from 'react-router-dom';
import Sidebar from './Sidebar';
import Topbar from './Topbar';
import api from '../../api/client';

export default function Shell() {
  const [health, setHealth] = useState(null);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [connectionError, setConnectionError] = useState(null);

  const fetchHealth = useCallback(async () => {
    setIsRefreshing(true);
    try {
      const data = await api.getHealth();
      setHealth(data);
      setConnectionError(null);
    } catch (err) {
      console.warn('Backend health check error:', err.message);
      setConnectionError(err.message);
    } finally {
      setIsRefreshing(false);
    }
  }, []);

  useEffect(() => {
    fetchHealth();
    // Poll telemetry periodically (every 30s)
    const interval = setInterval(fetchHealth, 30000);
    return () => clearInterval(interval);
  }, [fetchHealth]);

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-[#090d16] text-slate-100 font-sans">
      <Sidebar health={health} />
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        <Topbar
          health={health}
          isRefreshing={isRefreshing}
          onRefreshHealth={fetchHealth}
          connectionError={connectionError}
        />
        <main className="flex-1 overflow-y-auto p-6 md:p-8 bg-[#090d16]">
          <Outlet context={{ health, isRefreshing, refreshHealth: fetchHealth, connectionError }} />
        </main>
      </div>
    </div>
  );
}
