import os
import json
import uuid
import numpy as np
import cv2
from datetime import datetime, timezone, timedelta
from app.config import settings
from app.database.session import SessionLocal
from app.database.mongodb import is_mongo_enabled, get_mongo_inspections_collection
from app.models.inspection import Inspection
from app.services.inference.detector import pipeline

def create_sample_industrial_images():
    """Generates realistic sample industrial inspection images for initial seeding and testing."""
    os.makedirs(settings.ORIGINAL_UPLOAD_DIR, exist_ok=True)
    os.makedirs(settings.ANNOTATED_UPLOAD_DIR, exist_ok=True)

    samples = [
        ("sample_pristine_bracket.png", "pristine", "LOT-2026-A101"),
        ("sample_surface_scratch.png", "scratch", "LOT-2026-B204"),
        ("sample_metal_crack.png", "crack", "LOT-2026-C308"),
        ("sample_stamped_dent.png", "dent", "LOT-2026-D412"),
        ("sample_surface_abnormality.png", "abnormality", "LOT-2026-E516"),
        ("sample_multiple_defects.png", "multiple", "LOT-2026-M999"),
    ]

    created_files = []

    for filename, sample_type, batch_id in samples:
        target_path = settings.ORIGINAL_UPLOAD_DIR / filename
        if not target_path.exists():
            # Create a 400x400 synthetic industrial surface with realistic metallic texture
            img = np.full((400, 400, 3), 180, dtype=np.uint8)
            # Add subtle brushed metal noise
            noise = np.random.normal(0, 10, (400, 400)).astype(np.int16)
            for ch in range(3):
                channel = np.clip(img[:, :, ch].astype(np.int16) + noise, 0, 255).astype(np.uint8)
                img[:, :, ch] = channel

            # Draw industrial bevel/border
            cv2.rectangle(img, (20, 20), (380, 380), (140, 140, 140), 2)
            # Mounting holes
            cv2.circle(img, (60, 60), 18, (80, 80, 80), -1)
            cv2.circle(img, (340, 60), 18, (80, 80, 80), -1)
            cv2.circle(img, (60, 340), 18, (80, 80, 80), -1)
            cv2.circle(img, (340, 340), 18, (80, 80, 80), -1)

            if sample_type == "scratch":
                # Draw sharp diagonal scratch
                cv2.line(img, (120, 130), (280, 260), (30, 30, 30), 2)
                cv2.line(img, (125, 132), (275, 258), (240, 240, 240), 1)
            elif sample_type == "crack":
                # Draw jagged jagged crack path
                pts = np.array([[200, 100], [215, 140], [195, 180], [220, 230], [205, 270]], np.int32)
                cv2.polylines(img, [pts], False, (20, 20, 20), 3)
            elif sample_type == "dent":
                # Draw dark depressed circle with highlight
                cv2.circle(img, (200, 200), 35, (70, 70, 70), -1)
                cv2.circle(img, (190, 190), 25, (120, 120, 120), -1)
            elif sample_type == "abnormality":
                # Draw discoloration patch
                cv2.ellipse(img, (200, 200), (60, 35), 30, 0, 360, (100, 110, 120), -1)
            elif sample_type == "multiple":
                # Draw both a diagonal scratch and a dent
                cv2.line(img, (100, 120), (220, 210), (30, 30, 30), 2)
                cv2.circle(img, (270, 260), 30, (70, 70, 70), -1)

            cv2.imwrite(str(target_path), img)

        created_files.append((filename, batch_id))

    return created_files

def seed_database_if_empty():
    """Seeds the database (MongoDB or SQLite) with realistic initial records if empty."""
    if is_mongo_enabled():
        try:
            col = get_mongo_inspections_collection()
            if col.count_documents({}) > 0:
                return
            create_sample_industrial_images()
            now = datetime.now(timezone.utc)
            seed_records = [
                {"orig": "part_bracket_A101.png", "file": "sample_pristine_bracket.png", "batch": "LOT-2026-A101", "notes": "Machined bracket passed automated dimensional and surface check.", "days_ago": 6},
                {"orig": "housing_panel_B204.png", "file": "sample_surface_scratch.png", "batch": "LOT-2026-B204", "notes": "Surface scratch detected across central mounting flange.", "days_ago": 5},
                {"orig": "cast_flange_C308.png", "file": "sample_metal_crack.png", "batch": "LOT-2026-C308", "notes": "Critical hairline fracture detected. Part rejected.", "days_ago": 3},
                {"orig": "cover_plate_D412.png", "file": "sample_stamped_dent.png", "batch": "LOT-2026-D412", "notes": "Stamped depression exceeds tolerance. Marked for rework.", "days_ago": 2},
                {"orig": "bearing_seal_E516.png", "file": "sample_surface_abnormality.png", "batch": "LOT-2026-E516", "notes": "Discoloration and porosity noted on perimeter.", "days_ago": 1},
                {"orig": "turbine_blade_F620.png", "file": "sample_pristine_bracket.png", "batch": "LOT-2026-F620", "notes": "Surface integrity validated with zero defects.", "days_ago": 0}
            ]
            for s in seed_records:
                stored_path = settings.ORIGINAL_UPLOAD_DIR / s["file"]
                if stored_path.exists():
                    res = pipeline.inspect_image(stored_path)
                    annotated_name = f"annotated_{s['file']}"
                    annotated_path = settings.ANNOTATED_UPLOAD_DIR / annotated_name
                    if "annotated_image_np" in res:
                        cv2.imwrite(str(annotated_path), res["annotated_image_np"])
                    col.insert_one({
                        "id": str(uuid.uuid4()),
                        "original_filename": s["orig"],
                        "stored_filename": s["file"],
                        "annotated_filename": annotated_name,
                        "product_id": s["batch"],
                        "status": res["status"],
                        "defect_type": res["defect_type"],
                        "confidence_score": res["confidence_score"],
                        "model_name": res["model_name"],
                        "model_version": res["model_version"],
                        "inference_duration_ms": res["inference_duration_ms"],
                        "manual_review_required": res["manual_review_required"],
                        "inspection_notes": s["notes"],
                        "defect_regions": json.dumps(res.get("defect_regions", [])),
                        "created_at": now - timedelta(days=s["days_ago"], hours=s["days_ago"] * 2)
                    })
        except Exception as e:
            print(f"Error during initial MongoDB seed: {e}")
        return

    # SQLite Seeding
    db = SessionLocal()
    try:
        count = db.query(Inspection).count()
        if count > 0:
            return  # Already seeded

        sample_files = create_sample_industrial_images()
        now = datetime.now(timezone.utc)

        # Seed realistic inspections across past 7 days
        seed_records = [
            {
                "orig": "part_bracket_A101.png",
                "file": "sample_pristine_bracket.png",
                "batch": "LOT-2026-A101",
                "notes": "Machined bracket passed automated dimensional and surface check.",
                "days_ago": 6
            },
            {
                "orig": "housing_panel_B204.png",
                "file": "sample_surface_scratch.png",
                "batch": "LOT-2026-B204",
                "notes": "Surface scratch detected across central mounting flange.",
                "days_ago": 5
            },
            {
                "orig": "cast_flange_C308.png",
                "file": "sample_metal_crack.png",
                "batch": "LOT-2026-C308",
                "notes": "Critical hairline fracture detected. Part rejected.",
                "days_ago": 3
            },
            {
                "orig": "cover_plate_D412.png",
                "file": "sample_stamped_dent.png",
                "batch": "LOT-2026-D412",
                "notes": "Stamped depression exceeds tolerance. Marked for rework.",
                "days_ago": 2
            },
            {
                "orig": "bearing_seal_E516.png",
                "file": "sample_surface_abnormality.png",
                "batch": "LOT-2026-E516",
                "notes": "Discoloration and porosity noted on perimeter.",
                "days_ago": 1
            },
            {
                "orig": "turbine_blade_F620.png",
                "file": "sample_pristine_bracket.png",
                "batch": "LOT-2026-F620",
                "notes": "Surface integrity validated with zero defects.",
                "days_ago": 0
            }
        ]

        for s in seed_records:
            stored_path = settings.ORIGINAL_UPLOAD_DIR / s["file"]
            if stored_path.exists():
                res = pipeline.inspect_image(stored_path)
                annotated_name = f"annotated_{s['file']}"
                annotated_path = settings.ANNOTATED_UPLOAD_DIR / annotated_name
                if "annotated_image_np" in res:
                    cv2.imwrite(str(annotated_path), res["annotated_image_np"])

                record = Inspection(
                    original_filename=s["orig"],
                    stored_filename=s["file"],
                    annotated_filename=annotated_name,
                    product_id=s["batch"],
                    status=res["status"],
                    defect_type=res["defect_type"],
                    confidence_score=res["confidence_score"],
                    model_name=res["model_name"],
                    model_version=res["model_version"],
                    inference_duration_ms=res["inference_duration_ms"],
                    manual_review_required=res["manual_review_required"],
                    inspection_notes=s["notes"],
                    defect_regions=json.dumps(res.get("defect_regions", [])),
                    created_at=now - timedelta(days=s["days_ago"], hours=s["days_ago"] * 2)
                )
                db.add(record)

        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Error during initial seed: {e}")
    finally:
        db.close()
