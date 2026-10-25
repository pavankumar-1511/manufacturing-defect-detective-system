import io
from fastapi import status

def test_health_check(client):
    response = client.get("/api/health")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] == "healthy"
    assert "service" in data
    assert "version" in data

def test_dashboard_stats_empty_or_seeded(client):
    response = client.get("/api/dashboard/stats")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "total_inspections" in data
    assert "accepted_count" in data
    assert "defective_count" in data
    assert "defect_percentage" in data

def test_dashboard_trends(client):
    response = client.get("/api/dashboard/trends?days=7")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 7
    assert "date" in data[0]
    assert "total" in data[0]

def test_defect_distribution(client):
    response = client.get("/api/dashboard/defect-distribution")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    categories = [item["category"] for item in data]
    assert "Scratches" in categories
    assert "Cracks" in categories

def test_model_status(client):
    response = client.get("/api/models/status")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "name" in data
    assert "version" in data
    assert "status" in data
    assert "supported_defect_types" in data
    assert len(data["supported_defect_types"]) >= 4

def test_upload_valid_image(client, sample_defective_image_bytes):
    response = client.post(
        "/api/inspections",
        files={"file": ("test_part.png", sample_defective_image_bytes, "image/png")},
        data={"product_id": "TEST-PROD-001", "notes": "Quality audit sample"}
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["product_id"] == "TEST-PROD-001"
    assert data["status"] in ["ACCEPTED", "DEFECTIVE", "REVIEW_REQUIRED"]
    assert "id" in data
    assert "original_image_url" in data
    assert data["confidence_score"] is not None
    assert data["inference_duration_ms"] > 0

    # Retrieve by ID
    get_res = client.get(f"/api/inspections/{data['id']}")
    assert get_res.status_code == status.HTTP_200_OK
    assert get_res.json()["id"] == data["id"]

    # Retrieve printable report
    report_res = client.get(f"/api/inspections/{data['id']}/report")
    assert report_res.status_code == status.HTTP_200_OK
    report_data = report_res.json()
    assert report_data["inspection_id"] == data["id"]
    assert "quality_verdict" in report_data

def test_upload_corrupted_image(client):
    corrupted_data = b"This is clearly not a valid JPEG or PNG header"
    response = client.post(
        "/api/inspections",
        files={"file": ("corrupt.png", corrupted_data, "image/png")},
        data={"product_id": "BAD-001"}
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Corrupted or invalid image" in response.json()["detail"]

def test_upload_invalid_extension(client):
    response = client.post(
        "/api/inspections",
        files={"file": ("script.sh", b"echo hello", "text/x-sh")},
        data={"product_id": "HACK-001"}
    )
    assert response.status_code == status.HTTP_415_UNSUPPORTED_MEDIA_TYPE

def test_inspections_pagination_and_filter(client, sample_clean_image_bytes):
    # Upload clean image
    client.post(
        "/api/inspections",
        files={"file": ("clean_item.png", sample_clean_image_bytes, "image/png")},
        data={"product_id": "CLEAN-999"}
    )

    response = client.get("/api/inspections?search=CLEAN-999&page=1&page_size=10")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["total"] >= 1
    assert any(item["product_id"] == "CLEAN-999" for item in data["items"])

def test_csv_export(client):
    response = client.get("/api/inspections?export_csv=true")
    assert response.status_code == status.HTTP_200_OK
    assert "text/csv" in response.headers.get("content-type", "")
    assert "Inspection ID" in response.text

def test_thresholds_update(client):
    response = client.post("/api/models/thresholds?defect_threshold=0.45&review_threshold=0.70")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["defect_confidence_threshold"] == 0.45
    assert data["review_threshold"] == 0.70

def test_delete_inspection(client, sample_clean_image_bytes):
    create_res = client.post(
        "/api/inspections",
        files={"file": ("to_delete.png", sample_clean_image_bytes, "image/png")},
        data={"product_id": "DEL-123"}
    )
    ins_id = create_res.json()["id"]

    del_res = client.delete(f"/api/inspections/{ins_id}")
    assert del_res.status_code == status.HTTP_200_OK

    # Verify deleted
    get_res = client.get(f"/api/inspections/{ins_id}")
    assert get_res.status_code == status.HTTP_404_NOT_FOUND
