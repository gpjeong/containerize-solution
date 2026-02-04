"""API endpoints for Dockerfile generation"""
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse, Response
from typing import Dict
from uuid import uuid4
import logging

from app.models.schemas import (
    GenerateRequest,
    GenerateResponse,
    AnalyzeResponse,
    UploadResponse,
    PythonConfig,
    NodeJSConfig,
    JavaConfig,
    ProjectInfo
)
from app.utils.security import validate_upload
from app.utils.file_handler import upload_manager
from app.services.file_analyzer import file_analyzer
from app.services.dockerfile_generator import dockerfile_generator

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/upload/java", response_model=UploadResponse)
async def upload_java_artifact(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None
):
    """
    Upload JAR/WAR file for analysis

    - Validates file type and size
    - Analyzes JAR structure
    - Returns project info and session ID
    """
    try:
        # Validate upload
        await validate_upload(file)

        # Save file
        session_id, file_path = await upload_manager.save_upload(file)

        # Get file size
        file_size = file_path.stat().st_size

        # Analyze JAR file
        project_info = await file_analyzer.analyze_java_artifact(file_path)

        logger.info(f"Uploaded and analyzed Java artifact: {file.filename}")

        return UploadResponse(
            session_id=session_id,
            filename=file.filename,
            size=file_size,
            project_info=project_info
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to upload Java artifact: {e}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.post("/analyze/python", response_model=AnalyzeResponse)
async def analyze_python_config(config: PythonConfig):
    """
    Analyze Python project from configuration

    - Validates dependencies format
    - Detects framework and server
    - Returns analysis results
    """
    try:
        # Analyze Python configuration
        project_info = await file_analyzer.analyze_python_config(
            requirements_content=config.requirements_content,
            framework=config.framework
        )

        # Suggestions based on analysis
        suggestions = {}
        server = project_info.metadata.get("server")
        if server:
            suggestions["server"] = f"Recommended server: {server}"

        logger.info(f"Analyzed Python project: {config.framework}")

        return AnalyzeResponse(
            project_info=project_info,
            suggestions=suggestions
        )

    except Exception as e:
        logger.error(f"Failed to analyze Python config: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.post("/analyze/nodejs", response_model=AnalyzeResponse)
async def analyze_nodejs_config(config: NodeJSConfig):
    """
    Analyze Node.js project from configuration

    - Parses package.json
    - Detects framework and package manager
    - Returns analysis results
    """
    try:
        # Analyze Node.js configuration
        project_info = await file_analyzer.analyze_nodejs_config(
            package_json=config.package_json,
            framework=config.framework
        )

        # Suggestions based on analysis
        suggestions = {}
        package_manager = project_info.metadata.get("package_manager")
        if package_manager:
            suggestions["package_manager"] = f"Detected package manager: {package_manager}"

        build_cmd = project_info.metadata.get("build_command")
        if build_cmd:
            suggestions["build_command"] = f"Build command: {build_cmd}"

        logger.info(f"Analyzed Node.js project: {config.framework}")

        return AnalyzeResponse(
            project_info=project_info,
            suggestions=suggestions
        )

    except Exception as e:
        logger.error(f"Failed to analyze Node.js config: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.post("/generate", response_model=GenerateResponse)
async def generate_dockerfile(request: GenerateRequest):
    """
    Generate Dockerfile from project info and user config

    - Validates all inputs
    - Calls generator service
    - Returns Dockerfile content and metadata
    """
    try:
        # Use provided project_info or create minimal one from config
        project_info = request.project_info
        if not project_info:
            # Create minimal project info from config
            config = request.config
            project_info = ProjectInfo(
                language=config.get("language"),
                framework=config.get("framework"),
                detected_version=config.get("runtime_version")
            )

        # Generate Dockerfile
        dockerfile_content = await dockerfile_generator.generate(
            project_info=project_info,
            user_config=request.config
        )

        # Generate or use existing session ID
        session_id = str(uuid4())

        # Save Dockerfile to session
        await upload_manager.save_dockerfile(session_id, dockerfile_content)

        logger.info(f"Generated Dockerfile for {project_info.language}/{project_info.framework}")

        return GenerateResponse(
            dockerfile=dockerfile_content,
            session_id=session_id,
            metadata={
                "language": project_info.language,
                "framework": project_info.framework,
                "template": f"{project_info.language}/{project_info.framework}"
            }
        )

    except Exception as e:
        logger.error(f"Failed to generate Dockerfile: {e}")
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")


@router.get("/download/{session_id}")
async def download_dockerfile(session_id: str):
    """
    Download generated Dockerfile

    - Returns file response with proper headers
    """
    try:
        # Check if session exists
        if not upload_manager.session_exists(session_id):
            raise HTTPException(status_code=404, detail="Session not found or expired")

        # Get Dockerfile path
        dockerfile_path = upload_manager.get_session_dir(session_id) / "Dockerfile"

        if not dockerfile_path.exists():
            raise HTTPException(status_code=404, detail="Dockerfile not found")

        logger.info(f"Downloading Dockerfile from session {session_id}")

        # Return file for download
        return FileResponse(
            path=str(dockerfile_path),
            media_type="text/plain",
            filename="Dockerfile",
            headers={
                "Content-Disposition": "attachment; filename=Dockerfile"
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to download Dockerfile: {e}")
        raise HTTPException(status_code=500, detail=f"Download failed: {str(e)}")


@router.get("/templates")
async def list_templates():
    """
    List available Dockerfile templates

    - Returns all supported languages and frameworks
    """
    return {
        "templates": {
            "python": ["fastapi", "flask", "django"],
            "nodejs": ["express", "nestjs", "nextjs"],
            "java": ["spring-boot"]
        }
    }
