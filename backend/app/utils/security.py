"""Security utilities for file validation"""
from fastapi import UploadFile, HTTPException
import magic
from werkzeug.utils import secure_filename

from app.config import MAX_UPLOAD_SIZE, ALLOWED_EXTENSIONS, ALLOWED_CONTENT_TYPES


async def validate_upload(file: UploadFile) -> bool:
    """
    Multi-layer validation for uploaded files

    1. Extension check
    2. Content-Type header validation
    3. Magic number verification
    4. Size check

    Args:
        file: The uploaded file

    Returns:
        bool: True if validation passes

    Raises:
        HTTPException: If validation fails
    """
    # Layer 1: Extension check
    if not any(file.filename.lower().endswith(ext) for ext in ALLOWED_EXTENSIONS):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed extensions: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    # Layer 2: Content-Type header
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid content type: {file.content_type}"
        )

    # Layer 3: Magic number verification (first bytes)
    header = await file.read(4)
    await file.seek(0)  # Reset file pointer

    # JAR/WAR files are ZIP archives (PK\x03\x04)
    if header != b'PK\x03\x04':
        raise HTTPException(
            status_code=400,
            detail="File is not a valid JAR/WAR archive"
        )

    # Layer 4: File size check (read in chunks to avoid loading entire file)
    file.file.seek(0, 2)  # Seek to end
    file_size = file.file.tell()
    file.file.seek(0)  # Reset to beginning

    if file_size > MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size: {MAX_UPLOAD_SIZE / (1024*1024):.0f}MB"
        )

    return True


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to prevent path traversal attacks

    Args:
        filename: Original filename

    Returns:
        str: Sanitized filename
    """
    return secure_filename(filename)


async def validate_jar_structure(file_path: str) -> bool:
    """
    Validate JAR file structure

    Args:
        file_path: Path to JAR file

    Returns:
        bool: True if valid JAR structure
    """
    import zipfile

    try:
        with zipfile.ZipFile(file_path, 'r') as jar:
            # Check if it's a valid ZIP archive
            if jar.testzip() is not None:
                return False

            # Check for MANIFEST.MF (required for JAR files)
            files = jar.namelist()
            return 'META-INF/MANIFEST.MF' in files

    except zipfile.BadZipFile:
        return False
    except Exception:
        return False
