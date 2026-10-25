import React, { useEffect, useState } from 'react';
import {
  BarChart3,
  TrendingUp,
  Percent,
  Calendar,
  Layers,
  CheckCircle2,
  XCircle,
  AlertTriangle,
} from 'lucide-react';
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Legend,
  PieChart,
  Pie,
  Cell,
} from 'recharts';
import { DashboardStats, DefectDistributionItem, TrendPoint } from '../types';
import { getDashboardStats, getDashboardTrends, getDefectDistribution } from '../services/api';

const DEFECT_COLORS: Record<string, string> = {
  Scratches: '#f43f5e',
  Cracks: '#dc2626',
  Dents: '#f59e0b',
  'Surface Abnormalities': '#ea580c',
};

export const AnalyticsPage: React.FC = () => {
  const [days, setDays] = useState(14);
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [trends, setTrends] = useState<TrendPoint[]>([]);
  const [distribution, setDistribution] = useState<DefectDistributionItem[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchAnalytics = async () => {
    try {
      setLoading(true);
      const [statsData, trendsData, distData] = await Promise.all([
        getDashboardStats(),
        getDashboardTrends(days),
        getDefectDistribution(),
      ]);
      setStats(statsData);
      setTrends(trendsData);
      setDistribution(distData);
    } catch (err) {
      console.error('Analytics load error:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAnalytics();
  }, [days]);

  return (
    <div className="space-y-6">
      {/* Top Filter Bar */}
      <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Calendar className="w-4 h-4 text-blue-600" />
          <span className="text-xs font-bold uppercase tracking-wider text-slate-700">
            Time Range Window:
          </span>
        </div>

        <div className="inline-flex rounded-lg border border-slate-200 p-0.5 bg-slate-100 text-xs">
          {[7, 14, 30].map((d) => (
            <button
              key={d}
              onClick={() => setDays(d)}
              className={`px-3 py-1 rounded-md font-medium transition-all ${
                days === d
                  ? 'bg-white text-slate-900 shadow-xs'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              Last {d} Days
            </button>
          ))}
        </div>
      </div>

      {/* High-Level Yield KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center flex-shrink-0">
            <CheckCircle2 className="w-6 h-6" />
          </div>
          <div>
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
              Overall First-Pass Yield
            </span>
            <div className="text-2xl font-black text-emerald-700 mt-0.5">
              {stats?.total_inspections
                ? ((stats.accepted_count / stats.total_inspections) * 100).toFixed(1)
                : '100.0'}%
            </div>
            <p className="text-[11px] text-slate-400">Total units meeting standard tolerance</p>
          </div>
        </div>

        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-red-50 text-red-600 flex items-center justify-center flex-shrink-0">
            <XCircle className="w-6 h-6" />
          </div>
          <div>
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
              System Scrap Rate
            </span>
            <div className="text-2xl font-black text-red-600 mt-0.5">
              {stats?.defect_percentage ?? 0}%
            </div>
            <p className="text-[11px] text-slate-400">Defective parts rejected by AI vision</p>
          </div>
        </div>

        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-amber-50 text-amber-600 flex items-center justify-center flex-shrink-0">
            <AlertTriangle className="w-6 h-6" />
          </div>
          <div>
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
              Manual QA Review Flag Rate
            </span>
            <div className="text-2xl font-black text-amber-600 mt-0.5">
              {stats?.manual_review_percentage ?? 0}%
            </div>
            <p className="text-[11px] text-slate-400">Boundary cases requiring supervisor sign-off</p>
          </div>
        </div>
      </div>

      {/* Main Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Inspection Volume Trend by Verdict */}
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs">
          <h3 className="text-sm font-bold text-slate-900 mb-1">
            Inspection Throughput by Verdict
          </h3>
          <p className="text-xs text-slate-500 mb-4">
            Daily distribution of accepted, defective, and review-required parts
          </p>

          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={trends} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />
                <XAxis dataKey="date" tick={{ fontSize: 10, fill: '#64748b' }} tickLine={false} />
                <YAxis tick={{ fontSize: 10, fill: '#64748b' }} tickLine={false} allowDecimals={false} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', color: '#fff', fontSize: '12px' }}
                />
                <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '8px' }} />
                <Bar dataKey="accepted" name="Accepted" fill="#10b981" radius={[3, 3, 0, 0]} />
                <Bar dataKey="defective" name="Defective" fill="#ef4444" radius={[3, 3, 0, 0]} />
                <Bar dataKey="review" name="Review Required" fill="#f59e0b" radius={[3, 3, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Defect Category Breakdown */}
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs">
          <h3 className="text-sm font-bold text-slate-900 mb-1">
            Defect Category Breakdown
          </h3>
          <p className="text-xs text-slate-500 mb-4">
            Proportion of scrap attributable to each defect mechanism
          </p>

          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={distribution}
                  dataKey="count"
                  nameKey="category"
                  cx="50%"
                  cy="50%"
                  outerRadius={85}
                  label={({ name, percent }: any) => `${name}: ${(((percent || 0) as number) * 100).toFixed(0)}%`}
                  labelLine={false}
                >
                  {distribution.map((entry, index) => (
                    <Cell
                      key={`cell-${index}`}
                      fill={DEFECT_COLORS[entry.category] || '#94a3b8'}
                    />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', color: '#fff', fontSize: '12px' }}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Cumulative Defect Rate Curve */}
      <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs">
        <h3 className="text-sm font-bold text-slate-900 mb-1">
          Defect Rate Fluctuation
        </h3>
        <p className="text-xs text-slate-500 mb-4">
          Daily percentage of parts flagged as defective or requiring review
        </p>

        <div className="h-56 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart
              data={trends.map((t) => ({
                date: t.date,
                defect_pct: t.total > 0 ? Number(((t.defective / t.total) * 100).toFixed(1)) : 0,
              }))}
              margin={{ top: 10, right: 10, left: -20, bottom: 0 }}
            >
              <defs>
                <linearGradient id="colorDefectRate" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#f43f5e" stopOpacity={0.4} />
                  <stop offset="95%" stopColor="#f43f5e" stopOpacity={0.0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />
              <XAxis dataKey="date" tick={{ fontSize: 10, fill: '#64748b' }} tickLine={false} />
              <YAxis unit="%" tick={{ fontSize: 10, fill: '#64748b' }} tickLine={false} />
              <Tooltip
                contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', color: '#fff', fontSize: '12px' }}
              />
              <Area
                type="monotone"
                dataKey="defect_pct"
                name="Defect Rate %"
                stroke="#f43f5e"
                strokeWidth={2}
                fillOpacity={1}
                fill="url(#colorDefectRate)"
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
};
