import csv
import io
import json
from typing import List
from app.models.inspection import Inspection

def generate_inspections_csv(inspections: List[Inspection]) -> str:
    """Generates an RFC 4180 compliant CSV string from a list of inspections."""
    output = io.StringIO()
    writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)

    # Header
    writer.writerow([
        "Inspection ID",
        "Product / Batch ID",
        "Original Filename",
        "Inspection Status",
        "Defect Category",
        "Defect Severity",
        "Confidence Score",
        "Defect Regions Count",
        "Manual Review Required",
        "Inference Duration (ms)",
        "AI Model",
        "Model Version",
        "Timestamp (UTC)",
        "Notes"
    ])

    for item in inspections:
        regions_count = 0
        if item.defect_regions:
            try:
                regions = json.loads(item.defect_regions)
                regions_count = len(regions)
            except Exception:
                pass

        from app.services.root_cause import get_root_cause_analysis
        rca = get_root_cause_analysis(item.defect_type, item.status)

        writer.writerow([
            item.id,
            item.product_id or "N/A",
            item.original_filename,
            item.status,
            item.defect_type or "None",
            rca["severity"],
            f"{item.confidence_score:.3f}" if item.confidence_score is not None else "N/A",
            regions_count,
            "YES" if item.manual_review_required else "NO",
            f"{item.inference_duration_ms:.2f}",
            item.model_name,
            item.model_version,
            item.created_at.strftime("%Y-%m-%d %H:%M:%S") if item.created_at else "N/A",
            item.inspection_notes or ""
        ])

    return output.getvalue()
