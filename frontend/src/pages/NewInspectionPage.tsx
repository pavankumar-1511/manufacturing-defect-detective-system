import React, { useState, useRef } from 'react';
import {
  UploadCloud,
  FileImage,
  ScanEye,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Clock,
  Printer,
  RotateCcw,
  Sparkles,
  Layers,
  Cpu,
  ArrowRight,
} from 'lucide-react';
import { createInspection, getImageUrl } from '../services/api';
import { Inspection } from '../types';
import { StatusBadge, DefectTypeBadge } from '../components/common/StatusBadge';

interface NewInspectionPageProps {
  onInspectionCreated: (inspection: Inspection) => void;
  onOpenReport: (inspection: Inspection) => void;
  onNavigateHistory: () => void;
}

export const NewInspectionPage: React.FC<NewInspectionPageProps> = ({
  onInspectionCreated,
  onOpenReport,
  onNavigateHistory,
}) => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [productId, setProductId] = useState('');
  const [notes, setNotes] = useState('');
  const [isDragging, setIsDragging] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<Inspection | null>(null);
  const [imageTab, setImageTab] = useState<'annotated' | 'original'>('annotated');

  const fileInputRef = useRef<HTMLInputElement | null>(null);

  const handleFileChange = (file: File) => {
    setError(null);
    setResult(null);

    // Validate size (10MB max)
    if (file.size > 10 * 1024 * 1024) {
      setError('File exceeds 10 MB limit. Please select a smaller image.');
      return;
    }

    // Validate type
    const validTypes = ['image/jpeg', 'image/png', 'image/jpg'];
    if (!validTypes.includes(file.type)) {
      setError('Invalid file format. Please upload JPG, JPEG, or PNG.');
      return;
    }

    setSelectedFile(file);
    const url = URL.createObjectURL(file);
    setPreviewUrl(url);
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFileChange(e.dataTransfer.files[0]);
    }
  };

  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedFile) {
      setError('Please choose or drop a product image to inspect.');
      return;
    }

    try {
      setIsSubmitting(true);
      setError(null);
      const inspection = await createInspection(selectedFile, productId, notes);
      setResult(inspection);
      onInspectionCreated(inspection);
    } catch (err: any) {
      console.error('Inspection error:', err);
      const detail = err.response?.data?.detail || 'Inference pipeline failure. Please check backend logs.';
      setError(detail);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleReset = () => {
    setSelectedFile(null);
    setPreviewUrl(null);
    setResult(null);
    setError(null);
    setProductId('');
    setNotes('');
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  // Helper to load bundled synthetic test samples
  const handleLoadSample = async (sampleName: string, label: string) => {
    try {
      setError(null);
      const res = await fetch(`/api/images/original/${sampleName}`);
      if (!res.ok) {
        throw new Error('Sample not found on server');
      }
      const blob = await res.blob();
      const file = new File([blob], sampleName, { type: 'image/png' });
      setProductId(`SAMPLE-${label.toUpperCase()}`);
      setNotes(`Automated test verification on ${label} sample.`);
      handleFileChange(file);
    } catch (err) {
      setError('Could not load test sample image from server.');
    }
  };

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      {/* If result is ready, show comprehensive inspection verdict view */}
      {result ? (
        <div className="space-y-6 animate-in fade-in duration-300">
          {/* Verdict Banner Card */}
          <div
            className={`p-6 rounded-xl border-2 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4 ${
              result.status === 'ACCEPTED'
                ? 'bg-emerald-50 border-emerald-500'
                : result.status === 'DEFECTIVE'
                ? 'bg-red-50 border-red-500'
                : 'bg-amber-50 border-amber-500'
            }`}
          >
            <div className="flex items-center gap-4">
              <div
                className={`w-14 h-14 rounded-xl flex items-center justify-center text-white ${
                  result.status === 'ACCEPTED'
                    ? 'bg-emerald-600'
                    : result.status === 'DEFECTIVE'
                    ? 'bg-red-600'
                    : 'bg-amber-600'
                }`}
              >
                {result.status === 'ACCEPTED' && <CheckCircle2 className="w-8 h-8" />}
                {result.status === 'DEFECTIVE' && <XCircle className="w-8 h-8" />}
                {result.status === 'REVIEW_REQUIRED' && <AlertTriangle className="w-8 h-8" />}
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h2 className="text-xl font-black text-slate-900 tracking-tight uppercase">
                    INSPECTION VERDICT: {result.status}
                  </h2>
                </div>
                <p className="text-xs text-slate-600 mt-0.5">
                  {result.status === 'ACCEPTED'
                    ? 'All geometric and surface integrity checks passed without defects.'
                    : result.status === 'DEFECTIVE'
                    ? `Manufacturing defect detected: ${result.defect_type || 'Surface Anomaly'}. Flagged for rejection.`
                    : 'Discrepancy at decision threshold. QA inspector physical verification required.'}
                </p>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <button
                onClick={() => onOpenReport(result)}
                className="flex items-center gap-2 px-4 py-2 bg-white text-slate-800 border border-slate-300 rounded-lg text-xs font-semibold hover:bg-slate-50 transition-colors shadow-xs"
              >
                <Printer className="w-4 h-4 text-slate-600" />
                <span>Print Certificate</span>
              </button>
              <button
                onClick={handleReset}
                className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-semibold transition-colors shadow-xs"
              >
                <RotateCcw className="w-4 h-4" />
                <span>Inspect Another</span>
              </button>
            </div>
          </div>

          {/* Inspection Inspection Visualization */}
          <div className="bg-white rounded-xl border border-slate-200 shadow-xs overflow-hidden">
            <div className="p-4 border-b border-slate-200 flex items-center justify-between bg-slate-50">
              <div className="flex items-center gap-3">
                <span className="text-xs font-bold uppercase tracking-wider text-slate-700">
                  Inspection Optical Visualization
                </span>
                <span className="text-xs text-slate-500 font-mono">
                  Latency: {result.inference_duration_ms.toFixed(1)} ms
                </span>
              </div>
              <div className="inline-flex rounded-lg border border-slate-200 p-0.5 bg-slate-100 text-xs">
                <button
                  onClick={() => setImageTab('annotated')}
                  className={`px-3 py-1 rounded-md font-medium transition-all ${
                    imageTab === 'annotated' ? 'bg-white text-slate-900 shadow-xs' : 'text-slate-600'
                  }`}
                >
                  AI Annotated Heatmap
                </button>
                <button
                  onClick={() => setImageTab('original')}
                  className={`px-3 py-1 rounded-md font-medium transition-all ${
                    imageTab === 'original' ? 'bg-white text-slate-900 shadow-xs' : 'text-slate-600'
                  }`}
                >
                  Original Image
                </button>
              </div>
            </div>

            <div className="p-6 bg-slate-950 flex items-center justify-center min-h-[380px]">
              <img
                src={getImageUrl(
                  imageTab === 'annotated'
                    ? result.annotated_image_url || result.original_image_url
                    : result.original_image_url
                )}
                alt="Inspection Output"
                className="max-h-[440px] w-auto object-contain rounded-lg border border-slate-800"
              />
            </div>
          </div>

          {/* Metric Breakdown Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
              <span className="text-xs font-semibold text-slate-500">Defect Classification</span>
              <div className="mt-2 flex items-center gap-2">
                <DefectTypeBadge defectType={result.defect_type} />
                <span className="text-xs text-slate-600 font-medium">
                  {result.defect_type ? 'Flagged category' : 'No defect category'}
                </span>
              </div>
            </div>

            <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
              <span className="text-xs font-semibold text-slate-500">Confidence Metric</span>
              <div className="mt-1 flex items-baseline gap-2">
                <span className="text-2xl font-black text-slate-900">
                  {result.confidence_score !== null && result.confidence_score !== undefined
                    ? `${(result.confidence_score * 100).toFixed(1)}%`
                    : 'N/A'}
                </span>
                <span className="text-xs text-slate-500">
                  {result.status === 'ACCEPTED' ? 'Surface Integrity' : 'Defect Probability'}
                </span>
              </div>
            </div>

            <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
              <span className="text-xs font-semibold text-slate-500">Model Telemetry</span>
              <div className="mt-1">
                <p className="text-xs font-bold text-slate-800">{result.model_name}</p>
                <p className="text-[11px] font-mono text-slate-500">v{result.model_version} • ResNet-18 Backbone</p>
              </div>
            </div>
          </div>

          {/* Defect Regions Detail */}
          {result.defect_regions && result.defect_regions.length > 0 && (
            <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs">
              <div className="flex items-center gap-2 mb-3">
                <Layers className="w-4 h-4 text-blue-600" />
                <h3 className="text-xs font-bold uppercase tracking-wider text-slate-700">
                  Localized Defect Bounding Boxes ({result.defect_regions.length})
                </h3>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                {result.defect_regions.map((reg, idx) => (
                  <div
                    key={idx}
                    className="p-3 rounded-lg border border-slate-200 bg-slate-50 text-xs space-y-1"
                  >
                    <div className="flex justify-between items-center font-bold">
                      <span className="text-red-600">Region #{idx + 1}</span>
                      <span className="text-slate-800">{reg.label}</span>
                    </div>
                    <div className="text-slate-500 font-mono text-[11px]">
                      Bounding Box: [{reg.x}, {reg.y}, {reg.width}, {reg.height}]
                    </div>
                    <div className="text-slate-600">
                      Confidence: <span className="font-semibold text-slate-800">{(reg.confidence * 100).toFixed(1)}%</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      ) : (
        /* Inspection Upload Form */
        <div className="space-y-6">
          <form onSubmit={handleSubmit} className="bg-white p-6 rounded-xl border border-slate-200 shadow-xs space-y-6">
            <div>
              <h2 className="text-base font-bold text-slate-900">
                Product Image Inspection Upload
              </h2>
              <p className="text-xs text-slate-500 mt-0.5">
                Upload high-resolution manufactured part imagery (JPG, JPEG, PNG, up to 10 MB).
              </p>
            </div>

            {/* Drag & Drop Zone */}
            <div
              onDrop={handleDrop}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onClick={() => fileInputRef.current?.click()}
              className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all ${
                isDragging
                  ? 'border-blue-500 bg-blue-50/50'
                  : previewUrl
                  ? 'border-slate-300 bg-slate-50'
                  : 'border-slate-300 hover:border-blue-400 hover:bg-slate-50/50'
              }`}
            >
              <input
                ref={fileInputRef}
                type="file"
                accept="image/jpeg,image/png,image/jpg"
                className="hidden"
                onChange={(e) => {
                  if (e.target.files && e.target.files.length > 0) {
                    handleFileChange(e.target.files[0]);
                  }
                }}
              />

              {previewUrl ? (
                <div className="space-y-4">
                  <div className="relative inline-block max-h-64 rounded-lg overflow-hidden border border-slate-300 shadow-sm">
                    <img
                      src={previewUrl}
                      alt="Upload Preview"
                      className="max-h-64 w-auto object-contain bg-white"
                    />
                  </div>
                  <div className="text-xs text-slate-600 font-medium">
                    <span className="font-bold text-slate-800">{selectedFile?.name}</span>
                    <span className="mx-2">•</span>
                    <span>{((selectedFile?.size || 0) / (1024 * 1024)).toFixed(2)} MB</span>
                  </div>
                  <p className="text-[11px] text-blue-600 font-semibold">
                    Click or drop another image to replace
                  </p>
                </div>
              ) : (
                <div className="space-y-3">
                  <div className="w-14 h-14 bg-blue-50 text-blue-600 rounded-full flex items-center justify-center mx-auto shadow-xs">
                    <UploadCloud className="w-7 h-7" />
                  </div>
                  <div>
                    <p className="text-sm font-semibold text-slate-800">
                      Drag and drop your product image here, or{' '}
                      <span className="text-blue-600 underline">browse</span>
                    </p>
                    <p className="text-xs text-slate-400 mt-1">
                      Supports JPG, JPEG, and PNG up to 10 MB
                    </p>
                  </div>
                </div>
              )}
            </div>

            {/* Error Message */}
            {error && (
              <div className="p-3.5 bg-red-50 border border-red-200 rounded-lg text-xs text-red-700 flex items-center gap-2">
                <XCircle className="w-4 h-4 flex-shrink-0" />
                <span>{error}</span>
              </div>
            )}

            {/* Metadata Inputs */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1.5">
                  Batch or Product Serial ID (Optional)
                </label>
                <input
                  type="text"
                  value={productId}
                  onChange={(e) => setProductId(e.target.value)}
                  placeholder="e.g. LOT-2026-X891"
                  className="w-full px-3.5 py-2 border border-slate-300 rounded-lg text-xs focus:ring-2 focus:ring-blue-500 focus:outline-hidden"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1.5">
                  Inspection Notes / Line Identifier (Optional)
                </label>
                <input
                  type="text"
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  placeholder="e.g. Assembly Station 4 - High-stress surface check"
                  className="w-full px-3.5 py-2 border border-slate-300 rounded-lg text-xs focus:ring-2 focus:ring-blue-500 focus:outline-hidden"
                />
              </div>
            </div>

            {/* Submit Action */}
            <div className="pt-2 flex items-center justify-between border-t border-slate-200">
              <button
                type="button"
                onClick={handleReset}
                disabled={!selectedFile || isSubmitting}
                className="px-4 py-2 text-xs font-medium text-slate-600 hover:text-slate-800 hover:bg-slate-100 rounded-lg transition-colors disabled:opacity-40"
              >
                Clear
              </button>

              <button
                type="submit"
                disabled={!selectedFile || isSubmitting}
                className="flex items-center gap-2 px-6 py-2.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-bold shadow-md shadow-blue-500/20 transition-all active:scale-95 disabled:opacity-50"
              >
                {isSubmitting ? (
                  <>
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    <span>Executing AI Inference...</span>
                  </>
                ) : (
                  <>
                    <ScanEye className="w-4 h-4" />
                    <span>Run AI Defect Inspection</span>
                  </>
                )}
              </button>
            </div>
          </form>

          {/* Quick Demo Samples Picker */}
          <div className="bg-slate-50 p-5 rounded-xl border border-slate-200">
            <div className="flex items-center gap-2 mb-2">
              <Sparkles className="w-4 h-4 text-blue-600" />
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-700">
                Instant Test Fixtures (Pre-generated Industrial Parts)
              </h3>
            </div>
            <p className="text-xs text-slate-500 mb-3">
              Click any of the preloaded synthetic test components below to test the AI inspection pipeline immediately:
            </p>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              <button
                type="button"
                onClick={() => handleLoadSample('sample_surface_scratch.png', 'Scratch')}
                className="p-3 bg-white border border-slate-200 hover:border-blue-400 rounded-lg text-left text-xs transition-all shadow-2xs hover:shadow-xs group"
              >
                <span className="font-bold text-slate-800 block group-hover:text-blue-600">Scratch Sample</span>
                <span className="text-[11px] text-slate-500">Linear surface fissure</span>
              </button>

              <button
                type="button"
                onClick={() => handleLoadSample('sample_metal_crack.png', 'Crack')}
                className="p-3 bg-white border border-slate-200 hover:border-blue-400 rounded-lg text-left text-xs transition-all shadow-2xs hover:shadow-xs group"
              >
                <span className="font-bold text-slate-800 block group-hover:text-blue-600">Crack Sample</span>
                <span className="text-[11px] text-slate-500">Structural fatigue crack</span>
              </button>

              <button
                type="button"
                onClick={() => handleLoadSample('sample_stamped_dent.png', 'Dent')}
                className="p-3 bg-white border border-slate-200 hover:border-blue-400 rounded-lg text-left text-xs transition-all shadow-2xs hover:shadow-xs group"
              >
                <span className="font-bold text-slate-800 block group-hover:text-blue-600">Dent Sample</span>
                <span className="text-[11px] text-slate-500">Depressed contour flaw</span>
              </button>

              <button
                type="button"
                onClick={() => handleLoadSample('sample_pristine_bracket.png', 'Pristine')}
                className="p-3 bg-white border border-slate-200 hover:border-emerald-400 rounded-lg text-left text-xs transition-all shadow-2xs hover:shadow-xs group"
              >
                <span className="font-bold text-emerald-700 block group-hover:text-emerald-800">Pristine Part</span>
                <span className="text-[11px] text-slate-500">Zero surface defects</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
