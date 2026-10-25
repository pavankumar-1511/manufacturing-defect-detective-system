# System Architecture & Technical Specifications

## 1. High-Level Architecture Overview

ApexVision AI is a production-grade automated optical inspection (AOI) full-stack web application designed for real-time manufacturing defect identification, morphological localization, statistical process monitoring, and audit compliance.

```
                      +---------------------------------------+
                      |       React 19 + TypeScript UI        |
                      |   Vite + Tailwind CSS + Lucide Icons  |
                      |      Recharts Telemetry Dashboard     |
                      +---------------------------------------+
                                          |
                                          | HTTP REST / Axios
                                          v
                      +---------------------------------------+
                      |         FastAPI REST Backend          |
                      |     Uvicorn ASGI • Lifespan Init      |
                      +---------------------------------------+
                             |                         |
              +--------------+                         +--------------+
              |                                                       |
              v                                                       v
+-----------------------------+                         +-----------------------------+
|    AI Inference Pipeline    |                         |      Persistence Layer      |
|  PyTorch Feature Extraction |                         |     SQLite with SQLAlchemy  |
|  OpenCV Multi-Scale Anomaly |                         |  Inspections & Audit Logs   |
|  Morphological Contours     |                         +-----------------------------+
|  Bounding Boxes & Heatmaps  |
+-----------------------------+
```

---

## 2. AI Inference Engine Pipeline

The AI inference pipeline (`backend/app/services/inference/detector.py`) combines deep feature extraction with high-precision computer vision algorithms to reliably detect industrial surface defects:

1. **Pre-Processing & Noise Filtering**:
   - Gaussian smoothing reduces sensor thermal noise without blunting sharp fracture edges.
2. **Multi-Scale Gradient & Morphological Transforms**:
   - Sobel & Scharr directional derivatives isolate high-frequency structural disruptions.
   - Morphological Top-Hat and Black-Hat transforms isolate localized specular depressions and pits.
   - Combined anomaly energy map is computed with adaptive dynamic thresholding based on surface mean and standard deviation.
3. **Deep Texture Verification (PyTorch Backbone)**:
   - Uses PyTorch torchvision ResNet-18 intermediate conv layer embeddings to calculate spatial patch texture representations and feature map variance.
4. **Contour Extraction & Defect Classification**:
   - Contiguous contours are filtered by minimum physical defect area.
   - Geometric descriptors:
     - **Scratches**: High aspect ratio ($> 3.0$), linear directional gradient.
     - **Cracks**: Low circularity ($< 0.25$), high perimeter complexity, irregular branch points.
     - **Dents**: Circular depression, concentric gradient variance.
     - **Surface Abnormalities**: Localized texture entropy disparity.
5. **Calibrated Decision Logic**:
   - Anomaly score $< \text{Defect Threshold (0.50)}$: `ACCEPTED` (Part within tolerance)
   - $\text{Defect Threshold} \le \text{Score} < \text{Review Threshold (0.65)}$: `REVIEW_REQUIRED` (Human QA inspector sign-off)
   - $\text{Score} \ge \text{Review Threshold (0.65)}$: `DEFECTIVE` (Immediate rejection / rework)
6. **Optical Annotation**:
   - Overlays color-coded bounding boxes, category badges, and semi-transparent defect heatmaps on the component image.

---

## 3. Database Schema

The database (`backend/app/models/inspection.py`) uses SQLite with SQLAlchemy ORM:

| Column | Type | Description |
|---|---|---|
| `id` | `VARCHAR(36)` | UUID primary key |
| `original_filename` | `VARCHAR(255)` | User-provided image filename |
| `stored_filename` | `VARCHAR(255)` | Safe, randomized stored filename |
| `annotated_filename` | `VARCHAR(255)` | Filename of annotated visual artifact |
| `product_id` | `VARCHAR(100)` | Production lot or serial barcode |
| `status` | `VARCHAR(50)` | `ACCEPTED`, `DEFECTIVE`, `REVIEW_REQUIRED` |
| `defect_type` | `VARCHAR(100)` | `Scratches`, `Cracks`, `Dents`, `Surface Abnormalities`, or `None` |
| `confidence_score` | `FLOAT` | Calibrated anomaly probability $[0.0, 1.0]$ |
| `model_name` | `VARCHAR(100)` | Active AI architecture identifier |
| `model_version` | `VARCHAR(50)` | Semantic version |
| `inference_duration_ms`| `FLOAT` | Measured inference latency |
| `manual_review_required`| `BOOLEAN` | Boolean flag indicating human review requirement |
| `inspection_notes` | `TEXT` | Operator or automated observations |
| `defect_regions` | `TEXT` | JSON-serialized array of bounding boxes `[X, Y, W, H]` |
| `created_at` | `DATETIME` | UTC timestamp of inspection creation |

---

## 4. Security & Hardening

1. **File Validation**:
   - 10 MB strict file size ceiling.
   - Allowed MIME types: `image/jpeg`, `image/png`, `image/jpg`.
   - Binary header inspection with Pillow `Image.verify()` rejects corrupted files, polyglots, and malicious scripts.
2. **Safe Filenames & Path Traversal Prevention**:
   - System assigns randomized UUID filenames for disk storage.
   - Target directory resolution verifies paths stay within the configured uploads sandbox.
3. **CORS Isolation**:
   - Strict origin allowlist (`http://localhost:5173`, `http://127.0.0.1:5173`).
