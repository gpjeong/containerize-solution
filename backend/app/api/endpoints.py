"""API endpoints for Dockerfile generation"""
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks, Body
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
    ProjectInfo,
    JenkinsBuildRequest,
    JenkinsBuildResponse,
    JenkinsJobCheckRequest,
    JenkinsJobCheckResponse,
    JenkinsJobCreateRequest,
    JenkinsJobCreateResponse,
    HarborProjectCheckRequest,
    HarborProjectCheckResponse,
    HarborProjectCreateRequest,
    HarborProjectCreateResponse
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


@router.post("/preview/pipeline")
async def preview_pipeline_script(request: JenkinsBuildRequest):
    """
    Preview Jenkins Pipeline script without triggering build

    Generates the Pipeline script that would be used for Jenkins build
    Returns the Groovy script for preview/editing
    """
    try:
        from app.services.pipeline_generator import pipeline_generator

        logger.info(f"Generating pipeline preview for {request.config.get('language')}")

        # Generate Dockerfile
        project_info = ProjectInfo(
            language=request.config.get("language"),
            framework=request.config.get("framework", "generic"),
            detected_version=request.config.get("runtime_version")
        )

        dockerfile_content = await dockerfile_generator.generate(
            project_info=project_info,
            user_config=request.config
        )

        # Generate Pipeline script for preview (with readable Dockerfile)
        # Use Kubernetes-compatible pipeline if requested
        if request.use_kubernetes and request.use_kaniko:
            # Kubernetes with Kaniko (no privileged mode)
            pipeline_script = pipeline_generator.generate_k8s_kaniko_pipeline_script_for_preview(
                git_url=request.git_url,
                git_branch=request.git_branch,
                git_credential_id=request.git_credential_id,
                dockerfile_content=dockerfile_content,
                image_name=request.image_name,
                image_tag=request.image_tag,
                registry_url=request.harbor_url,
                registry_credential_id=request.harbor_credential_id
            )
        elif request.use_kubernetes:
            # Kubernetes with Docker-in-Docker
            pipeline_script = pipeline_generator.generate_k8s_pipeline_script_for_preview(
                git_url=request.git_url,
                git_branch=request.git_branch,
                git_credential_id=request.git_credential_id,
                dockerfile_content=dockerfile_content,
                image_name=request.image_name,
                image_tag=request.image_tag
            )
        else:
            # Standard pipeline
            pipeline_script = pipeline_generator.generate_pipeline_script_for_preview(
                git_url=request.git_url,
                git_branch=request.git_branch,
                git_credential_id=request.git_credential_id,
                dockerfile_content=dockerfile_content,
                image_name=request.image_name,
                image_tag=request.image_tag
            )

        return {
            "pipeline_script": pipeline_script,
            "dockerfile": dockerfile_content
        }

    except Exception as e:
        logger.error(f"Failed to generate pipeline preview: {e}")
        raise HTTPException(status_code=500, detail=f"Preview generation failed: {str(e)}")


@router.post("/build/jenkins/custom", response_model=JenkinsBuildResponse)
async def trigger_jenkins_build_custom(request: Dict):
    """
    Trigger Jenkins build with custom/edited Pipeline script

    This endpoint allows users to build with an edited pipeline script
    from the preview modal
    """
    try:
        from app.services.jenkins_client import create_jenkins_client

        jenkins_url = request.get("jenkins_url")
        jenkins_job = request.get("jenkins_job")
        jenkins_token = request.get("jenkins_token")
        jenkins_username = request.get("jenkins_username", "admin")
        pipeline_script = request.get("pipeline_script")

        logger.info(f"Custom Jenkins build request for job: {jenkins_job}")

        # Create Jenkins client
        jenkins_client = create_jenkins_client(
            jenkins_url=jenkins_url,
            username=jenkins_username,
            api_token=jenkins_token
        )

        # Update Pipeline script and trigger build
        build_info = jenkins_client.update_and_build(
            job_name=jenkins_job,
            pipeline_script=pipeline_script
        )

        logger.info(f"Custom Jenkins build triggered. Build Number: {build_info.get('build_number')}")

        return JenkinsBuildResponse(
            job_name=build_info["job_name"],
            queue_id=build_info.get("queue_id"),
            queue_url=build_info["queue_url"],
            job_url=build_info["job_url"],
            build_number=build_info.get("build_number"),
            build_url=build_info.get("build_url"),
            status=build_info["status"],
            message="Jenkins build triggered with custom pipeline"
        )

    except Exception as e:
        logger.error(f"Failed to trigger custom Jenkins build: {e}")
        raise HTTPException(status_code=500, detail=f"Jenkins build failed: {str(e)}")


@router.post("/build/jenkins", response_model=JenkinsBuildResponse)
async def trigger_jenkins_build(request: JenkinsBuildRequest):
    """
    Trigger Jenkins build with auto-generated Pipeline script

    Workflow:
    1. Generate Dockerfile from config
    2. Generate Jenkins Pipeline script
    3. Update Jenkins job with new Pipeline script
    4. Trigger build

    - **jenkins_url**: Jenkins server URL
    - **jenkins_job**: Pipeline job name (must exist)
    - **jenkins_token**: Jenkins API token
    - **git_url**: Git repository URL
    - **config**: Dockerfile generation config
    - **image_name**: Docker image name

    Returns build information including job URL and queue ID
    """
    try:
        # Import here to avoid circular imports
        from app.services.jenkins_client import create_jenkins_client
        from app.services.pipeline_generator import pipeline_generator

        logger.info(f"Jenkins build request for job: {request.jenkins_job}")

        # 1. Generate Dockerfile
        # Create minimal project info from config
        project_info = ProjectInfo(
            language=request.config.get("language"),
            framework=request.config.get("framework", "generic"),
            detected_version=request.config.get("runtime_version")
        )

        dockerfile_content = await dockerfile_generator.generate(
            project_info=project_info,
            user_config=request.config
        )

        logger.info(f"Generated Dockerfile for {project_info.language}/{project_info.framework}")

        # 2. Generate Pipeline script (Kubernetes or standard)
        if request.use_kubernetes and request.use_kaniko:
            # Kubernetes with Kaniko (no privileged mode)
            pipeline_script = pipeline_generator.generate_k8s_kaniko_pipeline_script(
                git_url=request.git_url,
                git_branch=request.git_branch,
                git_credential_id=request.git_credential_id,
                dockerfile_content=dockerfile_content,
                image_name=request.image_name,
                image_tag=request.image_tag,
                registry_url=request.harbor_url,
                registry_credential_id=request.harbor_credential_id
            )
        elif request.use_kubernetes:
            # Kubernetes with Docker-in-Docker
            pipeline_script = pipeline_generator.generate_k8s_pipeline_script(
                git_url=request.git_url,
                git_branch=request.git_branch,
                git_credential_id=request.git_credential_id,
                dockerfile_content=dockerfile_content,
                image_name=request.image_name,
                image_tag=request.image_tag
            )
        else:
            # Standard pipeline
            pipeline_script = pipeline_generator.generate_pipeline_script(
                git_url=request.git_url,
                git_branch=request.git_branch,
                git_credential_id=request.git_credential_id,
                dockerfile_content=dockerfile_content,
                image_name=request.image_name,
                image_tag=request.image_tag
            )

        logger.info(f"Generated Pipeline script for image: {request.image_name}:{request.image_tag}")

        # 3. Create Jenkins client and update + trigger build
        jenkins_client = create_jenkins_client(
            jenkins_url=request.jenkins_url,
            username=request.jenkins_username,
            api_token=request.jenkins_token
        )

        # Update Pipeline script and trigger build
        build_info = jenkins_client.update_and_build(
            job_name=request.jenkins_job,
            pipeline_script=pipeline_script
        )

        logger.info(f"Jenkins build triggered successfully. Queue ID: {build_info.get('queue_id')}, Build Number: {build_info.get('build_number')}")

        return JenkinsBuildResponse(
            job_name=build_info["job_name"],
            queue_id=build_info.get("queue_id"),
            queue_url=build_info["queue_url"],
            job_url=build_info["job_url"],
            build_number=build_info.get("build_number"),
            build_url=build_info.get("build_url"),
            status=build_info["status"],
            message="Jenkins build triggered successfully"
        )

    except ValueError as e:
        logger.error(f"Invalid configuration: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to trigger Jenkins build: {e}")
        raise HTTPException(status_code=500, detail=f"Jenkins build failed: {str(e)}")


# ============================================================
# Setup Endpoints - Jenkins Job & Harbor Project Creation
# ============================================================

@router.post("/setup/jenkins/check-job")
async def check_jenkins_job(
    jenkins_url: str = Body(...),
    jenkins_username: str = Body(...),
    jenkins_token: str = Body(...),
    job_name: str = Body(...)
):
    """
    Check if Jenkins job exists

    Request Body:
    - jenkins_url: Jenkins server URL
    - jenkins_username: Jenkins admin username
    - jenkins_token: Jenkins API token
    - job_name: Job name to check

    Response:
    - exists: bool
    - job_name: str
    - job_url: str (if exists)
    """
    try:
        from app.services.jenkins_client import create_jenkins_client

        jenkins_client = create_jenkins_client(
            jenkins_url=jenkins_url,
            username=jenkins_username,
            api_token=jenkins_token
        )

        exists = jenkins_client.check_job_exists(job_name)

        response = {
            "exists": exists,
            "job_name": job_name
        }

        if exists:
            response["job_url"] = f"{jenkins_url}/job/{job_name}"

        return response

    except Exception as e:
        logger.error(f"Failed to check Jenkins job: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/setup/jenkins/create-job")
async def create_jenkins_job(
    jenkins_url: str = Body(...),
    jenkins_username: str = Body(...),
    jenkins_token: str = Body(...),
    job_name: str = Body(...),
    description: str = Body("Auto-generated Pipeline job for containerization")
):
    """
    Create new Jenkins Pipeline job

    Request Body:
    - jenkins_url: Jenkins server URL
    - jenkins_username: Jenkins admin username
    - jenkins_token: Jenkins API token
    - job_name: Job name to create
    - description: Job description (optional)

    Response:
    - job_name: str
    - job_url: str
    - status: str
    - message: str
    """
    try:
        from app.services.jenkins_client import create_jenkins_client

        jenkins_client = create_jenkins_client(
            jenkins_url=jenkins_url,
            username=jenkins_username,
            api_token=jenkins_token
        )

        # Check if already exists
        if jenkins_client.check_job_exists(job_name):
            return {
                "job_name": job_name,
                "job_url": f"{jenkins_url}/job/{job_name}",
                "status": "already_exists",
                "message": f"Job '{job_name}' already exists"
            }

        # Create job
        result = jenkins_client.create_job(job_name, description)
        result["message"] = f"Job '{job_name}' created successfully"

        return result

    except ValueError as e:
        logger.error(f"Job creation failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create Jenkins job: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/setup/harbor/check-project")
async def check_harbor_project(
    harbor_url: str = Body(...),
    harbor_username: str = Body(...),
    harbor_password: str = Body(...),
    project_name: str = Body(...)
):
    """
    Check if Harbor project exists

    Request Body:
    - harbor_url: Harbor server URL (e.g., https://harbor.example.com)
    - harbor_username: Harbor admin username
    - harbor_password: Harbor admin password
    - project_name: Project name to check

    Response:
    - exists: bool
    - project_name: str
    - project_url: str (if exists)
    """
    try:
        from app.services.harbor_client import HarborClient

        # Remove project name from harbor_url if present
        base_harbor_url = harbor_url.split('/')[0:3]  # https://harbor.example.com
        base_harbor_url = '/'.join(base_harbor_url)

        harbor_client = HarborClient(
            harbor_url=base_harbor_url,
            username=harbor_username,
            password=harbor_password
        )

        exists = harbor_client.check_project_exists(project_name)

        response = {
            "exists": exists,
            "project_name": project_name
        }

        if exists:
            response["project_url"] = f"{base_harbor_url}/harbor/projects"

        return response

    except Exception as e:
        logger.error(f"Failed to check Harbor project: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/setup/harbor/create-project")
async def create_harbor_project(
    harbor_url: str = Body(...),
    harbor_username: str = Body(...),
    harbor_password: str = Body(...),
    project_name: str = Body(...),
    public: bool = Body(False),
    enable_content_trust: bool = Body(False),
    auto_scan: bool = Body(True),
    severity: str = Body("high"),
    prevent_vul: bool = Body(False)
):
    """
    Create new Harbor project

    Request Body:
    - harbor_url: Harbor server URL
    - harbor_username: Harbor admin username
    - harbor_password: Harbor admin password
    - project_name: Project name to create
    - public: Make project public (default: False)
    - enable_content_trust: Enable content trust (default: False)
    - auto_scan: Auto scan images (default: True)
    - severity: Vulnerability severity (critical/high/medium/low)
    - prevent_vul: Prevent vulnerable images (default: False)

    Response:
    - project_name: str
    - project_url: str
    - status: str
    - message: str
    - settings: dict
    """
    try:
        from app.services.harbor_client import HarborClient

        # Remove project name from harbor_url if present
        base_harbor_url = harbor_url.split('/')[0:3]
        base_harbor_url = '/'.join(base_harbor_url)

        harbor_client = HarborClient(
            harbor_url=base_harbor_url,
            username=harbor_username,
            password=harbor_password
        )

        # Check if already exists
        if harbor_client.check_project_exists(project_name):
            return {
                "project_name": project_name,
                "project_url": f"{base_harbor_url}/harbor/projects",
                "status": "already_exists",
                "message": f"Project '{project_name}' already exists"
            }

        # Create project
        result = harbor_client.create_project(
            project_name=project_name,
            public=public,
            enable_content_trust=enable_content_trust,
            auto_scan=auto_scan,
            severity=severity,
            prevent_vul=prevent_vul
        )

        return {
            "project_name": project_name,
            "project_url": f"{base_harbor_url}/harbor/projects",
            "status": "created",
            "message": f"Project '{project_name}' created successfully",
            "settings": {
                "public": public,
                "auto_scan": auto_scan,
                "severity": severity,
                "content_trust": enable_content_trust,
                "prevent_vulnerable": prevent_vul
            }
        }

    except ValueError as e:
        logger.error(f"Project creation failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create Harbor project: {e}")
        raise HTTPException(status_code=500, detail=str(e))
