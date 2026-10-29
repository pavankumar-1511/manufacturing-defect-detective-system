import base64
import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any
import cv2
import httpx
from app.config import settings

logger = logging.getLogger("groq_vision")

def encode_image_for_groq(image_path: Path, max_dimension: int = 768) -> Optional[str]:
    """Reads and downsizes image if necessary, returning base64 JPEG string."""
    try:
        img = cv2.imread(str(image_path))
        if img is None:
            return None
        
        h, w = img.shape[:2]
        if max(h, w) > max_dimension:
            scale = max_dimension / float(max(h, w))
            new_w, new_h = int(w * scale), int(h * scale)
            img = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)
            
        success, buffer = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, 85])
        if not success:
            return None
        return base64.b64encode(buffer).decode("utf-8")
    except Exception as e:
        logger.warning(f"Error encoding image for Groq: {e}")
        return None

def analyze_with_groq_vision(image_path: Path) -> Optional[Dict[str, Any]]:
    """
    Leverages Groq's high-speed multimodal LPU vision inference (Qwen 3.8 27B Vision)
    to perform deep industrial optical defect detection and root-cause classification.
    Returns parsed JSON dict or None on failure/missing key.
    """
    if not settings.GROQ_API_KEY or not settings.GROQ_API_KEY.strip():
        return None

    b64_img = encode_image_for_groq(image_path)
    if not b64_img:
        return None

    prompt = (
        "You are an automated optical inspection (AOI) deep learning quality assurance system. "
        "Carefully inspect the surface of this manufactured component for defects.\n"
        "Categories must strictly be one of:\n"
        "- 'Scratches' (linear surface abrasions or dragging cuts)\n"
        "- 'Cracks' (structural fracture lines or micro-stress fractures)\n"
        "- 'Dents' (impact depressions, tooling gouges, or craters)\n"
        "- 'Surface Abnormalities' (irregular texture, pitting, staining, or oxidation)\n"
        "- 'None' (if pristine, defect-free, and within tolerance)\n\n"
        "Return strictly a valid JSON object with these keys:\n"
        "{\n"
        '  "status": "ACCEPTED" or "DEFECTIVE" or "REVIEW_REQUIRED",\n'
        '  "defect_type": "Scratches" | "Cracks" | "Dents" | "Surface Abnormalities" | null,\n'
        '  "confidence_score": float between 0.0 and 1.0,\n'
        '  "analysis": "1-2 sentence engineering diagnosis of what was visually observed"\n'
        "}"
    )

    try:
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {settings.GROQ_API_KEY.strip()}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": settings.GROQ_MODEL,
            "response_format": {"type": "json_object"},
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{b64_img}"
                            }
                        }
                    ]
                }
            ],
            "temperature": 0.1,
            "max_tokens": 300
        }

        with httpx.Client(timeout=12.0) as client:
            response = client.post(url, headers=headers, json=payload)
            if response.status_code != 200:
                logger.warning(f"Groq API returned HTTP {response.status_code}: {response.text}")
                return None
            
            data = response.json()
            raw_content = data["choices"][0]["message"]["content"]
            result = json.loads(raw_content)
            
            # Normalize defect type
            dt = result.get("defect_type")
            if dt and dt.lower() in ["none", "null"]:
                dt = None
            elif dt and dt not in ["Scratches", "Cracks", "Dents", "Surface Abnormalities"]:
                # Map closest category if needed
                lower_dt = dt.lower()
                if "scratch" in lower_dt:
                    dt = "Scratches"
                elif "crack" in lower_dt or "fracture" in lower_dt:
                    dt = "Cracks"
                elif "dent" in lower_dt or "depression" in lower_dt:
                    dt = "Dents"
                else:
                    dt = "Surface Abnormalities"
            
            status = result.get("status", "ACCEPTED").upper()
            if status not in ["ACCEPTED", "DEFECTIVE", "REVIEW_REQUIRED"]:
                status = "DEFECTIVE" if dt else "ACCEPTED"

            conf = float(result.get("confidence_score", 0.90))
            conf = max(0.1, min(0.99, conf))

            return {
                "status": status,
                "defect_type": dt,
                "confidence_score": round(conf, 3),
                "analysis": result.get("analysis", "Multimodal visual inspection complete."),
                "model_name": f"Groq-{settings.GROQ_MODEL}"
            }
    except Exception as e:
        logger.warning(f"Groq Vision inference failed: {e}. Falling back to local pipeline.")
        return None

