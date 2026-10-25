import React, { useState, useEffect } from 'react';
import { Sidebar, PageId } from './components/layout/Sidebar';
import { Header } from './components/layout/Header';
import { DashboardPage } from './pages/DashboardPage';
import { NewInspectionPage } from './pages/NewInspectionPage';
import { HistoryPage } from './pages/HistoryPage';
import { AnalyticsPage } from './pages/AnalyticsPage';
import { ModelInfoPage } from './pages/ModelInfoPage';
import { SettingsPage } from './pages/SettingsPage';
import { InspectionDetailModal } from './components/common/InspectionDetailModal';
import { PrintableReportModal } from './components/common/PrintableReportModal';
import { Inspection } from './types';
import { getHealth, deleteInspection } from './services/api';

export function App() {
  const [currentPage, setCurrentPage] = useState<PageId>('dashboard');
  const [selectedInspection, setSelectedInspection] = useState<Inspection | null>(null);
  const [reportingInspection, setReportingInspection] = useState<Inspection | null>(null);
  const [apiConnected, setApiConnected] = useState<boolean>(true);
  const [refreshKey, setRefreshKey] = useState<number>(0);

  // Poll backend health every 15 seconds
  useEffect(() => {
    const checkConnection = () => {
      getHealth()
        .then(() => setApiConnected(true))
        .catch(() => setApiConnected(false));
    };

    checkConnection();
    const interval = setInterval(checkConnection, 15000);
    return () => clearInterval(interval);
  }, []);

  const handleRefresh = () => {
    setRefreshKey((k) => k + 1);
  };

  const handleInspectionCreated = (inspection: Inspection) => {
    // Automatically updated; user can choose to view or print
  };

  const handleDeleteInspection = async (id: string) => {
    try {
      await deleteInspection(id);
      handleRefresh();
    } catch (err) {
      console.error('Delete error:', err);
    }
  };

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-slate-50 text-slate-900 font-sans">
      {/* Dark Navy Sidebar */}
      <Sidebar
        currentPage={currentPage}
        onSelectPage={setCurrentPage}
        apiConnected={apiConnected}
      />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Header */}
        <Header
          currentPage={currentPage}
          onNavigateInspect={() => setCurrentPage('inspect')}
          onRefresh={handleRefresh}
        />

        {/* Page Container */}
        <main className="flex-1 overflow-y-auto p-6 md:p-8">
          {currentPage === 'dashboard' && (
            <DashboardPage
              key={refreshKey}
              onNavigateInspect={() => setCurrentPage('inspect')}
              onNavigateHistory={() => setCurrentPage('history')}
              onSelectInspection={setSelectedInspection}
            />
          )}

          {currentPage === 'inspect' && (
            <NewInspectionPage
              onInspectionCreated={handleInspectionCreated}
              onOpenReport={setReportingInspection}
              onNavigateHistory={() => setCurrentPage('history')}
            />
          )}

          {currentPage === 'history' && (
            <HistoryPage
              key={refreshKey}
              onSelectInspection={setSelectedInspection}
              onOpenReport={setReportingInspection}
            />
          )}

          {currentPage === 'analytics' && (
            <AnalyticsPage key={refreshKey} />
          )}

          {currentPage === 'models' && (
            <ModelInfoPage key={refreshKey} />
          )}

          {currentPage === 'settings' && (
            <SettingsPage key={refreshKey} />
          )}
        </main>
      </div>

      {/* Inspection Detail Modal */}
      <InspectionDetailModal
        inspection={selectedInspection}
        onClose={() => setSelectedInspection(null)}
        onOpenReport={(item) => {
          setSelectedInspection(null);
          setReportingInspection(item);
        }}
        onDelete={handleDeleteInspection}
      />

      {/* Official Printable Inspection Certificate & Report Modal */}
      <PrintableReportModal
        inspection={reportingInspection}
        onClose={() => setReportingInspection(null)}
      />
    </div>
  );
}

export default App;
