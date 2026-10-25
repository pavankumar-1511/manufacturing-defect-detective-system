import React from 'react';
import { ScanEye, RefreshCw } from 'lucide-react';
import { PageId } from './Sidebar';

interface HeaderProps {
  currentPage: PageId;
  onNavigateInspect: () => void;
  onRefresh?: () => void;
  loading?: boolean;
}

export const Header: React.FC<HeaderProps> = ({
  currentPage,
  onNavigateInspect,
  onRefresh,
  loading = false,
}) => {
  const titles: Record<PageId, { title: string; subtitle: string }> = {
    dashboard: {
      title: 'Smart Quality Dashboard',
      subtitle: 'Real-time AI-powered optical inspection telemetry, quality scoring & anomaly alerts',
    },
    inspect: {
      title: 'New Defect Inspection',
      subtitle: 'Upload industrial parts for deep learning anomaly classification',
    },
    history: {
      title: 'Inspection History & Logs',
      subtitle: 'Audit trail, searchable records, and compliance CSV export',
    },
    analytics: {
      title: 'Defect Analytics & Trends',
      subtitle: 'Statistical process control, defect distributions, and yield charts',
    },
    models: {
      title: 'AI Model Architecture & Telemetry',
      subtitle: 'PyTorch deep feature extractor and OpenCV morphology parameters',
    },
    settings: {
      title: 'System Settings & Thresholds',
      subtitle: 'Calibrate confidence decision boundaries and inspect system health',
    },
  };

  const current = titles[currentPage] || titles.dashboard;

  return (
    <header className="h-16 bg-white border-b border-slate-200 px-6 flex items-center justify-between flex-shrink-0 z-10">
      <div>
        <h2 className="text-lg font-bold text-slate-900 leading-tight">
          {current.title}
        </h2>
        <p className="text-xs text-slate-500">{current.subtitle}</p>
      </div>

      <div className="flex items-center gap-3">
        {onRefresh && (
          <button
            onClick={onRefresh}
            disabled={loading}
            title="Refresh live data"
            className="p-2 text-slate-500 hover:text-slate-800 hover:bg-slate-100 rounded-lg transition-colors disabled:opacity-50"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin text-blue-600' : ''}`} />
          </button>
        )}

        {currentPage !== 'inspect' && (
          <button
            onClick={onNavigateInspect}
            className="flex items-center gap-2 px-3.5 py-1.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-semibold shadow-sm transition-all shadow-blue-500/20 active:scale-95"
          >
            <ScanEye className="w-4 h-4" />
            <span>New Inspection</span>
          </button>
        )}
      </div>
    </header>
  );
};
