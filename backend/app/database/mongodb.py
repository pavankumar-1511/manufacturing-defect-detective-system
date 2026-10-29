import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone

try:
    import dns.resolver
    dns.resolver.default_resolver = dns.resolver.Resolver()
    dns.resolver.default_resolver.nameservers = ['8.8.8.8', '1.1.1.1']
except Exception:
    pass

from pymongo import MongoClient, DESCENDING
from app.config import settings

logger = logging.getLogger("mongodb")

_mongo_client: Optional[MongoClient] = None

class MongoInspectionRecord:
    """Wrapper to make MongoDB documents look and behave like SQLAlchemy Inspection objects."""
    def __init__(self, doc: Dict[str, Any]):
        self.id = doc.get("id") or str(doc.get("_id", ""))
        self.original_filename = doc.get("original_filename", "")
        self.stored_filename = doc.get("stored_filename", "")
        self.annotated_filename = doc.get("annotated_filename")
        self.product_id = doc.get("product_id")
        self.status = doc.get("status", "ACCEPTED")
        self.defect_type = doc.get("defect_type")
        self.confidence_score = doc.get("confidence_score")
        self.model_name = doc.get("model_name", "AI-Defect-Detection")
        self.model_version = doc.get("model_version", "2.1.0")
        self.inference_duration_ms = float(doc.get("inference_duration_ms", 0.0))
        self.manual_review_required = bool(doc.get("manual_review_required", False))
        self.inspection_notes = doc.get("inspection_notes")
        self.defect_regions = doc.get("defect_regions")
        
        created = doc.get("created_at")
        if isinstance(created, str):
            try:
                self.created_at = datetime.fromisoformat(created)
            except Exception:
                self.created_at = datetime.now(timezone.utc)
        elif isinstance(created, datetime):
            self.created_at = created
        else:
            self.created_at = datetime.now(timezone.utc)

    def to_dict(self) -> Dict[str, Any]:
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

def is_mongo_enabled() -> bool:
    """Returns True if DATABASE_URL points to MongoDB Atlas or local MongoDB."""
    url = settings.DATABASE_URL.strip().lower()
    return url.startswith("mongodb://") or url.startswith("mongodb+srv://")

def get_mongo_client() -> MongoClient:
    global _mongo_client
    if _mongo_client is None:
        logger.info("Initializing MongoDB Atlas client...")
        _mongo_client = MongoClient(
            settings.DATABASE_URL,
            serverSelectionTimeoutMS=8000,
            connectTimeoutMS=8000
        )
    return _mongo_client

def get_mongo_db():
    client = get_mongo_client()
    db_name = "defect_detection"
    try:
        from urllib.parse import urlparse
        parsed = urlparse(settings.DATABASE_URL)
        if parsed.path and len(parsed.path) > 1:
            clean_path = parsed.path.lstrip("/").split("?")[0]
            if clean_path:
                db_name = clean_path
    except Exception:
        pass
    return client[db_name]

def get_mongo_inspections_collection():
    db = get_mongo_db()
    col = db["inspections"]
    return col

def init_mongo_db():
    """Initializes indexes and verifies MongoDB Atlas connection."""
    try:
        col = get_mongo_inspections_collection()
        col.create_index("id", unique=True)
        col.create_index([("created_at", DESCENDING)])
        col.create_index("status")
        col.create_index("defect_type")
        col.create_index("product_id")
        logger.info("MongoDB Atlas indexes verified and initialized.")
    except Exception as e:
        logger.error(f"Failed to initialize MongoDB Atlas: {e}")
        raise e

def ping_mongo() -> bool:
    try:
        client = get_mongo_client()
        res = client.admin.command("ping")
        return res.get("ok") == 1
    except Exception as e:
        logger.warning(f"MongoDB ping failed: {e}")
        return False
