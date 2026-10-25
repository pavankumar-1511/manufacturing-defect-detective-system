import os
import uuid
from pathlib import Path
from fastapi import HTTPException, UploadFile, status
from PIL import Image
import io
from app.config import settings

def sanitize_filename(filename: str) -> str:
    """Sanitize filename to prevent directory traversal attacks."""
    # Strip any directory path components
    basename = os.path.basename(filename)
    # Remove null bytes and path separators
    clean_name = basename.replace("\0", "").replace("/", "").replace("\\", "").strip()
    if not clean_name or clean_name.startswith("."):
        clean_name = f"image_{uuid.uuid4().hex[:8]}.jpg"
    return clean_name

def validate_image_upload(file: UploadFile, content: bytes) -> tuple[str, str]:
    """
    Validates uploaded file size, extension, MIME type, and binary image header.
    Returns: (sanitized_original_filename, safe_stored_filename)
    """
    # Check file size
    if len(content) > settings.MAX_UPLOAD_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds maximum allowed size of {settings.MAX_UPLOAD_SIZE_BYTES // (1024*1024)} MB."
        )

    if len(content) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty."
        )

    # Check extension
    original_filename = sanitize_filename(file.filename or "upload.jpg")
    ext = os.path.splitext(original_filename)[1].lower()
    if ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported file format '{ext}'. Allowed: {', '.join(settings.ALLOWED_EXTENSIONS)}"
        )

    # Validate image data using PIL to prevent polyglot/corrupted files
    try:
        with Image.open(io.BytesIO(content)) as img:
            img.verify()
            format_name = (img.format or "").upper()
            if format_name not in {"JPEG", "JPG", "PNG"}:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"File is not a valid JPEG or PNG image (detected format: {format_name})."
                )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Corrupted or invalid image file: {str(e)}"
        )

    # Generate safe random stored filename
    safe_stored_filename = f"{uuid.uuid4().hex}{ext}"
    return original_filename, safe_stored_filename

def save_uploaded_image(content: bytes, filename: str) -> Path:
    """Safely saves original image to disk."""
    dest_path = settings.ORIGINAL_UPLOAD_DIR / filename
    with open(dest_path, "wb") as f:
        f.write(content)
    return dest_path

def get_safe_file_path(filename: str, folder_type: str = "original") -> Path:
    """
    Safely retrieves the path to a stored image, preventing path traversal.
    """
    safe_name = os.path.basename(filename)
    if folder_type == "annotated":
        target_dir = settings.ANNOTATED_UPLOAD_DIR
    else:
        target_dir = settings.ORIGINAL_UPLOAD_DIR

    resolved = (target_dir / safe_name).resolve()
    # Ensure resolved path is strictly within the allowed directory
    if not str(resolved).startswith(str(target_dir.resolve())):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: invalid file path."
        )
    return resolved
