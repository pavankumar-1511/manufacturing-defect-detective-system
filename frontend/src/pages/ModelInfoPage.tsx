import React, { useEffect, useState } from 'react';
import {
  Cpu,
  ShieldCheck,
  CheckCircle,
  Activity,
  Layers,
  Sparkles,
  Zap,
  Sliders,
  CheckCircle2,
  AlertTriangle,
  RotateCw,
} from 'lucide-react';
import { ModelStatus } from '../types';
import { getModelStatus } from '../services/api';

export const ModelInfoPage: React.FC = () => {
  const [modelStatus, setModelStatus] = useState<ModelStatus | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchStatus = async () => {
    try {
      setLoading(true);
      const res = await getModelStatus();
      setModelStatus(res);
    } catch (err) {
      console.error('Failed to load model status:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStatus();
  }, []);

  const defectClasses = [
    {
      title: 'Scratches',
      type: 'Linear / Shear Deformations',
      description: 'Elongated, thin fissures caused by mechanical abrasion, tool scoring, or handling slippage.',
      threshold: 'Aspect ratio > 3.0, high directional gradient',
      badge: 'bg-rose-50 text-rose-700 border-rose-200',
    },
    {
      title: 'Cracks',
      type: 'Structural Discontinuities',
      description: 'Jagged, branched hairline fractures stemming from casting thermal shock or mechanical fatigue.',
      threshold: 'High frequency perimeter irregularity, low circularity (<0.25)',
      badge: 'bg-red-50 text-red-800 border-red-200',
    },
    {
      title: 'Dents',
      type: 'Plastic Surface Depressions',
      description: 'Localized indentations from impact or die imperfections, altering planar specular reflections.',
      threshold: 'Circular depressions, concentric gradient dip',
      badge: 'bg-amber-50 text-amber-800 border-amber-200',
    },
    {
      title: 'Surface Abnormalities',
      type: 'Texture / Porosity Variations',
      description: 'Discoloration, oxidation patches, pitting, or roughness exceeding surface tolerance.',
      threshold: 'Deep feature texture entropy, intensity variance',
      badge: 'bg-orange-50 text-orange-800 border-orange-200',
    },
  ];

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      {/* Top Architecture Card */}
      <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-xs space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-100">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 bg-blue-600 rounded-xl flex items-center justify-center text-white shadow-md shadow-blue-500/20">
              <Cpu className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-base font-bold text-slate-900">
                  {modelStatus?.name || 'PatchAnomaly-ResNet-CV'}
                </h2>
                <span className="font-mono text-xs px-2 py-0.5 bg-blue-100 text-blue-700 rounded-md font-semibold">
                  v{modelStatus?.version || '2.1.0'}
                </span>
                <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
                  <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                  {modelStatus?.status || 'ONLINE'}
                </span>
              </div>
              <p className="text-xs text-slate-500 mt-0.5">
                {modelStatus?.details || 'PyTorch ResNet-18 Deep Feature Extractor + OpenCV Multi-Scale Anomaly Segmenter'}
              </p>
            </div>
          </div>

          <button
            onClick={fetchStatus}
            disabled={loading}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg text-xs font-semibold transition-colors disabled:opacity-50"
          >
            <RotateCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            <span>Refresh Telemetry</span>
          </button>
        </div>

        {/* Runtime Statistics Grid */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs">
          <div className="p-3 bg-slate-50 rounded-lg border border-slate-200">
            <span className="text-slate-500 font-medium block">Hardware Target</span>
            <span className="font-mono font-bold text-slate-900 text-sm uppercase">
              {modelStatus?.device || 'CPU'}
            </span>
            <span className="text-[10px] text-slate-400 block mt-0.5">Optimized Torch Execution</span>
          </div>

          <div className="p-3 bg-slate-50 rounded-lg border border-slate-200">
            <span className="text-slate-500 font-medium block">Total Inferences Run</span>
            <span className="font-mono font-bold text-slate-900 text-sm">
              {modelStatus?.total_inferences ?? 0}
            </span>
            <span className="text-[10px] text-slate-400 block mt-0.5">Lifetime processed parts</span>
          </div>

          <div className="p-3 bg-slate-50 rounded-lg border border-slate-200">
            <span className="text-slate-500 font-medium block">Defect Threshold</span>
            <span className="font-mono font-bold text-slate-900 text-sm">
              {modelStatus?.defect_confidence_threshold ?? 0.50}
            </span>
            <span className="text-[10px] text-slate-400 block mt-0.5">Decision boundary floor</span>
          </div>

          <div className="p-3 bg-slate-50 rounded-lg border border-slate-200">
            <span className="text-slate-500 font-medium block">System Uptime</span>
            <span className="font-mono font-bold text-slate-900 text-sm">
              {modelStatus?.uptime_seconds ? `${(modelStatus.uptime_seconds / 60).toFixed(0)} min` : '< 1 min'}
            </span>
            <span className="text-[10px] text-slate-400 block mt-0.5">Continuous runtime</span>
          </div>
        </div>
      </div>

      {/* Inference Pipeline Explanation */}
      <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-xs space-y-4">
        <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
          <Layers className="w-4 h-4 text-blue-600" />
          <span>Industrial Vision Pipeline Architecture</span>
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
          <div className="p-4 bg-slate-50 rounded-lg border border-slate-200 space-y-2">
            <div className="flex items-center gap-2 font-bold text-slate-800">
              <span className="w-5 h-5 rounded-full bg-blue-600 text-white flex items-center justify-center text-[10px]">
                1
              </span>
              <span>Deep Feature Extraction</span>
            </div>
            <p className="text-slate-600">
              PyTorch ResNet-18 intermediate conv layer embeddings extract spatial texture distributions across manufacturing surfaces, capturing micro-texture deviations.
            </p>
          </div>

          <div className="p-4 bg-slate-50 rounded-lg border border-slate-200 space-y-2">
            <div className="flex items-center gap-2 font-bold text-slate-800">
              <span className="w-5 h-5 rounded-full bg-blue-600 text-white flex items-center justify-center text-[10px]">
                2
              </span>
              <span>Morphological Localization</span>
            </div>
            <p className="text-slate-600">
              OpenCV multi-directional Sobel gradients, Top-Hat/Black-Hat transforms, and morphological closing isolate contiguous anomaly contours with sub-millimeter precision.
            </p>
          </div>

          <div className="p-4 bg-slate-50 rounded-lg border border-slate-200 space-y-2">
            <div className="flex items-center gap-2 font-bold text-slate-800">
              <span className="w-5 h-5 rounded-full bg-blue-600 text-white flex items-center justify-center text-[10px]">
                3
              </span>
              <span>Calibration & Bounding Box</span>
            </div>
            <p className="text-slate-600">
              Geometric contour metrics (aspect ratio, circularity, extent) classify defect category. Color-coded bounding boxes and heatmaps are overlaid onto the inspection output.
            </p>
          </div>
        </div>
      </div>

      {/* Supported Defect Categories */}
      <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-xs space-y-4">
        <div>
          <h3 className="text-sm font-bold text-slate-900">
            Supported Defect Classifications
          </h3>
          <p className="text-xs text-slate-500 mt-0.5">
            Model taxonomy calibrated for structural and cosmetic manufacturing flaws
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {defectClasses.map((item) => (
            <div key={item.title} className="p-4 rounded-lg border border-slate-200 bg-slate-50/50 space-y-2">
              <div className="flex items-center justify-between">
                <span className="font-bold text-slate-900 text-sm">{item.title}</span>
                <span className={`px-2 py-0.5 rounded text-[11px] font-semibold border ${item.badge}`}>
                  {item.type}
                </span>
              </div>
              <p className="text-xs text-slate-600 leading-relaxed">{item.description}</p>
              <div className="pt-2 border-t border-slate-200/60 text-[11px] font-mono text-slate-500">
                <span className="font-semibold text-slate-700">Heuristic: </span>
                {item.threshold}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
