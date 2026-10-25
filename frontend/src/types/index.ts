export type InspectionStatus = 'ACCEPTED' | 'DEFECTIVE' | 'REVIEW_REQUIRED';

export type DefectCategory = 
  | 'Scratches'
  | 'Cracks'
  | 'Dents'
  | 'Surface Abnormalities';

export interface DefectRegion {
  x: number;
  y: number;
  width: number;
  height: number;
  label: string;
  confidence: number;
}

export interface Inspection {
  id: string;
  original_filename: string;
  stored_filename: string;
  annotated_filename?: string | null;
  product_id?: string | null;
  status: InspectionStatus;
  defect_type?: string | null;
  confidence_score?: number | null;
  model_name: string;
  model_version: string;
  inference_duration_ms: number;
  manual_review_required: boolean;
  inspection_notes?: string | null;
  defect_regions?: DefectRegion[] | null;
  created_at: string;
  original_image_url: string;
  annotated_image_url?: string | null;
}

export interface PaginatedInspections {
  items: Inspection[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface DashboardStats {
  total_inspections: number;
  accepted_count: number;
  defective_count: number;
  review_required_count: number;
  defect_percentage: number;
  manual_review_percentage: number;
  avg_inference_time_ms: number;
}

export interface DefectDistributionItem {
  category: string;
  count: number;
  percentage: number;
}

export interface TrendPoint {
  date: string;
  total: number;
  accepted: number;
  defective: number;
  review: number;
}

export interface ModelStatus {
  name: string;
  version: string;
  status: string;
  device: string;
  supported_defect_types: string[];
  defect_confidence_threshold: number;
  review_threshold: number;
  uptime_seconds: number;
  total_inferences: number;
  model_configured: boolean;
  details: string;
}

export interface InspectionReport {
  inspection_id: string;
  product_id?: string | null;
  status: InspectionStatus;
  defect_type?: string | null;
  confidence_score?: number | null;
  model_name: string;
  model_version: string;
  created_at: string;
  inference_duration_ms: number;
  manual_review_required: boolean;
  inspection_notes?: string | null;
  defect_regions_count: number;
  defect_regions: DefectRegion[];
  original_image_url: string;
  annotated_image_url?: string | null;
  inspector: string;
  quality_verdict: string;
}
