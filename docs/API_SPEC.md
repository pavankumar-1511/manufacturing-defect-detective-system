# REST API Specification

ApexVision AI REST API conforms to OpenAPI 3.1 specifications. Interactive Swagger documentation is accessible at `http://localhost:8000/docs`.

---

## 1. System Endpoints

### `GET /api/health`
Checks server readiness, database connection, and model engine status.

**Response `200 OK`**:
```json
{
  "status": "healthy",
  "timestamp": "2026-10-20T15:10:00Z",
  "service": "AI-Based Manufacturing Defect Detection System",
  "version": "2.1.0",
  "database": "connected",
  "model_engine": "ready"
}
```

---

## 2. Dashboard & Telemetry Endpoints

### `GET /api/dashboard/stats`
Returns live aggregate inspection metrics calculated directly from database records.

**Response `200 OK`**:
```json
{
  "total_inspections": 128,
  "accepted_count": 98,
  "defective_count": 22,
  "review_required_count": 8,
  "defect_percentage": 17.2,
  "manual_review_percentage": 6.3,
  "avg_inference_time_ms": 34.6
}
```

### `GET /api/dashboard/trends?days=7`
Aggregates daily throughput counts for accepted, defective, and review-required parts.

**Parameters**:
- `days` (query integer, default: 7, range: 1 to 90)

### `GET /api/dashboard/defect-distribution`
Calculates percentage and frequency counts across supported defect categories.

---

## 3. Inspection Operations

### `POST /api/inspections`
Uploads a product image, executes AI inference, generates annotated defect overlays, and stores the inspection record.

**Request**: `multipart/form-data`
- `file`: Image binary (`JPG`, `JPEG`, or `PNG`, max 10 MB)
- `product_id`: (optional string) Production lot or serial barcode
- `notes`: (optional string) Inspector or line comments

**Response `201 Created`**:
```json
{
  "id": "e4c5d312-349f-43b2-9a08-1123456789ab",
  "original_filename": "part_bracket.png",
  "stored_filename": "9b12c8...png",
  "annotated_filename": "annotated_9b12c8...png",
  "product_id": "LOT-2026-A101",
  "status": "DEFECTIVE",
  "defect_type": "Scratches",
  "confidence_score": 0.884,
  "model_name": "PatchAnomaly-ResNet-CV",
  "model_version": "2.1.0",
  "inference_duration_ms": 32.4,
  "manual_review_required": false,
  "inspection_notes": "Surface check",
  "defect_regions": [
    {
      "x": 120,
      "y": 130,
      "width": 160,
      "height": 130,
      "label": "Scratches",
      "confidence": 0.912
    }
  ],
  "created_at": "2026-10-20T15:20:00Z",
  "original_image_url": "/api/images/original/9b12c8...png",
  "annotated_image_url": "/api/images/annotated/annotated_9b12c8...png"
}
```

### `GET /api/inspections`
Searchable and filterable pagination endpoint with optional CSV download.

**Parameters**:
- `search`: Query text matched against filename, product ID, and notes
- `status`: Filter by `ACCEPTED`, `DEFECTIVE`, or `REVIEW_REQUIRED`
- `defect_type`: Filter by defect category
- `date_from`: ISO date string (`YYYY-MM-DD`)
- `date_to`: ISO date string (`YYYY-MM-DD`)
- `page`: Page index (default: 1)
- `page_size`: Number of records per page (default: 10, max: 100)
- `export_csv`: Set to `true` to receive an `attachment; filename=inspection_history_export.csv`

### `GET /api/inspections/{id}`
Retrieves single inspection record by UUID.

### `DELETE /api/inspections/{id}`
Deletes the record from SQLite and unlinks original and annotated files from storage.

### `GET /api/inspections/{id}/report`
Returns structured certificate payload formatted for industrial quality assurance compliance.

---

## 4. AI Engine Configuration

### `GET /api/models/status`
Returns active AI model runtime telemetry, supported taxonomy, and current decision thresholds.

### `POST /api/models/thresholds?defect_threshold=0.50&review_threshold=0.65`
Dynamically adjusts acceptance and review confidence thresholds at runtime without restarting the server.
