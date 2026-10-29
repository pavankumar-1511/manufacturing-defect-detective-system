import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, List
from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status, Response
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, or_
import cv2

from app.database.session import get_db
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

def format_inspection_response(item: Inspection, base_url: str = "") -> dict:
    regions = []
    if item.defect_regions:
        try:
            regions_data = json.loads(item.defect_regions)
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
def get_health():
    """Health check endpoint to verify backend operational readiness."""
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "service": settings.PROJECT_NAME,
        "version": settings.MODEL_VERSION,
        "database": "connected",
        "model_engine": "ready" if pipeline.is_configured else "baseline"
    }

@router.get("/dashboard/stats", response_model=DashboardStats, tags=["Dashboard"])
def get_dashboard_stats(db: Session = Depends(get_db)):
    """Computes live inspection metrics from database records."""
    total = db.query(Inspection).count()
    if total == 0:
        return DashboardStats(
            total_inspections=0,
            accepted_count=0,
            defective_count=0,
            review_required_count=0,
            defect_percentage=0.0,
            manual_review_percentage=0.0,
            avg_inference_time_ms=0.0,
        )

    accepted = db.query(Inspection).filter(Inspection.status == "ACCEPTED").count()
    defective = db.query(Inspection).filter(Inspection.status == "DEFECTIVE").count()
    review = db.query(Inspection).filter(Inspection.status == "REVIEW_REQUIRED").count()
    
    avg_duration = db.query(func.avg(Inspection.inference_duration_ms)).scalar() or 0.0

    return DashboardStats(
        total_inspections=total,
        accepted_count=accepted,
        defective_count=defective,
        review_required_count=review,
        defect_percentage=round((defective / total) * 100.0, 1),
        manual_review_percentage=round((review / total) * 100.0, 1),
        avg_inference_time_ms=round(float(avg_duration), 1),
    )

@router.get("/dashboard/trends", response_model=List[TrendPoint], tags=["Dashboard"])
def get_inspection_trends(days: int = Query(7, ge=1, le=90), db: Session = Depends(get_db)):
    """Returns inspection volume trends aggregated by day."""
    start_date = datetime.now(timezone.utc) - timedelta(days=days - 1)
    
    # Query inspections in window
    records = (
        db.query(Inspection)
        .filter(Inspection.created_at >= start_date)
        .order_by(Inspection.created_at.asc())
        .all()
    )

    # Group by date string YYYY-MM-DD
    trend_map = {}
    for i in range(days):
        d = (start_date + timedelta(days=i)).strftime("%Y-%m-%d")
        trend_map[d] = {"date": d, "total": 0, "accepted": 0, "defective": 0, "review": 0}

    for item in records:
        d_str = item.created_at.strftime("%Y-%m-%d")
        if d_str in trend_map:
            trend_map[d_str]["total"] += 1
            if item.status == "ACCEPTED":
                trend_map[d_str]["accepted"] += 1
            elif item.status == "DEFECTIVE":
                trend_map[d_str]["defective"] += 1
            elif item.status == "REVIEW_REQUIRED":
                trend_map[d_str]["review"] += 1

    return [TrendPoint(**v) for v in trend_map.values()]

@router.get("/dashboard/defect-distribution", response_model=List[DefectDistributionItem], tags=["Dashboard"])
def get_defect_distribution(db: Session = Depends(get_db)):
    """Computes defect category distribution for defective & review records."""
    total_defects = db.query(Inspection).filter(Inspection.defect_type.isnot(None)).count()
    if total_defects == 0:
        # Return standard categories with 0%
        return [DefectDistributionItem(category=cat, count=0, percentage=0.0) for cat in pipeline.SUPPORTED_CATEGORIES]

    distribution = (
        db.query(Inspection.defect_type, func.count(Inspection.id))
        .filter(Inspection.defect_type.isnot(None))
        .group_by(Inspection.defect_type)
        .all()
    )

    results = []
    found_cats = set()
    for cat, cnt in distribution:
        if cat:
            found_cats.add(cat)
            results.append(DefectDistributionItem(
                category=cat,
                count=cnt,
                percentage=round((cnt / total_defects) * 100.0, 1)
            ))

    # Add missing supported categories with 0 for chart completeness
    for cat in pipeline.SUPPORTED_CATEGORIES:
        if cat not in found_cats:
            results.append(DefectDistributionItem(category=cat, count=0, percentage=0.0))

    return results

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

    # Persist to SQLite Database
    db_item = Inspection(
        original_filename=orig_name,
        stored_filename=safe_stored_name,
        annotated_filename=annotated_filename,
        product_id=product_id.strip() if product_id else None,
        status=inference_result["status"],
        defect_type=inference_result["defect_type"],
        confidence_score=inference_result["confidence_score"],
        model_name=inference_result["model_name"],
        model_version=inference_result["model_version"],
        inference_duration_ms=inference_result["inference_duration_ms"],
        manual_review_required=inference_result["manual_review_required"],
        inspection_notes=final_notes,
        defect_regions=json.dumps(inference_result.get("defect_regions", []))
    )
    db.add(db_item)
    db.commit()
    db.refresh(db_item)

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
    query = db.query(Inspection)

    if search:
        search_filter = f"%{search.strip()}%"
        query = query.filter(
            or_(
                Inspection.original_filename.ilike(search_filter),
                Inspection.product_id.ilike(search_filter),
                Inspection.inspection_notes.ilike(search_filter)
            )
        )

    if status and status.upper() in {"ACCEPTED", "DEFECTIVE", "REVIEW_REQUIRED"}:
        query = query.filter(Inspection.status == status.upper())

    if defect_type and defect_type != "ALL":
        query = query.filter(Inspection.defect_type == defect_type)

    if date_from:
        try:
            d_from = datetime.fromisoformat(date_from).replace(tzinfo=timezone.utc)
            query = query.filter(Inspection.created_at >= d_from)
        except ValueError:
            pass

    if date_to:
        try:
            d_to = datetime.fromisoformat(date_to).replace(hour=23, minute=59, second=59, tzinfo=timezone.utc)
            query = query.filter(Inspection.created_at <= d_to)
        except ValueError:
            pass

    # Order newest first
    query = query.order_by(desc(Inspection.created_at))

    # If CSV Export requested
    if export_csv:
        all_filtered = query.all()
        csv_data = generate_inspections_csv(all_filtered)
        return PlainTextResponse(
            content=csv_data,
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=inspection_history_export.csv"}
        )

    # Pagination
    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()
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
    item = db.query(Inspection).filter(Inspection.id == inspection_id).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inspection record not found")
    return format_inspection_response(item)

@router.delete("/inspections/{inspection_id}", status_code=status.HTTP_200_OK, tags=["Inspections"])
def delete_inspection(inspection_id: str, db: Session = Depends(get_db)):
    """Deletes an inspection record and its associated images from disk."""
    item = db.query(Inspection).filter(Inspection.id == inspection_id).first()
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

    db.delete(item)
    db.commit()
    return {"message": "Inspection record deleted successfully", "id": inspection_id}

@router.get("/inspections/{inspection_id}/report", response_model=InspectionReport, tags=["Inspections"])
def get_inspection_report(inspection_id: str, db: Session = Depends(get_db)):
    """Generates an official industrial quality inspection report."""
    item = db.query(Inspection).filter(Inspection.id == inspection_id).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inspection record not found")

    regions = []
    if item.defect_regions:
        try:
            regions = [DefectRegion(**r) for r in json.loads(item.defect_regions)]
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
