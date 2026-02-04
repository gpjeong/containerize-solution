"""FastAPI application entry point"""
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import time

from app.config import ALLOWED_ORIGINS, LOG_LEVEL, FRONTEND_DIR
from app.api import endpoints

# Configure logging
logging.basicConfig(
    level=LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="WebApp Dockerfile Generator",
    description="Automatically generate optimized Dockerfiles for web services",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all HTTP requests with timing"""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time

    logger.info(
        f"{request.method} {request.url.path} "
        f"status={response.status_code} "
        f"duration={process_time:.2f}s"
    )

    return response


# Include API routes
app.include_router(endpoints.router, prefix="/api", tags=["api"])


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "dockerfile-generator"}


# Serve frontend static files
try:
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")
    logger.info(f"Mounted static files from {FRONTEND_DIR}")
except RuntimeError:
    logger.warning(f"Frontend directory not found: {FRONTEND_DIR}")


# Serve index.html at root
@app.get("/")
async def read_root():
    """Serve the frontend application"""
    index_file = FRONTEND_DIR / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return {"message": "Dockerfile Generator API", "docs": "/api/docs"}


@app.on_event("startup")
async def startup_event():
    """Run on application startup"""
    logger.info("Starting Dockerfile Generator application")


@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown"""
    logger.info("Shutting down Dockerfile Generator application")
