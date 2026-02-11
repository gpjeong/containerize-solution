"""Application configuration"""
from pathlib import Path
import os

# Base paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# In Docker, paths are different
if os.path.exists("/app/frontend"):
    # Docker environment
    UPLOAD_DIR = Path("/app/uploads")
    TEMPLATE_DIR = Path("/app/app/templates")
    FRONTEND_DIR = Path("/app/frontend")
    STATIC_DIR = Path("/app/frontend/static")
else:
    # Local development
    UPLOAD_DIR = BASE_DIR / "uploads"
    TEMPLATE_DIR = BASE_DIR / "backend" / "app" / "templates"
    FRONTEND_DIR = BASE_DIR / "frontend"
    STATIC_DIR = BASE_DIR / "frontend" / "static"

# File upload settings
MAX_UPLOAD_SIZE = 500 * 1024 * 1024  # 500 MB
ALLOWED_EXTENSIONS = {".jar", ".war"}
ALLOWED_CONTENT_TYPES = ["application/java-archive", "application/x-java-archive"]

# Session settings
SESSION_CLEANUP_DELAY = 3600  # 1 hour in seconds

# CORS settings
ALLOWED_ORIGINS = [
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "http://localhost:4000",
    "http://127.0.0.1:4000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

# Logging
LOG_LEVEL = "DEBUG"
