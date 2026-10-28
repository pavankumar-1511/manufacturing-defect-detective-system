import React, { useEffect, useState } from 'react';
import { X, Printer, ShieldCheck, CheckCircle2, AlertOctagon, AlertTriangle } from 'lucide-react';
import { Inspection, InspectionReport } from '../../types';
import { getInspectionReport, getImageUrl } from '../../services/api';

interface PrintableReportModalProps {
  inspection: Inspection | null;
  onClose: () => void;
}

export const PrintableReportModal: React.FC<PrintableReportModalProps> = ({
  inspection,
  onClose,
}) => {
  const [report, setReport] = useState<InspectionReport | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!inspection) return;
    setLoading(true);
    getInspectionReport(inspection.id)
      .then((data) => setReport(data))
      .catch((err) => console.error('Failed to load report:', err))
      .finally(() => setLoading(false));
  }, [inspection]);

  if (!inspection) return null;

  const handlePrint = () => {
    window.print();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/70 backdrop-blur-xs overflow-y-auto">
      <div className="bg-white rounded-xl shadow-2xl border border-slate-200 max-w-4xl w-full my-8 flex flex-col overflow-hidden">
        {/* Modal Controls (Hidden in Print) */}
        <div className="no-print px-6 py-4 border-b border-slate-200 flex items-center justify-between bg-slate-900 text-white">
          <div className="flex items-center gap-2">
            <Printer className="w-5 h-5 text-blue-400" />
            <span className="font-bold text-sm">Industrial Inspection Certificate & Report</span>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={handlePrint}
              className="flex items-center gap-1.5 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold rounded-lg shadow-sm transition-all active:scale-95"
            >
              <Printer className="w-4 h-4" />
              <span>Print / Save PDF</span>
            </button>
            <button
              onClick={onClose}
              className="p-2 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800 transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Printable Report Document */}
        <div className="p-8 space-y-6 print-card bg-white text-slate-900 font-sans">
          {/* Official Document Header */}
          <div className="flex items-start justify-between border-b-2 border-slate-900 pb-5">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 bg-slate-900 rounded-lg flex items-center justify-center text-white">
                <ShieldCheck className="w-7 h-7" />
              </div>
              <div>
                <h1 className="text-xl font-black uppercase tracking-tight text-slate-900">
                  ApexVision Quality Assurance
                </h1>
                <p className="text-xs font-medium text-slate-500">
                  Automated Optical Inspection (AOI) — Surface Defect Audit Certificate
                </p>
              </div>
            </div>

            <div className="text-right text-xs space-y-0.5">
              <p className="font-mono font-bold text-slate-800">
                REPORT REF: <span className="text-blue-600">QA-{inspection.id.slice(0, 8).toUpperCase()}</span>
              </p>
              <p className="text-slate-500">
                Date: {new Date(inspection.created_at).toLocaleDateString()}
              </p>
              <p className="text-slate-500">
                Time: {new Date(inspection.created_at).toLocaleTimeString()} UTC
              </p>
            </div>
          </div>

          {/* Quality Verdict Banner */}
          <div
            className={`p-4 rounded-lg border-2 flex items-center justify-between ${
              inspection.status === 'ACCEPTED'
                ? 'bg-emerald-50 border-emerald-500 text-emerald-900'
                : inspection.status === 'DEFECTIVE'
                ? 'bg-red-50 border-red-500 text-red-900'
                : 'bg-amber-50 border-amber-500 text-amber-900'
            }`}
          >
            <div className="flex items-center gap-3">
              {inspection.status === 'ACCEPTED' && <CheckCircle2 className="w-7 h-7 text-emerald-600" />}
              {inspection.status === 'DEFECTIVE' && <AlertOctagon className="w-7 h-7 text-red-600" />}
              {inspection.status === 'REVIEW_REQUIRED' && <AlertTriangle className="w-7 h-7 text-amber-600" />}
              <div>
                <h2 className="text-base font-black tracking-wide uppercase">
                  VERDICT: {inspection.status}
                </h2>
                <p className="text-xs font-medium opacity-90">
                  {report?.quality_verdict ||
                    (inspection.status === 'ACCEPTED'
                      ? 'Component meets all surface and dimensional tolerance criteria.'
                      : 'Anomalies detected. Component flagged for rework or rejection.')}
                </p>
              </div>
            </div>

            <div className="text-right">
              <span className="text-xs uppercase font-bold tracking-wider opacity-75 block">
                Confidence
              </span>
              <span className="text-xl font-black">
                {inspection.confidence_score !== null && inspection.confidence_score !== undefined
                  ? `${(inspection.confidence_score * 100).toFixed(1)}%`
                  : 'N/A'}
              </span>
            </div>
          </div>

          {/* Inspection Metadata Table */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs">
            <div className="border border-slate-200 p-3 rounded-md bg-slate-50">
              <span className="text-slate-500 font-medium block">Batch / Product ID</span>
              <span className="font-mono font-bold text-slate-800 text-sm">
                {inspection.product_id || 'UNASSIGNED'}
              </span>
            </div>
            <div className="border border-slate-200 p-3 rounded-md bg-slate-50">
              <span className="text-slate-500 font-medium block">Defect Category</span>
              <span className="font-bold text-slate-800 text-sm">
                {inspection.defect_type || 'None (Normal)'}
              </span>
            </div>
            <div className="border border-slate-200 p-3 rounded-md bg-slate-50">
              <span className="text-slate-500 font-medium block">Inference Duration</span>
              <span className="font-mono font-semibold text-slate-800 text-sm">
                {inspection.inference_duration_ms.toFixed(1)} ms
              </span>
            </div>
            <div className="border border-slate-200 p-3 rounded-md bg-slate-50">
              <span className="text-slate-500 font-medium block">AI Model Engine</span>
              <span className="font-medium text-slate-800 text-xs">
                {inspection.model_name} (v{inspection.model_version})
              </span>
            </div>
          </div>

          {/* Inspection Images Side-by-Side */}
          <div>
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-600 mb-2">
              Optical Evidence & Defect Mapping
            </h3>
            <div className="grid grid-cols-2 gap-4">
              <div className="border border-slate-300 rounded-lg p-2 bg-slate-100 text-center">
                <span className="text-[11px] font-semibold text-slate-600 mb-1 block">
                  Original Captured Part
                </span>
                <img
                  src={getImageUrl(inspection.original_image_url)}
                  alt="Original"
                  className="max-h-56 mx-auto object-contain rounded"
                />
              </div>

              <div className="border border-slate-300 rounded-lg p-2 bg-slate-100 text-center">
                <span className="text-[11px] font-semibold text-blue-700 mb-1 block">
                  AI Defect Localization Heatmap
                </span>
                <img
                  src={getImageUrl(inspection.annotated_image_url || inspection.original_image_url)}
                  alt="Annotated"
                  className="max-h-56 mx-auto object-contain rounded"
                />
              </div>
            </div>
          </div>

          {/* Defect Regions List */}
          {inspection.defect_regions && inspection.defect_regions.length > 0 && (
            <div>
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-600 mb-2">
                Defect Region Coordinates
              </h3>
              <table className="w-full text-xs border border-slate-200 rounded-lg overflow-hidden">
                <thead className="bg-slate-100 text-slate-700 font-bold">
                  <tr>
                    <th className="py-2 px-3 text-left">Region</th>
                    <th className="py-2 px-3 text-left">Defect Type</th>
                    <th className="py-2 px-3 text-left">Bounding Box [X, Y, W, H]</th>
                    <th className="py-2 px-3 text-right">Confidence</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-200">
                  {inspection.defect_regions.map((reg, idx) => (
                    <tr key={idx}>
                      <td className="py-2 px-3 font-semibold text-red-600">Region #{idx + 1}</td>
                      <td className="py-2 px-3 font-medium">{reg.label}</td>
                      <td className="py-2 px-3 font-mono text-slate-600">
                        [{reg.x}, {reg.y}, {reg.width}, {reg.height}]
                      </td>
                      <td className="py-2 px-3 text-right font-bold">
                        {(reg.confidence * 100).toFixed(0)}%
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* Inspector Notes */}
          {inspection.inspection_notes && (
            <div className="border border-slate-200 p-3 rounded-lg text-xs">
              <span className="font-bold text-slate-700 block mb-0.5">Inspector Observations:</span>
              <p className="text-slate-600">{inspection.inspection_notes}</p>
            </div>
          )}

          {/* Formal Sign-off Section */}
          <div className="grid grid-cols-2 gap-8 pt-6 border-t border-slate-300 text-xs">
            <div>
              <span className="text-slate-500 font-medium block">Lead Quality Inspector</span>
              <div className="mt-4 border-b border-slate-400 w-48 h-8 flex items-end">
                <span className="font-serif italic text-sm text-slate-700">Autonomous Vision Agent</span>
              </div>
              <p className="text-[10px] text-slate-400 mt-1">Verified via Deep Vision Engine</p>
            </div>

            <div className="text-right">
              <span className="text-slate-500 font-medium block">Official System Stamp</span>
              <div className="mt-2 inline-block border-2 border-slate-700 rounded-md p-2 text-center">
                <span className="text-[10px] font-mono font-bold uppercase tracking-wider block text-slate-800">
                  APEXVISION QA LAB
                </span>
                <span className="text-[9px] text-slate-600 block">
                  STATUS: {inspection.status}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Modal Bottom Controls (Hidden in Print) */}
        <div className="no-print px-6 py-3.5 bg-slate-50 border-t border-slate-200 flex justify-end gap-2">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-slate-200 hover:bg-slate-300 text-slate-800 text-xs font-semibold rounded-lg transition-colors"
          >
            Close
          </button>
          <button
            onClick={handlePrint}
            className="flex items-center gap-1.5 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold rounded-lg shadow-sm transition-colors"
          >
            <Printer className="w-3.5 h-3.5" />
            <span>Print Report</span>
          </button>
        </div>
      </div>
    </div>
  );
};
