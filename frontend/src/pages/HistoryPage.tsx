import React, { useEffect, useState } from 'react';
import {
  Search,
  Filter,
  Download,
  RotateCcw,
  ChevronLeft,
  ChevronRight,
  Printer,
  Trash2,
  ExternalLink,
  Layers,
} from 'lucide-react';
import { Inspection, PaginatedInspections } from '../types';
import { getInspections, deleteInspection, getExportCsvUrl, getImageUrl } from '../services/api';
import { StatusBadge, DefectTypeBadge } from '../components/common/StatusBadge';

interface HistoryPageProps {
  onSelectInspection: (inspection: Inspection) => void;
  onOpenReport: (inspection: Inspection) => void;
}

export const HistoryPage: React.FC<HistoryPageProps> = ({
  onSelectInspection,
  onOpenReport,
}) => {
  const [data, setData] = useState<PaginatedInspections | null>(null);
  const [loading, setLoading] = useState(false);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [defectFilter, setDefectFilter] = useState('ALL');
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);

  const fetchHistory = async () => {
    try {
      setLoading(true);
      const res = await getInspections({
        search: search.trim() || undefined,
        status: statusFilter !== 'ALL' ? statusFilter : undefined,
        defect_type: defectFilter !== 'ALL' ? defectFilter : undefined,
        date_from: dateFrom || undefined,
        date_to: dateTo || undefined,
        page,
        page_size: pageSize,
      });
      setData(res);
    } catch (err) {
      console.error('Failed to load inspection history:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHistory();
  }, [page, pageSize, statusFilter, defectFilter]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    fetchHistory();
  };

  const handleClearFilters = () => {
    setSearch('');
    setStatusFilter('ALL');
    setDefectFilter('ALL');
    setDateFrom('');
    setDateTo('');
    setPage(1);
    // Directly fetch with clean state
    getInspections({ page: 1, page_size: pageSize }).then((res) => setData(res));
  };

  const handleDelete = async (id: string) => {
    if (window.confirm('Are you sure you want to delete this inspection record?')) {
      try {
        await deleteInspection(id);
        fetchHistory();
      } catch (err) {
        console.error('Delete failed:', err);
      }
    }
  };

  const handleExportCsv = () => {
    const url = getExportCsvUrl({
      search: search.trim() || undefined,
      status: statusFilter,
      defect_type: defectFilter,
      date_from: dateFrom || undefined,
      date_to: dateTo || undefined,
    });
    window.open(url, '_blank');
  };

  return (
    <div className="space-y-6">
      {/* Search and Filters Header */}
      <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs space-y-4">
        <form onSubmit={handleSearchSubmit} className="flex flex-col md:flex-row items-center gap-3">
          <div className="relative flex-1 w-full">
            <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search by product / batch ID, filename, or notes..."
              className="w-full pl-9 pr-4 py-2 border border-slate-300 rounded-lg text-xs focus:ring-2 focus:ring-blue-500 focus:outline-hidden"
            />
          </div>

          <div className="flex items-center gap-2 w-full md:w-auto">
            <button
              type="submit"
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-semibold shadow-xs transition-colors"
            >
              Search
            </button>
            <button
              type="button"
              onClick={handleExportCsv}
              className="flex items-center gap-1.5 px-3.5 py-2 bg-white border border-slate-300 hover:bg-slate-50 text-slate-700 rounded-lg text-xs font-semibold shadow-xs transition-colors"
            >
              <Download className="w-3.5 h-3.5 text-slate-500" />
              <span>Export CSV</span>
            </button>
          </div>
        </form>

        {/* Filter Controls */}
        <div className="pt-3 border-t border-slate-100 flex flex-wrap items-center justify-between gap-3 text-xs">
          <div className="flex flex-wrap items-center gap-3">
            <div className="flex items-center gap-1.5">
              <span className="text-slate-500 font-medium">Status:</span>
              <select
                value={statusFilter}
                onChange={(e) => {
                  setStatusFilter(e.target.value);
                  setPage(1);
                }}
                className="px-2.5 py-1.5 bg-slate-50 border border-slate-300 rounded-md font-medium text-slate-700 focus:outline-hidden focus:ring-1 focus:ring-blue-500"
              >
                <option value="ALL">All Verdicts</option>
                <option value="ACCEPTED">ACCEPTED</option>
                <option value="DEFECTIVE">DEFECTIVE</option>
                <option value="REVIEW_REQUIRED">REVIEW REQUIRED</option>
              </select>
            </div>

            <div className="flex items-center gap-1.5">
              <span className="text-slate-500 font-medium">Defect Class:</span>
              <select
                value={defectFilter}
                onChange={(e) => {
                  setDefectFilter(e.target.value);
                  setPage(1);
                }}
                className="px-2.5 py-1.5 bg-slate-50 border border-slate-300 rounded-md font-medium text-slate-700 focus:outline-hidden focus:ring-1 focus:ring-blue-500"
              >
                <option value="ALL">All Classes</option>
                <option value="Scratches">Scratches</option>
                <option value="Cracks">Cracks</option>
                <option value="Dents">Dents</option>
                <option value="Surface Abnormalities">Surface Abnormalities</option>
              </select>
            </div>

            <div className="flex items-center gap-1.5">
              <span className="text-slate-500 font-medium">Date Range:</span>
              <input
                type="date"
                value={dateFrom}
                onChange={(e) => setDateFrom(e.target.value)}
                className="px-2 py-1 bg-slate-50 border border-slate-300 rounded-md text-[11px]"
              />
              <span className="text-slate-400">to</span>
              <input
                type="date"
                value={dateTo}
                onChange={(e) => setDateTo(e.target.value)}
                className="px-2 py-1 bg-slate-50 border border-slate-300 rounded-md text-[11px]"
              />
              <button
                type="button"
                onClick={fetchHistory}
                className="px-2 py-1 bg-slate-200 hover:bg-slate-300 text-slate-700 rounded-md font-medium text-[11px]"
              >
                Apply
              </button>
            </div>
          </div>

          <button
            onClick={handleClearFilters}
            className="flex items-center gap-1 text-slate-500 hover:text-slate-800 transition-colors"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span>Reset Filters</span>
          </button>
        </div>
      </div>

      {/* History Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-xs overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-xs text-left">
            <thead className="bg-slate-50 text-slate-600 font-semibold border-b border-slate-200 uppercase tracking-wider text-[11px]">
              <tr>
                <th className="py-3 px-4">Thumbnail</th>
                <th className="py-3 px-4">Inspection ID</th>
                <th className="py-3 px-4">Batch / Product</th>
                <th className="py-3 px-4">AI Verdict</th>
                <th className="py-3 px-4">Defect Class</th>
                <th className="py-3 px-4">Confidence</th>
                <th className="py-3 px-4">Latency</th>
                <th className="py-3 px-4">Timestamp</th>
                <th className="py-3 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {loading ? (
                <tr>
                  <td colSpan={9} className="py-12 text-center text-slate-500">
                    <div className="inline-block w-6 h-6 border-2 border-blue-600 border-t-transparent rounded-full animate-spin mb-2" />
                    <p>Loading inspection audit records...</p>
                  </td>
                </tr>
              ) : !data || data.items.length === 0 ? (
                <tr>
                  <td colSpan={9} className="py-12 text-center text-slate-500">
                    No inspections match the specified filters.
                  </td>
                </tr>
              ) : (
                data.items.map((item) => (
                  <tr key={item.id} className="hover:bg-slate-50/80 transition-colors">
                    <td className="py-2.5 px-4">
                      <div className="w-10 h-10 rounded-md bg-slate-100 overflow-hidden border border-slate-200 flex-shrink-0">
                        <img
                          src={getImageUrl(item.annotated_image_url || item.original_image_url)}
                          alt={item.original_filename}
                          className="w-full h-full object-cover"
                        />
                      </div>
                    </td>
                    <td className="py-2.5 px-4 font-mono text-slate-500 text-[11px]">
                      {item.id.slice(0, 8)}...
                    </td>
                    <td className="py-2.5 px-4 font-mono font-medium text-slate-800">
                      {item.product_id || 'N/A'}
                    </td>
                    <td className="py-2.5 px-4">
                      <StatusBadge status={item.status} size="sm" />
                    </td>
                    <td className="py-2.5 px-4">
                      <DefectTypeBadge defectType={item.defect_type} />
                    </td>
                    <td className="py-2.5 px-4 font-semibold text-slate-800">
                      {item.confidence_score !== null && item.confidence_score !== undefined
                        ? `${(item.confidence_score * 100).toFixed(0)}%`
                        : 'N/A'}
                    </td>
                    <td className="py-2.5 px-4 font-mono text-slate-500">
                      {item.inference_duration_ms.toFixed(0)} ms
                    </td>
                    <td className="py-2.5 px-4 text-slate-500 whitespace-nowrap">
                      {new Date(item.created_at).toLocaleDateString()}{' '}
                      <span className="text-[10px] text-slate-400">
                        {new Date(item.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </span>
                    </td>
                    <td className="py-2.5 px-4 text-right">
                      <div className="flex items-center justify-end gap-1.5">
                        <button
                          onClick={() => onSelectInspection(item)}
                          className="px-2 py-1 text-xs font-semibold text-blue-600 hover:text-blue-800 hover:bg-blue-50 rounded-md transition-colors"
                        >
                          View
                        </button>
                        <button
                          onClick={() => onOpenReport(item)}
                          title="Print Official Certificate"
                          className="p-1 text-slate-500 hover:text-slate-800 hover:bg-slate-100 rounded-md transition-colors"
                        >
                          <Printer className="w-3.5 h-3.5" />
                        </button>
                        <button
                          onClick={() => handleDelete(item.id)}
                          title="Delete Inspection Record"
                          className="p-1 text-slate-400 hover:text-red-600 hover:bg-red-50 rounded-md transition-colors"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination Bar */}
        {data && data.total > 0 && (
          <div className="px-5 py-3 border-t border-slate-200 bg-slate-50 flex flex-col sm:flex-row items-center justify-between gap-3 text-xs text-slate-600">
            <div>
              Showing <span className="font-semibold text-slate-900">{(page - 1) * pageSize + 1}</span> to{' '}
              <span className="font-semibold text-slate-900">
                {Math.min(page * pageSize, data.total)}
              </span>{' '}
              of <span className="font-semibold text-slate-900">{data.total}</span> records
            </div>

            <div className="flex items-center gap-2">
              <div className="flex items-center gap-1 mr-2">
                <span>Per page:</span>
                <select
                  value={pageSize}
                  onChange={(e) => {
                    setPageSize(Number(e.target.value));
                    setPage(1);
                  }}
                  className="px-2 py-1 bg-white border border-slate-300 rounded-md font-medium text-slate-700 focus:outline-hidden"
                >
                  <option value={10}>10</option>
                  <option value={20}>20</option>
                  <option value={50}>50</option>
                </select>
              </div>

              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page <= 1}
                className="p-1.5 rounded-md border border-slate-300 bg-white hover:bg-slate-50 disabled:opacity-40 transition-colors"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>

              <span className="font-medium text-slate-800">
                Page {page} of {data.total_pages}
              </span>

              <button
                onClick={() => setPage((p) => Math.min(data.total_pages, p + 1))}
                disabled={page >= data.total_pages}
                className="p-1.5 rounded-md border border-slate-300 bg-white hover:bg-slate-50 disabled:opacity-40 transition-colors"
              >
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
