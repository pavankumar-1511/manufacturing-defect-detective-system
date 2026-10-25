import React, { useEffect, useState } from 'react';
import {
  Sliders,
  ShieldCheck,
  Server,
  HardDrive,
  Save,
  CheckCircle2,
  AlertCircle,
  RotateCcw,
  Sparkles,
} from 'lucide-react';
import { getHealth, getModelStatus, updateThresholds } from '../services/api';

export const SettingsPage: React.FC = () => {
  const [defectThreshold, setDefectThreshold] = useState(0.50);
  const [reviewThreshold, setReviewThreshold] = useState(0.65);
  const [healthData, setHealthData] = useState<any>(null);
  const [saving, setSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);

  useEffect(() => {
    getModelStatus().then((res) => {
      if (res.defect_confidence_threshold) setDefectThreshold(res.defect_confidence_threshold);
      if (res.review_threshold) setReviewThreshold(res.review_threshold);
    });
    getHealth().then((res) => setHealthData(res));
  }, []);

  const handleSaveThresholds = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaveSuccess(false);
    setSaveError(null);

    if (defectThreshold >= reviewThreshold) {
      setSaveError('Defect Threshold must be strictly less than Review Required Threshold.');
      return;
    }

    try {
      setSaving(true);
      await updateThresholds(defectThreshold, reviewThreshold);
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
    } catch (err: any) {
      setSaveError(err.response?.data?.detail || 'Failed to update thresholds.');
    } finally {
      setSaving(false);
    }
  };

  const handleResetDefaults = () => {
    setDefectThreshold(0.50);
    setReviewThreshold(0.65);
  };

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      {/* Threshold Calibration Form */}
      <form onSubmit={handleSaveThresholds} className="bg-white p-6 rounded-xl border border-slate-200 shadow-xs space-y-6">
        <div className="flex items-center justify-between border-b border-slate-100 pb-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-blue-50 text-blue-600 flex items-center justify-center">
              <Sliders className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-base font-bold text-slate-900">
                Inference Decision Boundaries
              </h2>
              <p className="text-xs text-slate-500">
                Fine-tune confidence limits for ACCEPTED, REVIEW REQUIRED, and DEFECTIVE verdicts
              </p>
            </div>
          </div>

          <button
            type="button"
            onClick={handleResetDefaults}
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-slate-600 hover:text-slate-900 bg-slate-100 hover:bg-slate-200 rounded-lg transition-colors"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span>Defaults</span>
          </button>
        </div>

        {saveSuccess && (
          <div className="p-3 bg-emerald-50 border border-emerald-200 text-emerald-800 rounded-lg text-xs flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-600" />
            <span>Thresholds saved and applied to active inference pipeline.</span>
          </div>
        )}

        {saveError && (
          <div className="p-3 bg-red-50 border border-red-200 text-red-700 rounded-lg text-xs flex items-center gap-2">
            <AlertCircle className="w-4 h-4 text-red-600" />
            <span>{saveError}</span>
          </div>
        )}

        <div className="space-y-5">
          {/* Defect Threshold Slider */}
          <div className="space-y-2">
            <div className="flex justify-between items-center text-xs">
              <div>
                <span className="font-bold text-slate-800">
                  Defect Detection Floor (Accepted vs Review)
                </span>
                <p className="text-slate-500 text-[11px]">
                  Samples with anomaly scores below this value are classified as ACCEPTED.
                </p>
              </div>
              <span className="font-mono font-bold text-sm text-blue-600 bg-blue-50 px-2.5 py-1 rounded">
                {(defectThreshold * 100).toFixed(0)}% ({defectThreshold.toFixed(2)})
              </span>
            </div>
            <input
              type="range"
              min="0.10"
              max="0.80"
              step="0.05"
              value={defectThreshold}
              onChange={(e) => setDefectThreshold(parseFloat(e.target.value))}
              className="w-full accent-blue-600 cursor-pointer"
            />
          </div>

          {/* Review Required Threshold Slider */}
          <div className="space-y-2">
            <div className="flex justify-between items-center text-xs">
              <div>
                <span className="font-bold text-slate-800">
                  Critical Defect Boundary (Review vs Defective)
                </span>
                <p className="text-slate-500 text-[11px]">
                  Samples with anomaly scores above this value are rejected as DEFECTIVE.
                </p>
              </div>
              <span className="font-mono font-bold text-sm text-red-600 bg-red-50 px-2.5 py-1 rounded">
                {(reviewThreshold * 100).toFixed(0)}% ({reviewThreshold.toFixed(2)})
              </span>
            </div>
            <input
              type="range"
              min="0.30"
              max="0.95"
              step="0.05"
              value={reviewThreshold}
              onChange={(e) => setReviewThreshold(parseFloat(e.target.value))}
              className="w-full accent-red-600 cursor-pointer"
            />
          </div>
        </div>

        <div className="pt-3 border-t border-slate-100 flex justify-end">
          <button
            type="submit"
            disabled={saving}
            className="flex items-center gap-2 px-5 py-2.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-bold shadow-sm transition-all active:scale-95 disabled:opacity-50"
          >
            <Save className="w-4 h-4" />
            <span>{saving ? 'Applying...' : 'Save Decision Boundaries'}</span>
          </button>
        </div>
      </form>

      {/* System Infrastructure Telemetry */}
      <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-xs space-y-4">
        <div className="flex items-center gap-3 pb-3 border-b border-slate-100">
          <div className="w-10 h-10 rounded-lg bg-slate-100 text-slate-700 flex items-center justify-center">
            <Server className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-base font-bold text-slate-900">
              System Infrastructure & Security
            </h2>
            <p className="text-xs text-slate-500">FastAPI backend, storage quotas, and security boundaries</p>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
          <div className="p-3.5 bg-slate-50 rounded-lg border border-slate-200 space-y-1.5">
            <span className="font-bold text-slate-700 block">FastAPI Server Status</span>
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse" />
              <span className="font-medium text-emerald-700">Healthy & Online</span>
            </div>
            <p className="text-slate-500 text-[11px] font-mono">
              Timestamp: {healthData?.timestamp || 'Synchronized'}
            </p>
          </div>

          <div className="p-3.5 bg-slate-50 rounded-lg border border-slate-200 space-y-1.5">
            <span className="font-bold text-slate-700 block">Database Storage</span>
            <div className="font-medium text-slate-800">SQLite + SQLAlchemy ORM</div>
            <p className="text-slate-500 text-[11px]">
              Schema: Auto-migrated with indexed audit logs
            </p>
          </div>

          <div className="p-3.5 bg-slate-50 rounded-lg border border-slate-200 space-y-1.5">
            <span className="font-bold text-slate-700 block">Upload Security Policy</span>
            <div className="font-medium text-slate-800">10 MB Strict Limit</div>
            <p className="text-slate-500 text-[11px]">
              Magic byte verification & path-traversal sanitization
            </p>
          </div>

          <div className="p-3.5 bg-slate-50 rounded-lg border border-slate-200 space-y-1.5">
            <span className="font-bold text-slate-700 block">Allowed Media MIME Types</span>
            <div className="font-mono font-medium text-slate-800">image/jpeg, image/png</div>
            <p className="text-slate-500 text-[11px]">
              Non-image uploads strictly rejected with 415 HTTP
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
