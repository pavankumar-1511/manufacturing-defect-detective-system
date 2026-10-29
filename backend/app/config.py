from pathlib import Path
from typing import Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    PROJECT_NAME: str = "AI-Based Manufacturing Defect Detection System"
    API_V1_PREFIX: str = "/api"
    
    # Database
    DATABASE_URL: str = "sqlite:///./defect_detection.db"
    
    # Upload directories (relative to backend/)
    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    UPLOAD_DIR: Path = Path(__file__).resolve().parent.parent / "uploads"
    ORIGINAL_UPLOAD_DIR: Path = Path(__file__).resolve().parent.parent / "uploads" / "original"
    ANNOTATED_UPLOAD_DIR: Path = Path(__file__).resolve().parent.parent / "uploads" / "annotated"
    
    # Upload security limits
    MAX_UPLOAD_SIZE_BYTES: int = 10 * 1024 * 1024  # 10 MB
    ALLOWED_EXTENSIONS: set[str] = {".jpg", ".jpeg", ".png"}
    ALLOWED_MIME_TYPES: set[str] = {"image/jpeg", "image/png", "image/jpg"}
    
    # CORS
    CORS_ORIGINS: Union[list[str], str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
    ]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: Union[str, list[str]]) -> list[str]:
        if isinstance(v, str):
            v = v.strip()
            if v == "*":
                return ["*"]
            if v.startswith("[") and v.endswith("]"):
                try:
                    import json
                    return json.loads(v)
                except Exception:
                    pass
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v
    
    # AI Inference settings
    MODEL_NAME: str = "PatchAnomaly-ResNet-CV"
    MODEL_VERSION: str = "2.1.0"
    DEFECT_CONFIDENCE_THRESHOLD: float = 0.50
    REVIEW_REQUIRED_THRESHOLD: float = 0.65
    FORCE_BASELINE: bool = False

settings = Settings()

# Ensure directories exist
settings.ORIGINAL_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
settings.ANNOTATED_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
