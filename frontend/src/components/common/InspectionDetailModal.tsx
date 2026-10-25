import React, { useState } from 'react';
import {
  X,
  Printer,
  Clock,
  Cpu,
  Layers,
  FileText,
  Trash2,
  Maximize2,
  CheckCircle,
  AlertTriangle,
  XCircle,
} from 'lucide-react';
import { Inspection } from '../../types';
import { StatusBadge, DefectTypeBadge } from './StatusBadge';

interface InspectionDetailModalProps {
  inspection: Inspection | null;
  onClose: () => void;
  onOpenReport: (inspection: Inspection) => void;
  onDelete?: (id: string) => void;
}

export const InspectionDetailModal: React.FC<InspectionDetailModalProps> = ({
  inspection,
  onClose,
  onOpenReport,
  onDelete,
}) => {
  const [viewMode, setViewMode] = useState<'annotated' | 'original' | 'split'>('annotated');

  if (!inspection) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-xs animate-in fade-in duration-200">
      <div className="bg-white rounded-xl shadow-2xl border border-slate-200 max-w-4xl w-full max-h-[92vh] flex flex-col overflow-hidden">
        {/* Modal Header */}
        <div className="px-6 py-4 border-b border-slate-200 flex items-center justify-between bg-slate-50">
          <div className="flex items-center gap-3">
            <h3 className="text-base font-bold text-slate-900">
              Inspection Details
            </h3>
            <span className="font-mono text-xs px-2 py-0.5 bg-slate-200 rounded text-slate-700">
              {inspection.id.slice(0, 8)}...
            </span>
            <StatusBadge status={inspection.status} size="sm" />
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => onOpenReport(inspection)}
              className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-slate-700 bg-white border border-slate-300 rounded-lg hover:bg-slate-50 transition-colors shadow-xs"
            >
              <Printer className="w-3.5 h-3.5 text-slate-500" />
              <span>Printable Report</span>
            </button>
            <button
              onClick={onClose}
              className="p-1.5 text-slate-400 hover:text-slate-600 rounded-lg hover:bg-slate-100 transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Modal Body */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {/* Image Display Section */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-500">
                Visual Inspection Inspection View
              </span>
              <div className="inline-flex rounded-lg border border-slate-200 p-0.5 bg-slate-100 text-xs">
                <button
                  onClick={() => setViewMode('annotated')}
                  className={`px-3 py-1 rounded-md font-medium transition-all ${
                    viewMode === 'annotated'
                      ? 'bg-white text-slate-900 shadow-xs'
                      : 'text-slate-600 hover:text-slate-900'
                  }`}
                >
                  AI Annotated
                </button>
                <button
                  onClick={() => setViewMode('original')}
                  className={`px-3 py-1 rounded-md font-medium transition-all ${
                    viewMode === 'original'
                      ? 'bg-white text-slate-900 shadow-xs'
                      : 'text-slate-600 hover:text-slate-900'
                  }`}
                >
                  Original Image
                </button>
                <button
                  onClick={() => setViewMode('split')}
                  className={`px-3 py-1 rounded-md font-medium transition-all ${
                    viewMode === 'split'
                      ? 'bg-white text-slate-900 shadow-xs'
                      : 'text-slate-600 hover:text-slate-900'
                  }`}
                >
                  Side by Side
                </button>
              </div>
            </div>

            <div className="bg-slate-950 rounded-xl overflow-hidden border border-slate-800 p-2 flex items-center justify-center min-h-[320px]">
              {viewMode === 'annotated' && (
                <div className="relative max-h-[420px] flex items-center justify-center">
                  <img
                    src={inspection.annotated_image_url || inspection.original_image_url}
                    alt="Annotated Inspection"
                    className="max-h-[400px] w-auto object-contain rounded-lg"
                  />
                </div>
              )}

              {viewMode === 'original' && (
                <div className="relative max-h-[420px] flex items-center justify-center">
                  <img
                    src={inspection.original_image_url}
                    alt="Original Upload"
                    className="max-h-[400px] w-auto object-contain rounded-lg"
                  />
                </div>
              )}

              {viewMode === 'split' && (
                <div className="grid grid-cols-2 gap-3 w-full">
                  <div className="text-center">
                    <p className="text-xs text-slate-400 mb-1 font-medium">Original</p>
                    <img
                      src={inspection.original_image_url}
                      alt="Original"
                      className="max-h-[360px] w-full object-contain rounded-lg bg-black/40"
                    />
                  </div>
                  <div className="text-center">
                    <p className="text-xs text-blue-400 mb-1 font-medium">AI Defect Heatmap Overlay</p>
                    <img
                      src={inspection.annotated_image_url || inspection.original_image_url}
                      alt="Annotated"
                      className="max-h-[360px] w-full object-contain rounded-lg bg-black/40"
                    />
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Key Metrics Grid */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div className="p-3.5 bg-slate-50 rounded-lg border border-slate-200">
              <span className="text-xs text-slate-500 font-medium">Defect Category</span>
              <div className="mt-1">
                <DefectTypeBadge defectType={inspection.defect_type} />
              </div>
            </div>

            <div className="p-3.5 bg-slate-50 rounded-lg border border-slate-200">
              <span className="text-xs text-slate-500 font-medium">AI Confidence</span>
              <div className="mt-1 font-bold text-slate-900 text-sm">
                {inspection.confidence_score !== null && inspection.confidence_score !== undefined
                  ? `${(inspection.confidence_score * 100).toFixed(1)}%`
                  : 'N/A'}
              </div>
            </div>

            <div className="p-3.5 bg-slate-50 rounded-lg border border-slate-200">
              <span className="text-xs text-slate-500 font-medium">Latency</span>
              <div className="mt-1 font-mono text-sm font-semibold text-slate-800">
                {inspection.inference_duration_ms.toFixed(1)} ms
              </div>
            </div>

            <div className="p-3.5 bg-slate-50 rounded-lg border border-slate-200">
              <span className="text-xs text-slate-500 font-medium">Product / Batch</span>
              <div className="mt-1 font-mono text-sm font-semibold text-slate-800 truncate" title={inspection.product_id || 'N/A'}>
                {inspection.product_id || 'Unassigned'}
              </div>
            </div>
          </div>

          {/* Technical Metadata & Defect Regions Table */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Defect Regions List */}
            <div className="border border-slate-200 rounded-lg p-4 bg-white">
              <div className="flex items-center gap-2 mb-3">
                <Layers className="w-4 h-4 text-blue-600" />
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-700">
                  Detected Defect Regions ({inspection.defect_regions?.length || 0})
                </h4>
              </div>

              {(!inspection.defect_regions || inspection.defect_regions.length === 0) ? (
                <div className="text-xs text-slate-500 py-4 text-center italic">
                  No localized surface anomalies detected in this part.
                </div>
              ) : (
                <div className="space-y-2 max-h-48 overflow-y-auto pr-1">
                  {inspection.defect_regions.map((reg, idx) => (
                    <div
                      key={idx}
                      className="p-2.5 rounded-md border border-slate-200 bg-slate-50 flex items-center justify-between text-xs"
                    >
                      <div className="flex items-center gap-2">
                        <span className="font-semibold text-red-600">#{idx + 1}</span>
                        <span className="font-medium text-slate-800">{reg.label}</span>
                      </div>
                      <div className="font-mono text-slate-500 text-[11px]">
                        X:{reg.x} Y:{reg.y} ({reg.width}x{reg.height}px)
                      </div>
                      <span className="font-semibold text-slate-700">
                        {(reg.confidence * 100).toFixed(0)}%
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Model & Audit Meta */}
            <div className="border border-slate-200 rounded-lg p-4 bg-white space-y-3">
              <div className="flex items-center gap-2">
                <Cpu className="w-4 h-4 text-blue-600" />
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-700">
                  Audit Telemetry
                </h4>
              </div>

              <div className="space-y-2 text-xs">
                <div className="flex justify-between py-1 border-b border-slate-100">
                  <span className="text-slate-500">Model Name</span>
                  <span className="font-medium text-slate-800">{inspection.model_name}</span>
                </div>
                <div className="flex justify-between py-1 border-b border-slate-100">
                  <span className="text-slate-500">Model Version</span>
                  <span className="font-mono text-slate-800">{inspection.model_version}</span>
                </div>
                <div className="flex justify-between py-1 border-b border-slate-100">
                  <span className="text-slate-500">Original Filename</span>
                  <span className="font-mono text-slate-800 truncate max-w-[200px]" title={inspection.original_filename}>
                    {inspection.original_filename}
                  </span>
                </div>
                <div className="flex justify-between py-1 border-b border-slate-100">
                  <span className="text-slate-500">Inspection Time</span>
                  <span className="text-slate-800">
                    {new Date(inspection.created_at).toLocaleString()}
                  </span>
                </div>
                <div className="flex justify-between py-1">
                  <span className="text-slate-500">Manual QA Review</span>
                  <span className={`font-semibold ${inspection.manual_review_required ? 'text-amber-600' : 'text-slate-600'}`}>
                    {inspection.manual_review_required ? 'REQUIRED' : 'NOT REQUIRED'}
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Inspector Notes */}
          {inspection.inspection_notes && (
            <div className="p-3.5 bg-slate-50 rounded-lg border border-slate-200 text-xs">
              <span className="font-bold text-slate-700 block mb-1">Inspector Notes:</span>
              <p className="text-slate-600">{inspection.inspection_notes}</p>
            </div>
          )}
        </div>

        {/* Modal Footer */}
        <div className="px-6 py-3.5 border-t border-slate-200 bg-slate-50 flex items-center justify-between">
          <div>
            {onDelete && (
              <button
                onClick={() => {
                  if (window.confirm('Are you sure you want to delete this inspection record?')) {
                    onDelete(inspection.id);
                    onClose();
                  }
                }}
                className="flex items-center gap-1.5 px-3 py-1.5 text-xs text-red-600 hover:text-red-700 hover:bg-red-50 rounded-lg transition-colors font-medium"
              >
                <Trash2 className="w-3.5 h-3.5" />
                <span>Delete Record</span>
              </button>
            )}
          </div>

          <button
            onClick={onClose}
            className="px-4 py-2 bg-slate-200 hover:bg-slate-300 text-slate-800 rounded-lg text-xs font-semibold transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
