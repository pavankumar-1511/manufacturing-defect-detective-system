import axios from 'axios';
import {
  DashboardStats,
  DefectDistributionItem,
  Inspection,
  InspectionReport,
  ModelStatus,
  PaginatedInspections,
  TrendPoint
} from '../types';

const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
});

export const getHealth = async () => {
  const res = await api.get('/health');
  return res.data;
};

export const getDashboardStats = async (): Promise<DashboardStats> => {
  const res = await api.get<DashboardStats>('/dashboard/stats');
  return res.data;
};

export const getDashboardTrends = async (days: number = 7): Promise<TrendPoint[]> => {
  const res = await api.get<TrendPoint[]>(`/dashboard/trends?days=${days}`);
  return res.data;
};

export const getDefectDistribution = async (): Promise<DefectDistributionItem[]> => {
  const res = await api.get<DefectDistributionItem[]>('/dashboard/defect-distribution');
  return res.data;
};

export const createInspection = async (
  file: File,
  productId?: string,
  notes?: string
): Promise<Inspection> => {
  const formData = new FormData();
  formData.append('file', file);
  if (productId) {
    formData.append('product_id', productId);
  }
  if (notes) {
    formData.append('notes', notes);
  }

  const res = await api.post<Inspection>('/inspections', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return res.data;
};

export const getInspections = async (params: {
  search?: string;
  status?: string;
  defect_type?: string;
  date_from?: string;
  date_to?: string;
  page?: number;
  page_size?: number;
}): Promise<PaginatedInspections> => {
  const res = await api.get<PaginatedInspections>('/inspections', { params });
  return res.data;
};

export const getInspectionById = async (id: string): Promise<Inspection> => {
  const res = await api.get<Inspection>(`/inspections/${id}`);
  return res.data;
};

export const deleteInspection = async (id: string): Promise<{ message: string; id: string }> => {
  const res = await api.delete(`/inspections/${id}`);
  return res.data;
};

export const getInspectionReport = async (id: string): Promise<InspectionReport> => {
  const res = await api.get<InspectionReport>(`/inspections/${id}/report`);
  return res.data;
};

export const getModelStatus = async (): Promise<ModelStatus> => {
  const res = await api.get<ModelStatus>('/models/status');
  return res.data;
};

export const updateThresholds = async (
  defectThreshold: number,
  reviewThreshold: number
): Promise<any> => {
  const res = await api.post(
    `/models/thresholds?defect_threshold=${defectThreshold}&review_threshold=${reviewThreshold}`
  );
  return res.data;
};

export const getExportCsvUrl = (filters?: {
  search?: string;
  status?: string;
  defect_type?: string;
  date_from?: string;
  date_to?: string;
}): string => {
  const query = new URLSearchParams();
  query.append('export_csv', 'true');
  if (filters?.search) query.append('search', filters.search);
  if (filters?.status && filters.status !== 'ALL') query.append('status', filters.status);
  if (filters?.defect_type && filters.defect_type !== 'ALL') query.append('defect_type', filters.defect_type);
  if (filters?.date_from) query.append('date_from', filters.date_from);
  if (filters?.date_to) query.append('date_to', filters.date_to);
  return `/api/inspections?${query.toString()}`;
};

export default api;
