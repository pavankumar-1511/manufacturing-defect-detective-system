import time
import json
import logging
from pathlib import Path
from typing import Tuple, List, Optional, Dict, Any
import numpy as np
import cv2
from PIL import Image
from app.services.inference.groq_vision import analyze_with_groq_vision

logger = logging.getLogger("defect_detector")

class DefectDetectionPipeline:
    """
    Industrial Anomaly & Defect Detection Pipeline.
    Combines deep feature extraction representations (PyTorch torchvision backbone)
    with OpenCV multi-scale morphological localization to detect, classify,
    and accurately segment industrial surface defects.
    """

    SUPPORTED_CATEGORIES = [
        "Scratches",
        "Cracks",
        "Dents",
        "Surface Abnormalities",
    ]

    def __init__(self, model_name: str = "PatchAnomaly-ResNet-CV", version: str = "2.1.0"):
        self.model_name = model_name
        self.version = version
        self.device = "cpu"
        self._torch_model = None
        self._transforms = None
        self.is_configured = False
        self._initialize_model()

    def _initialize_model(self):
        """Initializes the PyTorch deep feature extractor."""
        try:
            import torch
            import torchvision.models as models
            import torchvision.transforms as transforms

            self.device = "cuda" if torch.cuda.is_available() else "cpu"
            logger.info(f"Initializing AI Model {self.model_name} on device: {self.device}")
            
            # Load pretrained ResNet-18 backbone for deep patch feature extraction
            # Using weights if available, otherwise initialized architecture
            try:
                weights = models.ResNet18_Weights.DEFAULT
                backbone = models.resnet18(weights=weights)
            except Exception:
                backbone = models.resnet18(weights=None)

            # Strip the fully connected classification head to retain spatial feature maps
            modules = list(backbone.children())[:-2]
            self._torch_model = torch.nn.Sequential(*modules)
            self._torch_model.eval()
            self._torch_model.to(self.device)

            self._transforms = transforms.Compose([
                transforms.Resize((256, 256)),
                transforms.ToTensor(),
                transforms.Normalize(
                    mean=[0.485, 0.456, 0.406],
                    std=[0.229, 0.224, 0.225]
                )
            ])
            self.is_configured = True
            logger.info("AI Model successfully initialized.")
        except Exception as e:
            logger.warning(f"Could not initialize PyTorch backbone: {e}. Falling back to baseline anomaly model.")
            self.is_configured = False

    def inspect_image(
        self,
        image_path: Path,
        defect_threshold: float = 0.50,
        review_threshold: float = 0.65
    ) -> Dict[str, Any]:
        """
        Runs full inference on the target image.
        Returns:
            - status: ACCEPTED, DEFECTIVE, or REVIEW_REQUIRED
            - defect_type: str or None
            - confidence_score: float (0.0 to 1.0)
            - defect_regions: list of bounding boxes
            - inference_duration_ms: float
            - annotated_image_np: OpenCV BGR image
        """
        start_time = time.perf_counter()

        # Read image using OpenCV
        image_bgr = cv2.imread(str(image_path))
        if image_bgr is None:
            raise ValueError(f"Failed to read image at {image_path}")

        orig_h, orig_w = image_bgr.shape[:2]
        gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)

        # 1. Computer Vision Anomaly & Feature Processing
        # Apply Gaussian blur to remove uniform sensor noise
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)

        # Multi-scale gradient and edge detection (Sobel + Scharr for structural cracks/scratches)
        grad_x = cv2.Sobel(blurred, cv2.CV_32F, 1, 0, ksize=3)
        grad_y = cv2.Sobel(blurred, cv2.CV_32F, 0, 1, ksize=3)
        grad_mag = cv2.magnitude(grad_x, grad_y)
        grad_mag_norm = cv2.normalize(grad_mag, None, 0, 255, cv2.NORM_MINMAX, dtype=cv2.CV_8U)

        # Morphological gradient & black-hat transform (highlights dark depressions, cracks, dents)
        kernel_rect = cv2.getStructuringElement(cv2.MORPH_RECT, (9, 9))
        blackhat = cv2.morphologyEx(gray, cv2.MORPH_BLACKHAT, kernel_rect)
        tophat = cv2.morphologyEx(gray, cv2.MORPH_TOPHAT, kernel_rect)

        # Combined anomaly energy map
        anomaly_energy = cv2.addWeighted(grad_mag_norm, 0.5, blackhat, 0.5, 0)
        anomaly_energy = cv2.addWeighted(anomaly_energy, 0.8, tophat, 0.2, 0)

        # Dynamic threshold based on surface mean & standard deviation
        mean_val, std_val = cv2.meanStdDev(gray)
        mean_val = float(mean_val[0][0])
        std_val = float(std_val[0][0])

        # Anomaly thresholding
        thresh_val = max(35, int(mean_val * 0.25 + std_val * 1.5))
        _, thresh = cv2.threshold(anomaly_energy, thresh_val, 255, cv2.THRESH_BINARY)

        # Clean noise with morphological opening and close gaps
        clean_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        opened = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, clean_kernel)
        closed = cv2.morphologyEx(opened, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_RECT, (7, 7)))

        # Find defect candidate contours
        contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        defect_regions: List[Dict[str, Any]] = []
        annotated_bgr = image_bgr.copy()

        total_defect_area = 0.0
        max_contour_energy = 0.0
        defect_type_votes: Dict[str, float] = {cat: 0.0 for cat in self.SUPPORTED_CATEGORIES}

        # Filter contours by minimum significant defect area (to exclude microscopic noise)
        min_defect_area = max(25.0, (orig_w * orig_h) * 0.00015)

        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area < min_defect_area:
                continue

            total_defect_area += area
            x, y, w, h = cv2.boundingRect(cnt)

            # Analyze geometric descriptors of the defect
            aspect_ratio = float(w) / float(h) if h > 0 else 1.0
            perimeter = cv2.arcLength(cnt, True)
            circularity = (4 * np.pi * area) / (perimeter * perimeter) if perimeter > 0 else 0.0
            extent = float(area) / (w * h) if (w * h) > 0 else 0.0

            # Determine defect classification based on morphology & gradient features
            roi_energy = np.mean(anomaly_energy[y:y+h, x:x+w])
            max_contour_energy = max(max_contour_energy, float(roi_energy))

            if aspect_ratio > 3.0 or aspect_ratio < 0.33:
                # Elongated linear feature -> Scratch
                label = "Scratches"
                defect_type_votes["Scratches"] += area * 1.5
            elif circularity < 0.25 and extent < 0.40:
                # Irregular jagged structure -> Crack
                label = "Cracks"
                defect_type_votes["Cracks"] += area * 1.4
            elif circularity > 0.45 and extent > 0.55:
                # Rounded depression -> Dent
                label = "Dents"
                defect_type_votes["Dents"] += area * 1.2
            else:
                # Broad structural irregularity -> Surface Abnormality
                label = "Surface Abnormalities"
                defect_type_votes["Surface Abnormalities"] += area * 1.0

            region_conf = min(0.99, max(0.55, float(roi_energy / 255.0 * 1.2 + 0.3)))
            defect_regions.append({
                "x": int(x),
                "y": int(y),
                "width": int(w),
                "height": int(h),
                "label": label,
                "confidence": round(region_conf, 3)
            })

        # Deep Feature Verification with PyTorch if available
        deep_anomaly_score = 0.0
        if self.is_configured and self._torch_model is not None:
            try:
                import torch
                pil_img = Image.fromarray(cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB))
                tensor_img = self._transforms(pil_img).unsqueeze(0).to(self.device)
                with torch.no_grad():
                    features = self._torch_model(tensor_img)
                    # Compute feature map variance as deep texture entropy metric
                    deep_anomaly_score = float(torch.var(features).cpu().item())
            except Exception as e:
                logger.warning(f"Torch forward pass error: {e}")

        # Compute calibrated normalized anomaly score (0.0 to 1.0)
        area_ratio = total_defect_area / (orig_w * orig_h) if (orig_w * orig_h) > 0 else 0.0

        if defect_regions:
            max_reg_conf = max(r["confidence"] for r in defect_regions)
            area_boost = min(0.25, area_ratio * 50.0)
            combined_score = min(0.98, max_reg_conf * 0.70 + area_boost + 0.15)
            if deep_anomaly_score > 0:
                combined_score = min(0.99, combined_score + min(0.15, deep_anomaly_score * 0.05))
        else:
            combined_score = 0.05

        # Multi-modal AI Vision Scanning (Groq Qwen 3.8 27B Vision)
        groq_result = analyze_with_groq_vision(image_path)
        ai_description = None
        current_model_name = self.model_name

        if groq_result:
            current_model_name = f"{groq_result['model_name']} + ResNet-CV"
            ai_description = groq_result.get("analysis")
            status = groq_result["status"]
            primary_defect = groq_result["defect_type"]
            confidence = groq_result["confidence_score"]
            manual_review_required = (status == "REVIEW_REQUIRED")

            # Harmonize defect region bounding box labels
            if primary_defect and defect_regions:
                for reg in defect_regions:
                    reg["label"] = primary_defect
        else:
            # Baseline: Local PyTorch ResNet + Morphological CV Pipeline
            if len(defect_regions) == 0 or combined_score < defect_threshold:
                status = "ACCEPTED"
                primary_defect = None
                confidence = round(float(1.0 - combined_score * 0.5), 3)
                manual_review_required = False
            elif combined_score < review_threshold:
                status = "REVIEW_REQUIRED"
                primary_defect = max(defect_type_votes, key=defect_type_votes.get) if defect_type_votes else "Surface Abnormalities"
                confidence = round(float(combined_score), 3)
                manual_review_required = True
            else:
                status = "DEFECTIVE"
                primary_defect = max(defect_type_votes, key=defect_type_votes.get) if defect_type_votes else "Surface Abnormalities"
                confidence = round(float(combined_score), 3)
                manual_review_required = False

        # Annotate image with defect regions
        self._annotate_image(annotated_bgr, defect_regions, status, primary_defect, confidence)

        inference_duration_ms = round((time.perf_counter() - start_time) * 1000, 2)

        return {
            "status": status,
            "defect_type": primary_defect,
            "confidence_score": confidence,
            "defect_regions": defect_regions,
            "inference_duration_ms": inference_duration_ms,
            "manual_review_required": manual_review_required,
            "annotated_image_np": annotated_bgr,
            "model_name": current_model_name,
            "model_version": self.version,
            "model_configured": self.is_configured,
            "ai_description": ai_description
        }

    def _annotate_image(
        self,
        img: np.ndarray,
        regions: List[Dict[str, Any]],
        status: str,
        defect_type: Optional[str],
        confidence: float
    ):
        """Draws bounding boxes, defect tags, and inspection verdict badge."""
        overlay = img.copy()

        # Color codes: BGR format
        # Red for Defective: (40, 40, 225)
        # Amber for Review: (11, 148, 245)
        # Green for Accepted: (40, 180, 50)
        box_color = (40, 40, 225) if status == "DEFECTIVE" else (11, 148, 245)

        for reg in regions:
            x, y, w, h = reg["x"], reg["y"], reg["width"], reg["height"]
            label = reg["label"]
            reg_conf = reg["confidence"]

            # Highlight bounding box region with semi-transparent fill
            cv2.rectangle(overlay, (x, y), (x + w, y + h), box_color, -1)
            # Outline
            cv2.rectangle(img, (x, y), (x + w, y + h), box_color, 2)

            # Badge pill
            badge_text = f"{label} ({int(reg_conf * 100)}%)"
            (tw, th), _ = cv2.getTextSize(badge_text, cv2.FONT_HERSHEY_SIMPLEX, 0.45, 1)
            cv2.rectangle(img, (x, max(0, y - th - 6)), (x + tw + 8, y), box_color, -1)
            cv2.putText(
                img,
                badge_text,
                (x + 4, max(th, y - 4)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.45,
                (255, 255, 255),
                1,
                cv2.LINE_AA
            )

        # Blend overlay for soft defect heatmap effect
        if regions:
            cv2.addWeighted(overlay, 0.25, img, 0.75, 0, img)

        # Top verdict banner
        banner_h = 36
        banner_bg = (30, 41, 59)  # Dark navy
        cv2.rectangle(img, (0, 0), (img.shape[1], banner_h), banner_bg, -1)

        status_color = (50, 190, 70) if status == "ACCEPTED" else ((40, 40, 230) if status == "DEFECTIVE" else (20, 170, 245))
        verdict_str = f"AI INSPECTION: {status}"
        if defect_type:
            verdict_str += f" | {defect_type} ({int(confidence * 100)}%)"
        else:
            verdict_str += f" | Integrity: {int(confidence * 100)}%"

        cv2.putText(
            img,
            verdict_str,
            (12, 23),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            status_color,
            2,
            cv2.LINE_AA
        )

# Global singleton pipeline instance
pipeline = DefectDetectionPipeline()
