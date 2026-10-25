# ApexVision AI — Manufacturing Defect Detection System

ApexVision AI is an enterprise-grade automated optical inspection (AOI) full-stack web application designed for real-time manufacturing defect identification, morphological localization, statistical process control, and audit compliance.

![Status](https://img.shields.io/badge/Status-Production%20Ready-brightgreen)
![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688)
![PyTorch](https://img.shields.io/badge/AI-PyTorch%20%2B%20OpenCV-EE4C2C)
![React](https://img.shields.io/badge/Frontend-React%2019%20%2B%20TypeScript-61DAFB)
![Tailwind](https://img.shields.io/badge/Styling-Tailwind%20CSS-38B2AC)

---

## 1. System Features

- **Industrial Quality Dashboard**: Real-time production line statistics calculated directly from database records (Total inspections, Pass/Accept count, Scrap/Defect count, Review-required count, Defect yield rate, and Inference latency).
- **Interactive Visualizations**: Defect distribution pie/donut chart, 7-30 day inspection volume trend lines, and first-pass yield indicators using Recharts.
- **Deep Computer Vision Inference Pipeline**:
  - Deep texture feature extraction with PyTorch torchvision ResNet-18 backbone.
  - Multi-scale gradient and morphological spatial localization (Sobel, Top-Hat, Black-Hat).
  - Accurate extraction of contiguous defect bounding boxes (`[X, Y, W, H]`).
  - Defect categorization: **Scratches**, **Cracks**, **Dents**, and **Surface Abnormalities**.
  - Visual defect heatmaps and annotated overlay bounding boxes saved on disk.
- **Drag & Drop Inspection Workflow**:
  - Drag and drop or file upload (JPG, JPEG, PNG, max 10 MB).
  - Pre-upload image preview with file size and dimension checks.
  - Optional Batch/Product Serial ID and inspector notes.
  - Real-time verdict banner (`ACCEPTED`, `DEFECTIVE`, or `REVIEW REQUIRED`) with side-by-side original vs. annotated inspection viewer.
  - Quick-load instant test fixture buttons (preloaded scratch, crack, dent, and pristine test pieces).
- **Audit History & Search**:
  - Full-text search across filenames, batch IDs, and inspector notes.
  - Multi-criteria filtering by verdict, defect category, and date range.
  - Server-side pagination and item per page controls.
  - One-click RFC 4180-compliant CSV audit export.
- **Official Printable Quality Assurance Certificate**:
  - Standardized inspection report with ISO-style header, QA stamp, defect coordinate table, and side-by-side optical evidence.
  - Browser print-ready (`window.print()`) with print CSS media queries.
- **Model Telemetry & Dynamic Calibration**:
  - Live AI model status, hardware execution target (CPU/CUDA), and inference latency monitor.
  - Runtime adjustable decision thresholds for acceptance and manual review.
- **Industrial Security Hardening**:
  - Strict 10 MB payload limiter.
  - Magic byte binary image verification via Pillow prevents polyglots or corrupted uploads.
  - Sanitized UUID storage paths prevent directory traversal attacks.
  - Restricted CORS origin policy.

---

## 2. Technology Stack

- **Frontend**: React 19, TypeScript, Vite, Tailwind CSS, Lucide React icons, Recharts, Axios.
- **Backend**: Python 3.11+, FastAPI, Uvicorn ASGI, Pydantic v2.
- **AI & Computer Vision**: PyTorch (CPU/CUDA), Torchvision, OpenCV (`opencv-python-headless`), NumPy, Pillow.
- **Database**: SQLite with SQLAlchemy ORM.
- **Testing**: Pytest, HTTPX TestClient, TypeScript compiler type-checking (`tsc -b`), and Vite production builds.

---

## 3. Project Structure

```
ai/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   └── endpoints.py          # FastAPI route handlers
│   │   ├── database/
│   │   │   ├── __init__.py
│   │   │   └── session.py            # SQLite engine, sessionmaker, and init_db
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   └── inspection.py         # SQLAlchemy Inspection model
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   └── inspection.py         # Pydantic request/response schemas
│   │   ├── services/
│   │   │   ├── inference/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── detector.py       # PyTorch ResNet & OpenCV defect detector
│   │   │   │   └── model_registry.py # Model status, uptime & threshold manager
│   │   │   ├── storage.py            # Upload verification & traversal prevention
│   │   │   ├── reporting.py          # CSV & QA audit report generators
│   │   │   └── seed_data.py          # Synthetic demo parts & initial database seeder
│   │   ├── config.py                 # Pydantic Settings configuration
│   │   └── main.py                   # FastAPI lifespan, CORS, and mount points
│   ├── tests/
│   │   ├── conftest.py               # In-memory SQLite fixture and test images
│   │   ├── test_api.py               # Comprehensive REST API integration tests
│   │   └── test_inference.py         # AI inference unit tests
│   ├── uploads/
│   │   ├── original/                 # Stored original part images
│   │   └── annotated/                # AI annotated overlays & heatmaps
│   ├── requirements.txt
│   ├── .env.example
│   └── .env
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── common/
│   │   │   │   ├── StatusBadge.tsx
│   │   │   │   ├── InspectionDetailModal.tsx
│   │   │   │   └── PrintableReportModal.tsx
│   │   │   └── layout/
│   │   │       ├── Header.tsx
│   │   │       └── Sidebar.tsx
│   │   ├── pages/
│   │   │   ├── DashboardPage.tsx
│   │   │   ├── NewInspectionPage.tsx
│   │   │   ├── HistoryPage.tsx
│   │   │   ├── AnalyticsPage.tsx
│   │   │   ├── ModelInfoPage.tsx
│   │   │   └── SettingsPage.tsx
│   │   ├── services/
│   │   │   └── api.ts                # Axios API client
│   │   ├── types/
│   │   │   └── index.ts              # TypeScript interfaces
│   │   ├── App.tsx
│   │   ├── index.css                 # Industrial design system & print styles
│   │   └── main.tsx
│   ├── index.html
│   ├── package.json
│   ├── tailwind.config.js
│   ├── postcss.config.js
│   ├── tsconfig.json
│   └── vite.config.ts
├── docs/
│   ├── ARCHITECTURE.md               # Technical system design
│   └── API_SPEC.md                   # OpenAPI REST documentation
└── README.md
```

---

## 4. Installation & Setup

### Prerequisites
- **Python**: Version 3.11+
- **Node.js**: Version 18+ and `npm`

---

### Backend Setup

1. **Navigate to the backend directory**:
   ```bash
   cd backend
   ```

2. **Create and activate a virtual environment**:
   - On Windows (PowerShell):
     ```powershell
     python -m venv .venv
     .\.venv\Scripts\Activate.ps1
     ```
   - On Linux/macOS:
     ```bash
     python3 -m venv .venv
     source .venv/bin/activate
     ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt --extra-index-url https://download.pytorch.org/whl/cpu
   ```

4. **Initialize configuration**:
   ```bash
   cp .env.example .env
   ```

5. **Start the FastAPI backend server**:
   ```bash
   uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
   ```
   - The backend runs at: `http://localhost:8000`
   - Interactive API documentation: `http://localhost:8000/docs`

---

### Frontend Setup

1. **Navigate to the frontend directory**:
   ```bash
   cd frontend
   ```

2. **Install frontend dependencies**:
   ```bash
   npm install --legacy-peer-deps
   ```

3. **Start the Vite development server**:
   ```bash
   npm run dev
   ```
   - The frontend will be available at: `http://localhost:5173`

---

## 5. Running the Test Suite

### Backend Pytest Suite
Run the full 14-test unit and integration test suite:
```bash
# From workspace root
.\backend\.venv\Scripts\python.exe -m pytest backend/tests/ -v
```
**Test Coverage Includes**:
- Server health and readiness check (`/api/health`)
- Database automatic initialization and seeding
- Dashboard stats, 7-day trend calculations, and defect distribution
- Valid JPEG/PNG image upload and inference pipeline execution
- Rejection of corrupted files and unsupported file extensions
- Server-side search, filtering by status/category, and pagination
- CSV audit export validation
- Printable QA report generation
- Defect threshold adjustment
- Record deletion and physical file unlinking
- Morphology contour extraction, bounding box coordinates, and confidence bounds

### Frontend Build & Type Check
Verify that all TypeScript types and Vite bundles compile cleanly:
```bash
# In frontend directory
npm run build
```

---

## 6. AI Model Setup & Custom Datasets

The defect detection engine operates out of the box using deep convolutional feature extraction (PyTorch ResNet-18) combined with multi-scale morphological anomaly maps.

To fine-tune or replace the backbone with an MVTec AD industrial anomaly dataset (e.g. `metal_nut`, `screw`, `hazelnut`, `tile`):
1. Place custom model weights (`.pt` or `.pth`) in `backend/app/services/inference/weights/`.
2. Update `MODEL_NAME` and `MODEL_VERSION` in `backend/app/config.py` or `.env`.
3. The pipeline interface separates model inference from API routes (`backend/app/services/inference/detector.py`), allowing drop-in model swapping without modifying REST routes.

---

## 7. Troubleshooting

- **CORS Errors**: Ensure the frontend is running on `http://localhost:5173` or `http://127.0.0.1:5173`. Additional origins can be configured in `backend/app/config.py`.
- **Image Upload Rejected (415)**: Only `.jpg`, `.jpeg`, and `.png` files are permitted. Verify file extension and ensure the file is an authentic raster image.
- **Database Reset**: To re-seed the SQLite database with fresh synthetic defect records, stop the backend, delete `backend/defect_detection.db`, and restart the backend server.
