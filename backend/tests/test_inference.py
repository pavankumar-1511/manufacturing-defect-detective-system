import numpy as np
import cv2
from pathlib import Path
from app.services.inference.detector import DefectDetectionPipeline

def test_inference_clean_image(tmp_path):
    pipeline = DefectDetectionPipeline()
    img_path = tmp_path / "clean_part.png"
    # Create smooth surface
    img = np.full((250, 250, 3), 200, dtype=np.uint8)
    cv2.imwrite(str(img_path), img)

    result = pipeline.inspect_image(img_path)
    assert result["status"] in ["ACCEPTED", "REVIEW_REQUIRED", "DEFECTIVE"]
    assert 0.0 <= result["confidence_score"] <= 1.0
    assert result["inference_duration_ms"] > 0
    assert "annotated_image_np" in result

def test_inference_scratch_defect(tmp_path):
    pipeline = DefectDetectionPipeline()
    img_path = tmp_path / "scratch_part.png"
    img = np.full((300, 300, 3), 180, dtype=np.uint8)
    # Severe scratch
    cv2.line(img, (40, 50), (260, 250), (20, 20, 20), 4)
    cv2.imwrite(str(img_path), img)

    result = pipeline.inspect_image(img_path)
    assert result["status"] in ["DEFECTIVE", "REVIEW_REQUIRED"]
    assert len(result["defect_regions"]) >= 1
    assert result["confidence_score"] >= 0.50
    assert result["defect_type"] in pipeline.SUPPORTED_CATEGORIES
