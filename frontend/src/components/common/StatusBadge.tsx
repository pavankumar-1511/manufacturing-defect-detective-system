import React from 'react';
import { CheckCircle2, AlertTriangle, XCircle } from 'lucide-react';
import { InspectionStatus } from '../../types';

interface StatusBadgeProps {
  status: InspectionStatus;
  size?: 'sm' | 'md' | 'lg';
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status, size = 'md' }) => {
  const sizeClasses = {
    sm: 'px-2 py-0.5 text-xs',
    md: 'px-2.5 py-1 text-xs',
    lg: 'px-3.5 py-1.5 text-sm font-semibold',
  };

  if (status === 'ACCEPTED') {
    return (
      <span className={`inline-flex items-center gap-1.5 rounded-full font-medium bg-emerald-50 text-emerald-700 border border-emerald-200 ${sizeClasses[size]}`}>
        <CheckCircle2 className={size === 'lg' ? 'w-4 h-4' : 'w-3.5 h-3.5'} />
        <span>ACCEPTED</span>
      </span>
    );
  }

  if (status === 'DEFECTIVE') {
    return (
      <span className={`inline-flex items-center gap-1.5 rounded-full font-medium bg-red-50 text-red-700 border border-red-200 ${sizeClasses[size]}`}>
        <XCircle className={size === 'lg' ? 'w-4 h-4' : 'w-3.5 h-3.5'} />
        <span>DEFECTIVE</span>
      </span>
    );
  }

  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full font-medium bg-amber-50 text-amber-700 border border-amber-200 ${sizeClasses[size]}`}>
      <AlertTriangle className={size === 'lg' ? 'w-4 h-4' : 'w-3.5 h-3.5'} />
      <span>REVIEW REQUIRED</span>
    </span>
  );
};

export const DefectTypeBadge: React.FC<{ defectType?: string | null }> = ({ defectType }) => {
  if (!defectType || defectType === 'None') {
    return (
      <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-slate-100 text-slate-600">
        None
      </span>
    );
  }

  const categoryColors: Record<string, string> = {
    'Scratches': 'bg-rose-50 text-rose-700 border-rose-200',
    'Cracks': 'bg-red-50 text-red-800 border-red-200 font-semibold',
    'Dents': 'bg-amber-50 text-amber-800 border-amber-200',
    'Surface Abnormalities': 'bg-orange-50 text-orange-800 border-orange-200',
  };

  const style = categoryColors[defectType] || 'bg-slate-100 text-slate-700 border-slate-200';

  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium border ${style}`}>
      {defectType}
    </span>
  );
};
