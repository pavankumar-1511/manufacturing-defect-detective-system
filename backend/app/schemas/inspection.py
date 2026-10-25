from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime

class DefectRegion(BaseModel):
    x: int
    y: int
    width: int
    height: int
    label: str
    confidence: float

class RootCauseInfo(BaseModel):
    severity: str
    category: str
    probable_causes: List[str]
    corrective_actions: List[str]
    inspection_check: str
    verification_badge: str
    disclaimer: str

class InspectionBase(BaseModel):
    product_id: Optional[str] = None
    inspection_notes: Optional[str] = None

class InspectionCreate(InspectionBase):
    pass

class InspectionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    original_filename: str
    stored_filename: str
    annotated_filename: Optional[str] = None
    product_id: Optional[str] = None
    status: str
    defect_type: Optional[str] = None
    confidence_score: Optional[float] = None
    severity: Optional[str] = None
    model_name: str
    model_version: str
    inference_duration_ms: float
    manual_review_required: bool
    inspection_notes: Optional[str] = None
    defect_regions: Optional[List[DefectRegion]] = None
    root_cause_analysis: Optional[RootCauseInfo] = None
    created_at: datetime
    original_image_url: str
    annotated_image_url: Optional[str] = None

class PaginatedInspections(BaseModel):
    items: List[InspectionResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

class DashboardStats(BaseModel):
    total_inspections: int
    accepted_count: int
    defective_count: int
    review_required_count: int
    defect_percentage: float
    manual_review_percentage: float
    avg_inference_time_ms: float

class DefectDistributionItem(BaseModel):
    category: str
    count: int
    percentage: float

class TrendPoint(BaseModel):
    date: str
    total: int
    accepted: int
    defective: int
    review: int

class MachineDefectStat(BaseModel):
    machine_id: str
    machine_name: str
    station_type: str
    total_inspections: int
    passed_count: int
    defective_count: int
    review_count: int
    defect_rate: float
    top_defect: str

class ModelStatusResponse(BaseModel):
    name: str
    version: str
    status: str
    device: str
    supported_defect_types: List[str]
    defect_confidence_threshold: float
    review_threshold: float
    uptime_seconds: float
    total_inferences: int
    model_configured: bool
    details: str

class InspectionReport(BaseModel):
    inspection_id: str
    product_id: Optional[str]
    status: str
    defect_type: Optional[str]
    confidence_score: Optional[float]
    severity: Optional[str] = None
    model_name: str
    model_version: str
    created_at: datetime
    inference_duration_ms: float
    manual_review_required: bool
    inspection_notes: Optional[str]
    defect_regions_count: int
    defect_regions: List[DefectRegion]
    root_cause_analysis: Optional[RootCauseInfo] = None
    original_image_url: str
    annotated_image_url: Optional[str]
    inspector: str
    quality_verdict: str
