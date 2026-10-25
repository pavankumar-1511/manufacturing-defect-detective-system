import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, Boolean, Text, DateTime
from app.database.session import Base

class Inspection(Base):
    __tablename__ = "inspections"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    original_filename = Column(String(255), nullable=False)
    stored_filename = Column(String(255), nullable=False)
    annotated_filename = Column(String(255), nullable=True)
    product_id = Column(String(100), nullable=True, index=True)
    status = Column(String(50), nullable=False, index=True)  # ACCEPTED, DEFECTIVE, REVIEW_REQUIRED
    defect_type = Column(String(100), nullable=True, index=True)  # Scratches, Cracks, Dents, Surface Abnormalities, None
    confidence_score = Column(Float, nullable=True)
    model_name = Column(String(100), nullable=False)
    model_version = Column(String(50), nullable=False)
    inference_duration_ms = Column(Float, nullable=False, default=0.0)
    manual_review_required = Column(Boolean, nullable=False, default=False)
    inspection_notes = Column(Text, nullable=True)
    defect_regions = Column(Text, nullable=True)  # JSON-encoded array of bounding boxes/regions
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    def to_dict(self):
        return {
            "id": self.id,
            "original_filename": self.original_filename,
            "stored_filename": self.stored_filename,
            "annotated_filename": self.annotated_filename,
            "product_id": self.product_id,
            "status": self.status,
            "defect_type": self.defect_type,
            "confidence_score": self.confidence_score,
            "model_name": self.model_name,
            "model_version": self.model_version,
            "inference_duration_ms": self.inference_duration_ms,
            "manual_review_required": self.manual_review_required,
            "inspection_notes": self.inspection_notes,
            "defect_regions": self.defect_regions,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
