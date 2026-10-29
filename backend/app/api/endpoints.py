import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Any
from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status, Response
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, or_
import cv2

from app.database.session import get_db
from app.database.repo import DatabaseRepository
from app.database.mongodb import is_mongo_enabled
from app.models.inspection import Inspection
from app.schemas.inspection import (
    InspectionResponse,
    PaginatedInspections,
    DashboardStats,
    DefectDistributionItem,
    TrendPoint,
    ModelStatusResponse,
    InspectionReport,
    DefectRegion,
    RootCauseInfo,
    MachineDefectStat,
)
from app.services.storage import validate_image_upload, save_uploaded_image
from app.services.inference.detector import pipeline
from app.services.inference.model_registry import model_registry
from app.services.reporting import generate_inspections_csv
from app.services.root_cause import get_root_cause_analysis
from app.config import settings

logger = logging.getLogger("api_endpoints")
router = APIRouter()

def format_inspection_response(item: Any, base_url: str = "") -> dict:
    regions = []
    if item.defect_regions:
        try:
            regions_data = json.loads(item.defect_regions) if isinstance(item.defect_regions, str) else item.defect_regions
            regions = [DefectRegion(**r) for r in regions_data]
        except Exception:
            regions = []

    rca = get_root_cause_analysis(item.defect_type, item.status)

    return {
        "id": item.id,
        "original_filename": item.original_filename,
        "stored_filename": item.stored_filename,
        "annotated_filename": item.annotated_filename,
        "product_id": item.product_id,
        "status": item.status,
        "defect_type": item.defect_type,
        "confidence_score": item.confidence_score,
        "severity": rca["severity"],
        "model_name": item.model_name,
        "model_version": item.model_version,
        "inference_duration_ms": item.inference_duration_ms,
        "manual_review_required": item.manual_review_required,
        "inspection_notes": item.inspection_notes,
        "defect_regions": regions,
        "root_cause_analysis": RootCauseInfo(**rca),
        "created_at": item.created_at,
        "original_image_url": f"/api/images/original/{item.stored_filename}",
        "annotated_image_url": f"/api/images/annotated/{item.annotated_filename}" if item.annotated_filename else None,
    }

@router.get("/health", tags=["System"])
def get_health(db: Session = Depends(get_db)):
    """Health check endpoint to verify backend operational readiness."""
    db_ok = DatabaseRepository.is_connected(db)
    return {
        "status": "healthy" if db_ok else "degraded",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "service": settings.PROJECT_NAME,
        "version": settings.MODEL_VERSION,
        "database": "connected" if db_ok else "disconnected",
        "database_type": "MongoDB Atlas" if is_mongo_enabled() else "SQLite",
        "model_engine": "ready" if pipeline.is_configured else "baseline"
    }

@router.get("/dashboard/stats", response_model=DashboardStats, tags=["Dashboard"])
def get_dashboard_stats(db: Session = Depends(get_db)):
    """Computes live inspection metrics from database records."""
    return DatabaseRepository.get_dashboard_stats(db)

@router.get("/dashboard/trends", response_model=List[TrendPoint], tags=["Dashboard"])
def get_inspection_trends(days: int = Query(7, ge=1, le=90), db: Session = Depends(get_db)):
    """Returns inspection volume trends aggregated by day."""
    return DatabaseRepository.get_trends(days=days, db=db)

@router.get("/dashboard/defect-distribution", response_model=List[DefectDistributionItem], tags=["Dashboard"])
def get_defect_distribution(db: Session = Depends(get_db)):
    """Computes defect category distribution for defective & review records."""
    return DatabaseRepository.get_defect_distribution(db)

@router.post("/inspections", response_model=InspectionResponse, status_code=status.HTTP_201_CREATED, tags=["Inspections"])
async def create_inspection(
    file: UploadFile = File(...),
    product_id: Optional[str] = Form(None),
    notes: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """
    Accepts an uploaded manufacturing part image, validates it,
    runs the AI defect inference pipeline, annotates defect regions,
    saves images to disk, and records the inspection in the database.
    """
    content = await file.read()
    orig_name, safe_stored_name = validate_image_upload(file, content)

    # Save original image
    original_path = save_uploaded_image(content, safe_stored_name)

    # Run AI defect detection pipeline
    inference_result = pipeline.inspect_image(
        original_path,
        defect_threshold=model_registry.defect_threshold,
        review_threshold=model_registry.review_threshold
    )

    # Save annotated image if available
    annotated_filename = None
    if "annotated_image_np" in inference_result:
        annotated_filename = f"annotated_{safe_stored_name}"
        annotated_path = settings.ANNOTATED_UPLOAD_DIR / annotated_filename
        cv2.imwrite(str(annotated_path), inference_result["annotated_image_np"])

    # Track inference in registry
    model_registry.record_inference()

    # Format inspection notes with AI vision description if available
    final_notes = notes.strip() if notes else None
    if inference_result.get("ai_description"):
        groq_desc = f"[AI Diagnosis]: {inference_result['ai_description']}"
        final_notes = f"{final_notes} | {groq_desc}" if final_notes else groq_desc

    # Persist via Database Repository (MongoDB Atlas or SQLite)
    import uuid
    inspection_data = {
        "id": str(uuid.uuid4()),
        "original_filename": orig_name,
        "stored_filename": safe_stored_name,
        "annotated_filename": annotated_filename,
        "product_id": product_id.strip() if product_id else None,
        "status": inference_result["status"],
        "defect_type": inference_result["defect_type"],
        "confidence_score": inference_result["confidence_score"],
        "model_name": inference_result["model_name"],
        "model_version": inference_result["model_version"],
        "inference_duration_ms": inference_result["inference_duration_ms"],
        "manual_review_required": inference_result["manual_review_required"],
        "inspection_notes": final_notes,
        "defect_regions": json.dumps(inference_result.get("defect_regions", [])),
        "created_at": datetime.now(timezone.utc)
    }
    db_item = DatabaseRepository.save_inspection(inspection_data, db)
    return format_inspection_response(db_item)

@router.get("/inspections", tags=["Inspections"])
def get_inspections(
    search: Optional[str] = Query(None, description="Search in filename, product_id, or notes"),
    status: Optional[str] = Query(None, description="ACCEPTED, DEFECTIVE, or REVIEW_REQUIRED"),
    defect_type: Optional[str] = Query(None, description="Filter by defect type"),
    date_from: Optional[str] = Query(None, description="Filter from ISO date YYYY-MM-DD"),
    date_to: Optional[str] = Query(None, description="Filter to ISO date YYYY-MM-DD"),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    export_csv: bool = Query(False, description="Set to true to download CSV export"),
    db: Session = Depends(get_db)
):
    """
    Returns paginated inspections with searching, filtering, and optional CSV export.
    """
    if export_csv:
        all_filtered = DatabaseRepository.get_all_for_csv(
            search=search, status=status, defect_type=defect_type,
            date_from=date_from, date_to=date_to, db=db
        )
        csv_data = generate_inspections_csv(all_filtered)
        return PlainTextResponse(
            content=csv_data,
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=inspection_history_export.csv"}
        )

    items, total = DatabaseRepository.get_paginated_inspections(
        search=search, status=status, defect_type=defect_type,
        date_from=date_from, date_to=date_to, page=page, page_size=page_size, db=db
    )
    total_pages = max(1, (total + page_size - 1) // page_size)

    return {
        "items": [format_inspection_response(item) for item in items],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages
    }

@router.get("/inspections/{inspection_id}", response_model=InspectionResponse, tags=["Inspections"])
def get_inspection_by_id(inspection_id: str, db: Session = Depends(get_db)):
    """Fetch a single inspection record by UUID."""
    item = DatabaseRepository.get_inspection_by_id(inspection_id, db)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inspection record not found")
    return format_inspection_response(item)

@router.delete("/inspections/{inspection_id}", status_code=status.HTTP_200_OK, tags=["Inspections"])
def delete_inspection(inspection_id: str, db: Session = Depends(get_db)):
    """Deletes an inspection record and its associated images from disk."""
    item = DatabaseRepository.get_inspection_by_id(inspection_id, db)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inspection record not found")

    # Safely remove associated files
    try:
        orig_path = settings.ORIGINAL_UPLOAD_DIR / item.stored_filename
        if orig_path.exists():
            orig_path.unlink()
        if item.annotated_filename:
            annotated_path = settings.ANNOTATED_UPLOAD_DIR / item.annotated_filename
            if annotated_path.exists():
                annotated_path.unlink()
    except Exception as e:
        logger.warning(f"Error cleaning files for inspection {inspection_id}: {e}")

    DatabaseRepository.delete_inspection(inspection_id, db)
    return {"message": "Inspection record deleted successfully", "id": inspection_id}

@router.get("/inspections/{inspection_id}/report", response_model=InspectionReport, tags=["Inspections"])
def get_inspection_report(inspection_id: str, db: Session = Depends(get_db)):
    """Generates an official industrial quality inspection report."""
    item = DatabaseRepository.get_inspection_by_id(inspection_id, db)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inspection record not found")

    regions = []
    if item.defect_regions:
        try:
            regions_data = json.loads(item.defect_regions) if isinstance(item.defect_regions, str) else item.defect_regions
            regions = [DefectRegion(**r) for r in regions_data]
        except Exception:
            regions = []

    verdict_text = "PASS: Item meets manufacturing tolerance quality standards."
    if item.status == "DEFECTIVE":
        verdict_text = f"FAIL: Defect detected ({item.defect_type or 'Anomaly'}). Rejection / rework required."
    elif item.status == "REVIEW_REQUIRED":
        verdict_text = "HOLD: Boundary anomaly detected. Requires QA engineer physical inspection."

    return InspectionReport(
        inspection_id=item.id,
        product_id=item.product_id,
        status=item.status,
        defect_type=item.defect_type,
        confidence_score=item.confidence_score,
        model_name=item.model_name,
        model_version=item.model_version,
        created_at=item.created_at,
        inference_duration_ms=item.inference_duration_ms,
        manual_review_required=item.manual_review_required,
        inspection_notes=item.inspection_notes,
        defect_regions_count=len(regions),
        defect_regions=regions,
        original_image_url=f"/api/images/original/{item.stored_filename}",
        annotated_image_url=f"/api/images/annotated/{item.annotated_filename}" if item.annotated_filename else None,
        inspector="AI Automated Inspection System",
        quality_verdict=verdict_text
    )

@router.get("/models/status", response_model=ModelStatusResponse, tags=["AI Engine"])
def get_model_status():
    """Returns AI model runtime telemetry and configuration status."""
    return model_registry.get_status()

@router.post("/models/thresholds", tags=["AI Engine"])
def update_thresholds(
    defect_threshold: float = Query(..., ge=0.1, le=0.9),
    review_threshold: float = Query(..., ge=0.2, le=0.99)
):
    """Updates defect and review confidence thresholds dynamically."""
    try:
        model_registry.update_thresholds(defect_threshold, review_threshold)
        return {
            "message": "Thresholds updated successfully",
            "defect_confidence_threshold": model_registry.defect_threshold,
            "review_threshold": model_registry.review_threshold
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
