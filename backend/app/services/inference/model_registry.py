import time
from typing import Dict, Any, List
from app.config import settings
from app.services.inference.detector import pipeline

class ModelRegistry:
    def __init__(self):
        self.start_time = time.time()
        self.total_inferences = 0
        self.defect_threshold = settings.DEFECT_CONFIDENCE_THRESHOLD
        self.review_threshold = settings.REVIEW_REQUIRED_THRESHOLD

    def record_inference(self):
        self.total_inferences += 1

    def update_thresholds(self, defect_threshold: float, review_threshold: float):
        if not (0.0 < defect_threshold < review_threshold <= 1.0):
            raise ValueError("Defect threshold must be less than review threshold, and both must be between 0 and 1.")
        self.defect_threshold = defect_threshold
        self.review_threshold = review_threshold

    def get_status(self) -> Dict[str, Any]:
        uptime = round(time.time() - self.start_time, 1)
        return {
            "name": pipeline.model_name,
            "version": pipeline.version,
            "status": "ONLINE" if pipeline.is_configured else "BASELINE_ACTIVE",
            "device": pipeline.device,
            "supported_defect_types": pipeline.SUPPORTED_CATEGORIES,
            "defect_confidence_threshold": self.defect_threshold,
            "review_threshold": self.review_threshold,
            "uptime_seconds": uptime,
            "total_inferences": self.total_inferences,
            "model_configured": pipeline.is_configured,
            "details": "PyTorch ResNet-18 Deep Feature Extractor + OpenCV Multi-Scale Anomaly Segmenter" if pipeline.is_configured else "Baseline Computer Vision Anomaly Pipeline active"
        }

model_registry = ModelRegistry()
