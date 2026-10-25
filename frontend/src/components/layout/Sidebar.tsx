import React from 'react';
import {
  LayoutDashboard,
  ScanEye,
  History,
  BarChart3,
  Cpu,
  Settings,
  ShieldCheck,
  CheckCircle,
} from 'lucide-react';

export type PageId = 'dashboard' | 'inspect' | 'history' | 'analytics' | 'models' | 'settings';

interface SidebarProps {
  currentPage: PageId;
  onSelectPage: (page: PageId) => void;
  apiConnected: boolean;
}

export const Sidebar: React.FC<SidebarProps> = ({
  currentPage,
  onSelectPage,
  apiConnected,
}) => {
  const navItems: { id: PageId; label: string; icon: React.ReactNode }[] = [
    { id: 'dashboard', label: 'Smart Dashboard', icon: <LayoutDashboard className="w-5 h-5" /> },
    { id: 'inspect', label: 'New Inspection', icon: <ScanEye className="w-5 h-5" /> },
    { id: 'history', label: 'Inspection History', icon: <History className="w-5 h-5" /> },
    { id: 'analytics', label: 'Defect Analytics', icon: <BarChart3 className="w-5 h-5" /> },
    { id: 'models', label: 'AI Model Info', icon: <Cpu className="w-5 h-5" /> },
    { id: 'settings', label: 'Settings', icon: <Settings className="w-5 h-5" /> },
  ];

  return (
    <aside className="w-64 bg-slate-900 text-slate-200 flex flex-col h-screen flex-shrink-0 border-r border-slate-800 select-none">
      {/* Brand Header */}
      <div className="p-5 border-b border-slate-800 flex items-center gap-3">
        <div className="w-10 h-10 rounded-lg bg-blue-600 flex items-center justify-center text-white shadow-md shadow-blue-500/20">
          <ShieldCheck className="w-6 h-6" />
        </div>
        <div>
          <h1 className="font-bold text-white text-base leading-tight tracking-tight">
            ApexVision AI
          </h1>
          <p className="text-xs text-slate-400 font-medium">Defect Inspection Sys</p>
        </div>
      </div>

      {/* Navigation Links */}
      <nav className="flex-1 p-3 space-y-1.5 overflow-y-auto">
        <div className="px-3 py-2 text-xs font-semibold text-slate-400 uppercase tracking-wider">
          Operations
        </div>
        {navItems.map((item) => {
          const isActive = currentPage === item.id;
          return (
            <button
              key={item.id}
              onClick={() => onSelectPage(item.id)}
              className={`w-full flex items-center gap-3 px-3.5 py-2.5 rounded-lg text-sm font-medium transition-all duration-150 ${
                isActive
                  ? 'bg-blue-600 text-white shadow-sm shadow-blue-600/30'
                  : 'text-slate-300 hover:bg-slate-800/80 hover:text-white'
              }`}
            >
              <span className={isActive ? 'text-white' : 'text-slate-400'}>
                {item.icon}
              </span>
              <span>{item.label}</span>
            </button>
          );
        })}
      </nav>

      {/* System Telemetry Footer */}
      <div className="p-4 border-t border-slate-800 bg-slate-900/50">
        <div className="flex items-center justify-between text-xs">
          <span className="text-slate-400">Inference Core</span>
          <span className="font-mono text-xs text-blue-400">ResNet18-CV</span>
        </div>
        <div className="mt-2.5 flex items-center justify-between text-xs">
          <span className="text-slate-400">Backend API</span>
          <div className="flex items-center gap-1.5">
            <span
              className={`w-2 h-2 rounded-full ${
                apiConnected ? 'bg-emerald-500 animate-pulse' : 'bg-red-500'
              }`}
            />
            <span className={apiConnected ? 'text-emerald-400 font-medium' : 'text-red-400'}>
              {apiConnected ? 'ONLINE' : 'OFFLINE'}
            </span>
          </div>
        </div>
      </div>
    </aside>
  );
};
